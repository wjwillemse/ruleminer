"""Main module."""

import pandas as pd
import logging
import itertools
import re
import numpy as np
import pyparsing

from ruleminer import utils
from ruleminer import parser
from ruleminer import metrics
from ruleminer.const import CONFIDENCE
from ruleminer.const import ABSOLUTE_SUPPORT
from ruleminer.const import ABSOLUTE_EXCEPTIONS
from ruleminer.const import ADDED_VALUE

from ruleminer.const import RULE_ID
from ruleminer.const import RULE_GROUP
from ruleminer.const import RULE_DEF
from ruleminer.const import RULE_STATUS
from ruleminer.const import RULE_VARIABLES
from ruleminer.const import ENCODINGS
from ruleminer.const import DUNDER_DF
from ruleminer.parser import RULE_SYNTAX
from ruleminer.encodings import encodings_definitions


class RuleMiner:
    """ """

    def __init__(
        self,
        templates: list = None,
        rules: pd.DataFrame = None,
        data: pd.DataFrame = None,
        params: dict = None,
    ):
        """ """
        self.params = dict()
        self.update(templates=templates, rules=rules, data=data, params=params)

    def update(
        self,
        templates: list = None,
        rules: pd.DataFrame = None,
        data: pd.DataFrame = None,
        params: dict = None,
    ):
        """ """
        logger = logging.getLogger(__name__)

        if params is not None:
            self.params = params
        self.metrics = self.params.get(
            "metrics", [ABSOLUTE_SUPPORT, ABSOLUTE_EXCEPTIONS, CONFIDENCE]
        )
        self.metrics = metrics.metrics(self.metrics)
        self.required_variables = metrics.required_variables(self.metrics)
        self.filter = self.params.get("filter", {CONFIDENCE: 0.5, ABSOLUTE_SUPPORT: 2})

        if data is not None:
            self.data = data
            self.eval_dict = {
                "MAX": np.maximum,
                "MIN": np.minimum,
                "ABS": np.abs,
                "QUANTILE": np.quantile,
                "max": np.maximum,
                "min": np.minimum,
                "abs": np.abs,
                "quantile": np.quantile,
            }

            # def get_encodings():
            #     for item in encodings_definitions:
            #         exec(encodings_definitions[item])
            #     encodings = {
            #         encodings[item]: locals()[item]
            #         for item in encodings_definitions.keys()
            #     }
            #     return encodings
            # encodings = metapattern.get("encodings", None)
            # if encodings is not None:
            #     encodings_code = get_encodings()
            #     for c in self.data.columns:
            #         if c in encodings.keys():
            #             self.data[c] = eval(
            #                 str(encodings[c]) + "(s)",
            #                 encodings_code,
            #                 {"s": self.data[c]},
            #             )

        if templates is not None:
            self.templates = templates
            self.generate()

        if rules is not None:
            self.rules = rules
            self.evaluate()

        logger.info("Finished")

        return None

    def generate(self):
        """ """
        assert (
            self.templates is not None
        ), "Unable to generate rules, no templates defined."
        assert self.data is not None, "Unable to generate rules, no data defined."

        self.setup_rules_dataframe()

        for template in self.templates:
            self.generate_rules(template=template)

        return None

    def evaluate(self):
        """ """
        assert self.rules is not None, "Uable to evaluate data, no rules defined."
        assert self.data is not None, "Uable to evaluate data, no data defined."

        self.setup_results_dataframe()

        # add temporary index columns (to allow rules based on index data)
        for level in range(len(self.data.index.names)):
            self.data[
                str(self.data.index.names[level])
            ] = self.data.index.get_level_values(level=level)

        for idx in self.rules.index:

            required_variables = metrics.required_variables(
                [ABSOLUTE_SUPPORT, ABSOLUTE_EXCEPTIONS, CONFIDENCE]
            )

            expression = self.rules.loc[idx, RULE_DEF]
            rule_code = parser.python_code(
                expression=expression, required=required_variables, r_type="index"
            )
            results = self.evaluate_code(expressions=rule_code, dataframe=self.data)
            rule_metrics = metrics.calculate_metrics(
                results=results,
                metrics=[ABSOLUTE_SUPPORT, ABSOLUTE_EXCEPTIONS, CONFIDENCE],
            )
            self.add_results(idx, rule_metrics, results["X and Y"], results["X and ~Y"])

        # remove temporarily added index columns
        for level in range(len(self.data.index.names)):
            del self.data[str(self.data.index.names[level])]

        return self.results

    def setup_rules_dataframe(self):
        """
        Helper function to set up the rules dataframe
        """
        self.rules = pd.DataFrame(
            columns=[RULE_ID, RULE_GROUP, RULE_DEF, RULE_STATUS]
            + self.metrics
            + [ENCODINGS]
        )

    def setup_results_dataframe(self):
        """
        Helper function to set up the results dataframe
        """
        self.results = pd.DataFrame(
            columns=[RULE_ID, RULE_GROUP, RULE_DEF, RULE_STATUS]
            + [ABSOLUTE_SUPPORT, ABSOLUTE_EXCEPTIONS, CONFIDENCE]
            + ["result", "indices"]
        )

    def generate_rules(self, template: dict):
        """ """
        logger = logging.getLogger(__name__)

        group = template.get("group", 0)
        encodings = template.get("encodings", {})
        template_expression = template.get("expression", None)

        # temporarily add index names as columns, so we derive rules with index names
        for level in range(len(self.data.index.names)):
            self.data[
                str(self.data.index.names[level])
            ] = self.data.index.get_level_values(level=level)

        # if the template expression is not a if then rule then it is changed into a if then rule
        try:
            parsed, if_part, then_part = self.split_rule(expression=template_expression)
        except:
            logger.error(
                'Parsing error in expression "' + str(template_expression) + '"'
            )
            return None

        sorted_expressions = {}

        candidates = []
        if_part_column_values = self.search_column_value(if_part, [])
        if_part_substitutions = [
            utils.evaluate_column_regex(
                df=self.data,
                column_regex=col[0],
                value_regex=col[1],
            )
            for col in if_part_column_values
        ]
        if_part_substitutions = itertools.product(*if_part_substitutions)
        logger.info(
            "Expression for if-part ("+str(if_part)+") generated"
        )
        for if_part_substitution in if_part_substitutions:
            candidate, _, _, _, _ = self.substitute_list(
                expression=if_part,
                columns=[item[0] for item in if_part_column_values],
                values=[item[1] for item in if_part_column_values],
                column_substitutions=[item[0] for item in if_part_substitution],
                value_substitutions=[
                    item[1] if len(item) > 1 else None for item in if_part_substitution
                ],
            )
            df_code = parser.python_code_for_columns(expression=flatten(candidate))
            df_eval = self.evaluate_code(expressions=df_code, dataframe=self.data)["X"]
            if df_eval is not None:
                then_part_column_values = self.search_column_value(then_part, [])
                then_part_substitutions = [
                    utils.evaluate_column_regex(
                        df=df_eval,
                        column_regex=col[0],
                        value_regex=col[1],
                    )
                    for col in then_part_column_values
                ]
                if if_part_substitution != ():
                    expression_substitutions = [
                        if_part_substitution + item
                        for item in itertools.product(*then_part_substitutions)
                    ]
                else:
                    expression_substitutions = list(
                        itertools.product(*then_part_substitutions)
                    )
                template_column_values = if_part_column_values + then_part_column_values
                for substitution in expression_substitutions:
                    candidate_parsed, _, _, _, _ = self.substitute_list(
                        expression=parsed,
                        columns=[item[0] for item in template_column_values],
                        values=[item[1] for item in template_column_values],
                        column_substitutions=[item[0] for item in substitution],
                        value_substitutions=[
                            item[1] if len(item) > 1 else None for item in substitution
                        ],
                    )
                    sorted_expression = flatten_and_sort(candidate_parsed)[1:-1]
                    reformulated_expression = self.reformulate(candidate_parsed)[1:-1]
                    if sorted_expression not in sorted_expressions.keys():
                        sorted_expressions[sorted_expression] = True
                        rule_code = parser.python_code(
                            expression=reformulated_expression,
                            required=self.required_variables,
                            r_type="values",
                        )
                        rule_output = self.evaluate_code(
                            expressions=rule_code, dataframe=df_eval
                        )
                        rule_metrics = metrics.calculate_metrics(
                            results=rule_output, metrics=self.metrics
                        )
                        logger.debug(
                            "Candidate expression "
                            + reformulated_expression
                            + " has rule metrics "
                            + str(rule_metrics)
                        )
                        if self.apply_filter(metrics=rule_metrics):
                            self.add_rule(
                                rule_id=len(self.rules.index),
                                rule_group=group,
                                rule_def=reformulated_expression,
                                rule_status="",
                                rule_metrics=rule_metrics,
                                encodings=encodings,
                            )

        # remove temporarily added index columns
        for level in range(len(self.data.index.names)):
            del self.data[str(self.data.index.names[level])]

    def search_column_value(self, expr, column_value):
        """ """
        if isinstance(expr, str):
            if is_column(expr):
                column_value.append((expr, None))
        elif isinstance(expr, list):
            if len(expr) == 3 and is_column(expr[0]) and is_string(expr[2]):
                column_value.append((expr[0], expr[2]))
            elif len(expr) == 3 and is_column(expr[2]) and is_string(expr[0]):
                column_value.append((expr[2], expr[0]))
            else:
                for item in expr:
                    self.search_column_value(item, column_value)
        return column_value

    def split_rule(self, expression: str = ""):
        """ """
        condition = re.compile(r"if(.*)then(.*)", re.IGNORECASE)
        rule_parts = condition.search(expression)
        if rule_parts is not None:
            if_part = RULE_SYNTAX.parse_string(rule_parts.group(1)).as_list()
            then_part = RULE_SYNTAX.parse_string(rule_parts.group(2)).as_list()
        else:
            expression = "if () then " + expression
            if_part = ""
            then_part = RULE_SYNTAX.parse_string(expression).as_list()
        parsed = RULE_SYNTAX.parse_string(expression).as_list()
        return parsed, if_part, then_part

    def substitute_list(
        self,
        expression: str = "",
        columns: list = [],
        values: list = [],
        column_substitutions: list = [],
        value_substitutions: list = [],
    ):
        if isinstance(expression, str):
            if columns != [] and columns[0] in expression:
                # replace only first occurrence in string
                return (
                    expression.replace(
                        columns[0], '{"' + column_substitutions[0] + '"}', 1
                    ),
                    columns[1:],
                    values,
                    column_substitutions[1:],
                    value_substitutions,
                )
            elif values != [] and values[0] is not None and values[0] in expression:
                return (
                    expression.replace(
                        values[0], '"' + value_substitutions[0] + '"', 1
                    ),
                    columns,
                    values[1:],
                    column_substitutions,
                    value_substitutions[1:],
                )
            else:
                return (
                    expression,
                    columns,
                    values,
                    column_substitutions,
                    value_substitutions,
                )
        else:
            r = []
            for item in expression:
                (
                    item_s,
                    columns,
                    values,
                    column_substitutions,
                    value_substitutions,
                ) = self.substitute_list(
                    expression=item,
                    columns=columns,
                    values=values,
                    column_substitutions=column_substitutions,
                    value_substitutions=value_substitutions,
                )
                r.append(item_s)
            return r, columns, values, column_substitutions, value_substitutions

    def apply_filter(self, metrics: dict = {}):
        """
        This function applies the filter to the rule metrics (for example confidence > 0.75)
        """
        return all([metrics[metric] >= self.filter[metric] for metric in self.filter])

    def evaluate_code(
        self,
        expressions: dict = {},
        dataframe: pd.DataFrame = None,
        encodings: dict = {},
    ):
        """ """
        dict_values = {**{DUNDER_DF: dataframe}, **self.eval_dict}
        variables = {}
        for key in expressions.keys():
            try:
                variables[key] = eval(expressions[key], encodings, dict_values)
            except:
                variables[key] = None
        return variables

    def add_rule(
        self,
        rule_id: str = "",
        rule_group: int = 0,
        rule_def: str = "",
        rule_status: str = "",
        rule_metrics: dict = {},
        encodings: dict = {},
    ):
        """ """
        row = pd.DataFrame(
            data=[
                [rule_id, rule_group, rule_def, rule_status]
                + [rule_metrics[metric] for metric in self.metrics]
                + [encodings]
            ],
            columns=self.rules.columns,
        )
        self.rules = pd.concat([self.rules, row], ignore_index=True)

    def add_results(self, rule_idx, rule_metrics, co_indices, ex_indices):
        """ """

        nco = len(co_indices if co_indices is not None else [])
        nex = len(ex_indices if ex_indices is not None else [])

        if nco > 0:
            data = [
                [
                    self.rules.loc[rule_idx, RULE_ID],
                    self.rules.loc[rule_idx, RULE_GROUP],
                    self.rules.loc[rule_idx, RULE_DEF],
                    self.rules.loc[rule_idx, RULE_STATUS],
                    rule_metrics[ABSOLUTE_SUPPORT],
                    rule_metrics[ABSOLUTE_EXCEPTIONS],
                    rule_metrics[CONFIDENCE],
                    True,
                    None,
                ]
            ] * nco

            data = pd.DataFrame(columns=self.results.columns, data=data)
            data["indices"] = co_indices
            self.results = pd.concat([self.results, data], ignore_index=True)

        if nex > 0:
            data = [
                [
                    self.rules.loc[rule_idx, RULE_ID],
                    self.rules.loc[rule_idx, RULE_GROUP],
                    self.rules.loc[rule_idx, RULE_DEF],
                    self.rules.loc[rule_idx, RULE_STATUS],
                    rule_metrics[ABSOLUTE_SUPPORT],
                    rule_metrics[ABSOLUTE_EXCEPTIONS],
                    rule_metrics[CONFIDENCE],
                    False,
                    None,
                ]
            ] * nex

            data = pd.DataFrame(columns=self.results.columns, data=data)
            data["indices"] = ex_indices
            self.results = pd.concat([self.results, data], ignore_index=True)

        return None

    def reformulate(self, expression: str = ""):
        if isinstance(expression, str):
            return expression
        else:
            for idx, item in enumerate(expression):
                if (
                    "decimal" in self.params.keys()
                    and isinstance(item, str)
                    and (item in ["=="])
                ):
                    if not (
                        is_string(expression[idx - 1]) and len(expression[:idx]) == 1
                    ) and (
                        not (
                            is_string(expression[idx + 1])
                            and len(expression[idx + 1 :]) == 1
                        )
                    ):
                        decimal = self.params.get("decimal", 0)
                        precision = 1.5 * 10 ** (-decimal)
                        return (
                            "(abs("
                            + self.reformulate(expression[:idx])
                            + "-"
                            + self.reformulate(expression[idx + 1 :])
                            + ") <= "
                            + str(precision)
                            + ")"
                        )
                if (
                    self.params.get("evaluate_quantile", False)
                    and isinstance(item, str)
                    and item.lower() == "quantile"
                ):
                    l = ""
                    for item in expression[:idx]:
                        l += self.reformulate(item)
                    quantile_code = parser.python_code_for_intermediate(
                        flatten(expression[idx : idx + 2])
                    )
                    quantile_result = self.evaluate_code(
                        expressions=quantile_code, dataframe=self.data
                    )["X"]
                    l += str(np.round(quantile_result, 8))
                    for item in expression[idx + 2 :]:
                        l += self.reformulate(item)
                    return "(" + l + ")"

            l = ""
            for item in expression:
                l += self.reformulate(item)
            return "(" + l + ")"


def flatten_and_sort(expression: str = ""):
    if isinstance(expression, str):
        return expression
    else:
        if isinstance(expression[0], str) and expression[0].lower() in ["min", "max"]:
            l = (
                expression[0]
                + "("
                + "".join(sorted([flatten_and_sort(item) for item in expression[1:]]))
                + ")"
            )
        elif all(
            [is_string(item) or is_column(item) or item == "," for item in expression]
        ):
            return "".join(sorted(expression))
        else:
            # find elements to sort, sort then and add sorted to string
            idx_to_sort = set()
            for idx, item in enumerate(expression):
                if isinstance(item, str) and (item in ["==", "!="]):
                    idx_to_sort.add(idx - 1)
                    idx_to_sort.add(idx + 1)
                elif isinstance(item, str) and (item == "*"):
                    idx_to_sort.add(idx - 1)
                    idx_to_sort.add(idx + 1)
                elif (
                    isinstance(item, str) and (item == "+") and ("*" not in expression)
                ):
                    idx_to_sort.add(idx - 1)
                    idx_to_sort.add(idx + 1)
                elif isinstance(item, str) and (item == "&"):
                    idx_to_sort.add(idx - 1)
                    idx_to_sort.add(idx + 1)
                elif (
                    isinstance(item, str) and (item == "|") and ("&" not in expression)
                ):
                    idx_to_sort.add(idx - 1)
                    idx_to_sort.add(idx + 1)
            sorted_items = sorted(
                [flatten_and_sort(expression[i]) for i in list(idx_to_sort)]
            )

            l = ""
            count = 0
            for idx, item in enumerate(expression):
                if idx in idx_to_sort:
                    l += sorted_items[count]
                    count += 1
                else:
                    l += flatten_and_sort(item)
        return "(" + l + ")"


def flatten(expression):
    if isinstance(expression, str):
        return expression
    else:
        l = ""
        for item in expression:
            l += flatten(item)
        return "(" + l + ")"


def is_column(s):
    return len(s) > 4 and (
        (s[:2] == '{"' and s[-2:] == '"}') or (s[:2] == "{'" and s[-2:] == "'}")
    )


def is_string(s):
    return len(s) > 2 and (
        (s[:1] == '"' and s[-1:] == '"') or (s[:1] == "'" and s[-1:] == "'")
    )
