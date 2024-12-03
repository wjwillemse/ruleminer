"""Main module."""

import pandas as pd
import logging
import re
import abc
import numpy as np
from sklearn.tree import _tree, DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.ensemble import AdaBoostClassifier, AdaBoostRegressor
from sklearn.base import is_classifier, is_regressor


def generate_substitutions(
    df: pd.DataFrame = None,
    column_value: tuple = None,
    value_regex: str = None,
):
    """
    Util function to retrieve values of dataframe satisfying a regex
    """
    if df is not None:
        column_regex, value_regex = column_value

        compiled_column_regex = re.compile(column_regex[2:-2])
        columns_found = [
            col
            for col in df.columns
            if compiled_column_regex.fullmatch(col) is not None
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
                        except Exception as e:
                            logging.error(
                                "Error evaluating regex: "
                                + value_regex[1:-1]
                                + ", "
                                + str(e)
                            )
                        if r is not None:
                            yield (column, value, r.groups())
            else:
                yield (column, None, None)


def tree_to_expressions(tree, features, target):
    """
    Util function to derive rules from a decision tree (classifier or regressor)
    """
    tree_ = tree.tree_
    feature_name = [
        features[i] if i != _tree.TREE_UNDEFINED else "undefined!"
        for i in tree_.feature
    ]

    def evaluate_node(node, expr, solutions):
        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            # not a leaf, evaluate left and right path
            name = feature_name[node]
            threshold = tree_.threshold[node]
            evaluate_node(
                tree_.children_left[node],
                expr
                + (" & " if expr != "" else "")
                + '({"'
                + name
                + '"} <= '
                + str(threshold)
                + ")",
                solutions,
            )
            evaluate_node(
                tree_.children_right[node],
                expr
                + (" & " if expr != "" else "")
                + '({"'
                + name
                + '"} > '
                + str(threshold)
                + ")",
                solutions,
            )
        else:
            # leaf node so add complete path to solutions
            value = tree_.value[node][0]
            if isinstance(tree, DecisionTreeClassifier):
                class_name = np.argmax(value)
                if isinstance(tree.classes_[class_name], str):
                    solutions.add(
                        "if ("
                        + expr
                        + ') then ({"'
                        + target
                        + '"} == "'
                        + tree.classes_[class_name]
                        + '")'
                    )
                else:
                    solutions.add(
                        "if ("
                        + expr
                        + ') then ({"'
                        + target
                        + '"} == '
                        + str(tree.classes_[class_name])
                        + ")"
                    )
            elif isinstance(tree, DecisionTreeRegressor):
                solutions.add(
                    "if ("
                    + expr
                    + ') then ({"'
                    + target
                    + '"} == '
                    + str(value[0])
                    + ")"
                )
            else:
                logging.error("Unknown classifier or regressor")

    solutions = set()
    evaluate_node(0, "", solutions)
    return solutions


def fit_ensemble_and_extract_expressions(
    df: pd.DataFrame = None,
    target: str = None,
    estimator: abc.ABCMeta = None,
    base: abc.ABCMeta = None,
    random_state: int = 0,
    max_depth: int = 2,
    n_estimators: int = 10,
    min_samples_split: int = 2,
    min_samples_leaf: int = 1,
    min_weight_fraction_leaf: float = 0.0,
    sample_weight: list = None,
):
    features = [col for col in df.columns if col != target]
    X = df[features]
    Y = df[[target]].values.ravel()
    target_dtype = df.dtypes[df.columns.get_loc(target)]

    if estimator is None:
        if pd.api.types.is_float_dtype(target_dtype):
            estimator = AdaBoostRegressor
        elif pd.api.types.is_integer_dtype(target_dtype):
            estimator = AdaBoostClassifier
    else:
        if pd.api.types.is_float_dtype(target_dtype) and not is_regressor(estimator):
            logging.error("target has float type data and estimator is not a regressor")
        elif pd.api.types.is_integer_dtype(target_dtype) and not is_classifier(
            estimator
        ):
            logging.error(
                "target has integer type data and estimator is not a classifier"
            )

    if base is None:
        if pd.api.types.is_float_dtype(target_dtype):
            base = DecisionTreeRegressor
        elif pd.api.types.is_integer_dtype(target_dtype):
            base = DecisionTreeClassifier
    else:
        if pd.api.types.is_float_dtype(target_dtype) and not is_regressor(base):
            logging.error("target has float type data and base is not a regressor")
        elif pd.api.types.is_integer_dtype(target_dtype) and not is_classifier(base):
            logging.error("target has integer type data and base is not a classifier")

    regressor = estimator(
        base_estimator=base(
            random_state=random_state,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            min_weight_fraction_leaf=min_weight_fraction_leaf,
        ),
        n_estimators=n_estimators,
        random_state=random_state,
    )
    regressor = regressor.fit(
        X,
        Y,
        sample_weight=sample_weight,
    )
    ensemble_expressions = [
        tree_to_expressions(estimator, features, target)
        for estimator in regressor.estimators_
    ]
    return ensemble_expressions


def fit_dataframe_to_ensemble(
    df: pd.DataFrame = None,
    random_state: int = 0,
    max_depth: int = 1,
    n_estimators: int = 10,
    min_samples_split: int = 2,
    min_samples_leaf: int = 1,
    min_weight_fraction_leaf: float = 0.0,
):
    """
    fit and extract from an ensemble
    """
    solutions = set()
    for target in df.columns:
        ensemble_expressions = fit_ensemble_and_extract_expressions(
            df=df,
            target=target,
            random_state=random_state,
            max_depth=max_depth,
            n_estimators=n_estimators,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            min_weight_fraction_leaf=min_weight_fraction_leaf,
        )

        for expressions in ensemble_expressions:
            for sol in expressions:
                solutions.add(sol)

    return solutions


def is_column(s):
    """
    Check if a given string is formatted as a column reference.

    This function checks if a string is formatted as a column reference,
    which typically consists of double curly braces {""} enclosing a
    column name.

    Args:
        s (str): The string to be checked.

    Returns:
        bool: True if the string is formatted as a column reference,
        False otherwise.

    Example:
        is_column('{"A"}')
            True

        is_column('{"B"}')
            True

        is_column("Not a column reference")
            False
    """
    return len(s) > 4 and (
        (s[:2] == '{"' and s[-1:] == "}") or (s[:2] == "{'" and s[-1:] == "}")
    )


def is_string(s):
    """
    Check if a given string is enclosed in single or double quotes.

    This function checks if a string is enclosed in single ('') or
    double ("") quotes, indicating that it is a string literal.

    Args:
        s (str): The string to be checked.

    Returns:
        bool: True if the string is enclosed in quotes, False otherwise.

    Example:
        is_string('"life"')
            True

        is_string('{"A"}')
            False

        is_string('""')
            True
    """
    return len(s) > 1 and (
        (s[:1] == '"' and s[-1:] == '"') or (s[:1] == "'" and s[-1:] == "'")
    )


def is_number(s):
    """
    Check if a given string is a number

    This function checks if a string is a number.

    Args:
        s (str): The string to be checked.

    Returns:
        bool: True if the string is a number

    Example:
        is_number('1.2')
            True

        is_number('{"A"}')
            False

    """
    if isinstance(s, str):
        pattern = r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?"
        match = re.match(pattern, s)
        return bool(match)
    else:
        return False


def flatten(expression):
    """
    Recursively flatten a nested expression and return it as a string.

    This function takes an expression, which can be a nested list of strings
    or a single string, and recursively flattens it into a single string
    enclosed in parentheses.

    Args:
        expression (str or list): The expression to be flattened.

    Returns:
        str: The flattened expression as a string enclosed in parentheses.

    Example:
        expression = ["A", ["B", ["C", "D"]]]

        result = ruleminer.flatten(expression)

        print(result)

            "(A(B(CD)))"
    """
    if isinstance(expression, str):
        return expression
    else:
        res = "".join([flatten(item) for item in expression])
        return res
