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
                DUNDER_DF: self.data,
                "MAX": np.maximum,
                "MIN": np.minimum,
                "ABS": np.abs,
                "max": np.maximum,
                "min": np.minimum,
                "abs": np.abs,
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
            results = self.evaluate_code(expressions=rule_code)
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

        try:
            parsed = RULE_SYNTAX.parse_string(template_expression).as_list()
        except:
            logger.error(
                'Parsing error in expression "' + str(template_expression) + '"'
            )
            return None

        logger.info("Parsed template: " + str(parsed))

        template_column_values = self.search_column_value(parsed, [])
        v = [
            utils.evaluate_column_regex(
                df=self.data,
                column_regex=col[0],
                value_regex=col[1],
            )
            for col in template_column_values
        ]
        cartesian_product = utils.Cartesian(v)

        # determine candidate rules
        candidates = []
        for substitution_set in cartesian_product:
            candidate_expression = self.substitute(
                expression=template_expression,
                column_values=template_column_values,
                substitutions=substitution_set,
            )
            regex_condition = re.compile(r"if(.*)then(.*)", re.IGNORECASE)
            rule = regex_condition.search(candidate_expression)
            if rule is None:
                candidate_expression = "if () then " + candidate_expression

            candidates.append(candidate_expression)

        candidates = prune_expressions(expressions=candidates, params=self.params)
        logger.info(
            "Template expression "
            + template_expression
            + " has "
            + str(len([t for t in template_column_values]))
            + " column(s), "
            + str(len([t for t in template_column_values if t[1] is not None]))
            + " string value(s), and "
            + str(len(cartesian_product))
            + " possible expressions ("
            + str(len(candidates))
            + " after pruning)"
        )

        for expression in candidates:
            rule_code = parser.python_code(
                expression=expression, required=self.required_variables, r_type="values"
            )
            rule_output = self.evaluate_code(expressions=rule_code)
            rule_metrics = metrics.calculate_metrics(
                results=rule_output, metrics=self.metrics
            )
            logger.debug(
                "Candidate expression "
                + expression
                + " has rule metrics "
                + str(rule_metrics)
            )
            if self.apply_filter(metrics=rule_metrics):
                self.add_rule(
                    rule_id=len(self.rules.index),
                    rule_group=group,
                    rule_def=expression,
                    rule_status="",
                    rule_metrics=rule_metrics,
                    encodings=encodings,
                )

        # remove temporarily added index columns
        for level in range(len(self.data.index.names)):
            del self.data[str(self.data.index.names[level])]

    def search_column_value(self, expr, column_value):

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

    def substitute(
        self, expression: str = "", column_values: list = [], substitutions: list = []
    ):
        result = expression
        for idx, col in enumerate(column_values):
            # replace only first occurrence in string
            result = result.replace(col[0], '{"' + substitutions[idx][0] + '"}', 1)
            if len(substitutions[idx]) > 1:
                result = result.replace(col[1], '"' + substitutions[idx][1] + '"', 1)
        return result

    def apply_filter(self, metrics: dict = {}):
        """
        This function applies the filter to the rule metrics (for example confidence > 0.75)
        """
        return all([metrics[metric] >= self.filter[metric] for metric in self.filter])

    def evaluate_code(self, expressions: dict = {}, encodings: dict = {}):
        """ """
        variables = {}
        for key in expressions.keys():
            try:
                variables[key] = eval(expressions[key], encodings, self.eval_dict)
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
            data=[[rule_id, rule_group, rule_def, rule_status]
            + [rule_metrics[metric] for metric in self.metrics]
            + [encodings]],
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
            ]

            data = pd.DataFrame(columns=self.results.columns, data=data)

            data["indices"] = ex_indices

            self.results = pd.concat([self.results, data], ignore_index=True)

        return None


def prune_expressions(expressions: list = [], params: dict = {}):
    """ """
    pruned_expressions = []
    sorted_expressions = []
    for expression in expressions:
        parsed = RULE_SYNTAX.parse_string(expression).as_list()
        sorted_expression = flatten_and_sort(parsed)[1:-1]
        reformulated = reformulate(parsed, params)[1:-1]
        if sorted_expression not in sorted_expressions:
            pruned_expressions.append(reformulated)
            sorted_expressions.append(sorted_expression)
    return pruned_expressions


def flatten_and_sort(expression):
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


def reformulate(expression: str = "", params: dict = {}):
    if isinstance(expression, str):
        return expression
    else:
        for idx, item in enumerate(expression):
            if (
                "decimal" in params.keys()
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
                    decimal = params.get("decimal", 0)
                    precision = 1.5 * 10 ** (-decimal)
                    return (
                        "(abs("
                        + reformulate(expression[:idx], params)
                        + "-"
                        + reformulate(expression[idx + 1 :], params)
                        + ") <= "
                        + str(precision)
                        + ")"
                    )
        l = ""
        for item in expression:
            l += reformulate(item, params)
        return "(" + l + ")"


def is_column(s):
    return len(s) > 4 and (
        (s[:2] == '{"' and s[-2:] == '"}') or (s[:2] == "{'" and s[-2:] == "'}")
    )


def is_string(s):
    return len(s) > 2 and (
        (s[:1] == '"' and s[-1:] == '"') or (s[:1] == "'" and s[-1:] == "'")
    )
