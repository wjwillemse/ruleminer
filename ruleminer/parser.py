"""Main module."""

import pandas as pd
import logging
import itertools
import re
from pyparsing import *
from pyparsing import pyparsing_unicode as ppu

from ruleminer.const import DUNDER_DF
from ruleminer.const import VAR_Z

lpar, rpar = map(Suppress, "()")
e = CaselessKeyword("E")
number = Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?")
function = one_of("min max abs quantile sum substr MIN MAX ABS QUANTILE SUM SUBSTR")
empty = one_of(["None", '""', "pd.NA", "np.nan"])
quote = Literal('"')
sep = Literal(",")
string = srange(r"[a-zA-Z0-9_.,:;<>*=+-/?|@#$%^&\[\]{}\(\)\\']") + " " + "\x01" + "\x02" + "\x03" + ppu.Greek.alphas + ppu.Greek.alphanums
quoted_string = Combine(quote + Word(string) + quote)
column = Combine("{" + quote + Word(string) + quote + "}")
addop = Literal("+") | Literal("-")
multop = Literal("*") | Literal("/")
expop = Literal("^")    
compa_op = one_of(">= > <= < != == in IN")

list_element = quoted_string | column | number | empty
quoted_string_list = (
    Group(
        Literal("[") + list_element + (sep + list_element)[0, ...] + Literal("]")
    ) | Group
    (
        lpar + Literal("[") + list_element + (sep + list_element)[0, ...] + Literal("]") + rpar
    )
)

# exprStack = []

# def push_first(toks):
#     exprStack.append(toks[0])

# def push_unary_minus(toks):
#     for t in toks:
#         if t == "-":
#             exprStack.append("unary -")
#         else:
#             break

def term_expression():
    """
    """    
    expr = Forward()

    function_expr = (function + Group(lpar + expr + (sep + expr)[...] + rpar))
    
    atom = (
        addop[...]
        + (
            # (function_expr | quoted_string_list | quoted_string | column | number | empty ).setParseAction(push_first)
            (function_expr | quoted_string_list | quoted_string | column | number | empty )
            | Group(lpar + expr + rpar)
        )
    # ).setParseAction(push_unary_minus)
    )

    factor = Forward()
    # factor <<= atom + (expop + factor).setParseAction(push_first)[...]
    # term = factor + (multop + factor).setParseAction(push_first)[...]
    # expr <<= term + (addop + term).setParseAction(push_first)[...]
    factor <<= atom + (expop + factor)[...]
    term = factor + (multop + factor)[...]
    expr <<= term + (addop + term)[...]

    return expr

def rule_expression():
    """
    """    
    condition_item = term_expression() + compa_op + term_expression()
    comp_expr = Group(lpar + condition_item + rpar)
    condition = infixNotation(
        comp_expr,
        [
            (
                one_of(["NOT", "not", "~"]),
                1,
                opAssoc.RIGHT,
            ),
            (
                one_of(["AND", "and", "&"]),
                2,
                opAssoc.LEFT,
            ),
            (
                one_of(["OR", "or", "|"]),
                2,
                opAssoc.LEFT,
            ),
        ],
    )
    if_then = "if" + condition + "then" + condition | "IF" + condition + "THEN" + condition
    rule_syntax = if_then | "if () then " + condition | "IF () THEN " + condition | condition
    return rule_syntax

def python_code_lengths(expression: str = "", required: list = []):
    """ """

    regex_condition = re.compile(r"if(.*)then(.*)", re.IGNORECASE)
    rule = regex_condition.search(expression)

    if_part = rule.group(1).strip()
    then_part = rule.group(2).strip()

    python_expressions = {}
    for variable in required:
        if variable == "N":
            python_expressions[variable] = "len("+DUNDER_DF+".values)"
        if variable == "X":
            if if_part == "()":
                python_expressions[variable] = "len("+DUNDER_DF+".index)"
            else:
                python_expressions[variable] = "("+replace_columns(if_part)+").sum()"
        elif variable == "~X":
            python_expressions[variable] = "(~("+replace_columns(if_part)+")).sum()"
        elif variable == "Y":
            python_expressions[variable] = "("+replace_columns(then_part)+").sum()"
        elif variable == "~Y":
            python_expressions[variable] = "(~("+replace_columns(then_part)+")).sum()"
        elif variable == "X and Y":
            python_expressions[variable] = "(("+replace_columns(if_part)+") & ("+replace_columns(then_part)+ ")).sum()"
        elif variable == "X and ~Y":
            python_expressions[variable] = "(("+replace_columns(if_part)+") & ~("+replace_columns(then_part)+ ")).sum()"
        elif variable == "~X and ~Y":
            python_expressions[variable] = "(~("+replace_columns(if_part)+") & ~("+replace_columns(then_part)+ ")).sum()"

    for e in python_expressions.keys():
        python_expressions[e] = python_expressions[e].replace("[(())]", "")
        python_expressions[e] = python_expressions[e].replace("(()) & ", "")
        python_expressions[e] = python_expressions[e].replace("[~(())]", "[False]")
    return python_expressions


def python_code_index(expression: str = "", required: list = []):
    """ """

    regex_condition = re.compile(r"if(.*)then(.*)", re.IGNORECASE)
    rule = regex_condition.search(expression)

    if_part = rule.group(1).strip()
    then_part = rule.group(2).strip()

    python_expressions = {}
    for variable in required:
        if variable == "N":
            python_expressions[variable] = DUNDER_DF + ".index"
        if variable == "X":
            python_expressions[variable] = (
                DUNDER_DF + ".index[(" + replace_columns(if_part) + ")]"
            )
        elif variable == "~X":
            python_expressions[variable] = (
                DUNDER_DF + ".index[~(" + replace_columns(if_part) + ")]"
            )
        elif variable == "Y":
            python_expressions[variable] = (
                DUNDER_DF + ".index[(" + replace_columns(then_part) + ")]"
            )
        elif variable == "~Y":
            python_expressions[variable] = (
                DUNDER_DF + ".index[~(" + replace_columns(then_part) + ")]"
            )
        elif variable == "X and Y":
            python_expressions[variable] = (
                DUNDER_DF
                + ".index[("
                + replace_columns(if_part)
                + ") & ("
                + replace_columns(then_part)
                + ")]"
            )
        elif variable == "X and ~Y":
            python_expressions[variable] = (
                DUNDER_DF
                + ".index[("
                + replace_columns(if_part)
                + ") & ~("
                + replace_columns(then_part)
                + ")]"
            )
        elif variable == "~X and ~Y":
            python_expressions[variable] = (
                DUNDER_DF
                + ".index[~("
                + replace_columns(if_part)
                + ") & ~("
                + replace_columns(then_part)
                + ")]"
            )
    for e in python_expressions.keys():
        python_expressions[e] = python_expressions[e].replace("[(())]", "")
        python_expressions[e] = python_expressions[e].replace("(()) & ", "")
        python_expressions[e] = python_expressions[e].replace("[~(())]", "[False]")
    return python_expressions


def replace_columns(s: str = ""):
    """Function to replace the column names by a numpy expressions

    Numpy approach:
    {"A"} is rewritten to __df__.values[:, __df__.columns.get_loc("A")]

    Pandas approach:
    {"A"} is rewritten to __df__["A"]

    """
    # return s.replace(
    #     "{", DUNDER_DF + ".values[:, " + DUNDER_DF + ".columns.get_loc("
    # ).replace("}", ")]")
    return s.replace("{", DUNDER_DF + "[").replace("}", "]")


def python_code_for_columns(expression: str = ""):
    """ """
    return {
        VAR_Z: (DUNDER_DF + "[(" + replace_columns(expression) + ")]").replace("[()]", "")
    }


def python_code_for_intermediate(expression: str = ""):
    """ """
    return {VAR_Z: (replace_columns(expression)).replace("[()]", "")}
