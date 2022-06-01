"""Main module."""

import pandas as pd
import logging
import itertools
import re
import numpy as np
from sklearn.tree import _tree, DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.ensemble import AdaBoostClassifier, AdaBoostRegressor

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
            evaluate_node(tree_.children_left[node], 
                    expr+(" & " if expr!="" else "")+'({"'+name+'"} <= '+str(threshold)+')', 
                    solutions)
            evaluate_node(tree_.children_right[node], 
                    expr+(" & " if expr!="" else "")+'({"'+name+'"} > '+str(threshold)+')', 
                    solutions)
        else:
            # leaf node so add complete path to solutions
            value = tree_.value[node][0]
            if isinstance(tree, DecisionTreeClassifier):
                class_name = np.argmax(value)
                if isinstance(tree.classes_[class_name], str):
                    solutions.add('if ('+expr+') then ({"'+target+'"} == "'+tree.classes_[class_name]+'")')
                else:
                    solutions.add('if ('+expr+') then ({"'+target+'"} == '+str(tree.classes_[class_name])+')')
            elif isinstance(tree, DecisionTreeRegressor):
                solutions.add('if ('+expr+') then ({"'+target+'"} == '+str(value[0])+')')
            else:
                logging.error("Unknown classifier or regressor")
    solutions = set()
    evaluate_node(0, "", solutions)
    return solutions

def fit_ensemble_and_extract_expressions(df: pd.DataFrame = None,
                                         target: str = None,
                                         random_state: int = 0,
                                         max_depth: int = 1,
                                         n_estimators: int = 10):
    
    features = [col for col in df.columns if col != target]
    X = df[features]
    Y = df[[target]].values.ravel()
    target_dtype = df.dtypes[df.columns.get_loc(target)]
    
    if pd.api.types.is_float_dtype(target_dtype):
        base, estimator = DecisionTreeRegressor, AdaBoostRegressor
    elif pd.api.types.is_integer_dtype(target_dtype):
        base, estimator = DecisionTreeClassifier, AdaBoostClassifier

    regressor = estimator(
        base_estimator = base(random_state=random_state, max_depth=max_depth),
        n_estimators=n_estimators,
        random_state=random_state)
    regressor = regressor.fit(X, Y)
    ensemble_expressions = [
        tree_to_expressions(estimator, features, target)
        for estimator in regressor.estimators_]
    return ensemble_expressions

def fit_dataframe_to_ensemble(df: pd.DataFrame = None,
                 random_state: int = 0,
                 max_depth: int = 1,
                 n_estimators: int = 10):
    
    """
    fit and extract from an ensemble
    """
    solutions = set()
    for target in df.columns:
        
        ensemble_expressions = fit_ensemble_and_extract_expressions(
            df,
            target = target,
            random_state = random_state,
            max_depth = max_depth,
            n_estimators = n_estimators)
        
        for expressions in ensemble_expressions:
            for sol in expressions:
                solutions.add(sol)

    return solutions