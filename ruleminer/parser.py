"""Parser module."""

from typing import Union
from .utils import (
    flatten,
    is_column,
    is_string,
)
from .const import VAR_Z
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

    """

    def __init__(
        self,
    ):
        """ """
        self.keywords_function_mapping = [
            (set(["==", "!=", "<", "<=", ">", ">="]), self.parse_comparison),
            (set(["quantile"]), self.parse_quantile),
            (set(["for"]), self.parse_list_comprehension),
            (set(["in"]), self.parse_in),
            (set(["substr"]), self.parse_substr),
            (set(["split"]), self.parse_split),
            (set(["sum"]), self.parse_sum),
            (set(["sumif"]), self.parse_sumif),
            (set(["countif"]), self.parse_countif),
            (set(["match"]), self.parse_match),
            (set(["max", "min", "abs"]), self.parse_maxminabs),
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
            (set(["-", "/"]), self.parse_minus_divide),
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
            expression = ['SUBSTR', ['(', {"C"}', ',', '2', ',', '4', ')']]

            result = ruleminer.RuleMiner().parse_substr(
                idx=0,
                expression=expression,
                apply_tolerance=False
            )
            print(result)
                '
                (({"C"}.str.slice(2,4)))
                '
        """
        _, string, _, start, _, stop, _ = expression[idx + 1]
        res = (
            self.parse(
                string,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
            + ".str.slice("
            + start
            + ","
            + stop
            + ")"
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

            result = ruleminer.RuleMiner().parse_timedatefunction(
                idx=0,
                expression=expression,
                apply_tolerance=False
            )
            print(result)
                '
                (({"C"}.dt.day))
                '
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

            result = ruleminer.RuleMiner().parse_timedelta_function(
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
            s = "'D'"
        elif item.lower() == "months":
            s = "'M'"
        elif item.lower() == "years":
            s = "'Y'"
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

            result = ruleminer.RuleMiner().parse_substr(
                idx=0,
                expression=expression,
                apply_tolerance=False
            )
            print(result)
                '
                (({"C"}.str.slice("C",2)).isin("D"))
                '
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
        # process sum and sumif functions
        # do not apply tolerance on the list of datapoints
        # because we use list comprehension below
        """
        ['sumif', [['[', '{"Assets"}', ',', '{"Own_funds"}', ']'], ',', '{"Type"}', '==', '"life_insurer"']]
        """
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
        # process count and countif functions
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
        if isinstance(expression[1][3], str):
            # the sumif conditions a single condition that has to be applied to all item in the sumlist
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
            # the sumif conditions a list of conditions
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

        Example:
            expression = ['{"A"}', 'in', ['[', '"B"', ',', '"A"', ']']]

            result = ruleminer.RuleMiner().parse_in(
                idx=1,
                expression=expression,
                apply_tolerance=False
            )
            print(result)
                '
                ({"A"}.isin(["B","A"]))
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
        res += ".isin("
        for i in right_side:
            res += self.parse(
                i,
                apply_tolerance=apply_tolerance,
                positive_tolerance=positive_tolerance,
            )
        return res + ")"

    def parse_quantile(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process quantile function

        """
        if self.params.get("evaluate_quantile", False):
            res = ""
            for i in expression[:idx]:
                res += self.parse(
                    i,
                    apply_tolerance=apply_tolerance,
                    positive_tolerance=positive_tolerance,
                )
            quantile_code = {
                VAR_Z: pandas_column(
                    expression=flatten(expression[idx : idx + 2]),
                    data=self.data,
                )
            }
            evaluator = CodeEvaluator()
            evaluator.set_params(self.params)
            evaluator.set_data(self.data)
            quantile_result = evaluator.evaluate(expressions=quantile_code)[VAR_Z]
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
            return "quantile" + res

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
            Input: ['[', ['K'], 'for', 'K', 'in', '[', [['{"A"}'], ',', ['{"B"}']], ']']
            Output: "[K for K in ['A', 'B']]"

        Args:
            idx (int): The index position of the current element in the list.
            item (str): The item to be processed (not used in the current function).
            expression (Union[str, list]): The list comprehension expression to be processed.
            apply_tolerance (bool, optional): Flag to apply tolerance while parsing (default is False).
            positive_tolerance (bool, optional): Flag to determine positive tolerance behavior (default is True).

        Returns:
            str: A string representation of the processed list comprehension.

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
            expression = ['{"A"}', '<', '{"B"}']

            parameters = {
                "tolerance": {
                    "default": {
                        (0, 1e3): 0,
                    },
                },
            }

            result = ruleminer.RuleMiner(params=parameters).parse_comparison(
                expression=expression,
                apply_tolerance=True
            )
            print(result)
                '
                (
                    (
                        ({"A"}.apply(_tol, args=("+", "default",))))
                    )
                    <
                    (
                        ({"B"}.apply(_tol, args=("-", "default",))))
                    )
                )
                '
        """
        if "tolerance" in self.params.keys() and (
            not (
                contains_string(expression[:idx])
                or contains_string(expression[idx + 1 :])
            )
        ):
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
                    "_equal("
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
                    "_unequal("
                    + left_side_pos
                    + ", "
                    + left_side_neg
                    + ", "
                    + right_side_pos
                    + ", "
                    + right_side_neg
                    + ")"
                )
            elif item in [">", ">="]:
                res = left_side_pos + item + right_side_neg
            elif item in ["<", "<="]:
                res = left_side_neg + item + right_side_pos
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

    def parse_minus_divide(
        self,
        idx: int,
        item: str,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process - and /

        If the operator is - or / then the tolerance direction must be reversed

        """
        left_side = self.parse(
            expression=expression[:idx],
            apply_tolerance=apply_tolerance,
            positive_tolerance=positive_tolerance,
        )
        # the rest of the expression if evaluated as a list with reversed tolerance
        right_side = ""
        current_positive_tolerance = (
            not positive_tolerance if apply_tolerance else positive_tolerance
        )
        for right_side_item in expression[idx + 1 :]:
            if right_side_item in ["+", "*"]:
                current_positive_tolerance = (
                    positive_tolerance if apply_tolerance else positive_tolerance
                )
            elif right_side_item in ["-", "/"]:
                current_positive_tolerance = (
                    not positive_tolerance if apply_tolerance else positive_tolerance
                )
            right_side += self.parse(
                expression=[right_side_item],
                apply_tolerance=apply_tolerance,
                positive_tolerance=current_positive_tolerance,
            )
        return left_side + item + right_side

    def parse_column(
        self,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        Process expression with column

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
        if apply_tolerance:
            # process tolerance on column
            args = ""
            for key, tol in self.tolerance.items():
                if re.fullmatch(key, expression[2:-2]):
                    args = key
            if args == "":
                args = "default"
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

            result = ruleminer.RuleMiner().parse_string(
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
        Process in operator

        Example:
            expression = ['{"A"}', 'match', '"A"']

            result = ruleminer.RuleMiner().parse_in(
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

            result = ruleminer.RuleMiner().parse_decimal(
                idx=1,
                expression=expression
            )
            print(result)

                '(abs(({"A"})-({"B"})) <= 1.5)'
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

            result = ruleminer.RuleMiner().parse_decimal(
                idx=1,
                expression=expression
            )
            print(result)

                '(abs(({"A"})-({"B"})) <= 1.5)'
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

    def parse(
        self,
        expression: Union[str, list],
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ) -> str:
        """
        General fcuntion to parse expression (tree structure) to pseudo code (str).

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

            result = ruleminer.RuleMiner().parse(expression)

            print(result)

                "({"A"}.str.slice(1,1))"

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
            if contains_string(item):
                return True
        return False
