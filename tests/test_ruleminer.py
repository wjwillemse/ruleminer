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
        expected = [["(", '{"f"}', "==", "0", ")"]]
        self.assertTrue(actual == expected)

    def test_7(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('({"f"} > 0)', parse_all=True)
            .as_list()
        )
        expected = [["(", '{"f"}', ">", "0", ")"]]
        self.assertTrue(actual == expected)

    def test_8(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('({"f"} == 0) & ({"w"} == 0)', parse_all=True)
            .as_list()
        )
        expected = [
            [["(", '{"f"}', "==", "0", ")"], "&", ["(", '{"w"}', "==", "0", ")"]]
        ]
        self.assertTrue(actual == expected)

    def test_9(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('~({"f"} == 0) & ({"d"} == "s")', parse_all=True)
            .as_list()
        )
        expected = [
            [
                ["~", ["(", '{"f"}', "==", "0", ")"]],
                "&",
                ["(", '{"d"}', "==", '"s"', ")"],
            ]
        ]
        self.assertTrue(actual == expected)

    def test_10(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(min({"f"}, {"d"})>0) & ({"d"} == "s")', parse_all=True)
            .as_list()
        )
        expected = [
            [
                ["(", ["min", ["(", '{"f"}', ",", '{"d"}', ")"]], ">", "0", ")"],
                "&",
                ["(", '{"d"}', "==", '"s"', ")"],
            ]
        ]
        self.assertTrue(actual == expected)

    def test_11(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(({"f"} + {"d"}) > 0)', parse_all=True)
            .as_list()
        )
        expected = [["(", ["(", '{"f"}', "+", '{"d"}', ")"], ">", "0", ")"]]
        self.assertTrue(actual == expected)

    def test_12(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(abs({"f"}) == 0)', parse_all=True)
            .as_list()
        )
        expected = [["(", ["abs", ["(", '{"f"}', ")"]], "==", "0", ")"]]
        self.assertTrue(actual == expected)

    def test_13(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(abs({"f"} + {"d"}) > 1) & ({"s"} < 2)', parse_all=True)
            .as_list()
        )
        expected = [
            [
                ["(", ["abs", ["(", '{"f"}', "+", '{"d"}', ")"]], ">", "1", ")"],
                "&",
                ["(", '{"s"}', "<", "2", ")"],
            ]
        ]
        self.assertTrue(actual == expected)

    def test_14(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('(({"4"} + {"3"} + {"2"} + {"1"}) > 0)', parse_all=True)
            .as_list()
        )
        expected = '(({"1"}+{"2"}+{"3"}+{"4"})>0)'
        self.assertTrue(actual == expected)

    def test_15(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('IF () THEN ("A"=="")', parse_all=True)
            .as_list()
        )
        expected = ["IF () THEN ", ["(", '"A"', "==", '""', ")"]]
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
            [
                "(",
                ["not", ["(", '"F3"', "in", ["[", '"G1"', ",", '"G3"', "]"], ")"]],
                ")",
            ],
            "THEN",
            [
                "(",
                ["SUBSTR", ["(", '{"A"}', ",", "2", ",", "4", ")"]],
                "in",
                ["[", '"D1"', ",", '"D3"', "]"],
                ")",
            ],
        ]
        self.assertTrue(actual == expected)

    def test_16b(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string(
                'IF ( not("F3" not in ["G1","G3"])) THEN \
                (SUBSTR({"A"}, 2, 4) not in ["D1","D3"])',
                parse_all=True,
            )
            .as_list()
        )
        expected = [
            "IF",
            [
                "(",
                ["not", ["(", '"F3"', "not in", ["[", '"G1"', ",", '"G3"', "]"], ")"]],
                ")",
            ],
            "THEN",
            [
                "(",
                ["SUBSTR", ["(", '{"A"}', ",", "2", ",", "4", ")"]],
                "not in",
                ["[", '"D1"', ",", '"D3"', "]"],
                ")",
            ],
        ]
        self.assertTrue(actual == expected)

    def test_17(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('if ("C" != "pd.NA") then ( "A" > -1)', parse_all=True)
            .as_list()
        )
        expected = [
            "if",
            ["(", '"C"', "!=", '"pd.NA"', ")"],
            "then",
            ["(", '"A"', ">", "-1", ")"],
        ]
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
            ["(", "0", ">", ["min", ["(", '{"C"}', ",", '{"B"}', ")"]], ")"],
            "then",
            ["(", "1", "==", ["sum", ["(", '{"A"}', ",", '{"B"}', ")"]], ")"],
        ]
        self.assertTrue(actual == expected)

    def test_19(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('(({"4"} + {"3"} + {"2"} * {"1"}) > 0)', parse_all=True)
            .as_list()
        )
        expected = '(({"1"}*{"2"}+{"3"}+{"4"})>0)'
        self.assertTrue(actual == expected)

    def test_20(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('(({"4"} + {"3"} * {"2"} + {"1"}) > 0)', parse_all=True)
            .as_list()
        )
        expected = '(({"1"}+{"2"}*{"3"}+{"4"})>0)'
        self.assertTrue(actual == expected)

    def test_21(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('(({"4"} * {"3"} + {"2"} + {"1"}) > 0)', parse_all=True)
            .as_list()
        )
        expected = '(({"1"}+{"2"}+{"3"}*{"4"})>0)'
        self.assertTrue(actual == expected)

    def test_22(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('({"4"} == {"3"})', parse_all=True)
            .as_list()
        )
        expected = '({"3"}=={"4"})'
        self.assertTrue(actual == expected)

    def test_23(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('({"4"} != {"3"})', parse_all=True)
            .as_list()
        )
        expected = '({"3"}!={"4"})'
        self.assertTrue(actual == expected)

    def test_24(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('({"4"} > {"3"})', parse_all=True)
            .as_list()
        )
        expected = '({"4"}>{"3"})'
        self.assertTrue(actual == expected)

    def test_25(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('(({"4"} > {"3"}) & ({"2"} > {"1"}))', parse_all=True)
            .as_list()
        )
        expected = '(({"2"}>{"1"})&({"4"}>{"3"}))'
        self.assertTrue(actual == expected)

    def test_26(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string('(({"4"} > {"3"}) & ({"2"} == {"1"}))', parse_all=True)
            .as_list()
        )
        expected = '(({"1"}=={"2"})&({"4"}>{"3"}))'
        self.assertTrue(actual == expected)

    def test_27(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.rule_expression()
            .parse_string(
                '(({"4"} > {"3"}) & (({"2"}+{"0"}) == {"1"}))', parse_all=True
            )
            .as_list()
        )
        expected = '((({"0"}+{"2"})=={"1"})&({"4"}>{"3"}))'
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
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.NOT_APPLICABLE,
                ruleminer.ENCODINGS,
            ],
        )
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_29a(self):
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

        templates = [{"expression": '({"Own_funds"} <= quantile({"Own_funds"},0.95))'}]
        actual = ruleminer.RuleMiner(
            templates=templates, data=df, params={"evaluate_statistics": True}
        ).rules
        expected = pd.DataFrame(
            data=[[0, 0, 'if () then ({"Own_funds"}<=755.0)', 9, 1, 0.9, 0, {}]],
            columns=[
                ruleminer.RULE_ID,
                ruleminer.RULE_GROUP,
                ruleminer.RULE_DEF,
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.NOT_APPLICABLE,
                ruleminer.ENCODINGS,
            ],
        )
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_29b(self):
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

        templates = [{"expression": '({"Own_funds"} <= mean({"Own_funds"}))'}]
        actual = ruleminer.RuleMiner(
            templates=templates, data=df, params={"evaluate_statistics": True}
        ).rules
        expected = pd.DataFrame(
            data=[[0, 0, 'if () then ({"Own_funds"}<=300.0)', 8, 2, 0.8, 0, {}]],
            columns=[
                ruleminer.RULE_ID,
                ruleminer.RULE_GROUP,
                ruleminer.RULE_DEF,
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.NOT_APPLICABLE,
                ruleminer.ENCODINGS,
            ],
        )
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_29c(self):
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

        templates = [{"expression": '({"Own_funds"} <= std({"Own_funds"}))'}]
        actual = ruleminer.RuleMiner(
            templates=templates, data=df, params={"evaluate_statistics": True}
        ).rules
        expected = pd.DataFrame(
            data=[[0, 0, 'if () then ({"Own_funds"}<=228.03508502)', 8, 2, 0.8, 0, {}]],
            columns=[
                ruleminer.RULE_ID,
                ruleminer.RULE_GROUP,
                ruleminer.RULE_DEF,
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.NOT_APPLICABLE,
                ruleminer.ENCODINGS,
            ],
        )
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_30a(self):
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
                    'if () then ({"Own_funds"}<=quantile({"Own_funds"},0.95))',
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
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.NOT_APPLICABLE,
                ruleminer.ENCODINGS,
            ],
        )
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_30b(self):
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

        templates = [{"expression": '({"Own_funds"} <= mean({"Own_funds"}))'}]
        actual = ruleminer.RuleMiner(templates=templates, data=df).rules
        expected = pd.DataFrame(
            data=[
                [
                    0,
                    0,
                    'if () then ({"Own_funds"}<=mean({"Own_funds"}))',
                    8,
                    2,
                    0.8,
                    0,
                    {},
                ]
            ],
            columns=[
                ruleminer.RULE_ID,
                ruleminer.RULE_GROUP,
                ruleminer.RULE_DEF,
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.NOT_APPLICABLE,
                ruleminer.ENCODINGS,
            ],
        )
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_30c(self):
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

        templates = [{"expression": '({"Own_funds"} <= std({"Own_funds"}))'}]
        actual = ruleminer.RuleMiner(templates=templates, data=df).rules
        expected = pd.DataFrame(
            data=[
                [
                    0,
                    0,
                    'if () then ({"Own_funds"}<=std({"Own_funds"}))',
                    8,
                    2,
                    0.8,
                    0,
                    {},
                ]
            ],
            columns=[
                ruleminer.RULE_ID,
                ruleminer.RULE_GROUP,
                ruleminer.RULE_DEF,
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
                    'if () then (sum([K for K in [{"Assets"}.where({"Type"}=="life_insurer", other=0),{"Own_funds"}.where({"Type"}=="life_insurer", other=0)]], axis=0, dtype=float)>0)',
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
                    'if () then (sum([v.where(c, other=0) for (v,c) in zip([K for K in [{"Assets"},{"Own_funds"}]],[K=="life_insurer" for K in [{"Type"},{"Type"}]])], axis=0, dtype=float)>0)',
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
                    'if () then (sum([K for K in [{"Assets"},{"Own_funds"}]], axis=0, dtype=float)>0)',
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
            [
                "(",
                [
                    "0.05",
                    "*",
                    ["(", '{"A"}', "+", ["0.5", "*", '{"B"}'], "+", '{"C"}', ")"],
                ],
                ">",
                "0",
                ")",
            ]
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
                "(",
                [
                    "1",
                    "*",
                    [
                        "(",
                        "1",
                        "+",
                        [
                            "0.5",
                            "*",
                            [
                                "(",
                                '{"A"}',
                                "+",
                                ["0.5", "*", ["(", '{"B"}', "+", "1", ")"]],
                                "+",
                                ["0.5", "*", ["(", '{"C"}', "+", "1", ")"]],
                                ")",
                            ],
                        ],
                        ")",
                    ],
                ],
                ">",
                "5",
                ")",
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
                "(",
                [
                    "0.05",
                    "*",
                    [
                        "(",
                        ["0.5", "*", ["(", '{"A"}', "+", "1", ")"]],
                        "+",
                        ["0.5", "*", ["(", '{"B"}', "+", '{"C"}', ")"]],
                        ")",
                    ],
                ],
                ">",
                "0",
                ")",
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
            [
                "(",
                [
                    "0.05",
                    "*",
                    [
                        "(",
                        '{"A"}',
                        "+",
                        ["0.5", "*", ["(", '{"B"}', "+", "1", ")"]],
                        ")",
                    ],
                ],
                ">",
                "2",
                ")",
            ]
        ]
        self.assertTrue(actual == expected)

    def test_35(self):
        actual = (
            ruleminer.function_expression()
            .parse_string('substr({"Type"}, 0, 3)', parseAll=True)
            .as_list()
        )
        expected = [["substr", ["(", '{"Type"}', ",", "0", ",", "3", ")"]]]
        self.assertTrue(actual == expected)

    def test_36(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(substr({"Type"}, 0, 3) > 0)', parseAll=True)
            .as_list()
        )
        expected = [
            ["(", ["substr", ["(", '{"Type"}', ",", "0", ",", "3", ")"]], ">", "0", ")"]
        ]
        self.assertTrue(actual == expected)

    def test_37(self):
        actual = (
            ruleminer.function_expression()
            .parse_string('max(substr({"Type"}, 0, 1) in ["d"])', parseAll=True)
            .as_list()
        )
        expected = [
            [
                "max",
                [
                    "(",
                    ["substr", ["(", '{"Type"}', ",", "0", ",", "1", ")"]],
                    "in",
                    ["[", '"d"', "]"],
                    ")",
                ],
            ]
        ]
        self.assertTrue(actual == expected)

    def test_38(self):
        actual = (
            ruleminer.rule_expression()
            .parse_string('(max(substr({"Type"}, 0, 1) in ["d"]) > 0)', parseAll=True)
            .as_list()
        )
        expected = [
            [
                "(",
                [
                    "max",
                    [
                        "(",
                        ["substr", ["(", '{"Type"}', ",", "0", ",", "1", ")"]],
                        "in",
                        ["[", '"d"', "]"],
                        ")",
                    ],
                ],
                ">",
                "0",
                ")",
            ]
        ]
        self.assertTrue(actual == expected)

    def test_39(self):
        actual = (
            ruleminer.function_expression().parse_string('abs({"f"} + {"d"})').as_list()
        )
        expected = [["abs", ["(", '{"f"}', "+", '{"d"}', ")"]]]
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
            [
                "(",
                '{"Own funds"}',
                "<=",
                ["quantile", ["(", '{"Own funds"}', ",", "0.95", ")"]],
                ")",
            ]
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
        expected = 'if () then ((_ge({"1"}, 0, {"1"}.apply(_tol, args=("+", "default",)), {"1"}.apply(_tol, args=("-", "default",)), 0, 0)))'
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
        expected = 'if () then (_eq(({"1"}-{"2"}-{"3"}), 0, ({"1"}.apply(_tol, args=("+", "default",))-{"2"}.apply(_tol, args=("-", "default",))-{"3"}.apply(_tol, args=("-", "default",))), ({"1"}.apply(_tol, args=("-", "default",))-{"2"}.apply(_tol, args=("+", "default",))-{"3"}.apply(_tol, args=("+", "default",))), 0, 0))'

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
        expected = 'if () then (_eq(({"1"}-({"2"}+{"3"})), 0, ({"1"}.apply(_tol, args=("+", "default",))-({"2"}.apply(_tol, args=("-", "default",))+{"3"}.apply(_tol, args=("-", "default",)))), ({"1"}.apply(_tol, args=("-", "default",))-({"2"}.apply(_tol, args=("+", "default",))+{"3"}.apply(_tol, args=("+", "default",)))), 0, 0))'
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
        expected = 'if () then (_eq({"A"}, {"B"}*0.25, {"A"}.apply(_tol, args=("+", "default",)), {"A"}.apply(_tol, args=("-", "default",)), {"B"}.apply(_tol, args=("+", "default",))*0.25, {"B"}.apply(_tol, args=("-", "default",))*0.25))'
        self.assertTrue(actual == expected)

    def test_45a(self):
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
                ["Test_2", 0.5, 1.0, "ABCD"],
                ["Test_3", 1.0, 1.0, "ABCD"],
                ["Test_4", 1.0, 0.0, "ABCD"],
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
            ["Test_2", True],
            ["Test_3", False],
            ["Test_4", True],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])
        self.assertListEqual(list(actual[3]), expected[3])

    def test_45b(self):
        # Specify tolerance input parameters for ruleminer
        parameters = {
            "tolerance": {
                "default": {
                    (0, np.inf): -1,  # 4,
                },
            },
        }
        formulas = [
            '(ABS({"A"}) == {"B"})',
        ]
        df = pd.DataFrame(
            [
                ["Test_1", 0.1, 1.0],
                ["Test_2", 0.1, 0.1],
                ["Test_3", -0.1, 1.0],
                ["Test_4", -0.1, 0.1],
            ],
            columns=["Name", "A", "B"],
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
            ["Test_1", False],
            ["Test_2", True],
            ["Test_3", False],
            ["Test_4", True],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])
        self.assertListEqual(list(actual[3]), expected[3])

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
            '(({"A"} == 0) & (SUBSTR({"C"}, 3, 2) IN ["CD"]))',
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
            '(COUNTIF([{"A"}, {"B"}], [SUBSTR(K, 3, 2) IN ["CD"] for K IN [{"C"}, {"D"}]]) > 1)',
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
            '(SUMIF([{"A"}, {"B"}], [SUBSTR(K, 3, 2) IN ["CD"] for K IN [{"C"}, {"D"}]]) > 1.0)',
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
            == 'if () then (_gt(sum([v.where(c, other=0) for (v,c) in zip([K.apply(_tol, args=("+", "default",)) for K in [{"A"},{"B"}]],[K.str.slice(2,4).isin(["CD"]) for K in [{"C"},{"D"}]])], axis=0, dtype=float), 1.0, sum([v.where(c, other=0) for (v,c) in zip([K.apply(_tol, args=("+", "default",)) for K in [{"A"},{"B"}]],[K.str.slice(2,4).isin(["CD"]) for K in [{"C"},{"D"}]])], axis=0, dtype=float), sum([v.where(c, other=0) for (v,c) in zip([K.apply(_tol, args=("-", "default",)) for K in [{"A"},{"B"}]],[K.str.slice(2,4).isin(["CD"]) for K in [{"C"},{"D"}]])], axis=0, dtype=float), 1.0, 1.0))'
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

    def test_50b(self):
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
            '(SPLIT({"C"}, "C", 2) not in ["D"])',
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
            ["Test_1", False],
            ["Test_2", True],
            ["Test_3", False],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_51a(self):
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
            r.rules.values[0][2]
            == 'if () then (_eq((sum([K for K in [{"A"},{"B"}]], axis=0, dtype=float)), 0, (sum([K.apply(_tol, args=("+", "default",)) for K in [{"A"},{"B"}]], axis=0, dtype=float)), (sum([K.apply(_tol, args=("-", "default",)) for K in [{"A"},{"B"}]], axis=0, dtype=float)), 0, 0))'
        )

    def test_51b(self):
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
            '((SUMIF([{"A"}, {"B"}], [SUBSTR(K, 3, 2) IN ["CD"] for K IN [{"C"}, {"D"}]])) == 0)',
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
            == 'if () then (_eq((sum([v.where(c, other=0) for (v,c) in zip([K.apply(_tol, args=("+", "default",)) for K in [{"A"},{"B"}]],[K.str.slice(2,4).isin(["CD"]) for K in [{"C"},{"D"}]])], axis=0, dtype=float)), 0, (sum([v.where(c, other=0) for (v,c) in zip([K.apply(_tol, args=("+", "default",)) for K in [{"A"},{"B"}]],[K.str.slice(2,4).isin(["CD"]) for K in [{"C"},{"D"}]])], axis=0, dtype=float)), (sum([v.where(c, other=0) for (v,c) in zip([K.apply(_tol, args=("-", "default",)) for K in [{"A"},{"B"}]],[K.str.slice(2,4).isin(["CD"]) for K in [{"C"},{"D"}]])], axis=0, dtype=float)), 0, 0))',
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
        self.assertTrue(r.rules.values[0][2] == 'if () then (MAX(0,{"A"})>0)')
        self.assertTrue(r.rules.values[1][2] == 'if () then (MAX(0,({"A"}))>0)')
        self.assertTrue(r.rules.values[2][2] == 'if () then ((MAX(0,({"A"})))>(0))')
        self.assertTrue(r.rules.values[3][2] == 'if () then (MAX(0,{"A"}-{"B"})>0)')
        self.assertTrue(r.rules.values[4][2] == 'if () then (MAX(0,({"A"}-{"B"}))>0)')
        self.assertTrue(
            r.rules.values[5][2] == 'if () then ((MAX(0,({"A"}-{"B"})))>(0))'
        )
        self.assertTrue(r.rules.values[6][2] == 'if () then (MAX(0,({"A"})-{"B"})>0)')
        self.assertTrue(
            r.rules.values[7][2] == 'if () then ((MAX(0,(({"A"})-{"B"})))>(0))'
        )
        self.assertTrue(
            r.rules.values[8][2]
            == 'if () then ({"A"}==MAX(0,MAX(0,{"A"})-MAX(0,{"B"})))'
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
                'if () then (MAX(0,{"A"})>0)',
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
                'if () then (MAX(0,{"A"})>0)',
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
                'if () then (MAX(0,{"A"})>0)',
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
                'if () then ({"A"}==MAX(0,MAX(0,{"A"})-MAX(0,{"B"})))',
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
                r'if () then ({"C0450"}.str.match(r"^\s*[\w\s]+\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*\w{3}$", na=False))',
                2,
                2,
                0.5,
                0,
                True,
                1,
                None,
            ],
        )
        self.assertListEqual(
            list(actual[1]),
            [
                0,
                0,
                r'if () then ({"C0450"}.str.match(r"^\s*[\w\s]+\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*\w{3}$", na=False))',
                2,
                2,
                0.5,
                0,
                True,
                3,
                None,
            ],
        )
        self.assertListEqual(
            list(actual[2]),
            [
                0,
                0,
                r'if () then ({"C0450"}.str.match(r"^\s*[\w\s]+\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*\w{3}$", na=False))',
                2,
                2,
                0.5,
                0,
                False,
                0,
                None,
            ],
        )
        self.assertListEqual(
            list(actual[3]),
            [
                0,
                0,
                r'if () then ({"C0450"}.str.match(r"^\s*[\w\s]+\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*[+-]?\d+([.,]\d+)?\s*%\s*;\s*\w{3}$", na=False))',
                2,
                2,
                0.5,
                0,
                False,
                2,
                None,
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
            'if () then _equal(({"C" + default}, ({"C" - default}, {"D" + default}), {"D" - default}))',
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

    def test_56(self):
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
        formulas = ['({"A"} == (2*{"B"}*{"B"} + 0.3*{"B"}*{"C"})**0.5)']
        df = pd.DataFrame(
            [
                ["Test_1", 0.0, 0.0, 0.25, "ABCD"],
                ["Test_2", 1.0, 1.0, 0.25, "ABCD"],
                ["Test_3", 2.0, 0.0, 0.25, "EFGH"],
            ],
            columns=["Name", "A", "B", "C", "D"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        actual = r.rules.values[0][2]
        expected = """if () then (_eq({"A"}, max(0, (2*{"B"}*{"B"}+0.3*{"B"}*{"C"}))**0.5, {"A"}.apply(_tol, args=("+", "default",)), {"A"}.apply(_tol, args=("-", "default",)), max(0, (_mul(2*{"B"}.apply(_tol, args=("+", "default",)), 2*{"B"}.apply(_tol, args=("-", "default",)), {"B"}.apply(_tol, args=("+", "default",)), {"B"}.apply(_tol, args=("-", "default",)),"+")+_mul(0.3*{"B"}.apply(_tol, args=("+", "default",)), 0.3*{"B"}.apply(_tol, args=("-", "default",)), {"C"}.apply(_tol, args=("+", "default",)), {"C"}.apply(_tol, args=("-", "default",)),"+")))**0.5, max(0, (_mul(2*{"B"}.apply(_tol, args=("+", "default",)), 2*{"B"}.apply(_tol, args=("-", "default",)), {"B"}.apply(_tol, args=("+", "default",)), {"B"}.apply(_tol, args=("-", "default",)),"-")+_mul(0.3*{"B"}.apply(_tol, args=("+", "default",)), 0.3*{"B"}.apply(_tol, args=("-", "default",)), {"C"}.apply(_tol, args=("+", "default",)), {"C"}.apply(_tol, args=("-", "default",)),"-")))**0.5))"""
        self.assertEqual(expected, actual)
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
            ["Test_2", True],
            ["Test_3", False],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_57(self):
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
        formulas = ['(exact({"A"}) == 0)', '({"A"} == 0)']
        df = pd.DataFrame(
            [
                ["Test_1", 0.0],
                ["Test_2", 1.0],
                ["Test_3", 2.0],
            ],
            columns=["Name", "A"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then (_eq({"A"}, 0, {"A"}, {"A"}, 0, 0))'
        actual = r.rules.values[0][2]
        self.assertEqual(actual, expected)
        expected = 'if () then (_eq({"A"}, 0, {"A"}.apply(_tol, args=("+", "default",)), {"A"}.apply(_tol, args=("-", "default",)), 0, 0))'
        actual = r.rules.values[1][2]
        self.assertEqual(actual, expected)

    def test_57b(self):
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
        formulas = ['(exact({"A"}, 10) == 0)', '({"A"} == 0)']
        df = pd.DataFrame(
            [
                ["Test_1", 0.0],
                ["Test_2", 9.0],
                ["Test_3", 15.0],
            ],
            columns=["Name", "A"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then (_eq({"A"}, 0, ({"A"}+10), ({"A"}-10), 0, 0))'
        actual = r.rules.values[0][2]
        self.assertEqual(actual, expected)
        expected = 'if () then (_eq({"A"}, 0, {"A"}.apply(_tol, args=("+", "default",)), {"A"}.apply(_tol, args=("-", "default",)), 0, 0))'
        actual = r.rules.values[1][2]
        self.assertEqual(actual, expected)
        r.evaluate()
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "rule_id", "result"]
            ]
            .values
        )
        expected = [
            ["Test_1", 0, True],
            ["Test_1", 1, True],
            ["Test_2", 0, True],
            ["Test_2", 1, False],
            ["Test_3", 0, False],
            ["Test_3", 1, False],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])
        self.assertListEqual(list(actual[3]), expected[3])
        self.assertListEqual(list(actual[4]), expected[4])
        self.assertListEqual(list(actual[5]), expected[5])

    def test_57c(self):
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
        formulas = ['(exact({"A"}, 10, 20) == 0)', '({"A"} == 0)']
        df = pd.DataFrame(
            [
                ["Test_1", 0.0],
                ["Test_2", 1.0],
                ["Test_3", 2.0],
            ],
            columns=["Name", "A"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then (_eq({"A"}, 0, ({"A"}+20), ({"A"}-10), 0, 0))'
        actual = r.rules.values[0][2]
        self.assertEqual(actual, expected)
        expected = 'if () then (_eq({"A"}, 0, {"A"}.apply(_tol, args=("+", "default",)), {"A"}.apply(_tol, args=("-", "default",)), 0, 0))'
        actual = r.rules.values[1][2]
        self.assertEqual(actual, expected)

    def test_58(self):
        parameters = {
            "tolerance": {
                "default": None,
            },
        }
        formulas = ['(exact({"A"}) == 0)', '({"A"} == 0)']
        df = pd.DataFrame(
            [
                ["Test_1", 0.0],
                ["Test_2", 1.0],
                ["Test_3", 2.0],
            ],
            columns=["Name", "A"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then (_eq({"A"}, 0, {"A"}, {"A"}, 0, 0))'
        actual = r.rules.values[0][2]
        self.assertEqual(actual, expected)
        expected = 'if () then (_eq({"A"}, 0, {"A"}, {"A"}, 0, 0))'
        actual = r.rules.values[1][2]
        self.assertEqual(actual, expected)

    def test_59(self):
        parameters = {
            "tolerance": {
                "default": None,
            },
            "matrices": {
                "matrix_1": [
                    [1, 2, 3, 4],
                    [5, 6, 7, 8],
                    [9, 10, 11, 12],
                    [13, 14, 15, 16],
                ]
            },
        }
        formulas = ['(corr("matrix_1", {"a"}, {"b"}, {"c"}, {"d"})==10)']
        df = pd.DataFrame(
            [
                ["Test_1", 3, 1, 1, 0],
                ["Test_2", 2, 2, 2, 2],
                ["Test_3", 3, 3, 3, 3],
            ],
            columns=["Name", "a", "b", "c", "d"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then (_eq(_corr("matrix_1",{"a"},{"b"},{"c"},{"d"}), 10, _corr("matrix_1",{"a"},{"b"},{"c"},{"d"}), _corr("matrix_1",{"a"},{"b"},{"c"},{"d"}), 10, 10))'
        actual = r.rules.values[0][2]
        self.assertEqual(actual, expected)
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

    def test_60(self):
        parameters = {
            "tolerance": {
                "default": None,
            },
        }
        formulas = ['({"Name"} contains "Test")']
        df = pd.DataFrame(
            [
                ["Test_1", 0.0],
                ["Test_2", 1.0],
                ["Tst_3", 2.0],
            ],
            columns=["Name", "A"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then ({"Name"}.str.contains("Test", na=False))'
        actual = r.rules.values[0][2]
        self.assertEqual(actual, expected)
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result"]
            ]
            .values
        )
        expected = [
            ["Test_1", True],
            ["Test_2", True],
            ["Tst_3", False],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_61(self):
        parameters = {
            "tolerance": {
                "default": None,
            },
        }
        formulas = ['({"Name"} not contains "Test")']
        df = pd.DataFrame(
            [
                ["Test_1", 0.0],
                ["Test_2", 1.0],
                ["Tst_3", 2.0],
            ],
            columns=["Name", "A"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then (~{"Name"}.str.contains("Test", na=False))'
        actual = r.rules.values[0][2]
        self.assertEqual(actual, expected)
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
            ["Tst_3", True],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_62(self):
        parameters = {
            "tolerance": {
                "default": None,
            },
        }
        formulas = ['(ROUND({"A"}, -1)==10)']
        df = pd.DataFrame(
            [
                ["Test_1", 11.0],
                ["Test_2", 15.0],
                ["Test_3", 16.0],
            ],
            columns=["Name", "A"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then (_eq(_round({"A"}, -1, "round"), 10, _round({"A"}, -1, "round"), _round({"A"}, -1, "round"), 10, 10))'
        actual = r.rules.values[0][2]
        self.assertEqual(actual, expected)
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

    def test_63(self):
        parameters = {
            "tolerance": {
                "default": None,
            },
        }
        formulas = ['({"A"} between [1, 15])']
        df = pd.DataFrame(
            [
                ["Test_1", 11.0],
                ["Test_2", 15.0],
                ["Test_3", 16.0],
            ],
            columns=["Name", "A"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then ({"A"}.between(1,15))'
        actual = r.rules.values[0][2]
        self.assertEqual(actual, expected)
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result"]
            ]
            .values
        )
        expected = [
            ["Test_1", True],
            ["Test_2", True],
            ["Test_3", False],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_64(self):
        parameters = {
            "tolerance": {
                "default": None,
            },
        }
        formulas = ['({"A"} not between [1, 15])']
        df = pd.DataFrame(
            [
                ["Test_1", 11.0],
                ["Test_2", 15.0],
                ["Test_3", 16.0],
            ],
            columns=["Name", "A"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then (~{"A"}.between(1,15))'
        actual = r.rules.values[0][2]
        self.assertEqual(actual, expected)
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

    def test_parser_1(self):
        assert not ruleminer.contains_column('"A"')
        assert ruleminer.contains_column('{"A"}')
        assert ruleminer.contains_column(['{"A"}', '"B"'])
        assert ruleminer.contains_string('"A"')
        assert not ruleminer.contains_string('{"A"}')
        assert ruleminer.contains_string(['{"A"}', '"B"'])
        # when expression is a sumif or countif then skip the condition part
        expression = [
            "sumif",
            [
                ["[", '{"Assets"}', ",", '{"Own_funds"}', "]"],
                ",",
                '{"Type"}',
                "==",
                '"life_insurer"',
            ],
        ]
        assert not ruleminer.contains_string(expression)
        assert ruleminer.contains_column(expression)

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
