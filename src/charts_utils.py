# -*- coding: utf-8 -*-
"""
Created on Fri Nov 26 15:46:10 2021

@author: Roberto.Rossignoli
v1.4
"""
import matplotlib.font_manager as fm
from matplotlib.ticker import FuncFormatter
import matplotlib


def _setDefaultOptions() -> dict:
    """
    Function sets the formatting for the "default option" for charts
    """
    italic, normal, bold = _importFonts()
    chartOptions = {
        'title': '',
        'titleFontSize': 13,
        'titleFont': italic,
        'titleHorizontalAlignmnet': 'right',
        'titleColor': 'black',

        'xLabel': "",
        'yLabel': "",

        'labelFont': italic,
        'labelFontSize': 10,
        'labelColor': "black",

        'ticksLabelFont': italic,
        'ticksLabelFontSize': 10,
        'ticksLabelColor': 'black',

        'xTicksLabel%': False,
        'yTicksLabel%': False,  # '{:.1%}',

        'legendVisible': True,
        'legendFont': italic,
        'legendFontSize': 10,
        'legendFontColor': 'black',
        'legendPosition': 'best',
        'legend_bbox_to_anchor': (0, 0),
        'legendNcol': 1,

        'xGridSwitcher': True,
        'xGridLineStyle': 'dashed',
        'xGridAlpha': 0.5,
        'xGridLineWidth': 0.2,
        'xGridColor': "grey",
        'yGridSwitcher': True,
        'yGridLineStyle': 'dashed',
        'yGridAlpha': 0.5,
        'yGridLineWidth': 0.2,
        'yGridColor': "grey",

        'faceColor': '#F9f9f9',
        'borderLines': True,
    }
    return chartOptions


def _axProperties(
        ax,
        chartOptions: dict
):
    """
    Function to update the properties of a matplotlib plot
    to those in the chartOptions dict
    """

    ax.set_title(
        chartOptions["title"],
        fontproperties=fm.FontProperties(
            fname=chartOptions["titleFont"].get_file(),
            size=chartOptions["titleFontSize"]),
        color=chartOptions["titleColor"])

    for item in (ax.get_xticklabels(which="both") + \
                 ax.get_yticklabels(which="both")):
        item.set_font_properties(
            fm.FontProperties(
                fname=chartOptions["ticksLabelFont"].get_file(),
                size=chartOptions["ticksLabelFontSize"]))
        item.set_color(chartOptions["ticksLabelColor"])

    if chartOptions["xTicksLabel%"] is not False:
        ax.xaxis.set_major_formatter(
            FuncFormatter(
                lambda y, _: chartOptions["xTicksLabel%"].format(y)))

    if chartOptions["yTicksLabel%"] is not False:
        ax.yaxis.set_major_formatter(
            FuncFormatter(
                lambda y, _: chartOptions["yTicksLabel%"].format(y)))

    ax.set_xlabel(
        chartOptions["xLabel"],
        fontproperties=fm.FontProperties(
            fname=chartOptions["labelFont"].get_file(),
            size=chartOptions["labelFontSize"]),
        color=chartOptions["labelColor"])

    ax.set_ylabel(
        chartOptions["yLabel"],
        fontproperties=fm.FontProperties(
            fname=chartOptions["labelFont"].get_file(),
            size=chartOptions["labelFontSize"]),
        color=chartOptions["labelColor"])

    if chartOptions["legendVisible"] is False:
        ax.legend([]).set_visible(False)
    else:
        if chartOptions["legendPosition"] is not None:
            ax.legend(
                loc=chartOptions['legendPosition'],
                ncol=chartOptions['legendNcol'],
                prop=fm.FontProperties(
                    fname=chartOptions["legendFont"].get_file(),
                    size=chartOptions["legendFontSize"]),
                labelcolor=chartOptions["legendFontColor"]
            )
        else:
            ax.legend(
                bbox_to_anchor=chartOptions["legend_bbox_to_anchor"],
                ncol=chartOptions['legendNcol'],
                prop=fm.FontProperties(
                    fname=chartOptions["legendFont"].get_file(),
                    size=chartOptions["legendFontSize"]),
                labelcolor=chartOptions["legendFontColor"]
            )

    ax.grid(
        axis='x',
        visible=chartOptions['xGridSwitcher'],
        linestyle=chartOptions['xGridLineStyle'],
        alpha=chartOptions['xGridAlpha'],
        linewidth=chartOptions['xGridLineWidth'],
        color=chartOptions['xGridColor']
    )
    ax.grid(
        axis='y',
        linestyle=chartOptions['yGridLineStyle'],
        alpha=chartOptions['yGridAlpha'],
        linewidth=chartOptions['yGridLineWidth'],
        color=chartOptions['yGridColor']
    )
    ax.set_facecolor(chartOptions['faceColor'])
    if chartOptions["borderLines"] is False:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)


def _importFonts() -> tuple:
    """
    Returns a tuple of font_manager.FontProperties items, to set the fonts for
    the charts
    """
    italic = fm.FontProperties(
        fname=fm.findfont('arial'), 
        style='italic', 
        weight='light')

    normal = fm.FontProperties(
        fname=fm.findfont('arial'), 
        style='normal', 
        weight='light')

    bold = fm.FontProperties(
        fname=fm.findfont('arial'), 
        style='normal', 
        weight='bold')

    return italic, normal, bold

