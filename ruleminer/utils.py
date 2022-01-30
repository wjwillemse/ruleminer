"""Main module."""

import pandas as pd
import logging
import itertools
import re


def get_columns(df: pd.DataFrame = None, column_regex: str = None):
    """
    Util function to retrieve columns of dataframe satisfying a regex
    """
    return [col for col in df.columns if re.match(column_regex, col) is not None]


def evaluate_column_regex(
    df: pd.DataFrame = None, column_regex: str = None, value_regex: str = None
):
    """
    Util function to retrieve values of dataframe satisfying a regex
    """
    results = list()
    columns_found = [
        col for col in df.columns if re.match(column_regex[2:-2], col) is not None
    ]
    for column in columns_found:
        combinations = list()
        if value_regex is not None and value_regex[0] != "{":
            value_list = []
            for value in df[column].unique():
                if isinstance(value, str):
                    try:
                        r = re.match(value_regex[1:-1], value)
                    except:
                        logging.error("Error evaluating regex: " + value_regex[1:-1])
                        return results
                    if r is not None:
                        value_list.append(value)
            for value in value_list:
                if (column, value) not in combinations:
                    combinations.append((column, value))
        else:
            if (column,) not in combinations:
                combinations.append((column,))
        results.extend(combinations)
    return results
