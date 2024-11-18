#!/usr/bin/env python

"""Tests for `ruleminer` package."""

import unittest
import pandas as pd
import numpy as np
import ruleminer

# import logging
# import sys
# logging.basicConfig(
#     stream=sys.stdout,
#     format='%(asctime)s %(message)s',
#     level=logging.DEBUG
# )


class TestRuleminer(unittest.TestCase):
    """Tests for `ruleminer` package."""

    def setUp_ruleminer(self):
        """Set up test fixtures, if any."""
        r = ruleminer.RuleMiner()
        assert r is not None

    def test_1(self):
        actual = ruleminer._column.parse_string('{"A"}', parse_all=True).as_list()
        expected = ['{"A"}']
        self.assertTrue(actual == expected)

    def test_2(self):
        actual = ruleminer._quoted_string.parse_string('"A"', parse_all=True).as_list()
        expected = ['"A"']
        self.assertTrue(actual == expected)

    def test_3(self):
        actual = (
            ruleminer.math_expression().parse_string('"b"', parse_all=True).as_list()
        )
        expected = ['"b"']
        self.assertTrue(actual == expected)

    def test_4(self):
        actual = (
            ruleminer.math_expression().parse_string('{"b"}', parse_all=True).as_list()
        )
        expected = ['{"b"}']
        self.assertTrue(actual == expected)

    def test_5(self):
        actual = (
            ruleminer.math_expression().parse_string("221", parse_all=True).as_list()
        )
        expected = ["221"]
        self.assertTrue(actual == expected)

    def test_6(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('({"f"} == 0)', parse_all=True)
            .as_list()
        )
        expected = [['{"f"}', "==", "0"]]
        self.assertTrue(actual == expected)

    def test_7(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('({"f"} > 0)', parse_all=True)
            .as_list()
        )
        expected = [['{"f"}', ">", "0"]]
        self.assertTrue(actual == expected)

    def test_8(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('({"f"} == 0) & ({"w"} == 0)', parse_all=True)
            .as_list()
        )
        expected = [[['{"f"}', "==", "0"], "&", ['{"w"}', "==", "0"]]]
        self.assertTrue(actual == expected)

    def test_9(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('~({"f"} == 0) & ({"d"} == "s")', parse_all=True)
            .as_list()
        )
        expected = [[["~", ['{"f"}', "==", "0"]], "&", ['{"d"}', "==", '"s"']]]
        self.assertTrue(actual == expected)

    def test_10(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(min({"f"}, {"d"})>0) & ({"d"} == "s")', parse_all=True)
            .as_list()
        )
        expected = [
            [[["min", ['{"f"}', ",", '{"d"}']], ">", "0"], "&", ['{"d"}', "==", '"s"']]
        ]
        self.assertTrue(actual == expected)

    def test_11(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(({"f"} + {"d"}) > 0)', parse_all=True)
            .as_list()
        )
        expected = [[['{"f"}', "+", '{"d"}'], ">", "0"]]
        self.assertTrue(actual == expected)

    def test_12(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(abs({"f"}) == 0)', parse_all=True)
            .as_list()
        )
        expected = [[["abs", ['{"f"}']], "==", "0"]]
        self.assertTrue(actual == expected)

    def test_13(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(abs({"f"} + {"d"}) > 1) & ({"s"} < 2)', parse_all=True)
            .as_list()
        )
        expected = [
            [[["abs", ['{"f"}', "+", '{"d"}']], ">", "1"], "&", ['{"s"}', "<", "2"]]
        ]
        self.assertTrue(actual == expected)

    def test_14(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('(({"4"} + {"3"} + {"2"} + {"1"}) > 0)', parse_all=True)
            .as_list()
        )
        expected = '((({"1"}+{"2"}+{"3"}+{"4"})>0))'
        self.assertTrue(actual == expected)

    def test_15(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('IF () THEN ("A"=="")', parse_all=True)
            .as_list()
        )
        expected = ["IF () THEN ", ['"A"', "==", '""']]
        self.assertTrue(actual == expected)

    def test_16(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string(
                'IF ( not("F3" in ["G1","G3"])) THEN \
                (SUBSTR({"A"}, 2, 4) in ["D1","D3"])',
                parse_all=True,
            )
            .as_list()
        )
        expected = [
            "IF",
            ["not", ['"F3"', "in", ['"G1"', ",", '"G3"']]],
            "THEN",
            [
                ["SUBSTR", ['{"A"}', ",", "2", ",", "4"]],
                "in",
                ['"D1"', ",", '"D3"'],
            ],
        ]
        self.assertTrue(actual == expected)

    def test_17(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('if ("C" != "pd.NA") then ( "A" > -1)', parse_all=True)
            .as_list()
        )
        expected = ["if", ['"C"', "!=", '"pd.NA"'], "then", ['"A"', ">", "-1"]]
        self.assertTrue(actual == expected)

    def test_18(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string(
                'if (0 > min({"C"}, {"B"})) then (1 == sum({"A"}, {"B"}))',
                parse_all=True,
            )
            .as_list()
        )
        expected = [
            "if",
            ["0", ">", ["min", ['{"C"}', ",", '{"B"}']]],
            "then",
            ["1", "==", ["sum", ['{"A"}', ",", '{"B"}']]],
        ]
        self.assertTrue(actual == expected)

    def test_19(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('(({"4"} + {"3"} + {"2"} * {"1"}) > 0)', parse_all=True)
            .as_list()
        )
        expected = '((({"4"}+{"3"}+{"1"}*{"2"})>0))'
        self.assertTrue(actual == expected)

    def test_20(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('(({"4"} + {"3"} * {"2"} + {"1"}) > 0)', parse_all=True)
            .as_list()
        )
        expected = '((({"4"}+{"2"}*{"3"}+{"1"})>0))'
        self.assertTrue(actual == expected)

    def test_21(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('(({"4"} * {"3"} + {"2"} + {"1"}) > 0)', parse_all=True)
            .as_list()
        )
        expected = '((({"3"}*{"4"}+{"2"}+{"1"})>0))'
        self.assertTrue(actual == expected)

    def test_22(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('({"4"} == {"3"})', parse_all=True)
            .as_list()
        )
        expected = '(({"3"}=={"4"}))'
        self.assertTrue(actual == expected)

    def test_23(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('({"4"} != {"3"})', parse_all=True)
            .as_list()
        )
        expected = '(({"3"}!={"4"}))'
        self.assertTrue(actual == expected)

    def test_24(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('({"4"} > {"3"})', parse_all=True)
            .as_list()
        )
        expected = '(({"4"}>{"3"}))'
        self.assertTrue(actual == expected)

    def test_25(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('(({"4"} > {"3"}) & ({"2"} > {"1"}))', parse_all=True)
            .as_list()
        )
        expected = '((({"2"}>{"1"})&({"4"}>{"3"})))'
        self.assertTrue(actual == expected)

    def test_26(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('(({"4"} > {"3"}) & ({"2"} == {"1"}))', parse_all=True)
            .as_list()
        )
        expected = '((({"1"}=={"2"})&({"4"}>{"3"})))'
        self.assertTrue(actual == expected)

    def test_27(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string(
                '(({"4"} > {"3"}) & (({"2"}+{"0"}) == {"1"}))', parse_all=True
            )
            .as_list()
        )
        expected = '(((({"0"}+{"2"})=={"1"})&({"4"}>{"3"})))'
        self.assertTrue(actual == expected)

    def test_28(self):
        df = pd.DataFrame(
            columns=[
                "Name",
                "Type",
                "Assets",
                "TP-life",
                "TP-nonlife",
                "Own_funds",
                "Excess",
            ],
            data=[
                ["Insurer1", "life_insurer", 1000, 800, 0, 200, 200],
                ["Insurer2", "non-life_insurer", 4000, 0, 3200, 800, 800],
                ["Insurer3", "non-life_insurer", 800, 0, 700, 100, 100],
                ["Insurer4", "life_insurer", 2500, 1800, 0, 700, 700],
                ["Insurer5", "non-life_insurer", 2100, 0, 2200, 200, 200],
                ["Insurer6", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer7", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer8", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer9", "non-life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer10", "non-life_insurer", 9000, 0, 8800, 200, 199.99],
            ],
        )

        templates = [{"expression": 'if ({".*"} == ".*") then ({"TP.*"} > 0)'}]
        actual = ruleminer.RuleMiner(templates=templates, data=df).rules
        expected = pd.DataFrame(
            data=[
                [
                    0,
                    0,
                    'if({"Type"}=="life_insurer")then({"TP-life"}>0)',
                    "",
                    5,
                    0,
                    1.0,
                    5,
                    {},
                ],
                [
                    1,
                    0,
                    'if({"Type"}=="non-life_insurer")then({"TP-nonlife"}>0)',
                    "",
                    4,
                    1,
                    0.8,
                    5,
                    {},
                ],
            ],
            columns=[
                ruleminer.RULE_ID,
                ruleminer.RULE_GROUP,
                ruleminer.RULE_DEF,
                ruleminer.RULE_STATUS,
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.NOT_APPLICABLE,
                ruleminer.ENCODINGS,
            ],
        )
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_29(self):
        df = pd.DataFrame(
            columns=[
                "Name",
                "Type",
                "Assets",
                "TP-life",
                "TP-nonlife",
                "Own_funds",
                "Excess",
            ],
            data=[
                ["Insurer1", "life_insurer", 1000, 800, 0, 200, 200],
                ["Insurer2", "non-life_insurer", 4000, 0, 3200, 800, 800],
                ["Insurer3", "non-life_insurer", 800, 0, 700, 100, 100],
                ["Insurer4", "life_insurer", 2500, 1800, 0, 700, 700],
                ["Insurer5", "non-life_insurer", 2100, 0, 2200, 200, 200],
                ["Insurer6", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer7", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer8", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer9", "non-life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer10", "non-life_insurer", 9000, 0, 8800, 200, 199.99],
            ],
        )

        templates = [{"expression": '({"Own_funds"} <= quantile({"Own_funds"}, 0.95))'}]
        actual = ruleminer.RuleMiner(
            templates=templates, data=df, params={"evaluate_quantile": True}
        ).rules
        expected = pd.DataFrame(
            data=[[0, 0, 'if () then ({"Own_funds"}<=755.0)', "", 9, 1, 0.9, 0, {}]],
            columns=[
                ruleminer.RULE_ID,
                ruleminer.RULE_GROUP,
                ruleminer.RULE_DEF,
                ruleminer.RULE_STATUS,
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.NOT_APPLICABLE,
                ruleminer.ENCODINGS,
            ],
        )
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_30(self):
        df = pd.DataFrame(
            columns=[
                "Name",
                "Type",
                "Assets",
                "TP-life",
                "TP-nonlife",
                "Own_funds",
                "Excess",
            ],
            data=[
                ["Insurer1", "life_insurer", 1000, 800, 0, 200, 200],
                ["Insurer2", "non-life_insurer", 4000, 0, 3200, 800, 800],
                ["Insurer3", "non-life_insurer", 800, 0, 700, 100, 100],
                ["Insurer4", "life_insurer", 2500, 1800, 0, 700, 700],
                ["Insurer5", "non-life_insurer", 2100, 0, 2200, 200, 200],
                ["Insurer6", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer7", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer8", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer9", "non-life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer10", "non-life_insurer", 9000, 0, 8800, 200, 199.99],
            ],
        )

        templates = [{"expression": '({"Own_funds"} <= quantile({"Own_funds"}, 0.95))'}]
        actual = ruleminer.RuleMiner(templates=templates, data=df).rules
        expected = pd.DataFrame(
            data=[
                [
                    0,
                    0,
                    'if () then ({"Own_funds"}<=quantile({"Own_funds"}, 0.95))',
                    "",
                    9,
                    1,
                    0.9,
                    0,
                    {},
                ]
            ],
            columns=[
                ruleminer.RULE_ID,
                ruleminer.RULE_GROUP,
                ruleminer.RULE_DEF,
                ruleminer.RULE_STATUS,
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.NOT_APPLICABLE,
                ruleminer.ENCODINGS,
            ],
        )
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_30_1(self):
        df = pd.DataFrame(
            columns=[
                "Name",
                "Type",
                "Assets",
                "TP-life",
                "TP-nonlife",
                "Own_funds",
                "Excess",
            ],
            data=[
                ["Insurer1", "life_insurer", 1000, 800, 0, 200, 200],
                ["Insurer2", "non-life_insurer", 4000, 0, 3200, 800, 800],
                ["Insurer3", "non-life_insurer", 800, 0, 700, 100, 100],
                ["Insurer4", "life_insurer", 2500, 1800, 0, 700, 700],
                ["Insurer5", "non-life_insurer", 2100, 0, 2200, 200, 200],
                ["Insurer6", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer7", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer8", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer9", "non-life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer10", "non-life_insurer", 9000, 0, 8800, 200, 199.99],
            ],
        )

        templates = [
            {
                "expression": """(sumif([{"Assets"}, {"Own_funds"}],
            {"Type"}=="life_insurer") > 0)"""
            }
        ]
        actual = ruleminer.RuleMiner(templates=templates, data=df).rules
        expected = pd.DataFrame(
            data=[
                [
                    0,
                    0,
                    'if () then (sum([K for K in [{"Assets"}.where(({"Type"}=="life_insurer"), other=0), {"Own_funds"}.where(({"Type"}=="life_insurer"), other=0)]], axis=0)>0)',
                    "",
                    5,
                    5,
                    0.5,
                    0,
                    {},
                ]
            ],
            columns=[
                ruleminer.RULE_ID,
                ruleminer.RULE_GROUP,
                ruleminer.RULE_DEF,
                ruleminer.RULE_STATUS,
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.NOT_APPLICABLE,
                ruleminer.ENCODINGS,
            ],
        )
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_30_1_2(self):
        df = pd.DataFrame(
            columns=[
                "Name",
                "Type",
                "Assets",
                "TP-life",
                "TP-nonlife",
                "Own_funds",
                "Excess",
            ],
            data=[
                ["Insurer1", "life_insurer", 1000, 800, 0, 200, 200],
                ["Insurer2", "non-life_insurer", 4000, 0, 3200, 800, 800],
                ["Insurer3", "non-life_insurer", 800, 0, 700, 100, 100],
                ["Insurer4", "life_insurer", 2500, 1800, 0, 700, 700],
                ["Insurer5", "non-life_insurer", 2100, 0, 2200, 200, 200],
                ["Insurer6", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer7", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer8", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer9", "non-life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer10", "non-life_insurer", 9000, 0, 8800, 200, 199.99],
            ],
        )

        templates = [
            {
                "expression": """(sumif([{"Assets"}, {"Own_funds"}],
            [K=="life_insurer" for K in [{"Type"}, {"Type"}]]) > 0)"""
            }
        ]
        actual = ruleminer.RuleMiner(templates=templates, data=df).rules
        expected = pd.DataFrame(
            data=[
                [
                    0,
                    0,
                    'if () then (sum([v.where(c, other=0) for (v,c) in zip([K for K in [{"Assets"}, {"Own_funds"}]],[(K=="life_insurer") for K in [{"Type"}, {"Type"}]])], axis=0)>0)',
                    "",
                    5,
                    5,
                    0.5,
                    0,
                    {},
                ]
            ],
            columns=[
                ruleminer.RULE_ID,
                ruleminer.RULE_GROUP,
                ruleminer.RULE_DEF,
                ruleminer.RULE_STATUS,
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.NOT_APPLICABLE,
                ruleminer.ENCODINGS,
            ],
        )
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_30_1_3(self):
        df = pd.DataFrame(
            columns=[
                "Name",
                "Type",
                "Assets",
                "TP-life",
                "TP-nonlife",
                "Own_funds",
                "Excess",
            ],
            data=[
                ["Insurer1", "life_insurer", 1000, 800, 0, 200, 200],
                ["Insurer2", "non-life_insurer", 4000, 0, 3200, 800, 800],
                ["Insurer3", "non-life_insurer", 800, 0, 700, 100, 100],
                ["Insurer4", "life_insurer", 2500, 1800, 0, 700, 700],
                ["Insurer5", "non-life_insurer", 2100, 0, 2200, 200, 200],
                ["Insurer6", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer7", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer8", "life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer9", "non-life_insurer", 9000, 8800, 0, 200, 200],
                ["Insurer10", "non-life_insurer", 9000, 0, 8800, 200, 199.99],
            ],
        )

        templates = [{"expression": """(sum([{"Assets"}, {"Own_funds"}]) > 0)"""}]
        actual = ruleminer.RuleMiner(templates=templates, data=df).rules
        expected = pd.DataFrame(
            data=[
                [
                    0,
                    0,
                    'if () then (sum([K for K in [{"Assets"}, {"Own_funds"}]], axis=0)>0)',
                    "",
                    10,
                    0,
                    1.0,
                    0,
                    {},
                ]
            ],
            columns=[
                ruleminer.RULE_ID,
                ruleminer.RULE_GROUP,
                ruleminer.RULE_DEF,
                ruleminer.RULE_STATUS,
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.NOT_APPLICABLE,
                ruleminer.ENCODINGS,
            ],
        )
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_31(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(0.05*({"A"}+0.5*{"B"}+{"C"})>0)', parse_all=True)
            .as_list()
        )
        expected = [
            ["0.05", "*", ['{"A"}', "+", "0.5", "*", '{"B"}', "+", '{"C"}'], ">", "0"]
        ]
        self.assertTrue(actual == expected)

    def test_32(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string(
                '(1*(1+0.5*({"A"}+0.5*({"B"}+1)+0.5*({"C"}+1)))>5)', parse_all=True
            )
            .as_list()
        )
        expected = [
            [
                "1",
                "*",
                [
                    "1",
                    "+",
                    "0.5",
                    "*",
                    [
                        '{"A"}',
                        "+",
                        "0.5",
                        "*",
                        ['{"B"}', "+", "1"],
                        "+",
                        "0.5",
                        "*",
                        ['{"C"}', "+", "1"],
                    ],
                ],
                ">",
                "5",
            ]
        ]

        self.assertTrue(actual == expected)

    def test_33(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(0.05*(0.5*({"A"}+1)+0.5*({"B"}+{"C"}))>0)', parse_all=True)
            .as_list()
        )
        expected = [
            [
                "0.05",
                "*",
                [
                    "0.5",
                    "*",
                    ['{"A"}', "+", "1"],
                    "+",
                    "0.5",
                    "*",
                    ['{"B"}', "+", '{"C"}'],
                ],
                ">",
                "0",
            ]
        ]
        self.assertTrue(actual == expected)

    def test_34(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(0.05*({"A"}+0.5*({"B"}+1))>2)', parse_all=True)
            .as_list()
        )
        expected = [
            ["0.05", "*", ['{"A"}', "+", "0.5", "*", ['{"B"}', "+", "1"]], ">", "2"]
        ]
        self.assertTrue(actual == expected)

    def test_35(self):
        actual = (
            ruleminer.function_expression()
            .parse_string('substr({"Type"}, 0, 3)', parseAll=True)
            .as_list()
        )
        expected = [["substr", ['{"Type"}', ",", "0", ",", "3"]]]
        self.assertTrue(actual == expected)

    def test_36(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(substr({"Type"}, 0, 3) > 0)', parseAll=True)
            .as_list()
        )
        expected = [[["substr", ['{"Type"}', ",", "0", ",", "3"]], ">", "0"]]
        self.assertTrue(actual == expected)

    def test_37(self):
        actual = (
            ruleminer.function_expression()
            .parse_string('max((substr({"Type"}, 0, 1)) in ["d"])', parseAll=True)
            .as_list()
        )
        expected = [
            [
                "max",
                [
                    [["substr", ['{"Type"}', ",", "0", ",", "1"]]],
                    "in",
                    ['"d"'],
                ],
            ]
        ]
        self.assertTrue(actual == expected)

    def test_38(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(max((substr({"Type"}, 0, 1)) in ["d"]) > 0)', parseAll=True)
            .as_list()
        )
        expected = [
            [
                [
                    "max",
                    [
                        [["substr", ['{"Type"}', ",", "0", ",", "1"]]],
                        "in",
                        ['"d"'],
                    ],
                ],
                ">",
                "0",
            ]
        ]
        self.assertTrue(actual == expected)

    def test_39(self):
        actual = (
            ruleminer.function_expression()
            .parse_string('abs(({"f"} + {"d"}))')
            .as_list()
        )
        expected = [["abs", [['{"f"}', "+", '{"d"}']]]]
        self.assertTrue(actual == expected)

    def test_40(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string(
                '({"Own funds"} <= quantile({"Own funds"}, 0.95))', parseAll=True
            )
            .as_list()
        )
        expected = [
            ['{"Own funds"}', "<=", ["quantile", ['{"Own funds"}', ",", "0.95"]]]
        ]
        self.assertTrue(actual == expected)

    def test_41(self):
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): -1,
                    (1e3, 1e6): -2,
                    (1e6, 1e8): -3,
                    (1e8, np.inf): -4,
                },
            },
        }
        formula = '(({"1"} >= 0))'
        rm_rules = ruleminer.RuleMiner(
            templates=[{"expression": formula}], params=parameters
        )
        actual = rm_rules.rules.values[0][2]
        expected = 'if () then ({"1" + default}>=0)'
        self.assertTrue(actual == expected)

    def test_42(self):
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): -1,
                    (1e3, 1e6): -2,
                    (1e6, 1e8): -3,
                    (1e8, np.inf): -4,
                },
            },
        }
        formula = '(({"1"}-{"2"}-{"3"}) == 0)'
        rm_rules = ruleminer.RuleMiner(
            templates=[{"expression": formula}], params=parameters
        )
        actual = rm_rules.rules.values[0][2]
        expected = 'if () then (((({"1" + default}-{"2" - default}-{"3" - default})) >= 0) & ((({"1" - default}-{"2" + default}-{"3" + default})) <= 0))'
        self.assertTrue(actual == expected)

    def test_43(self):
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): -1,
                    (1e3, 1e6): -2,
                    (1e6, 1e8): -3,
                    (1e8, np.inf): -4,
                },
            },
        }
        formula = '(({"1"}-({"2"}+{"3"})) == 0)'
        rm_rules = ruleminer.RuleMiner(
            templates=[{"expression": formula}], params=parameters
        )
        actual = rm_rules.rules.values[0][2]
        expected = 'if () then (((({"1" + default}-({"2" - default}+{"3" - default}))) >= 0) & ((({"1" - default}-({"2" + default}+{"3" + default}))) <= 0))'
        self.assertTrue(actual == expected)

    def test_44(self):
        # Specify tolerance input parameters for ruleminer
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): 0,  # 1,
                    (1e3, 1e6): 0,  # 2,
                    (1e6, 1e8): 0,  # 3,
                    (1e8, np.inf): 0,  # 4,
                },
            },
        }
        formulas = [
            '({"A"} == {"B"} * 0.25)',
        ]
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas], params=parameters
        )
        actual = r.rules.values[0][2]
        expected = 'if () then (({"A" + default} >= {"B" - default}*0.25) & ({"A" - default} <= {"B" + default}*0.25))'
        self.assertTrue(actual == expected)

    def test_45(self):
        # Specify tolerance input parameters for ruleminer
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): -20,  # 1,
                    (1e3, 1e6): -20,  # 2,
                    (1e6, 1e8): -20,  # 3,
                    (1e8, np.inf): -20,  # 4,
                },
            },
        }
        formulas = [
            'IF ({"A"} > 0) THEN (ABS({"A"} - {"B"}) > 0)',
        ]
        df = pd.DataFrame(
            [
                ["Test_1", 0.25, 1.0, "ABCD"],
                ["Test_2", 1.0, 1.0, ""],
                ["Test_3", 0.0, 0.0, "ABCD"],
            ],
            columns=["Name", "A", "B", "C"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            data=df,
            params=parameters,
        )
        r.evaluate()
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result"]
            ]
            .values
        )
        expected = [
            ["Test_1", True],
            ["Test_2", False],
            ["Test_3", True],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_46(self):
        # Specify tolerance input parameters for ruleminer
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): -20,  # 1,
                    (1e3, 1e6): -20,  # 2,
                    (1e6, 1e8): -20,  # 3,
                    (1e8, np.inf): -20,  # 4,
                },
            },
        }
        formulas = [
            '(({"A"} == 0) & (SUBSTR({"C"}, 2, 4) IN ["CD"]))',
        ]
        df = pd.DataFrame(
            [
                ["Test_1", 0.25, 1.0, "ABCD"],
                ["Test_2", 1.0, 1.0, ""],
                ["Test_3", 0.0, 0.0, "ABCD"],
            ],
            columns=["Name", "A", "B", "C"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        r.evaluate()
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result"]
            ]
            .values
        )
        expected = [
            ["Test_1", False],
            ["Test_2", False],
            ["Test_3", True],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_47(self):
        # Specify tolerance input parameters for ruleminer
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): -20,  # 1,
                    (1e3, 1e6): -20,  # 2,
                    (1e6, 1e8): -20,  # 3,
                    (1e8, np.inf): -20,  # 4,
                },
            },
        }
        formulas = [
            '(({"A"} == 0) & ({"C"}!=""))',
        ]
        df = pd.DataFrame(
            [
                ["Test_1", 0.25, 1.0, "ABCD"],
                ["Test_2", 1.0, 1.0, ""],
                ["Test_3", 0.0, 0.0, "ABCD"],
            ],
            columns=["Name", "A", "B", "C"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        r.evaluate()
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result"]
            ]
            .values
        )
        expected = [
            ["Test_1", False],
            ["Test_2", False],
            ["Test_3", True],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_48(self):
        # Specify tolerance input parameters for ruleminer
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): 0,  # 1,
                    (1e3, 1e6): 0,  # 2,
                    (1e6, 1e8): 0,  # 3,
                    (1e8, np.inf): 0,  # 4,
                },
            },
        }
        formulas = [
            '(COUNTIF([{"A"}, {"B"}], [SUBSTR(K, 2, 4) IN ["CD"] for K IN [{"C"}, {"D"}]]) > 1)',
        ]
        df = pd.DataFrame(
            [
                ["Test_1", 0.25, 1.0, "ABCD", "ABCD"],
                ["Test_2", 1.0, 1.0, "", "ABCD"],
                ["Test_3", 0.0, 0.0, "ABCD", "EFGH"],
            ],
            columns=["Name", "A", "B", "C", "D"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        r.evaluate()
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result"]
            ]
            .values
        )
        expected = [
            ["Test_1", True],
            ["Test_2", False],
            ["Test_3", False],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_49(self):
        # Specify tolerance input parameters for ruleminer
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): -20,  # 1,
                    (1e3, 1e6): -20,  # 2,
                    (1e6, 1e8): -20,  # 3,
                    (1e8, np.inf): -20,  # 4,
                },
            },
        }
        formulas = [
            '(SUMIF([{"A"}, {"B"}], [SUBSTR(K, 2, 4) IN ["CD"] for K IN [{"C"}, {"D"}]]) > 1.0)',
        ]
        df = pd.DataFrame(
            [
                ["Test_1", 0.25, 1.0, "ABCD", "ABCD"],
                ["Test_2", 1.0, 1.0, "", "ABCD"],
                ["Test_3", 0.0, 0.0, "ABCD", "EFGH"],
            ],
            columns=["Name", "A", "B", "C", "D"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        self.assertTrue(
            r.rules.values[0][2]
            == 'if () then (sum([v.where(c, other=0) for (v,c) in zip([K for K in [{"A"}, {"B"}]],[K.str.slice(2,4).isin(["CD"]) for K in [{"C"}, {"D"}]])], axis=0)>1.0)'
        )
        r.evaluate()
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result"]
            ]
            .values
        )
        expected = [
            ["Test_1", True],
            ["Test_2", False],
            ["Test_3", False],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_50(self):
        # Specify tolerance input parameters for ruleminer
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): 0,  # 1,
                    (1e3, 1e6): 0,  # 2,
                    (1e6, 1e8): 0,  # 3,
                    (1e8, np.inf): 0,  # 4,
                },
            },
        }
        formulas = [
            '(SPLIT({"C"}, "C", 2) in ["D"])',
        ]
        df = pd.DataFrame(
            [
                ["Test_1", 0.25, 1.0, "ABCD", "ABCD"],
                ["Test_2", 1.0, 1.0, "", "ABCD"],
                ["Test_3", 0.0, 0.0, "ABCD", "EFGH"],
            ],
            columns=["Name", "A", "B", "C", "D"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        r.evaluate()
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result"]
            ]
            .values
        )
        expected = [
            ["Test_1", True],
            ["Test_2", False],
            ["Test_3", True],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_51(self):
        # Specify tolerance input parameters for ruleminer
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): 0,  # 1,
                    (1e3, 1e6): 0,  # 2,
                    (1e6, 1e8): 0,  # 3,
                    (1e8, np.inf): 0,  # 4,
                },
            },
        }
        formulas = [
            '((SUM([{"A"}, {"B"}])) == 0)',
        ]
        df = pd.DataFrame(
            [
                ["Test_1", 0.25, 1.0, "ABCD", "ABCD"],
                ["Test_2", 1.0, 1.0, "", "ABCD"],
                ["Test_3", 0.0, 0.0, "ABCD", "EFGH"],
            ],
            columns=["Name", "A", "B", "C", "D"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        self.assertTrue(
            r.rules.values[0][2],
            'if () then ((((sum([(K+0.5*abs(K.apply(__tol__, args=("default",)))) for K in [{"A"}, {"B"}]], axis=0))) >= 0) & (((sum([(K-0.5*abs(K.apply(__tol__, args=("default",)))) for K in [{"A"}, {"B"}]], axis=0))) <= 0))',
        )
        r.evaluate()
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result"]
            ]
            .values
        )
        expected = [
            ["Test_1", False],
            ["Test_2", False],
            ["Test_3", True],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_52(self):
        # Specify tolerance input parameters for ruleminer
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): 0,  # 1,
                    (1e3, 1e6): 0,  # 2,
                    (1e6, 1e8): 0,  # 3,
                    (1e8, np.inf): 0,  # 4,
                },
            },
        }
        formulas = [
            '((SUMIF([{"A"}, {"B"}], [SUBSTR(K, 2, 4) IN ["CD"] for K IN [{"C"}, {"D"}]])) == 0)',
        ]
        df = pd.DataFrame(
            [
                ["Test_1", 0.25, 1.0, "ABCD", "ABCD"],
                ["Test_2", 1.0, 1.0, "", "ABCD"],
                ["Test_3", 0.0, 0.0, "ABCD", "EFGH"],
            ],
            columns=["Name", "A", "B", "C", "D"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        self.assertTrue(
            r.rules.values[0][2],
            'if () then ((((sum([v.where(c, other=0) for (v,c) in zip([K for K in ([{"A"}, {"B"}])],[K.str.slice(2,4).isin(["CD"]) for K in [{"C"}, {"D"}]])], axis=0))))==0)',
        )
        r.evaluate()
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result"]
            ]
            .values
        )
        expected = [
            ["Test_1", False],
            ["Test_2", False],
            ["Test_3", True],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_53(self):
        formulas = [
            '(MAX(0, {"A"}) > 0)',
            '(MAX(0, ({"A"})) > 0)',
            '((MAX(0, ({"A"}))) > (0))',
            '(MAX(0, {"A"} - {"B"}) > 0)',
            '(MAX(0, ({"A"}- {"B"})) > 0)',
            '((MAX(0, ({"A"}- {"B"}))) > (0))',
            '(MAX(0, ({"A"}) - {"B"}) > 0)',
            '((MAX(0, (({"A"})- {"B"}))) > (0))',
            '({"A"}==MAX(0, MAX(0, {"A"})-MAX(0, {"B"})))',
        ]
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params={},
        )
        self.assertTrue(r.rules.values[0][2] == 'if () then (MAX(0, {"A"})>0)')
        self.assertTrue(r.rules.values[1][2] == 'if () then (MAX(0, {"A"})>0)')
        self.assertTrue(r.rules.values[2][2] == 'if () then (MAX(0, {"A"})>0)')
        self.assertTrue(r.rules.values[3][2] == 'if () then (MAX(0, {"A"}-{"B"})>0)')
        self.assertTrue(r.rules.values[4][2] == 'if () then (MAX(0, ({"A"}-{"B"}))>0)')
        self.assertTrue(r.rules.values[5][2] == 'if () then (MAX(0, ({"A"}-{"B"}))>0)')
        self.assertTrue(r.rules.values[6][2] == 'if () then (MAX(0, {"A"}-{"B"})>0)')
        self.assertTrue(r.rules.values[7][2] == 'if () then (MAX(0, ({"A"}-{"B"}))>0)')
        self.assertTrue(
            r.rules.values[8][2]
            == 'if () then ({"A"}==MAX(0, MAX(0, {"A"})-MAX(0, {"B"})))'
        )
        df = pd.DataFrame(
            [
                ["Test_1", 0.5, 1.0],
                ["Test_2", 1.0, 0.5],
                ["Test_3", 0.0, 0.0],
            ],
            columns=["Name", "A", "B"],
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df)
        r.evaluate()
        actual = list(
            r.results.sort_values(by=["rule_id", "indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                [
                    "rule_id",
                    "rule_group",
                    "rule_definition",
                    "rule_status",
                    "abs support",
                    "abs exceptions",
                    "confidence",
                    "result",
                    "indices",
                ]
            ]
            .values
        )
        self.assertListEqual(
            list(actual[0]),
            [
                0,
                0,
                'if () then (MAX(0, {"A"})>0)',
                "",
                2,
                1,
                0.6666666666666666,
                True,
                0,
            ],
        )
        self.assertListEqual(
            list(actual[1]),
            [
                0,
                0,
                'if () then (MAX(0, {"A"})>0)',
                "",
                2,
                1,
                0.6666666666666666,
                True,
                1,
            ],
        )
        self.assertListEqual(
            list(actual[2]),
            [
                0,
                0,
                'if () then (MAX(0, {"A"})>0)',
                "",
                2,
                1,
                0.6666666666666666,
                False,
                2,
            ],
        )
        self.assertListEqual(
            list(actual[26]),
            [
                8,
                0,
                'if () then ({"A"}==MAX(0, MAX(0, {"A"})-MAX(0, {"B"})))',
                "",
                1,
                2,
                0.3333333333333333,
                True,
                2,
            ],
        )

    def test_54(self):
        data = {
            "C0450": [
                np.nan,
                "ESTR CMP-0.11%;4.5%;USD",
                "INVALID DATA",
                "ESTR CMP-0.25%;3.14%;EUR",
            ],
            "C0460": [
                np.nan,
                "ESTR CMP+0.25%;2.56%;EUR",
                "ESTR CMP-0.10%;3.10%;EUR",
                "INVALID DATA",
            ],
        }
        df = pd.DataFrame(data)
        formulas = [
            r'({"C0450"} match "^\s*[\w\s]+\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*\w{3}$")'
        ]
        rm_rules = ruleminer.RuleMiner(
            templates=[
                {"expression": formulas[0]},
            ],
        )
        rm_eval = ruleminer.RuleMiner(rules=rm_rules.rules, data=df)
        rm_eval.evaluate()
        actual = rm_eval.results.values

        self.assertListEqual(
            list(actual[0]),
            [
                0,
                0,
                r'if () then {"C0450"}.str.match(r"^\s*[\w\s]+\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*\w{3}$", na=False)',
                "",
                2,
                2,
                0.5,
                0,
                True,
                1,
            ],
        )
        self.assertListEqual(
            list(actual[1]),
            [
                0,
                0,
                r'if () then {"C0450"}.str.match(r"^\s*[\w\s]+\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*\w{3}$", na=False)',
                "",
                2,
                2,
                0.5,
                0,
                True,
                3,
            ],
        )
        self.assertListEqual(
            list(actual[2]),
            [
                0,
                0,
                r'if () then {"C0450"}.str.match(r"^\s*[\w\s]+\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*\w{3}$", na=False)',
                "",
                2,
                2,
                0.5,
                0,
                False,
                0,
            ],
        )
        self.assertListEqual(
            list(actual[3]),
            [
                0,
                0,
                r'if () then {"C0450"}.str.match(r"^\s*[\w\s]+\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*\w{3}$", na=False)',
                "",
                2,
                2,
                0.5,
                0,
                False,
                2,
            ],
        )

    def test_55(self):
        # Specify tolerance input parameters for ruleminer
        parameters = {
            "tolerance": {
                "default": {
                    (0, 1e3): 0,  # 1,
                    (1e3, 1e6): 0,  # 2,
                    (1e6, 1e8): 0,  # 3,
                    (1e8, np.inf): 0,  # 4,
                },
            },
        }
        formulas = [
            '({"C"}=={"D"})',
        ]
        df = pd.DataFrame(
            [
                ["Test_1", 0.25, 1.0, "ABCD", "ABCD"],
                ["Test_2", 1.0, 1.0, "", "ABCD"],
                ["Test_3", 0.0, 0.0, "ABCD", "EFGH"],
            ],
            columns=["Name", "A", "B", "C", "D"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        self.assertTrue(
            r.rules.values[0][2],
            'if () then (({"C" + default} >= {"D" - default}) & ({"C" - default} <= {"D" + default}))',
        )
        r.evaluate()
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result"]
            ]
            .values
        )
        expected = [
            ["Test_1", True],
            ["Test_2", False],
            ["Test_3", False],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    # def setUp_templates(self):
    #     """Set up test fixtures, if any."""
    #     templates = ["template"]
    #     r = ruleminer.RuleMiner(templates=templates, rules=rules)
    #     assert r.templates == ["template"]

    # def test_command_line_interface(self):
    #     """Test the CLI."""
    #     runner = CliRunner()
    #     result = runner.invoke(cli.main)
    #     assert result.exit_code == 0
    #     assert 'ruleminer.cli.main' in result.output
    #     help_result = runner.invoke(cli.main, ['--help'])
    #     assert help_result.exit_code == 0
    #     assert '--help  Show this message and exit.' in help_result.output
