"""Main module."""

import pandas as pd
import logging
import itertools
import re
from pyparsing import *

from ruleminer.const import DUNDER_DF

AND = one_of(["AND", "and", "&"])
OR = one_of(["OR", "or", "|"])
NOT = one_of(["NOT", "~"])
SEP = Literal(",")

QUOTE = Literal("'") | Literal('"')
ARITH_OP = one_of("+ - * /")
LOGIC_OP = one_of("& |")
COMPA_OP = one_of(">= > <= < != ==")
PREFIX_OP = one_of("min max abs quantile MIN MAX ABS QUANTILE")
NUMBER = Combine(Word(nums) + "." + Word(nums)) | Word(nums)
STRING = srange(r"[a-zA-Z0-9_.,:;<>*=+-/\\?|@#$%^&()']") + " "
COLUMN = Combine("{" + QUOTE + Word(STRING) + QUOTE + "}")
QUOTED_STRING = Combine(QUOTE + Word(STRING) + QUOTE)

PARL = Literal("(").suppress()
PARR = Literal(")").suppress()

ARITH_COLUMNS = Group((COLUMN | NUMBER) + (ARITH_OP + (COLUMN | NUMBER))[1, ...])
COLUMNS = (PARL + ARITH_COLUMNS + PARR) | ARITH_COLUMNS | COLUMN | NUMBER
PREFIX_COLUMN = PREFIX_OP + Group(PARL + COLUMNS + (SEP + COLUMNS)[0, ...] + PARR)

TERM = PREFIX_COLUMN | COLUMNS | QUOTED_STRING

COMP_EL = TERM + COMPA_OP + TERM
COMP = Group((PARL + COMP_EL + PARR))
CONDITION = infixNotation(
    COMP,
    [
        (
            NOT,
            1,
            opAssoc.RIGHT,
        ),
        (
            AND,
            2,
            opAssoc.LEFT,
        ),
        (
            OR,
            2,
            opAssoc.LEFT,
        ),
    ],
)
IF_THEN = "if" + CONDITION + "then" + CONDITION
RULE_SYNTAX = IF_THEN | "if () then " + CONDITION | CONDITION


def python_code(expression: str = "", required: list = [], r_type: str = "values"):
    """ """

    regex_condition = re.compile(r"if(.*)then(.*)", re.IGNORECASE)
    rule = regex_condition.search(expression)

    if_part = rule.group(1).strip()
    then_part = rule.group(2).strip()

    python_expressions = {}
    for variable in required:
        if variable == "X":
            python_expressions["X"] = (
                DUNDER_DF + "." + r_type + "[(" + to_numpy(if_part) + ")]"
            )
        elif variable == "~X":
            python_expressions["~X"] = (
                DUNDER_DF + "." + r_type + "[~(" + to_numpy(if_part) + ")]"
            )
        elif variable == "Y":
            python_expressions["Y"] = (
                DUNDER_DF + "." + r_type + "[(" + to_numpy(then_part) + ")]"
            )
        elif variable == "~Y":
            python_expressions["~Y"] = (
                DUNDER_DF + "." + r_type + "[~(" + to_numpy(then_part) + ")]"
            )
        elif variable == "X and Y":
            python_expressions[variable] = (
                DUNDER_DF
                + "."
                + r_type
                + "[("
                + to_numpy(if_part)
                + ") & ("
                + to_numpy(then_part)
                + ")]"
            )
        elif variable == "X and ~Y":
            python_expressions[variable] = (
                DUNDER_DF
                + "."
                + r_type
                + "[("
                + to_numpy(if_part)
                + ") & ~("
                + to_numpy(then_part)
                + ")]"
            )
        elif variable == "~X and ~Y":
            python_expressions[variable] = (
                DUNDER_DF
                + "."
                + r_type
                + "[~("
                + to_numpy(if_part)
                + ") & ~("
                + to_numpy(then_part)
                + ")]"
            )
    for e in python_expressions.keys():
        python_expressions[e] = python_expressions[e].replace("[(())]", "")
        python_expressions[e] = python_expressions[e].replace("(()) & ", "")
        python_expressions[e] = python_expressions[e].replace("[~(())]", "[False]")
    return python_expressions


def to_numpy(s: str = ""):
    """Function to replace the column names by a numpy expressions"""
    return s.replace(
        "{", DUNDER_DF + ".values[:, " + DUNDER_DF + ".columns.get_loc("
    ).replace("}", ")]")


def python_code_for_columns(expression: str = ""):
    """ """
    return {"X": (DUNDER_DF + "[(" + to_numpy(expression) + ")]").replace("[()]", "")}

def add_brackets(s: str):
    """
    Add brackets around expressions with & and |
    """

    item = re.search(r"(.*)([&|\|])(\s*[(df|df].*)", s)
    if item is not None:
        return (
            "("
            + add_brackets(item.group(1))
            + ") "
            + item.group(2).strip()
            + " ("
            + add_brackets(item.group(3))
            + ")"
        )
    else:
        item = re.search(r"(.*)([>|<|!=|<=|>=|==])(.*)", s)
        if item is not None:
            return (
                add_brackets(item.group(1))
                + item.group(2).strip()
                + add_brackets(item.group(3))
            )
        else:
            return s.strip()


def parenthetic_contents(string):
    """
    Generate parenthesized contents in string as pairs (level, contents).
    """
    stack = []
    if "(" not in string and ")" not in string:
        yield (0, string)
    for i, c in enumerate(string):
        if c == "(":
            stack.append(i)
        elif c == ")" and stack:
            start = stack.pop()
            yield (len(stack), string[start + 1 : i])
