"""Main module."""

import logging
import itertools
import re
import numpy as np
import pandas as pd

from .parser import (
    dataframe_index,
    dataframe_values,
    dataframe_lengths,
    pandas_column,
    rule_expression,
)

from .utils import generate_substitutions
from .metrics import metrics, required_variables, calculate_metrics
from .const import (
    CONFIDENCE,
    ABSOLUTE_SUPPORT,
    ABSOLUTE_EXCEPTIONS,
    RULE_ID,
    RULE_GROUP,
    RULE_DEF,
    RULE_STATUS,
    RESULT,
    INDICES,
    ENCODINGS,
    DUNDER_DF,
    VAR_X_AND_Y,
    VAR_X_AND_NOT_Y,
    VAR_Z,
)


class RuleMiner:
    """
    The RuleMiner object contains rules and data

    It used three basic functions:
    - update (rule expressions, rules or data)
    - generate (rules from rule expressions and data)
    - evaluate (results from rule)

    """

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
        self.metrics = metrics(self.metrics)
        self.required_vars = required_variables(self.metrics)
        self.filter = self.params.get("filter", {CONFIDENCE: 0.5, ABSOLUTE_SUPPORT: 2})
        self.tolerance = self.params.get("tolerance", None)
        if self.tolerance is not None:
            if "default" not in self.tolerance.keys():
                raise Exception("No 'default' key found in tolerance definition.")

        self.data = data
        self.eval_dict = {
            "MAX": np.maximum,
            "MIN": np.minimum,
            "ABS": np.abs,
            "QUANTILE": np.quantile,
            "SUM": np.nansum,
            "max": np.maximum,
            "min": np.minimum,
            "abs": np.abs,
            "quantile": np.quantile,
            "sum": np.nansum,
            "np": np,
            "nan": np.nan,
        }

        if self.tolerance is not None:

            def __tol__(value, column=None):
                for key, tol in self.tolerance.items():
                    if key == column:
                        for ((start, end)), decimals in tol.items():
                            if abs(value) >= start and abs(value) < end:
                                return 0.5 * 10 ** (decimals)

            self.eval_dict["__tol__"] = __tol__

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

        self.setup_rules_dataframe()

        if self.data is None:
            for template in self.templates:
                self.convert_template(template=template)
        else:
            for template in self.templates:
                self.generate_rules(template=template)

        return None

    def evaluate(
        self,
        data: pd.DataFrame = None,
    ):
        """ """
        if data is not None:
            self.update(data=data)

        assert self.rules is not None, "Unable to evaluate data, no rules defined."
        assert self.data is not None, "Unable to evaluate data, no data defined."

        self.setup_results_dataframe()

        # add temporary index columns (to allow rules based on index data)
        for level in range(len(self.data.index.names)):
            self.data[
                str(self.data.index.names[level])
            ] = self.data.index.get_level_values(level=level)

        for idx in self.rules.index:
            required_vars = required_variables(
                [ABSOLUTE_SUPPORT, ABSOLUTE_EXCEPTIONS, CONFIDENCE]
            )

            expression = self.rules.loc[idx, RULE_DEF]
            rule_code = dataframe_index(expression=expression, required=required_vars)
            print(rule_code)
            results = self.evaluate_code(expressions=rule_code, dataframe=self.data)
            len_results = {
                key: len(results[key]) if not isinstance(results[key], float) else 0
                for key in results.keys()
                if results[key] is not None
            }
            rule_metrics = calculate_metrics(
                len_results=len_results,
                metrics=[ABSOLUTE_SUPPORT, ABSOLUTE_EXCEPTIONS, CONFIDENCE],
            )
            self.add_results(
                idx,
                rule_metrics,
                results[VAR_X_AND_Y],
                results[VAR_X_AND_NOT_Y],
            )

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
            + [RESULT, INDICES]
        )
        self.results[RESULT] = self.results[RESULT].astype(bool)

    def convert_template(self, template: dict = {}):
        """
        Main function to convert templates to rules without data and regexes
        """
        logger = logging.getLogger(__name__)
        group = template.get("group", 0)
        encodings = template.get("encodings", {})
        template_expression = template.get("expression", None)

        # if the template expression is not a if then rule then it is changed
        # into an if then rule
        try:
            condition = re.compile(r"if(.*)then(.*)", re.IGNORECASE)
            rule_parts = condition.search(template_expression)
            if rule_parts is None:
                template_expression = "if () then " + template_expression
            parsed = (
                rule_expression()
                .parse_string(template_expression, parseAll=True)
                .as_list()
            )
        except Exception as e:
            logger.error("Parsing error in " + repr(template_expression))
            if logging.root.level == logging.DEBUG:
                logger.debug("Parsing error message: " + repr(e))
            return None

        reformulated_expression = self.reformulate(parsed)[1:-1]
        self.add_rule(
            rule_id=len(self.rules.index),
            rule_group=group,
            rule_def=reformulated_expression,
            rule_status="",
            rule_metrics={m: np.nan for m in self.metrics},
            encodings=encodings,
        )

    def generate_rules(self, template: dict):
        """
        Generate rules from data using a rule template.

        This method generates rules based on a provided rule template.
        It uses the template expression to create a set of rules by
        substituting variable values and applying conditions. The
        resulting rules are evaluated and filtered based on specified
        metrics.

        Args:
            template (dict): A dictionary containing the rule template
            with the following keys:
                - "group" (int): The group identifier for the rules.
                - "encodings" (dict): A dictionary of encodings for the rules.
                - "expression" (str): The rule template expression.

        Returns:
            None

        Example:
            >>> rule_template = {
            ...     "expression": 'if ({"A.*"} > 10) then ({"B.*"} == "X")'
            ...     "group": 1,
            ...     "encodings": {},
            ... }
            >>> generator.generate_rules(rule_template)

        Note:
            - The method first parses the provided rule expression into
              'if' and 'then' parts.
            - It generates rule candidates by substituting variables and
              applying conditions.
            - The candidates are evaluated, and the resulting rules are
              filtered using metrics.
            - The rules are added to the discovered rule list.

        - Temporary index name columns are added to the data to derive rules
          based on index names.
        - If the template expression is not in 'if-then' format, it is converted
          into such a format.
        - Substitutions are made for variable values, and rules are generated
          and evaluated.
        - Temporary index columns are removed from the data after rule generation.
        """
        logger = logging.getLogger(__name__)

        group = template.get("group", 0)
        encodings = template.get("encodings", {})
        template_expression = template.get("expression", None)

        # temporarily add index names as columns, so we derive rules with index names
        if self.data is not None:
            for level in range(len(self.data.index.names)):
                self.data[
                    str(self.data.index.names[level])
                ] = self.data.index.get_level_values(level=level)

        # if the template expression is not a if then rule then it is changed
        # into an if then rule
        try:
            parsed, if_part, then_part = self.split_rule(expression=template_expression)
        except Exception as e:
            logger.error("Parsing error in expression " + repr(template_expression))
            if logging.root.level == logging.DEBUG:
                logger.debug("Parsing error message: " + repr(e))
            return None

        sorted_expressions = {}

        if_part_column_values = self.search_column_value(if_part, [])
        if_part_substitutions = [
            generate_substitutions(df=self.data, column_value=column_value)
            for column_value in if_part_column_values
        ]
        if_part_substitutions = itertools.product(*if_part_substitutions)

        logger.info("Expression for if-part (" + str(if_part) + ") generated")
        for if_part_substitution in if_part_substitutions:
            candidate, _, _, _, _ = self.substitute_list(
                expression=if_part,
                columns=[item[0] for item in if_part_column_values],
                values=[item[1] for item in if_part_column_values],
                column_substitutions=[item[0] for item in if_part_substitution],
                value_substitutions=[item[1] for item in if_part_substitution],
            )
            candidate = self.reformulate(candidate)
            df_code = {VAR_Z: dataframe_values(expression=flatten(candidate))}
            df_eval = self.evaluate_code(expressions=df_code, dataframe=self.data)[
                VAR_Z
            ]
            if not isinstance(df_eval, float):  # then it is nan
                # substitute variables in then_part
                then_part_substituted = self.substitute_group_names(
                    then_part, [item[2] for item in if_part_substitution]
                )
                then_part_column_values = self.search_column_value(
                    then_part_substituted, []
                )
                then_part_substitutions = [
                    generate_substitutions(df=df_eval, column_value=column_value)
                    for column_value in then_part_column_values
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

                candidates = []
                if expression_substitutions == []:
                    # no substitutions, so original parsed expression
                    candidates.append(parsed)
                else:
                    # add all substitutions to candidate list
                    for substitution in expression_substitutions:
                        # substitute variables in full expression
                        parsed_substituted = self.substitute_group_names(
                            parsed, [item[2] for item in substitution]
                        )
                        candidate_parsed, _, _, _, _ = self.substitute_list(
                            expression=parsed_substituted,
                            columns=[item[0] for item in template_column_values],
                            values=[item[1] for item in template_column_values],
                            column_substitutions=[item[0] for item in substitution],
                            value_substitutions=[item[1] for item in substitution],
                        )
                        candidates.append(candidate_parsed)

                for candidate in candidates:
                    sorted_expression = flatten_and_sort(candidate)[1:-1]
                    reformulated_expression = self.reformulate(candidate)[1:-1]
                    if sorted_expression not in sorted_expressions.keys():
                        sorted_expressions[sorted_expression] = True
                        rule_code = dataframe_lengths(
                            expression=reformulated_expression,
                            required=self.required_vars,
                        )
                        len_results = self.evaluate_code(
                            expressions=rule_code, dataframe=self.data
                        )
                        rule_metrics = calculate_metrics(
                            len_results=len_results, metrics=self.metrics
                        )
                        if logging.root.level == logging.DEBUG:
                            logger.debug(
                                "Rule code: \n"
                                + str(
                                    "\n".join(
                                        [key + ": " + s for key, s in rule_code.items()]
                                    )
                                )
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
        if self.data is not None:
            for level in range(len(self.data.index.names)):
                del self.data[str(self.data.index.names[level])]

    def substitute_group_names(self, expr: str = None, group_names_list: list = []):
        """
        Substitute group names in an expression.

        This method substitutes placeholders in an expression with their
        corresponding group names. Group names are provided as a list,
        and placeholders in the expression are represented as '\x01',
        '\x02', and so on. The method replaces these placeholders with
        the group names from the list.

        Args:
            expr (str or list): The expression or list of expressions to
            be processed.
            group_names_list (list): A list of group names to use as
            substitutions.

        Returns:
            str or list: The expression with placeholders replaced by group names.

        Example:
            >>> expression = "Column '\x01' contains values from group '\x02'"
            >>> group_names = ['Group A', 'Numbers']
            >>> result = ruleminer.RuleMiner().substitute_group_names(
                expression, group_names)
            >>> print(result)
            "Column 'Group A' contains values from group 'Numbers'"

        Note:
            The method can be applied to both strings and lists of expressions.
            It searches for placeholders in the format '\x01', '\x02', and so on,
            and substitutes them with the corresponding group names from the list.
        """
        if isinstance(expr, str):
            for group_names in group_names_list:
                if group_names is not None:
                    for idx, key in enumerate(group_names):
                        expr = re.sub("\\x0" + str(idx + 1), key, expr)
            return expr
        elif isinstance(expr, list):
            return [self.substitute_group_names(i, group_names_list) for i in expr]

    def search_column_value(self, expr, column_value) -> list:
        """
        Search for column-value pairs in an expression.

        This method recursively searches for column-value pairs within an
        expression and appends them to the provided list. It identifies
        column-value pairs by checking the structure of the expression.

        Args:
            expr (str or list): The expression to search for column-value
            pairs.
            column_value (list): A list to store the identified column-value
            pairs.

        Returns:
            list: A list containing the discovered column-value pairs as tuples.

        Example:

            >>> expression = ['{"A"}', '==', '"b"']
            >>> column_value_pairs = ruleminer.RuleMiner().search_column_value(
                expression, [])
            >>> print(column_value_pairs)
            [('{"A"}', '"b"')]

        Note:
            The method examines the structure of the expression and identifies
            column-value pairs by checking for specific patterns. It recursively
            traverses the expression to find such pairs and appends them to the
            provided list.
        """
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

    def split_rule(self, expression: str = "") -> tuple:
        """
        Split a rule expression into its 'if' and 'then' parts.

        This method takes a rule expression and splits it into its 'if' and
        'then' components. It uses regular expressions to identify these parts,
        and if the 'if' part is empty, it is assumed to be the entire rule
        expression. The resulting 'if' and 'then' parts are parsed and returned
        as lists.

        Args:
            expression (str): The rule expression to be split.

        Returns:
            tuple: A tuple containing the following elements:
                - list: The parsed rule expression as a list.
                - list: The 'if' part of the rule as a parsed list (empty
                  if not present).
                - list: The 'then' part of the rule as a parsed list.

        Example:
            >>> rule_expression = 'if ({"A"} > 10) then ({"B"} == "C")'
            >>> parsed, if_part, then_part = split_rule(rule_expression)
            >>> print(parsed)
            ['if', ['{"A"}', '>', '10'], 'then', ['{"B"}', '==', '"C"']]
            >>> print(if_part)
            [['{"A"}', '>', '10']]
            >>> print(then_part)
            [['{"B"}', '==', '"C"']]

        Note:
            The method employs regular expressions to identify 'if' and 'then'
            parts, and if the 'if' part is not present, the entire expression
            is considered the 'then' part. The parsed results are returned as
            lists for further evaluation.
        """
        condition = re.compile(r"if(.*)then(.*)", re.IGNORECASE)
        rule_parts = condition.search(expression)
        if rule_parts is not None:
            if rule_parts.group(1).strip() != "()":
                if_part = (
                    rule_expression()
                    .parse_string(rule_parts.group(1), parseAll=True)
                    .as_list()
                )
            else:
                if_part = ""
            then_part = (
                rule_expression()
                .parse_string(rule_parts.group(2), parseAll=True)
                .as_list()
            )
        else:
            expression = "if () then " + expression
            if_part = ""
            then_part = (
                rule_expression().parse_string(expression, parseAll=True).as_list()
            )
        parsed = rule_expression().parse_string(expression, parseAll=True).as_list()
        return parsed, if_part, then_part

    def substitute_list(
        self,
        expression: str = "",
        columns: list = [],
        values: list = [],
        column_substitutions: list = [],
        value_substitutions: list = [],
    ):
        """
        Substitute columns and values in an expression with their substitutions.

        This method allows for the substitution of columns and values within an
        expression using the provided lists of column and value substitutions.
        It recursively processes the expression, replacing the first occurrence
        of a column or value with its substitution.

        Args:
            expression (str or list): The input expression to be processed.
            columns (list): A list of original columns to be substituted.
            values (list): A list of original values to be substituted.
            column_substitutions (list): A list of column substitutions.
            value_substitutions (list): A list of value substitutions.

        Returns:
            tuple: A tuple containing the following elements:
                - str or list: The processed expression with substitutions.
                - list: The remaining columns for substitution.
                - list: The remaining values for substitution.
                - list: The remaining column substitutions.
                - list: The remaining value substitutions.

        Example:
            >>> expression = '({"A.*"} > 10) & ({"B.*"} == 20)'
            >>> columns = ['{"A.*"}', {"B.*"}]
            >>> values = [10, 20]
            >>> column_subs = ["Aa", "Bb"]
            >>> value_subs = [30, 40]
            >>> result = ruleminer.RuleMiner().substitute_list(expression,
            columns, values, column_subs, value_subs)
            >>> print(result)
            ('({"Aa"} > 10) & ({"B.*"} == 20)', [{'B.*'}], [10, 20], ['Bb'], [30, 40])

        """

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
            elif values != [] and values[0] is None:
                return (
                    expression,
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
            return (
                r,
                columns,
                values,
                column_substitutions,
                value_substitutions,
            )

    def apply_filter(self, metrics: dict = {}):
        """
        This function applies the filter to the rule metrics (for example
        confidence > 0.75)
        """
        return self.data is None or all(
            [metrics[metric] >= self.filter[metric] for metric in self.filter]
        )

    def evaluate_code(
        self,
        expressions: dict = {},
        dataframe: pd.DataFrame = None,
        encodings: dict = {},
    ):
        """
        Evaluate a set of expressions and return their results.

        This method evaluates a dictionary of expressions using the provided data
        frame, encodings, and additional variables from the evaluation context.
        The results of the expressions are stored in a dictionary and returned.

        Args:
            expressions (dict): A dictionary of variable names as keys and expressions
            as values.
            dataframe (pd.DataFrame): The Pandas DataFrame containing the data for
            evaluation.
            encodings (dict): A dictionary of variable encodings or transformations for
            evaluation.

        Returns:
            dict: A dictionary containing the results of evaluated expressions.

        """
        logger = logging.getLogger(__name__)
        dict_values = {**{DUNDER_DF: dataframe}, **self.eval_dict}
        variables = {}
        for key in expressions.keys():
            try:
                variables[key] = eval(expressions[key], dict_values, encodings)
            except Exception as e:
                if logging.root.level == logging.DEBUG:
                    logger.debug(
                        "Error evaluating the code '"
                        + expressions[key]
                        + "': "
                        + repr(e)
                    )
                variables[key] = np.nan
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
        """
        Add a rule with information to the discovered rule list.

        This method adds a new rule to the discovered rule list. The rule
        is defined by a unique rule ID, a rule group, a rule definition
        (expression or description), a rule status, a dictionary of rule-
        specific metrics, and a dictionary of encodings used in the rule
        evaluation.

        Args:
            rule_id (str): A unique identifier for the rule.
            rule_group (int): An integer representing the group or category
            to which the rule belongs.
            rule_def (str): The definition or expression of the rule.
            rule_status (str): The status of the rule
            rule_metrics (dict): A dictionary of rule-specific metrics and
            their values.
            encodings (dict): A dictionary of variable encodings used in the
            rule.

        Example:
            >>> my_rule = {
            ...     'rule_id': 'R001',
            ...     'rule_group': 1,
            ...     'rule_def': 'column_A > 10',
            ...     'rule_status': 'active',
            ...     'rule_metrics': {'coverage': 0.9, 'accuracy': 0.85},
            ...     'encodings': {}
            ... }
            >>> add_rule(**my_rule)

        """
        row = pd.DataFrame(
            data=[
                [rule_id, rule_group, rule_def, rule_status]
                + [rule_metrics[metric] for metric in self.metrics]
                + [encodings]
            ],
            columns=self.rules.columns,
        )
        if not self.rules.empty:
            self.rules = pd.concat([self.rules, row], ignore_index=True)
        else:
            self.rules = row

    def add_results(self, rule_idx, rule_metrics, co_indices, ex_indices) -> None:
        """
        Add results for a rule to the results list.

        This method adds results for a specific rule, including its metrics
        and indices, to the results list. It updates both the results for
        confirmations (co_indices) and exceptions (ex_indices). If no indices
        are provided for either category, an error message is logged.

        Args:
            rule_idx (int): The index of the rule in the rule list.
            rule_metrics (dict): A dictionary of rule-specific metrics for evaluation.
            co_indices (list or None): A list of indices for confirmations.
            ex_indices (list or None): A list of indices for exceptions.

        Returns:
            None: This method updates the results list in-place.

        Example:
            >>> rule_index = 0
            >>> metrics = {
            ...     'absolute_support': 50,
            ...     'absolute_exceptions': 5,
            ...     'confidence': 0.9
            ... }
            >>> co_indices = [1, 2, 3, 4, 5]
            >>> ex_indices = [10, 11, 12, 13]
            >>> add_results(rule_index, metrics, co_indices, ex_indices)

        """
        logger = logging.getLogger(__name__)
        if co_indices is not None and not isinstance(co_indices, float):
            nco = len(co_indices)
        else:
            nco = 0
        if ex_indices is not None and not isinstance(ex_indices, float):
            nex = len(ex_indices)
        else:
            nex = 0

        if nco == 0 and nex == 0:
            logger.info(
                "Error when evaluating rule results for rule id " + str(rule_idx)
            )

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
            data[INDICES] = co_indices
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
            data[INDICES] = ex_indices
            self.results = pd.concat([self.results, data], ignore_index=True)

        return None

    def reformulate(
        self,
        expression: str = "",
        apply_tolerance: bool = False,
        positive_tolerance: bool = True,
    ):
        """
        Convert parameters, settings, and functions to Pandas code within
        an expression.

        This method takes an input expression and converts specific parameters,
        settings, and functions into their equivalent Pandas code. It allows
        for custom transformations and conversions that are used in the evaluation
        of rules.

        Args:
            expression (str): The input expression to be reformulated into Pandas code.
            apply_tolerance (bool):
            positive_tolerance (bool):

        Returns:
            str: The reformulated expression in Pandas code.

        Example:
            >>> expression = ['substr', ['{"A"}', ',', '1', ',', '1']]
            >>> result = ruleminer.RuleMiner().reformulate(expression)
            >>> print(result)
            "({"A"}.str.slice(1,1))"

        """
        if isinstance(expression, str):
            if is_column(expression) and apply_tolerance:
                args = ""
                for key, tol in self.tolerance.items():
                    if re.fullmatch(key, expression[2:-2]):
                        args = ', args=("' + key + '",)'
                if args == "":
                    args = ', args=("default",)'
                if positive_tolerance:
                    return (
                        expression
                        + "+0.5*abs("
                        + expression
                        + ".apply(__tol__"
                        + args
                        + "))"
                    )
                else:
                    return (
                        expression
                        + "-0.5*abs("
                        + expression
                        + ".apply(__tol__"
                        + args
                        + "))"
                    )
            elif expression.lower() == "in":
                return ".isin"
            else:
                return expression
        else:

            if len(expression) == 1 and expression[0] in ["+", "-", "*", "/"]:
                return expression[0]

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
                            + self.reformulate(
                                expression[:idx],
                                apply_tolerance=apply_tolerance,
                                positive_tolerance=positive_tolerance,
                            )
                            + "-"
                            + self.reformulate(
                                expression[idx + 1 :],
                                apply_tolerance=apply_tolerance,
                                positive_tolerance=positive_tolerance,
                            )
                            + ") <= "
                            + str(precision)
                            + ")"
                        )
                if (
                    "tolerance" in self.params.keys()
                    and isinstance(item, str)
                    and item in ["==", "!=", "<", "<=", ">", ">="]
                ):
                    if not (
                        is_string(expression[idx - 1]) and len(expression[:idx]) == 1
                    ) and (
                        not (
                            is_string(expression[idx + 1])
                            and len(expression[idx + 1 :]) == 1
                        )
                    ):
                        left_side_pos = self.reformulate(
                            expression=expression[:idx],
                            apply_tolerance=True,
                            positive_tolerance=True,
                        )
                        left_side_neg = self.reformulate(
                            expression=expression[:idx],
                            apply_tolerance=True,
                            positive_tolerance=False,
                        )
                        right_side_pos = self.reformulate(
                            expression=expression[idx + 1 :],
                            apply_tolerance=True,
                            positive_tolerance=True,
                        )
                        right_side_neg = self.reformulate(
                            expression=expression[idx + 1 :],
                            apply_tolerance=True,
                            positive_tolerance=False,
                        )
                        if item in ["=="]:
                            return (
                                "(("
                                + left_side_pos
                                + " >= "
                                + right_side_neg
                                + ") & ("
                                + left_side_neg
                                + " <= "
                                + right_side_pos
                                + "))"
                            )
                        if item in ["!="]:
                            return (
                                "(("
                                + left_side_pos
                                + " < "
                                + right_side_neg
                                + ") | ("
                                + left_side_neg
                                + " > "
                                + right_side_pos
                                + "))"
                            )
                        elif item in [">", ">="]:
                            return (
                                "(" 
                                + left_side_pos
                                + item
                                + right_side_neg
                                + ")"
                            )
                        elif item in ["<", "<="]:
                            return (
                                "(" 
                                + left_side_neg
                                + item
                                + right_side_pos
                                + ")"
                            )
                if (
                    self.params.get("evaluate_quantile", False)
                    and isinstance(item, str)
                    and item.lower() == "quantile"
                ):
                    res = ""
                    for i in expression[:idx]:
                        res += self.reformulate(
                            i,
                            apply_tolerance=apply_tolerance,
                            positive_tolerance=positive_tolerance,
                        )
                    quantile_code = {
                        VAR_Z: pandas_column(flatten(expression[idx : idx + 2]))
                    }
                    quantile_result = self.evaluate_code(
                        expressions=quantile_code, dataframe=self.data
                    )[VAR_Z]
                    res += str(np.round(quantile_result, 8))
                    for i in expression[idx + 2 :]:
                        res += self.reformulate(
                            i,
                            apply_tolerance=apply_tolerance,
                            positive_tolerance=positive_tolerance,
                        )
                    return "(" + res + ")"
                if isinstance(item, str) and item.lower() == "in":
                    # replace in by .isin
                    res = ""
                    for i in expression[:idx]:
                        res += self.reformulate(
                            i,
                            apply_tolerance=apply_tolerance,
                            positive_tolerance=positive_tolerance,
                        )
                    res += ".isin"
                    for i in expression[idx + 1 :]:
                        res += self.reformulate(
                            i,
                            apply_tolerance=apply_tolerance,
                            positive_tolerance=positive_tolerance,
                        )
                    return res
                if isinstance(item, str) and item.lower() == "substr":
                    string, _, start, _, stop = expression[idx + 1]
                    res = (
                        "("
                        + self.reformulate(
                            string,
                            apply_tolerance=apply_tolerance,
                            positive_tolerance=positive_tolerance,
                        )
                        + ".str.slice("
                        + start
                        + ","
                        + stop
                        + "))"
                    )
                    for i in expression[idx + 2 :]:
                        res += self.reformulate(
                            i,
                            apply_tolerance=apply_tolerance,
                            positive_tolerance=positive_tolerance,
                        )
                    return res
                if isinstance(item, str) and item.lower() == "split":
                    string, _, separator, _, position = expression[idx + 1]
                    res = (
                        "("
                        + self.reformulate(
                            string,
                            apply_tolerance=apply_tolerance,
                            positive_tolerance=positive_tolerance,
                        )
                        + ".str.split("
                        + separator
                        + ").str["
                        + position
                        + "])"
                    )
                    for i in expression[idx + 2 :]:
                        res += self.reformulate(
                            i,
                            apply_tolerance=apply_tolerance,
                            positive_tolerance=positive_tolerance,
                        )
                    return res
                if isinstance(item, str) and item.lower() in ["sum", "sumif"]:
                    sumlist = self.reformulate(
                        expression[idx + 1][0],
                        apply_tolerance=apply_tolerance,
                        positive_tolerance=positive_tolerance,
                    )
                    # if it is a sumif then parse the condition(s)
                    if item.lower() == "sumif":
                        condition_tree = expression[idx + 1][2:]
                        if isinstance(condition_tree[0], str):
                            # the content of condition is not a list of conditions
                            condition = self.reformulate(
                                condition_tree,
                                apply_tolerance=apply_tolerance,
                                positive_tolerance=positive_tolerance,
                            )
                            # a single condition applied to all columns
                            sumlist = sumlist.replace("}", "}.where(" + condition + ")")
                        else:
                            # the content of condition is a list of conditions
                            conditions = []
                            for condition_idx in range(1, len(condition_tree[0]), 2):
                                conditions.append(
                                    self.reformulate(
                                        condition_tree[0][condition_idx],
                                        apply_tolerance=apply_tolerance,
                                        positive_tolerance=positive_tolerance,
                                    )
                                )
                            # apply list of condition to each respective column
                            parts = sumlist.split("}")
                            if len(parts) - 1 != len(conditions):
                                logging.error(
                                    "Number of items to sum is not equal to number of conditions: "
                                    + str(parts[:-1])
                                    + " versus "
                                    + str(conditions)
                                )
                                return ""
                            sumlist = (
                                "".join(
                                    [
                                        item + "}.where(" + conditions[idx][1:-1] + ")"
                                        for idx, item in enumerate(parts[:-1])
                                    ]
                                )
                                + parts[-1]
                            )
                    res = "sum(" + sumlist + ", axis=0)"
                    for i in expression[idx + 2 :]:
                        res += self.reformulate(
                            i,
                            apply_tolerance=apply_tolerance,
                            positive_tolerance=positive_tolerance,
                        )
                    return res
                if isinstance(item, str) and item.lower() in ["count", "countif"]:
                    countlist = self.reformulate(
                        expression[idx + 1][0],
                        apply_tolerance=apply_tolerance,
                        positive_tolerance=positive_tolerance,
                    )
                    # if it is a countif then parse the condition(s)
                    if item.lower() == "countif":
                        condition_tree = expression[idx + 1][2:]
                        if isinstance(condition_tree[0], str):
                            # the content of condition is not a list of conditions
                            condition = self.reformulate(
                                condition_tree,
                                apply_tolerance=apply_tolerance,
                                positive_tolerance=positive_tolerance,
                            )
                            # a single condition applied to all columns
                            countlist = countlist.replace("{", "~{").replace(
                                "}", "}.where(" + condition + ").isna()"
                            )
                        else:
                            # the content of condition is a list of conditions
                            conditions = []
                            for condition_idx in range(1, len(condition_tree[0]), 2):
                                conditions.append(
                                    self.reformulate(
                                        condition_tree[0][condition_idx],
                                        apply_tolerance=apply_tolerance,
                                        positive_tolerance=positive_tolerance,
                                    )
                                )
                            # apply list of condition to each respective column
                            parts = countlist.split("}")
                            if len(parts) - 1 != len(conditions):
                                logging.error(
                                    "Number of items to count is not equal to number of conditions: "
                                    + str(parts[:-1])
                                    + " versus "
                                    + str(conditions)
                                )
                                return ""
                            countlist = (
                                "".join(
                                    [
                                        item
                                        + "}.where("
                                        + conditions[idx][1:-1]
                                        + ").isna()"
                                        for idx, item in enumerate(parts[:-1])
                                    ]
                                )
                                + parts[-1]
                            )
                    res = "sum(" + countlist + ", axis=0)"
                    for i in expression[idx + 2 :]:
                        res += self.reformulate(
                            i,
                            apply_tolerance=apply_tolerance,
                            positive_tolerance=positive_tolerance,
                        )
                    return res

                if isinstance(item, str) and item in ["-", "/"]:
                    # if the operator is - or / then the tolerance direction should be reversed
                    left_side = self.reformulate(
                        expression=expression[:idx],
                        apply_tolerance=apply_tolerance,
                        positive_tolerance=positive_tolerance,
                    )
                    # the rest of the expression if evaluated as a list with reversed tolerance
                    right_side = ""
                    for right_side_item in expression[idx + 1 :]:
                        right_side += self.reformulate(
                            expression=[right_side_item],
                            apply_tolerance=apply_tolerance,
                            positive_tolerance=not positive_tolerance
                            if apply_tolerance
                            else positive_tolerance,
                        )
                    return "(" + left_side + item + right_side + ")"

            res = ""
            for i in expression:
                res += self.reformulate(
                    i,
                    apply_tolerance=apply_tolerance,
                    positive_tolerance=positive_tolerance,
                )
            return "(" + res + ")"


def flatten_and_sort(expression: str = ""):
    """
    Recursively flatten and sort a nested expression and return it as a string.

    This function takes an expression, which can be a nested list of strings
    or a single string, and recursively flattens and sorts it into a single
    string enclosed in parentheses. Sorting is applied to certain elements
    within the expression, such as mathematical operations, column references,
    and strings, based on their relationships and order of precedence.

    Args:
        expression (str or list): The expression to be flattened and sorted.

    Returns:
        str: The flattened and sorted expression as a string enclosed in
        parentheses.

    Example:
        >>> expression = ["max", ["C", "A"]]
        >>> result = ruleminer.flatten_and_sort(expression)
        >>> print(result)
        "(max((CA)))"

        >>> expression = ["C", "==", ["A", "+", "B"]]
        >>> result = ruleminer.flatten_and_sort(expression)
        >>> print(result)
        "((A+B)==C)"
    """
    if isinstance(expression, str):
        return expression
    else:
        if isinstance(expression[0], str) and expression[0].lower() in [
            "min",
            "max",
        ]:
            res = (
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

            res = ""
            count = 0
            for idx, item in enumerate(expression):
                if idx in idx_to_sort:
                    res += sorted_items[count]
                    count += 1
                else:
                    res += flatten_and_sort(item)
        return "(" + res + ")"


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
        >>> expression = ["A", ["B", ["C", "D"]]]
        >>> result = ruleminer.flatten(expression)
        >>> print(result)
        "(A(B(CD)))"
    """
    if isinstance(expression, str):
        return expression
    else:
        res = ""
        for item in expression:
            res += flatten(item)
        return "(" + res + ")"


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
        >>> is_column('{"A"}')
        True

        >>> is_column('{"B"}')
        True

        >>> is_column("Not a column reference")
        False
    """
    return len(s) > 4 and (
        (s[:2] == '{"' and s[-2:] == '"}') or (s[:2] == "{'" and s[-2:] == "'}")
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
        >>> is_string("'Hello, World!'")
        True

        >>> is_string('"42"')
        True

        >>> is_string("Not a string")
        False
    """
    return len(s) > 2 and (
        (s[:1] == '"' and s[-1:] == '"') or (s[:1] == "'" and s[-1:] == "'")
    )
