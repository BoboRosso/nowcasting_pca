# -*- coding: utf-8 -*-
"""
Created on Fri Nov  4 11:18:16 2022

@author: Roberto.Rossignoli
"""

import pandas as pd
import numpy as np
from arch.covariance.kernel import Bartlett

''' Paper: https://repository.upenn.edu/cgi/viewcontent.cgi?article=1051&context=fnce_papers '''

#%%

def define_expectations(j, y, expectations, coefficients):
    if j == 0:
        expectations[j] = y.mean()
    else:
        expectations[j] = pd.concat(
            [expectations[j-1],\
             expectations[j-1] @ coefficients[j].drop("const") + \
                coefficients[j].loc["const"]])
    return expectations

            
def define_coefficients(j, x, y, coefficients, mode="OLS"):
    if j > 0:
        if mode == "OLS":
            beta_j = np.linalg.inv(x.T @ x) @ x.T @ y
            beta_j.index = x.columns
            coefficients[j] = beta_j
    return coefficients


def define_residuals(j, x, y, coefficients, residuals):
    if j > 0:
        residuals[j] = y - x @ coefficients[j]
    return residuals

                
def define_covariance(
        j,
        x, 
        y, 
        coefficients,
        residuals,
        expectations,
        covariance,
        mode="sample",
        ):
    if j == 0:
        if mode=="sample":
            covariance[j] = y.cov(ddof=0)
        elif mode=="barlett":
            covariance[j] = Bartlett(y).cov.short_run
    else:
        if mode=="sample":
            sigma_res = residuals[j].cov(ddof=0)
        elif mode=="barlett":
            sigma_res = Bartlett(residuals[j]).cov.short_run
        
        Vj_1_j = coefficients[j].loc[covariance[j-1].index].T @ covariance[j-1]
        
        Vjj = sigma_res + \
                coefficients[j].loc[covariance[j-1].index].T @ \
                 covariance[j-1] @ \
                     coefficients[j].loc[covariance[j-1].index]
        
        covariance[j] = pd.concat(
            [ pd.concat([covariance[j-1], Vj_1_j.T], axis=1), \
              pd.concat([Vj_1_j, Vjj], axis=1)])
        
    return covariance

        
def prepend_ones(x):  
    x.insert(0, "const", 1)
    return x

# data_raw = pd.read_clipboard()
# data = data_raw.set_index('Date')
# data.index = pd.to_datetime(data.index)
# data = data.sort_index(ascending=True)

def stambaugh_covariance(data, covariance_mode="barlett"):

    starting_dates = data.apply(pd.Series.first_valid_index)
    
    # covariance_output = pd.DataFrame(
    #     index=data.columns,
    #     columns=data.columns,
    #     dtype=float)
    # covariance_temp = []
    
    expectations = {}
    covariance = {}
    coefficients = {}
    residuals = {}

    for j, s in enumerate(np.unique(starting_dates.values)):
        y = data.loc[:, starting_dates == s].dropna()
        x = prepend_ones(data.loc[:, starting_dates < s]).loc[s:] if j > 0 else None
        #if i == 0:
        coefficients = define_coefficients(j, x, y, coefficients)
        residuals = define_residuals(j, x, y, coefficients, residuals)
        expectations = define_expectations(j, y, expectations, coefficients)
        covariance = define_covariance(
            j,
            x, 
            y, 
            coefficients,
            residuals,
            expectations,
            covariance,
            mode=covariance_mode,
            )
    
    return covariance[j].loc[data.columns, data.columns]











                      
                      
