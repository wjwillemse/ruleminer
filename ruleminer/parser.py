"""Parser module."""

from typing import Union
from .utils import (
    flatten,
    is_column,
    is_string,
)
from .pandas_parser import (
    pandas_column,
)
from .evaluator import CodeEvaluator
import regex as re
import numpy as np
import logging


class RuleParser:
    """
    The RuleParser object

    It uses three main functions
    - set_params
    - set_data
    - parse

    The parse function call underlying functions for specific structures

    """

    def __init__(
        self,
    ):
        """ """
        self.keywords_function_mapping = [
            (set(["==", "!=", "<", "<=", ">", ">="]), self.parse_comparison),
            (set(["quantile", "mean", "std"]), self.parse_statistical_functions),
            (set(["for"]), self.parse_list_comprehension),
            (set(["in", "not in", "between", "not between"]), self.parse_in),
            (set(["substr"]), self.parse_substr),
            (set(["split"]), self.parse_split),
            (set(["sum"]), self.parse_sum),
            (set(["sumif"]), self.parse_sumif),
            (set(["countif"]), self.parse_countif),
            (set(["match"]), self.parse_match),
            (set(["contains", "not contains"]), self.parse_contains),
            (set(["exact"]), self.parse_exact),
            (set(["corr"]), self.parse_corr),
            (set(["abs"]), self.parse_abs),
            (set(["max", "min", "abs"]), self.parse_maxminabs),
            (set(["round", "floor", "ceil"]), self.parse_round),
            (
                set(
                    [
                        "day",
                        "month",
                        "quarter",
                        "year",
                        "day_name",
                        "month_name",
                        "days_in_month",
                        "daysinmonth",
                        "is_leap_year",
                        "is_year_end",
                        "dayofweek",
                        "weekofyear",
                        "weekday",
                        "week",
                        "is_month_end",
                        "is_month_start",
                        "is_year_start",
                        "is_quarter_end",
                        "is_quarter_start",
                    ]
                ),
                self.parse_timedate_function,
            ),
            (set(["days", "months", "years"]), self.parse_timedelta_function),
            (set(["+", "-", "*", "/", "**"]), self.parse_math_operator),
        ]

        self.params = dict()

    def set_params(self, params):
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

    def set_data(self, data):
        self.data = data

    def parse(
        self,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        General function to parse expression (tree structure) to pseudo code (str).

        This method takes an input expression and converts specific parameters,
        settings, and functions into their equivalent Pandas code. It allows
        for custom transformations and conversions that are used in the evaluation
        of rules.

        Args:
            expression (Union[str, list]): The list comprehension expression to be processed.
            apply_tolerance (bool, optional): Flag to apply tolerance while parsing (default is False).
            positive_tolerance (bool, optional): Flag to determine positive tolerance behavior (default is True).

        Returns:
            str: The parsed expression in pseudo code.

        Example:
            expression = ['substr', ['{"A"}', ',', '1', ',', '1']]

            result = ruleminer.RuleParser().parse(expression)

            print(result)

                "({"A"}.str.slice(0,1))"

        """
        if isinstance(expression, str):
            if is_column(expression) or expression == "K":
                return self.parse_column(
                    expression,
                    apply_tolerance=apply_tolerance,
                    positive_tolerance=positive_tolerance,
                )
            else:
                return self.parse_string(
                    expression,
                    apply_tolerance=apply_tolerance,
                    positive_tolerance=positive_tolerance,
                )
        else:
            # to avoid constructions like (() - (...))
            if len(expression) == 1 and expression[0] in ["+", "-", "*", "/", "**"]:
                return expression[0]

            if len(expression) >= 3 and expression[0] == "(" and expression[-1] == ")":
                return (
                    "("
                    + self.parse(
                        expression[1:-1],
                        apply_tolerance=apply_tolerance,
                        positive_tolerance=positive_tolerance,
                    )
                    + ")"
                )

            for idx, item in enumerate(expression):
                if isinstance(item, str):
                    if (
                        "decimal" in self.params.keys()
                        and (item in ["=="])
                        and (
                            not (
                                contains_string(expression[:idx])
                                or contains_string(expression[idx + 1 :])
                            )
                        )
                    ):
                        return self.parse_decimal(
                            idx,
                            item,
                            expression,
                            apply_tolerance=apply_tolerance,
                            positive_tolerance=positive_tolerance,
                        )
                    for keywords, parse_function in self.keywords_function_mapping:
                        if item.lower() in keywords:
                            return parse_function(
                                idx,
                                item,
                                expression,
                                apply_tolerance=apply_tolerance,
                                positive_tolerance=positive_tolerance,
                            )

            res = "".join(
                [
                    self.parse(
                        i,
                        apply_tolerance=apply_tolerance,
                        positive_tolerance=positive_tolerance,
                    )
                    for i in expression
                ]
            )
            return res

    def parse_substr(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process substr function

        Example:
            expression = ['SUBSTR', ['(', '"C"', ',', '2', ',', '4', ')']]
            idx = 0

            # Call the parse_substr method
            result = ruleminer.RuleParser().parse_substr(
                idx=idx,
                item="SUBSTR",
                expression=expression,
            )

            # Print the result
            print(result)

            expression = ['SUBSTR', ['(', {"C"}', ',', '2', ',', '4', ')']]

            result = ruleminer.RuleParser().parse_substr(
                idx=0,
                expression=expression,
                apply_tolerance=False
            )
            print(result)
                '({"C"}.str.slice(2,4))'
        """
        _, string, _, start, _, stop, _ = expression[idx + 1]
        res = (
            self.parse(
                string,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            + ".str.slice("
            + str(int(start) - 1)
            + ","
            + str(int(start) + int(stop) - 1)
            + ")"
        )
        return res

    def parse_corr(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process corr function

        Example:
            expression = ['CORR', ['(', '"matrix"', ',', '{"a"}', ',', '{"b"}', ',', '{"c"}, ',', '{"d"}',')']]
            idx = 0

            result = ruleminer.RuleParser().parse_corr(
                idx=idx,
                expression=expression,
                apply_tolerance=False
            )
            print(result)
                '_corr("matrix", {"a"}, {"b"}, {"c"}, {"d"})'
        """
        corr_params = expression[idx + 1]
        matrix_key = corr_params[1][1:-1]
        if matrix_key not in list(self.params["matrices"].keys()):
            logging.error(
                "Matrix key is not in predefined matrices dictionary of parameters."
            )
        res = "_corr" + self.parse(
            corr_params,
            apply_tolerance=apply_tolerance,
            positive_tolerance=positive_tolerance,
        )
        return res

    def parse_round(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process round function

        Example:
            expression = ['CEIL', ['(', '{"d"}', ',', '2', ')']]
            idx = 0

            result = ruleminer.RuleParser().parse_round(
                idx=idx,
                expression=expression,
                apply_tolerance=False
            )
            print(result)
                '_round({"d"}, 2, "ceil")'
        """
        _, data_series, _, rounding_param, _ = expression[idx + 1]
        res = (
            "_round("
            + self.parse(
                data_series,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            + ", "
            + self.parse(
                rounding_param,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            + ', "'
            + item.lower()
            + '")'
        )
        return res

    def parse_timedate_function(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process date function

        Example:
            expression = ['day', ['(', '{"C"}', ')']]
            idx = 0

            # Call the parse_substr method
            result = ruleminer.RuleParser.parse_substr(
                idx=idx,
                item="SUBSTR",
                expression=expression,
            )

            # Print the result
            print(result)

            expression = ['SUBSTR', ['(', {"C"}', ',', '2', ',', '4', ')']]

            result = ruleminer.RuleParser().parse_substr(
                idx=0,
                expression=expression,
                apply_tolerance=False
            )
            print(result)
                '({"C"}.dt.day))'
        """
        date = expression[idx + 1][1:-1]
        res = (
            self.parse(
                date,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            + ".dt."
            + item.lower()
        )
        return res

    def parse_timedelta_function(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process timedelta function

        Example:
            expression = ['days', ['(', '{"C"}', '-', '{"D"}', ')']]

            result = ruleminer.RuleParser().parse_timedelta_function(
                idx=0,
                expression=expression,
                apply_tolerance=False
            )
            print(result)
                '
                ((({"C"}-{"D"}) / np.timedelta64(1, 'D')))
                '
        """
        date = expression[idx + 1][1:-1]
        if item.lower() == "days":
            s = '"D"'
        elif item.lower() == "months":
            s = '"M"'
        elif item.lower() == "years":
            s = '"Y"'
        res = (
            "(("
            + self.parse(
                date,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            + ") / np.timedelta64(1, "
            + s
            + "))"
        )
        return res

    def parse_split(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process split function

        Example:
            expression = ['SPLIT', ['(', '{"C"}', ',', '"C"', ',', '2'], 'IN', [['"D"']], ')']

            result = ruleminer.RuleParser().parse_substr(
                idx=0,
                expression=expression,
                apply_tolerance=False
            )
            print(result)
                '(({"C"}.str.slice("C",2)).isin("D"))'
        """
        _, string, _, separator, _, position, _ = expression[idx + 1]
        if not position.isdigit():
            logging.error(
                "Third parameter of split function is not a digit, taking first position"
            )
            position = "0"
        else:
            position = str(int(position) - 1)
        res = (
            self.parse(
                string,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            + ".str.split("
            + separator
            + ").str["
            + position
            + "]"
        )
        return res

    def parse_sum(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process sum function

        Example
            expression = ['SUM', ['(', '2', ',', '3', ',', '5', ')']]  # Example expression for sum operation
            idx = 0  # Index for the expression list

            # Call the parse_sum method
            result = ruleminer.RuleParser().parse_sum(
                idx=idx,
                item="SUM",
                expression=expression,
            )

            # Print the result
            print(result)
                sum([K for K in [2,3,5]], axis=0, dtype=float)
        """
        # process sum and sumif functions
        # do not apply tolerance on the list of datapoints
        # because we use list comprehension below
        if "for" not in expression[1][1]:
            sumlist = self.parse_list(
                0,
                expression[1][1],
                apply_tolerance=False,
                positive_tolerance=positive_tolerance,
            )
            # add tolerance to list comprehension variable
            var_k = self.parse(
                expression="K",
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            res = "sum([" + var_k + " for K in " + sumlist + "], axis=0, dtype=float)"
        else:
            sumlist = self.parse_list(
                0,
                expression[1][1],
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            res = "sum(" + sumlist + ", axis=0, dtype=float)"
        return res

    def parse_sumif(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process sumif function

        Example:
            expression = [
            'sumif',
            [['[', '{"Assets"}', ',', '{"Own_funds"}', ']'], ',', '{"Type"}', '==', '"life_insurer"']]
            ]
            idx = 0  # Index for the expression list

            # Call the parse_sumif method
            result = ruleminer.RuleParser().parse_sumif(
                idx=idx,
                item="sumif",
                expression=expression,
            )

            # Print the result
            print(result)
                sum([K for K in [{"Assets"},{"Own_funds"}].where({"Type"}=="life_insurer", other=0)], axis=0, dtype=float)
        """
        # do not apply tolerance on the list of datapoints
        # because we use list comprehension below
        if "for" not in expression[1][1]:
            sumlist = self.parse(
                expression[1][1],
                apply_tolerance=False,
                positive_tolerance=positive_tolerance,
            )
            # add tolerance to list comprehension variable
            var_k = self.parse(
                expression="K",
                apply_tolerance=True if "tolerance" in self.params.keys() else False,
                positive_tolerance=positive_tolerance,
            )
            sumlist = "[" + var_k + " for K in " + sumlist + "]"
        else:
            sumlist = self.parse(
                expression[1][1],
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
        if isinstance(expression[1][3], str):
            # the sumif conditions a single condition that has to be applied to all item in the sumlist
            condition = self.parse(
                expression[1][3:],
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )[:-1]
            # a single condition applied to all columns
            # other=0 is used so that we have zero instead of NaN
            # we then sum so this has no influence on the result
            res = (
                "sum("
                + sumlist.replace("}", "}.where(" + condition + ", other=0)")
                + ", axis=0, dtype=float)"
            )
        else:
            # the sumif conditions a list of conditions
            conditionlist = self.parse(
                expression[1][3][:-1],
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            # other=0 is used so that we have zero instead of NaN
            # we then sum so this has no influence on the result
            res = (
                "sum("
                + "[v.where(c, other=0) for (v,c) in zip("
                + sumlist
                + ","
                + conditionlist
                + ")]"
                + ", axis=0, dtype=float)"
            )
        return res

    def parse_countif(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process countif function

        Example:
            expression = [
                'COUNTIF',
                [
                    '(',
                    '{"Assets"}',
                    ',',
                    '{"Type"}',
                    '==',
                    '"life_insurer"'
                ]
            ]
            idx = 0  # Index for the expression list

            # Call the parse_countif method
            result = ruleminer.RuleParser().parse_countif(
                idx=idx,
                item="COUNTIF",
                expression=expression,
            )

            # Print the result
            print(result)
                sum([K for K in {"Assets"}.where({"Type"}=="life_insurer").isna()], axis=0, dtype=float)
        """
        # do not apply tolerance on the list of datapoints
        # because we use list comprehension below
        # expression[0] == COUNTIF
        # expression[1][0] == "("
        # expression[1][1] == countlist
        if "for" not in expression[1][1]:
            countlist = self.parse(
                expression[1][1],
                apply_tolerance=False,
                positive_tolerance=positive_tolerance,
            )
            # add tolerance to list comprehension variable
            var_k = self.parse(
                expression="K",
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            countlist = "[" + var_k + " for K in " + countlist + "]"
        else:
            countlist = self.parse(
                expression[1][1],
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
        if len(expression[1]) == 3:
            # the countif conditions is empty so count the True elements
            res = "(sum(" + countlist[:-1] + ", axis=0, dtype=float))"
        elif isinstance(expression[1][3], str):
            # the countif conditions a single condition that has to be applied to all item in the sumlist
            condition = self.parse(
                expression[1][3:],
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )[:-1]
            # a single condition applied to all columns
            # if the condition does not apply, it results in NaN
            # and then we check if it is not NaN
            res = (
                "(sum("
                + countlist.replace("{", "~{").replace(
                    "}", "}.where(" + condition + ").isna()"
                )
                + ", axis=0, dtype=float))"
            )
        else:
            # the countif conditions a list of conditions
            conditionlist = self.parse(
                expression[1][3][:-1],
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            res = (
                "(sum("
                + "[~v.where(c).isna() for (v,c) in zip("
                + countlist
                + ","
                + conditionlist
                + ")]"
                + ", axis=0, dtype=float))"
            )
        return res

    def parse_in(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process in operator

        Example
            # Test Case for the parse_in method
            expression = ['{"A"}', 'in', ['[', '"B"', ',', '"A"', ']']]  # Example expression for 'in' operation
            idx = 1  # The index of 'in' in the expression

            # Call the parse_in method
            result = ruleminer.RuleParser().parse_in(
                idx=idx,
                item="in",
                expression=expression,
            )

            # Print the result
            print(result)
                ({"A"}.isin(["B","A"]))
        """
        left_side = expression[:idx]
        right_side = expression[idx + 1 :]
        # process in operator
        if item.lower() in ["not in", "not between"]:
            res = "~"
        else:
            res = ""
        for i in left_side:
            res += self.parse(
                i,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
        if item.lower() in ["in", "not in"]:
            res += ".isin("
            for i in right_side:
                res += self.parse(
                    i,
                    apply_tolerance=apply_tolerance,
                    positive_tolerance=positive_tolerance,
                )
            res += ")"
        elif item.lower() in ["between", "not between"]:
            res += ".between("
            for i in right_side[0][1:-1]:
                res += self.parse(
                    i,
                    apply_tolerance=apply_tolerance,
                    positive_tolerance=positive_tolerance,
                ).lower()
            res += ")"
        return res

    def parse_statistical_functions(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process quantile function

        Example
            # Test Case for `parse_quantile`
            expression = ['{"A"}', 'quantile', ['[', '0.75', ']']]  # Example expression for quantile function
            idx = 1  # The index of 'quantile' in the expression

            # Parameters and data for the test
            params = {"evaluate_statistics": True}  # Simulate that quantile evaluation is enabled
            data = {"A": [1, 2, 3, 4, 5]}  # Mock data, not directly used in this test

            # Initialize RuleMiner object
            rule_miner = RuleMiner(params=params, data=data)

            # Call the parse_quantile method
            result = rule_miner.parse_quantile(
                idx=idx,
                item="quantile",
                expression=expression,
            )

            # Print the result
            print(result)
                0.75
        """
        if self.params.get("evaluate_statistics", False):
            res = ""
            for i in expression[:idx]:
                res += self.parse(
                    i,
                    apply_tolerance=apply_tolerance,
                    positive_tolerance=positive_tolerance,
                )
            quantile_code = pandas_column(
                expression=flatten(expression[idx : idx + 2]),
                data=self.data,
            )
            evaluator = CodeEvaluator(self.params)
            evaluator.set_params(self.params)
            evaluator.set_data(self.data)
            quantile_result, _ = evaluator.evaluate_str(
                expression=quantile_code, encodings={}
            )
            res += str(np.round(quantile_result, 8))
            return res
        else:
            res = ""
            for i in expression[idx + 1 :]:
                res += self.parse(
                    i,
                    apply_tolerance=apply_tolerance,
                    positive_tolerance=positive_tolerance,
                )
            return item + res

    def parse_list_comprehension(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process and generate a list comprehension string representation.

        Example:
            # Test Case for `parse_list_comprehension`
            expression = ['[', ['K'], 'for', 'K', 'in', '[', [['{"A"}'], ',', ['{"B"}']], ']']]
            idx = 1  # The index of 'for' in the expression

            # Call the parse_list_comprehension method
            result = ruleminer.RuleParser().parse_list_comprehension(
                idx=idx,
                item="for",
                expression=expression,
            )

            # Print the result
            print(result)
                '[K for K in ['A', 'B']]'

        """
        lc_expr = self.parse(
            expression[1],
            apply_tolerance=False
            if contains_string(expression[1])
            else apply_tolerance,
            positive_tolerance=positive_tolerance,
        )
        lc_var = expression[3]
        lc_iter = self.parse_list(
            0,
            expression[5:],
            apply_tolerance=False,
            positive_tolerance=positive_tolerance,
        )
        return "[" + lc_expr + " for " + lc_var + " in " + lc_iter + "]"

    def parse_comparison(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process tolerance parameter to comparison
        Do not apply if left side or right side of the comparison is a string

        Example:

            # Test Case for `parse_comparison`

            # Example 1: Without tolerance (basic comparison)
            expression = ['A', '==', 'B']
            idx = 1  # Index of '==' in the expression
            item = '=='  # Comparison operator
            params = {}  # No tolerance parameter set

            rule_miner = RuleMiner(params=params)

            # Call parse_comparison with no tolerance
            result_no_tolerance = rule_miner.parse_comparison(
                idx=idx,
                item=item,
                expression=expression,
                apply_tolerance=False,
                positive_tolerance=True
            )

            print(f"Result without tolerance: {result_no_tolerance}")
                A == B

            # Example 2: With tolerance (comparison with tolerance applied)
            expression_with_tolerance = ['A', '==', 'B']
            params_with_tolerance = {'tolerance': True}  # Tolerance parameter set

            rule_miner_with_tolerance = RuleMiner(params=params_with_tolerance)

            # Call parse_comparison with tolerance
            result_with_tolerance = rule_miner_with_tolerance.parse_comparison(
                idx=idx,
                item=item,
                expression=expression_with_tolerance,
                apply_tolerance=True,
                positive_tolerance=True
            )

            print(f"Result with tolerance: {result_with_tolerance}")
                Result with tolerance: _equal(A(+), A(-), B(+), B(-))

        """
        if "tolerance" in self.params.keys() and (
            not (
                contains_string(expression[:idx])
                or contains_string(expression[idx + 1 :])
            )
        ):
            left_side = self.parse(
                expression=expression[:idx],
                apply_tolerance=False,
                positive_tolerance=True,
            )
            left_side_pos = self.parse(
                expression=expression[:idx],
                apply_tolerance=True,
                positive_tolerance=True,
            )
            left_side_neg = self.parse(
                expression=expression[:idx],
                apply_tolerance=True,
                positive_tolerance=False,
            )
            right_side = self.parse(
                expression=expression[idx + 1 :],
                apply_tolerance=False,
                positive_tolerance=True,
            )
            right_side_pos = self.parse(
                expression=expression[idx + 1 :],
                apply_tolerance=True,
                positive_tolerance=True,
            )
            right_side_neg = self.parse(
                expression=expression[idx + 1 :],
                apply_tolerance=True,
                positive_tolerance=False,
            )
            if item in ["=="]:
                res = (
                    "_eq("
                    + left_side
                    + ", "
                    + right_side
                    + ", "
                    + left_side_pos
                    + ", "
                    + left_side_neg
                    + ", "
                    + right_side_pos
                    + ", "
                    + right_side_neg
                    + ")"
                )
            if item in ["!="]:
                res = (
                    "_ne("
                    + left_side
                    + ", "
                    + right_side
                    + ", "
                    + left_side_pos
                    + ", "
                    + left_side_neg
                    + ", "
                    + right_side_pos
                    + ", "
                    + right_side_neg
                    + ")"
                )
            if item in [">="]:
                res = (
                    "_ge("
                    + left_side
                    + ", "
                    + right_side
                    + ", "
                    + left_side_pos
                    + ", "
                    + left_side_neg
                    + ", "
                    + right_side_pos
                    + ", "
                    + right_side_neg
                    + ")"
                )
            if item in ["<="]:
                res = (
                    "_le("
                    + left_side
                    + ", "
                    + right_side
                    + ", "
                    + left_side_pos
                    + ", "
                    + left_side_neg
                    + ", "
                    + right_side_pos
                    + ", "
                    + right_side_neg
                    + ")"
                )
            elif item in [">"]:
                res = (
                    "_gt("
                    + left_side
                    + ", "
                    + right_side
                    + ", "
                    + left_side_pos
                    + ", "
                    + left_side_neg
                    + ", "
                    + right_side_pos
                    + ", "
                    + right_side_neg
                    + ")"
                )
            elif item in ["<"]:
                res = (
                    "_lt("
                    + left_side
                    + ", "
                    + right_side
                    + ", "
                    + left_side_pos
                    + ", "
                    + left_side_neg
                    + ", "
                    + right_side_pos
                    + ", "
                    + right_side_neg
                    + ")"
                )
        else:
            left_side = expression[:idx]
            right_side = expression[idx + 1 :]
            res = (
                self.parse(
                    left_side,
                    apply_tolerance=apply_tolerance,
                    positive_tolerance=positive_tolerance,
                )
                + item
                + self.parse(
                    right_side,
                    apply_tolerance=apply_tolerance,
                    positive_tolerance=positive_tolerance,
                )
            )
        return res

    def parse_math_operator(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process math operators

        If the operator is - or / then the tolerance direction must be reversed

        The item is the first math operator in de expression

        We process the expression from left to right

        The parser grouped + and - together and the * and / (so these are not mixed)

        """
        # parse left side and put in res
        res = self.parse(
            expression=expression[:idx],
            apply_tolerance=apply_tolerance,
            positive_tolerance=positive_tolerance,
        )
        res_pos = self.parse(
            expression=expression[:idx],
            apply_tolerance=apply_tolerance,
            positive_tolerance=True,
        )
        res_neg = self.parse(
            expression=expression[:idx],
            apply_tolerance=apply_tolerance,
            positive_tolerance=False,
        )
        while idx < len(expression):
            item = expression[idx]
            # change direction depending on item
            if item in ["+", "*", "**"]:
                # for + and * do not change direction of tolerance
                current_positive_tolerance = (
                    positive_tolerance if apply_tolerance else positive_tolerance
                )
            elif item in ["-", "/"]:
                # for - and / change direction of tolerance
                current_positive_tolerance = (
                    not positive_tolerance if apply_tolerance else positive_tolerance
                )
            if item in ["*", "/"]:
                if (
                    apply_tolerance
                    and contains_column(expression[idx + 1])
                    and contains_column(expression[:idx])
                ):
                    # both sides contain at least one column that are multiplied or divided
                    # so we must use adjusted * and / operators that calculate the
                    # lower and upper bound correctly
                    right_pos = self.parse(
                        expression=expression[idx + 1],
                        apply_tolerance=apply_tolerance,
                        positive_tolerance=True,
                    )
                    right_neg = self.parse(
                        expression=expression[idx + 1],
                        apply_tolerance=apply_tolerance,
                        positive_tolerance=False,
                    )
                    if item == "*":
                        new_res = "_mul"
                    elif item == "/":
                        new_res = "_div"
                    new_res += (
                        "("
                        + res_pos
                        + ", "
                        + res_neg
                        + ", "
                        + right_pos
                        + ", "
                        + right_neg
                    )
                    res_pos = new_res + ',"+")'
                    res_neg = new_res + ',"-")'
                    if positive_tolerance:
                        res = res_pos
                    else:
                        res = res_neg
                else:
                    res += item + self.parse(
                        expression=expression[idx + 1],
                        apply_tolerance=apply_tolerance,
                        positive_tolerance=current_positive_tolerance,
                    )
                    res_pos += item + self.parse(
                        expression=expression[idx + 1],
                        apply_tolerance=apply_tolerance,
                        positive_tolerance=True,
                    )
                    res_neg += item + self.parse(
                        expression=expression[idx + 1],
                        apply_tolerance=apply_tolerance,
                        positive_tolerance=False,
                    )
            elif item == "**":
                res = (
                    "max(0, "
                    + res
                    + ")"
                    + item
                    + self.parse(
                        expression=expression[idx + 1],
                        apply_tolerance=apply_tolerance,
                        positive_tolerance=current_positive_tolerance,
                    )
                )
            else:
                # for + and - simply process expression
                res += item + self.parse(
                    expression=expression[idx + 1],
                    apply_tolerance=apply_tolerance,
                    positive_tolerance=current_positive_tolerance,
                )
            idx += 2
        return res

    def parse_abs(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process math operators

        If the operator is - or / then the tolerance direction must be reversed

        The item is the first math operator in de expression

        We process the expression from left to right

        The parser grouped + and - together and the * and / (so these are not mixed)

        """
        # parse left side and put in res
        res = self.parse(
            expression=expression[idx + 1 :],
            apply_tolerance=apply_tolerance,
            positive_tolerance=positive_tolerance,
        )
        if apply_tolerance:
            res_pos = self.parse(
                expression=expression[idx + 1 :],
                apply_tolerance=apply_tolerance,
                positive_tolerance=True,
            )
            res_neg = self.parse(
                expression=expression[idx + 1 :],
                apply_tolerance=apply_tolerance,
                positive_tolerance=False,
            )
            if positive_tolerance:
                res = "_abs" + "(" + res_pos + ", " + res_neg + ', "+")'
            else:
                res = "_abs" + "(" + res_pos + ", " + res_neg + ', "-")'
            return res
        else:
            res = "abs" + "(" + res + ")"
            return res

    def parse_column(
        self,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process expression with column

        If apply_tolerance is True then a self.tolerance must be given
        The key of the tolerance to be used is initially set to 'default'
        If the tolerance definition of the key is None then tolerance is not applied

        Example:
            parameters = {
                "tolerance": {
                    "default": {
                        (0, 1e3): 0,
                    },
                },
            }
            expression = '{"A"}'

            result = ruleminer.RuleMiner(params=parameters).parse_column(
                expression=expression,
                apply_tolerance=True
            )
            print(result)
                '({"A"}.apply(_tol, args=("+", "default",))))'

        """
        args = "default"
        if apply_tolerance:
            if self.tolerance is not None:
                for key, tol in self.tolerance.items():
                    # check is default tolerance is set to None then do not apply
                    if key == "default" and tol is None:
                        args = None
                    # match key with column name
                    if re.fullmatch(key, expression[2:-2]):
                        if tol is None:
                            args = None
                        else:
                            args = key
        if apply_tolerance and args:
            # process tolerance on column
            if expression == "K":
                if positive_tolerance:
                    return expression + '.apply(_tol, args=("+", "' + args + '",))'
                else:
                    return expression + '.apply(_tol, args=("-", "' + args + '",))'
            if positive_tolerance:
                return expression.replace(
                    "}", '}.apply(_tol, args=("+", "' + args + '",))'
                )
            else:
                return expression.replace(
                    "}", '}.apply(_tol, args=("-", "' + args + '",))'
                )
        elif expression.lower() == "in":
            return ".isin"
        else:
            return expression

    def parse_string(
        self,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process expression with string

        Example:
            expression = ['"A"']

            result = ruleminer.RuleParser().parse_string(
                expression=expression
            )
            print(result)
                'A'

            parameters = {
                "tolerance": {
                    "default": {
                        (0, 1e3): 0,
                    },
                },
            }
        """
        if expression.lower() == "in":
            return ".isin"
        else:
            return expression

    def parse_match(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process match operator

        Example:
            expression = ['{"A"}', 'match', '"A"']

            result = ruleminer.RuleParser().parse_match(
                idx=1,
                expression=expression,
                apply_tolerance=False
            )
            print(result)
                '
                ({"A"}.str.match("A"))
                '
        """
        left_side = expression[:idx]
        right_side = expression[idx + 1 :]
        # process in operator
        res = ""
        for i in left_side:
            res += self.parse(
                i,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
        res += ".str.match(r"
        for i in right_side:
            res += self.parse(
                i,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
        return res + ", na=False)"

    def parse_contains(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process match operator

        Example:
            expression = ['{"A"}', 'contains', '"A"']

            result = ruleminer.RuleParser().parse_match(
                idx=1,
                expression=expression,
                apply_tolerance=False
            )
            print(result)
                '
                ({"A"}.str.contains("A"))
                '
        """
        left_side = expression[:idx]
        right_side = expression[idx + 1 :]
        # process in operator
        if item.lower() == "not contains":
            res = "~"
        else:
            res = ""
        for i in left_side:
            res += self.parse(
                i,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
        res += ".str.contains("
        for i in right_side:
            res += self.parse(
                i,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
        return res + ", na=False)"

    def parse_exact(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process exact operator

        Example:
            expression = ['exact', '(', {"A"}', ')']

            result = ruleminer.RuleParser().parse_exact(
                idx=0,
                expression=expression,
                apply_tolerance=True
            )
            print(result)
                '
                ({"A"})
                '
        """
        parameters_len = len(expression[idx + 1])
        if parameters_len == 3:
            # no parameters, only expression -> do no apply lower and upper bound
            return self.parse(
                expression[idx + 1][1],
                apply_tolerance=False,
                positive_tolerance=positive_tolerance,
            )
        elif parameters_len == 5:
            # one parameter -> upper and lower bound combined
            bound = expression[idx + 1][3]
            if apply_tolerance:
                if positive_tolerance:
                    return (
                        "("
                        + self.parse(
                            expression[idx + 1][1],
                            apply_tolerance=False,
                            positive_tolerance=positive_tolerance,
                        )
                        + "+"
                        + str(bound)
                        + ")"
                    )
                else:
                    return (
                        "("
                        + self.parse(
                            expression[idx + 1][1],
                            apply_tolerance=False,
                            positive_tolerance=positive_tolerance,
                        )
                        + "-"
                        + str(bound)
                        + ")"
                    )
            else:
                return self.parse(
                    expression[idx + 1][1],
                    apply_tolerance=False,
                    positive_tolerance=positive_tolerance,
                )
        elif parameters_len == 7:
            lower_bound = expression[idx + 1][3]
            upper_bound = expression[idx + 1][5]
            # two parameter -> upper and lower bound separately
            if apply_tolerance:
                if positive_tolerance:
                    return (
                        "("
                        + self.parse(
                            expression[idx + 1][1],
                            apply_tolerance=False,
                            positive_tolerance=positive_tolerance,
                        )
                        + "+"
                        + str(upper_bound)
                        + ")"
                    )
                else:
                    return (
                        "("
                        + self.parse(
                            expression[idx + 1][1],
                            apply_tolerance=False,
                            positive_tolerance=positive_tolerance,
                        )
                        + "-"
                        + str(lower_bound)
                        + ")"
                    )
            else:
                return self.parse(
                    expression[idx + 1][1],
                    apply_tolerance=False,
                    positive_tolerance=positive_tolerance,
                )

    def parse_maxminabs(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process min, max, abs operator
        """
        res = ""
        for i in expression[idx + 1 :]:
            res += self.parse(
                i,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
        return item + res

    def parse_list(
        self,
        idx: int,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process decimal parameter to expression with ==

        Example:
            expression = ['{"A"}', '==', '{"B"}']

            result = ruleminer.RuleParser().parse_decimal(
                idx=1,
                expression=expression
            )
            print(result)

                '(abs({"A"}-{"B"}) <= 1.5)'
        """
        return "".join(
            [
                self.parse(
                    i,
                    apply_tolerance=apply_tolerance,
                    positive_tolerance=positive_tolerance,
                )
                for i in expression
            ]
        )

    def parse_decimal(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process decimal parameter to expression with ==

        Example:
            expression = ['{"A"}', '==', '{"B"}']

            result = ruleminer.RuleParser().parse_decimal(
                idx=1,
                expression=expression
            )
            print(result)

                '(abs({"A"}-{"B"}) <= 1.5)'
        """
        decimal = self.params.get("decimal", 0)
        precision = 1.5 * 10 ** (-decimal)
        res = (
            "abs("
            + self.parse(
                expression[:idx],
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            + "-"
            + self.parse(
                expression[idx + 1 :],
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            + ") <= "
            + str(precision)
        )
        return res


def contains_string(expression: Union[str, list]):
    """
    Check if a given expression contains a string

    Args:
        s (str, list): The expression or string to be checked.

    Returns:
        bool: True if the string is enclosed in quotes, False otherwise.

    Example:
        contains_string('"A"')
            True

        contains_string('{"A"}')
            False

        contains_string(['{"A"}', '"0"'])
            True
    """
    if isinstance(expression, str):
        return is_string(expression)
    else:
        for idx, item in enumerate(expression):
            if isinstance(item, str) and item.lower() in ["sumif", "countif"]:
                # if sumif or countif then do not search for string in conditions
                return contains_string(expression[idx + 1][0])
            elif isinstance(item, str) and item.lower() in ["corr"]:
                # if corr then do not search for string in first parameter
                return contains_string(expression[idx + 1][2:])
            elif contains_string(item):
                return True
        return False


def contains_column(expression: Union[str, list]):
    """
    Check if a given expression contains a column expression

    Args:
        s (str, list): The expression or string to be checked.

    Returns:
        bool: True if the string is enclosed in curly brackets and quotes, False otherwise.

    Example:
        contains_column('"A"')
            False

        contains_column('{"A"}')
            False

        contains_column(['{"A"}', '"0"'])
            True
    """
    if isinstance(expression, str):
        return is_column(expression)
    else:
        for idx, item in enumerate(expression):
            if isinstance(item, str) and item.lower() in ["sumif", "countif"]:
                # if sumif or countif then do not search for string in conditions
                return contains_column(expression[idx + 1][0])
            if contains_column(item):
                return True
        return False
