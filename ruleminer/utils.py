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
        combinations = set()
        if value_regex is not None and value_regex[0] != "{":
            value_list = []
            for value in df[column].values:
                if isinstance(value, str):
                    try:
                        r = re.match(value_regex[1:-1], value)
                    except:
                        logging.error("Error evaluating regex: " + value_regex[1:-1])
                        return results
                    if r is not None:
                        value_list.append(value)
            for value in value_list:
                combinations.add((column, value))
        else:
            combinations.add((column,))
        results.extend(combinations)
    return results


def cartesianProduct(set_a, set_b):
    """
    Util function to find cartesian product of two sets
    """
    result = []
    for i in range(0, len(set_a)):
        for j in range(0, len(set_b)):
            # for handling case having cartesian
            # product first time of two sets
            if type(set_a[i]) != list:
                set_a[i] = [set_a[i]]

            # coping all the members
            # of set_a to temp
            temp = [num for num in set_a[i]]

            # add member of set_b to
            # temp to have cartesian product
            temp.append(set_b[j])
            result.append(temp)

    return result


def Cartesian(l):
    """
    Util function to find cartesian product of two sets
    """
    # result of cartesian product
    # of all the sets taken two at a time
    if len(l) == 1:
        return [[i] for i in l[0]]
    temp = l[0]
    # do product of N sets
    for i in range(1, len(l)):
        temp = cartesianProduct(temp, l[i])
    return temp
