"""Main module."""

import pandas as pd
import logging
import itertools
import re


def generate_substitutions(
    df: pd.DataFrame = None, column_value: tuple = None, value_regex: str = None
):
    """
    Util function to retrieve values of dataframe satisfying a regex
    """

    column_regex, value_regex = column_value

    compiled_column_regex = re.compile(column_regex[2:-2])
    columns_found = [
        col for col in df.columns if compiled_column_regex.fullmatch(col) is not None
    ]
    # if there is a value_regex then we compile it in advance
    if value_regex is not None and value_regex[0] != "{":
        compiled_value_regex = re.compile(value_regex[1:-1])
    else:
        compiled_value_regex = None
    for column in columns_found:
        if compiled_value_regex is not None:
            for value in df[column].unique():
                if isinstance(value, str):
                    try:
                        r = compiled_value_regex.fullmatch(value)
                    except:
                        logging.error("Error evaluating regex: " + value_regex[1:-1])
                    if r is not None:
                        yield (column, value)
        else:
            yield (column, None)
