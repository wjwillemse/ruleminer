import pandas as pd
import constraint
import logging
import regex as re

from .const import (
    RULE_ID,
    RULE_DEF,
)


def setup_problem(
    args,
    solver,
    variable_range,
    all_different_constraint,
):
    problem = constraint.Problem(solver=solver)
    if all_different_constraint:
        problem.addConstraint(constraint.AllDifferentConstraint())
        logging.debug("Added all different constraint")
    problem.addVariables(args, variable_range)
    logging.debug("Added variables: " + str(args))
    return problem


def get_testcases(
    self,
    rules=pd.DataFrame,
    solver=None,
    variable_range=range(0, 10),
    all_different_constraint=True,
):
    """
    Generate testcases from rules

    Args:
        solver (constraint.Solver): the solver to be used
        variable (range): variable range to be used
        all_different_constraint (bool): generate testcases with all different values

    Returns:
        pd.DataFrame with testcases

    """
    assert rules is not None, "Unable to generate test cases, no rules defined."

    functions = {}
    # column names are mapped to internal names because they can contains
    # spaces and other symbols
    col2args = dict()
    for idx in rules.index:
        expression = rules.loc[idx, RULE_DEF]
        regex_condition = re.compile(r"if(.*)then(.*)", re.IGNORECASE)
        rule = regex_condition.search(expression)
        func_rule_def = {
            "X": {
                "expr": rule.group(1).strip(),
            },
            "Y": {
                "expr": rule.group(2).strip(),
            },
            "not_Y": {
                "expr": "not " + rule.group(2).strip(),
            },
        }
        for part in func_rule_def.keys():
            if func_rule_def[part]["expr"] != "()":
                def_body = func_rule_def[part]["expr"]
                def_name = "_rule_" + str(idx) + "_" + part
                columns = list(
                    set([item[2:-2] for item in re.findall(r'{".*?"}', def_body)])
                )
                for col in columns:
                    if col not in col2args.keys():
                        col2args[col] = "var_" + str(len(col2args.keys()))
                def_args = [col2args[arg] for arg in columns]
                for key, value in col2args.items():
                    def_body = def_body.replace(key, value)
                def_code = (
                    "def "
                    + def_name
                    + "("
                    + ", ".join(def_args)
                    + "):\n"
                    + "    return "
                    + def_body.replace('{"', "").replace('"}', "")
                )
                func_rule_def[part]["def_name"] = def_name
                func_rule_def[part]["def_args"] = def_args
                exec(def_code)
                logging.debug('Executed:\n"' + str(def_code) + '\n"')
            functions[idx] = func_rule_def
    args2col = {value: key for key, value in col2args.items()}
    testcases = pd.DataFrame()

    # testcase that satisfies all rules
    problem = setup_problem(
        args=col2args.values(),
        solver=solver,
        variable_range=variable_range,
        all_different_constraint=all_different_constraint,
    )
    for idx in rules.index:
        expression = rules.loc[idx, RULE_DEF]
        for part in ["X", "Y"]:
            if "def_name" in functions[idx][part].keys():
                def_name = functions[idx][part]["def_name"]
                def_args = functions[idx][part]["def_args"]
                logging.debug("Added constraint: " + str((def_name, def_args)))
                problem.addConstraint(eval(def_name), def_args)
    solution = problem.getSolution()
    if solution is not None:
        testcases = pd.concat(
            [
                testcases,
                pd.DataFrame(
                    columns=["result"] + list(args2col[col] for col in solution.keys()),
                    data=[["all satisfied"] + list(solution.values())],
                ),
            ],
            ignore_index=True,
        )
    else:
        logging.error("No solution found that satisfy all rules")

    # testcases that satisfy all but one rule
    for idx2 in rules.index:
        rule_id = rules.loc[idx2, RULE_ID]
        problem = setup_problem(
            args=col2args.values(),
            solver=solver,
            variable_range=variable_range,
            all_different_constraint=all_different_constraint,
        )
        for idx in rules.index:
            expression = rules.loc[idx, RULE_DEF]
            parts = ["X", "Y" if idx != idx2 else "not_Y"]
            for part in parts:
                if "def_name" in functions[idx][part].keys():
                    def_name = functions[idx][part]["def_name"]
                    def_args = functions[idx][part]["def_args"]
                    logging.debug("Added constraint: " + str((def_name, def_args)))
                    problem.addConstraint(eval(def_name), def_args)
        solution = problem.getSolution()
        if solution is not None:
            testcases = pd.concat(
                [
                    testcases,
                    pd.DataFrame(
                        columns=["result"]
                        + list(args2col[col] for col in solution.keys()),
                        data=[
                            ["all satisfied, except " + str(rule_id)]
                            + list(solution.values())
                        ],
                    ),
                ],
                ignore_index=True,
            )
        else:
            logging.error(
                "No solution found that satisfy all rules except " + str(rule_id)
            )

    return testcases
