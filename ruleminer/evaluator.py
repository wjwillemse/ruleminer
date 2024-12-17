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
        self.logger = logging.getLogger(__name__)

        # general tolerance function
        def _tol(value, direction=bool, column=None):
            """
            Adjusts the given numerical value based on the specified tolerance and direction for a given column.

            This function is designed to apply a tolerance-based adjustment to a numerical value depending on its range
            and the specified direction. If the value falls within a defined range for a given column, the function
            modifies the value by either adding or subtracting a calculated adjustment (based on the number of decimals
            defined in the tolerance configuration).

            Args:
                value (float or str): The value to be adjusted. Can be a numerical value or a string. If it's NaN, the function returns NaN.
                direction (str, optional): The direction of adjustment. If "+" (default), the value will be increased. If "-" the value will be decreased.
                column (str, optional): The column to check for the corresponding tolerance. If not specified, no adjustment is made based on column.

            Returns:
                float or str:
                    - If the value is NaN, returns NaN.
                    - If the value is a string, returns the string unmodified.
                    - If the value falls within a tolerance range, returns the adjusted value based on the direction.
                    - Otherwise, returns the unmodified value.

            Notes:
                - Tolerance ranges and corresponding decimal adjustments are retrieved from `self.tolerance`
                - The function adjusts the value by adding or subtracting a calculated amount, based on the specified number of decimals in the tolerance configuration.
                - The tolerance dictionary is structured such that `self.tolerance[column]` is a dictionary mapping `(start, end)` ranges to decimal precision.

            Example:
                # Assuming self.tolerance is properly set
                _tol(5.75, direction="+", column="some_column")
                # Adjust the value 5.75 based on the tolerance for 'some_column' and direction '+'
            """
            if pd.isna(value):
                return np.nan
            elif isinstance(value, str):
                return value
            for key, tol in self.tolerance.items():
                if key == column:
                    for ((start, end)), decimals in tol.items():
                        if abs(value) >= start and abs(value) < end:
                            if direction == "+":
                                return value + 0.5 * 10 ** (decimals)
                            else:
                                return value - 0.5 * 10 ** (decimals)

        def _equal(
            left_side,
            right_side,
            left_side_pos,
            left_side_neg,
            right_side_pos,
            right_side_neg,
        ):
            if (
                any(
                    [
                        p(left_side)
                        for p in [
                            pd.api.types.is_string_dtype,
                            pd.api.types.is_bool_dtype,
                            pd.api.types.is_datetime64_ns_dtype,
                        ]
                    ]
                )
            ) or (
                any(
                    [
                        p(right_side)
                        for p in [
                            pd.api.types.is_string_dtype,
                            pd.api.types.is_bool_dtype,
                            pd.api.types.is_datetime64_ns_dtype,
                        ]
                    ]
                )
            ):
                return left_side == right_side
            else:
                if logging.DEBUG == logging.root.level:
                    lhs = [
                        (str(a), str(b))
                        for a, b in zip(
                            np.minimum(left_side_pos, left_side_neg),
                            np.maximum(left_side_pos, left_side_neg),
                        )
                    ]
                    rhs = [
                        (str(a), str(b))
                        for a, b in zip(
                            np.minimum(right_side_pos, right_side_neg),
                            np.maximum(right_side_pos, right_side_neg),
                        )
                    ]
                    self.logger.debug("Evaluating equality:")
                    for idx in range(len(lhs)):
                        self.logger.debug(
                            "  LHS: " + str(lhs[idx]) + ", RHS: " + str(rhs[idx])
                        )
                return (
                    np.maximum(left_side_pos, left_side_neg)
                    >= np.minimum(right_side_pos, right_side_neg)
                ) & (
                    np.minimum(left_side_pos, left_side_neg)
                    <= np.maximum(right_side_pos, right_side_neg)
                )

        def _unequal(
            left_side,
            right_side,
            left_side_pos,
            left_side_neg,
            right_side_pos,
            right_side_neg,
        ):
            if (
                any(
                    [
                        p(left_side)
                        for p in [
                            pd.api.types.is_string_dtype,
                            pd.api.types.is_bool_dtype,
                            pd.api.types.is_datetime64_ns_dtype,
                        ]
                    ]
                )
            ) or (
                any(
                    [
                        p(right_side)
                        for p in [
                            pd.api.types.is_string_dtype,
                            pd.api.types.is_bool_dtype,
                            pd.api.types.is_datetime64_ns_dtype,
                        ]
                    ]
                )
            ):
                return left_side != right_side
            else:
                if logging.DEBUG == logging.root.level:
                    lhs = [
                        (str(a), str(b))
                        for a, b in zip(
                            np.minimum(left_side_pos, left_side_neg),
                            np.maximum(left_side_pos, left_side_neg),
                        )
                    ]
                    rhs = [
                        (str(a), str(b))
                        for a, b in zip(
                            np.minimum(right_side_pos, right_side_neg),
                            np.maximum(right_side_pos, right_side_neg),
                        )
                    ]
                    self.logger.debug("Evaluating inequality:")
                    for idx in range(len(lhs)):
                        self.logger.debug(
                            "  LHS: " + str(lhs[idx]) + ", RHS: " + str(rhs[idx])
                        )
                return (
                    np.minimum(left_side_pos, left_side_neg)
                    < np.maximum(right_side_pos, right_side_neg)
                ) | (
                    np.maximum(left_side_pos, left_side_neg)
                    > np.minimum(right_side_pos, right_side_neg)
                )

        def _multiply(a_pos, a_neg, b_pos, b_neg, direction: str):
            """
            Perform multiplication based on the given direction and return the maximum or minimum result
            based on the values of a+, a-, b+, b-.

            Input is pd.Series, so output should be pd.Series

            """
            if direction == "+":
                return pd.concat(
                    [
                        (a_neg * b_neg),
                        (a_neg * b_pos),
                        (a_pos * b_neg),
                        (a_pos * b_pos),
                    ],
                    join="inner",
                    ignore_index=True,
                    axis=1,
                ).max(axis=1)
            else:
                return pd.concat(
                    [
                        (a_neg * b_neg),
                        (a_neg * b_pos),
                        (a_pos * b_neg),
                        (a_pos * b_pos),
                    ],
                    join="inner",
                    ignore_index=True,
                    axis=1,
                ).min(axis=1)

        def _divide(a_pos, a_neg, b_pos, b_neg, direction: str):
            """
            Perform division based on the given direction and return the maximum or minimum result
            based on the values of a+, a-, b+, b-.

            Input is pd.Series, so output should be pd.Series

            """
            if direction == "+":
                return pd.concat(
                    [
                        (a_neg / b_neg),
                        (a_neg / b_pos),
                        (a_pos / b_neg),
                        (a_pos / b_pos),
                    ],
                    join="inner",
                    ignore_index=True,
                    axis=1,
                ).max(axis=1)
            else:
                return pd.concat(
                    [
                        (a_neg / b_neg),
                        (a_neg / b_pos),
                        (a_pos / b_neg),
                        (a_pos / b_pos),
                    ],
                    join="inner",
                    ignore_index=True,
                    axis=1,
                ).min(axis=1)

        self.globals["_tol"] = _tol
        self.globals["_equal"] = _equal
        self.globals["_unequal"] = _unequal
        self.globals["_multiply"] = _multiply
        self.globals["_divide"] = _divide

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
        variables = {}
        for key in expressions.keys():
            try:
                variables[key] = eval(expressions[key], self.globals, encodings)
            except Exception as e:
                self.logger.debug(
                    "Error evaluating the code '" + expressions[key] + "': " + repr(e)
                )
                variables[key] = np.nan
        return variables
