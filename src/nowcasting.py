# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 11:22:56 2022

@author: Roberto.Rossignoli
"""

import numpy as np
import pandas as pd
import pickle
import datetime as dt

from src import covariance_function
from src import bloomebrg_api

import copy

bbg = bloomebrg_api.Pybbg()
bbg.service_refData()

# %%  Macro timeseries management
def eco_release_str_2_date(x):
    if pd.isna(x):
        return np.nan
    else:
        return dt.datetime.strptime(str(int(x)), "%Y%m%d")


def fix_macro_ts(ts, end_date, ticker):
    # ts = ts.drop_duplicates().droplevel(0,axis=1)#.dropna()
    ts = ts.droplevel(0, axis=1)  # .dropna()
    ts = ts.drop_duplicates()
    # def merge_price_actual_release
    # Data no longer available as actual but still there as price
    ts.loc[
        (ts.ECO_RELEASE_DT == ts.ECO_RELEASE_DT.shift(1)),
        ["ECO_RELEASE_DT", "ACTUAL_RELEASE"]
    ] = np.nan
    ts["ACTUAL_RELEASE"] = ts["ACTUAL_RELEASE"].fillna(ts["PX LAST"])

    # def bfill_eco_relase(ts):
    ts["ECO_RELEASE_DT"] = ts["ECO_RELEASE_DT"].map(
        lambda x: eco_release_str_2_date(x))
    ts_gap = ts["ECO_RELEASE_DT"] - ts.index
    ts["ECO_RELEASE_DT"] = ts["ECO_RELEASE_DT"].fillna(pd.Series(
        index=ts.index,
        data=ts.index + ts_gap.median()))

    ts = ts.set_index("ECO_RELEASE_DT")
    ts.rename(columns={'ACTUAL_RELEASE': ticker}, inplace=True)
    ## Index to DatetimeIndex
    # ts.index = ts.index
    ## Kill future date due to Bloomberg API functioning
    ts = ts.loc[:end_date.strftime("%Y-%m-%d"), :]
    ## Avoid to have two datapoints for the same date
    ts = ts.groupby(ts.index)[ticker].last()
    return ts


def discontinue_ts(ts):
    discontinued_ts = pd.read_excel(
        r'data/Nowcasting_input.xlsx',
        sheet_name="discontinued_ts",
        index_col=0)

    delta_dict = {"M": 22, "W": 5}

    for i in discontinued_ts.index:
        start_t = discontinued_ts.loc[i, "date"] + \
                  delta_dict[discontinued_ts.loc[i, "period"]] * ts.index.freq
        ts.loc[start_t:, i] = np.nan

    return ts


def replace_ts(ts_dict, end_date):
    replacement_ts_info = pd.read_excel(
        r'data/Nowcasting_input.xlsx',
        sheet_name="replace_ts",
        index_col=0)

    replacement_ts = {}
    for i in replacement_ts_info.TickerOld:
        data_i = download_actual_release(
            i,
            end_date,
            frequency=replacement_ts_info[
                replacement_ts_info.TickerOld == i].period_selection.iloc[0],
            api_structure=replacement_ts_info[
                replacement_ts_info.TickerOld == i].api_structure.iloc[0],
        )
        replacement_ts[i] = fix_macro_ts(data_i, end_date, i)

    for i in replacement_ts_info.TickerNew:
        sub_id = replacement_ts_info[
            replacement_ts_info.TickerNew == i].TickerOld.values[0]
        break_date = replacement_ts_info[
            replacement_ts_info.TickerNew == i].Date.values[0]

        ts_dict[i] = pd.concat(
            [replacement_ts[sub_id].loc[:break_date],
             ts_dict[i].loc[break_date:]])
    return ts_dict


def download_actual_release(
        ticker,
        end_date,
        frequency,
        api_structure):
    if api_structure == 1:
        data_i = bbg.bdh(
            ticker,
            ['ACTUAL_RELEASE', 'ECO_RELEASE_DT', 'PX LAST'],
            '19600101',
            end_date,
            periodselection=frequency)
    if api_structure == 2:
        data_i = bbg.bdh(
            ticker,
            ['ACTUAL_RELEASE', 'ECO_RELEASE_DT', 'PX LAST'],
            '19600101',
            end_date,
            periodselection=frequency,
            override={'RELEASE_STAGE_OVERRIDE': 'A'})
    if api_structure == 3:
        data_i_p = bbg.bdh(
            ticker,
            ['ACTUAL_RELEASE', 'ECO_RELEASE_DT', 'PX LAST'],
            '19600101',
            end_date,
            periodselection=frequency,
            override={'RELEASE_STAGE_OVERRIDE': 'P'})
        data_i_f = bbg.bdh(
            ticker,
            ['ACTUAL_RELEASE', 'ECO_RELEASE_DT', 'PX LAST'],
            '19600101',
            end_date,
            periodselection=frequency)
        # override={'RELEASE_STAGE_OVERRIDE': 'F'})
        data_i = pd.concat([data_i_p, data_i_f]).sort_index()
    if data_i.shape[0] == 0:
        print(ticker)
    return data_i


# %%
def main():
    end_date = dt.date.today()

    mapping_info = pd.read_excel(
        r'data/Nowcasting_input.xlsx',
        sheet_name="main_input")
    mapping_info = mapping_info.set_index(['Ticker'])

    data_raw = {}
    for ticker in mapping_info.index:
        data_i = download_actual_release(
            ticker,
            end_date,
            frequency=mapping_info.loc[ticker, "period_selection"],
            api_structure=mapping_info.loc[ticker, "api_structure"])
        data_raw[ticker] = fix_macro_ts(data_i, end_date, ticker)

    data_dict = replace_ts(data_raw, end_date)

    data_adj = copy.deepcopy(data_dict)
    for i in mapping_info.loc[mapping_info.First_diff == 1].index:
        data_adj[i] = data_adj[i].diff(1)

    df_adj = pd.concat(data_adj, axis=1)  # .droplevel(0, axis=1)
    df_adj = df_adj.resample("B").last()
    df_adj = df_adj.reindex(
        df_adj.index.append(
            pd.date_range(start=df_adj.index[-1],
                          end=pd.Timestamp.today() - pd.DateOffset(1, "B"),
                          freq='B')).drop_duplicates()
    )
    df_adj = df_adj.ffill().astype(float)
    df_adj.index.freq = "B"

    ## Manage termination date
    df_adj = discontinue_ts(df_adj)

    weights = {}
    for category in mapping_info.Group.unique():
        data_adj_cat = df_adj.loc[:, mapping_info.Group == category]  # .dropna(axis=1)
        t = data_adj_cat.index[-1]
        weights[category] = {}

        x = data_adj_cat.loc[:t, :]
        x = x.loc[:, ~x.iloc[-1, :].isna()]

        x_std = (x - x.mean()) / x.std()

        k = x.shape[1]
        max_days_lag = 22

        cov_t = pd.DataFrame(
            index=pd.MultiIndex.from_product([range(0, max_days_lag), x.columns]),
            columns=x.columns
        )

        for l in range(0, max_days_lag):
            x_temp = x_std.loc[
                     : t - l * x.index.freq].iloc[::-max_days_lag] \
                .sort_index()  # .dropna()
            # x_temp_cov = Bartlett(x_temp.dropna()).cov.short_run

            x_temp_cov = covariance_function.stambaugh_covariance(
                x_temp.dropna(how="all"))

            cov_t.loc[
                list(zip([l] * k, x_temp_cov.index)),
                x_temp_cov.columns] = x_temp_cov.values

        cov_t_def = cov_t.groupby(level=1, sort=False).mean()

        _, w = np.linalg.eig(cov_t_def)

        w_t = w[:, 0] / sum(w[:, 0])
        weights[category][t] = pd.Series(w_t, index=x_std.columns)

    future_release = bbg.bdp(
        mapping_info.index,
        ['BN_SURVEY_MEDIAN', 'ECO_FUTURE_RELEASE_DATE', "PX LAST"],
        overrides={
            "START_DT": (end_date + dt.timedelta(days=1)).strftime("%Y%m%d")}
    ).T

    future_release["ECO_RELEASE_DATE"] = pd.to_datetime(
        future_release.ECO_FUTURE_RELEASE_DATE).dt.date

    for i in mapping_info.loc[mapping_info.First_diff == 1].index:
        future_release.loc[i, "BN_SURVEY_MEDIAN"] = \
            future_release.loc[i, "BN_SURVEY_MEDIAN"] - \
            future_release.loc[i, "PX LAST"]

    future_release_pivot = future_release.reset_index().pivot(
        index="ECO_RELEASE_DATE",
        columns="index",
        values="BN_SURVEY_MEDIAN"
    ).dropna(how="all")

    future_release_pivot.index = pd.DatetimeIndex(
        future_release_pivot.index)

    future_release_pivot = pd.concat(
        [df_adj.iloc[[-1], :],
         future_release_pivot]).resample("B").last().ffill()

    df_adj_future = pd.concat(
        [df_adj,
         future_release_pivot.resample("B").last()],
    ).drop_duplicates()

    # Save for front end purposes
    pickle.dump(
        {"end_date": end_date,
         "df_adj": df_adj,
         "weights": weights,
         "df_adj_future": df_adj_future},
        open('data/output_nowcast.pkl', 'wb')
    )
