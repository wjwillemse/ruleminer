# Module CodeEvaluator

import logging
import pandas as pd
import numpy as np
from .const import (
    DUNDER_DF,
)


class CodeEvaluator:
    """
    The CodeEvaluator class

    A class that evaluates mathematical expressions and manages global variables for evaluation.

    The `CodeEvaluator` class is designed to evaluate mathematical expressions provided as
    strings using a set of predefined functions and variables. It supports expression evaluation
    with tolerance levels, comparisons, and the ability to dynamically access variables (such as
    `numpy` functions, custom tolerance definitions, and a DataFrame). The class allows for
    setting parameters (including tolerance settings), data (as a pandas DataFrame), and evaluates
    expressions while handling errors gracefully.

    The class maintains an internal `globals` dictionary that contains:
    - Mathematical functions from `numpy` (e.g., `max`, `min`, `abs`, `sum`, `quantile`).
    - Helper functions for comparisons (`_equal`, `_unequal`) and tolerance calculations (`_tol`).
    - References to `numpy` itself and `numpy.nan`.

    Attributes:
    - globals (dict): A dictionary of global functions and variables available for expression
      evaluation, including `numpy` functions, custom helper functions, and the `nan` constant.
    - params (dict): A dictionary of parameters set by the `set_params` method, including tolerance
      settings.
    - tolerance (dict): A dictionary of tolerance settings, extracted from `params`.
    - DUNDER_DF (str): A constant key used to store a pandas DataFrame in the `globals`.

    Methods:
    - __init__: Initializes the `CodeEvaluator` object with default global functions and helper methods.
    - set_params: Sets parameters for the object, including tolerance settings, and performs validation.
    - set_data: Sets the DataFrame used for evaluation in the `globals` dictionary.
    - evaluate: Evaluates a set of mathematical expressions and stores the results in a dictionary.
    """

    def __init__(
        self,
    ):
        """
        Initializes the CodeEvaluator object with a set of predefined mathematical functions
        and helper methods for evaluating expressions.

        This constructor sets up the `globals` dictionary with various mathematical functions
        from the `numpy` library, such as `maximum`, `minimum`, `abs`, `quantile`, and `sum`,
        as well as custom helper functions for evaluating tolerance and comparisons:

        - 'MAX', 'MIN', 'ABS', 'QUANTILE', 'SUM', 'max', 'min', 'abs', 'quantile', 'sum':
          Mappings to the corresponding functions in `numpy`.
        - 'np': Reference to the `numpy` library.
        - 'nan': Reference to `numpy.nan`.
        - '_tol': A helper function that calculates tolerance for a given value based on
          predefined ranges and decimal precision.
        - '_equal': A helper function that checks if two values (considering both positive
          and negative sides) are equal.
        - '_unequal': A helper function that checks if two values (considering both positive
          and negative sides) are unequal.

        These functions are added to the `globals` attribute of the object, making them available
        for use in code evaluation or further processing.

        Attributes:
        - globals (dict): A dictionary that contains mathematical functions, helper functions
          for tolerance and comparison, and references to `numpy` and `numpy.nan`.

        Notes:
        - The tolerance functions rely on the `self.tolerance` attribute, which must be set
          separately for proper functionality.

        """
        self.globals = {
            "MAX": np.maximum,
            "MIN": np.minimum,
            "ABS": np.abs,
            "QUANTILE": np.quantile,
            "SUM": np.sum,
            "max": np.maximum,
            "min": np.minimum,
            "abs": np.abs,
            "quantile": np.quantile,
            "sum": np.sum,
            "np": np,
            "nan": np.nan,
        }

        def _tol(value, column=None):
            if pd.isna(value):
                return np.nan
            for key, tol in self.tolerance.items():
                if key == column:
                    for ((start, end)), decimals in tol.items():
                        if abs(value) >= start and abs(value) < end:
                            return 0.5 * 10 ** (decimals)

        def _equal(left_side_pos, left_side_neg, right_side_pos, right_side_neg):
            return (
                np.maximum(left_side_pos, left_side_neg)
                >= np.minimum(right_side_pos, right_side_neg)
            ) & (
                np.minimum(left_side_pos, left_side_neg)
                <= np.maximum(right_side_pos, right_side_neg)
            )

        def _unequal(left_side_pos, left_side_neg, right_side_pos, right_side_neg):
            return (
                np.minimum(left_side_pos, left_side_neg)
                < np.maximum(right_side_pos, right_side_neg)
            ) | (
                np.maximum(left_side_pos, left_side_neg)
                > np.minimum(right_side_pos, right_side_neg)
            )

        self.globals["_tol"] = _tol
        self.globals["_equal"] = _equal
        self.globals["_unequal"] = _unequal

    def set_params(self, params):
        """
        Sets parameters for the object, including tolerance settings, and performs validation.

        This method stores the provided parameters in the `params` attribute, extracts
        the tolerance settings (if available), and validates the structure of the tolerance
        dictionary. Specifically, it checks for the presence of a "default" key and ensures
        that no keys in the tolerance definition contain spaces.

        Parameters:
        - params (dict): A dictionary containing the parameters to be set for the object.
          The dictionary may include a "tolerance" key with tolerance settings.

        Raises:
        - Exception: If the tolerance dictionary is provided but does not contain a "default"
          key, or if any keys in the tolerance dictionary contain spaces, an exception is raised.

        Returns:
        - None: This method does not return any value. It updates the internal state with the
          provided parameters and validates the tolerance settings.
        """
        self.params = params
        self.tolerance = self.params.get("tolerance", None)
        if self.tolerance is not None:
            if "default" not in self.tolerance.keys():
                raise Exception("No 'default' key found in tolerance definition.")
            for key in self.tolerance.keys():
                if " " in key:
                    raise Exception(
                        "No spaces allowed in keys of tolerance definition."
                    )

    def set_data(
        self,
        dataframe: pd.DataFrame = None,
    ) -> None:
        """
        Sets the DataFrame to evaluate the expressions on.

        This method stores the provided pandas DataFrame in the `globals` under a
        predefined key. The DataFrame can then be accessed by other methods in the class
        for evaluation or further manipulation.

        Parameters:
        - dataframe (pd.DataFrame): The pandas DataFrame to be stored in the `globals`.
          If no DataFrame is provided, `None` is used by default.

        Returns:
        - None: This method does not return any value. It updates the internal state
          by setting the DataFrame.

        Notes:
        - The DataFrame is stored under the constant key `DUNDER_DF` within the
          `globals`.
        """
        self.globals[DUNDER_DF] = dataframe

    def evaluate(
        self,
        expressions: dict = {},
        encodings: dict = {},
    ) -> dict:
        """
        Evaluates a set of mathematical expressions and stores the results in a dictionary.

        This method processes each expression provided in the `expressions` dictionary,
        evaluating it using the functions and variables available in the `globals` and
        additional encoding values from the `encodings` dictionary. If an expression cannot
        be evaluated, it logs an error and assigns `NaN` as the result for that expression.

        Parameters:
        - expressions (dict): A dictionary where keys are variable names and values are
          the corresponding mathematical expressions as strings to be evaluated.
        - encodings (dict): A dictionary of additional variables or encoding values to be
          used during the evaluation of expressions.

        Returns:
        - dict: A dictionary where keys are the variable names from the `expressions`
          dictionary, and values are the results of evaluating those expressions. If an error
          occurs during evaluation, the corresponding value is set to `NaN`.

        Logs:
        - Errors encountered during the evaluation of expressions are logged with a debug level.

        """
        logger = logging.getLogger(__name__)
        variables = {}
        for key in expressions.keys():
            try:
                variables[key] = eval(expressions[key], self.globals, encodings)
            except Exception as e:
                logger.debug(
                    "Error evaluating the code '" + expressions[key] + "': " + repr(e)
                )
                variables[key] = np.nan
        return variables