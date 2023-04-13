#!/usr/bin/env python

"""Tests for `ruleminer` package."""


import unittest
from click.testing import CliRunner

from ruleminer import ruleminer
from ruleminer import cli
import pandas as pd

class TestRuleminer(unittest.TestCase):
    """Tests for `ruleminer` package."""

    def setUp_ruleminer(self):
        """Set up test fixtures, if any."""
        r = ruleminer.RuleMiner()
        assert r is not None

    def test_1(self):
        actual = ruleminer.parser.COLUMN.parse_string('{"A"}', parse_all=True).as_list()
        expected = ['{"A"}']
        self.assertTrue(actual == expected)

    def test_2(self):
        actual = ruleminer.parser.QUOTED_STRING.parse_string(
            '"A"', parse_all=True
        ).as_list()
        expected = ['"A"']
        self.assertTrue(actual == expected)

    def test_3(self):
        actual = ruleminer.parser.TERM.parse_string('"b"', parse_all=True).as_list()
        expected = ['"b"']
        self.assertTrue(actual == expected)

    def test_4(self):
        actual = ruleminer.parser.TERM.parse_string('{"b"}', parse_all=True).as_list()
        expected = ['{"b"}']
        self.assertTrue(actual == expected)

    def test_5(self):
        actual = ruleminer.parser.TERM.parse_string("221", parse_all=True).as_list()
        expected = ["221"]
        self.assertTrue(actual == expected)

    def test_6(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            '({"f"} == 0)', parse_all=True
        ).as_list()
        expected = [['{"f"}', "==", "0"]]
        self.assertTrue(actual == expected)

    def test_7(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            '({"f"} > 0)', parse_all=True
        ).as_list()
        expected = [['{"f"}', ">", "0"]]
        self.assertTrue(actual == expected)

    def test_8(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            '({"f"} == 0) & ({"w"} == 0)', parse_all=True
        ).as_list()
        expected = [[['{"f"}', "==", "0"], "&", ['{"w"}', "==", "0"]]]
        self.assertTrue(actual == expected)

    def test_9(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            '~({"f"} == 0) & ({"d"} == "s")', parse_all=True
        ).as_list()
        expected = [[["~", ['{"f"}', "==", "0"]], "&", ['{"d"}', "==", '"s"']]]
        self.assertTrue(actual == expected)

    def test_10(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            '(min({"f"}, {"d"})>0) & ({"d"} == "s")', parse_all=True
        ).as_list()
        expected = [
            [["min", ['{"f"}', ',', '{"d"}'], ">", "0"], "&", ['{"d"}', "==", '"s"']]
        ]
        self.assertTrue(actual == expected)

    def test_11(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            '(({"f"} + {"d"}) > 0)', parse_all=True
        ).as_list()
        expected = [[['{"f"}', "+", '{"d"}'], ">", "0"]]
        self.assertTrue(actual == expected)

    def test_12(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            '(abs({"f"}) == 0)', parse_all=True
        ).as_list()
        expected = [["abs", ['{"f"}'], "==", "0"]]
        self.assertTrue(actual == expected)

    def test_13(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            '(abs({"f"} + {"d"}) > 1) & ({"s"} < 2)', parse_all=True
        ).as_list()
        expected = [
            [["abs", [['{"f"}', "+", '{"d"}']], ">", "1"], "&", ['{"s"}', "<", "2"]]
        ]
        self.assertTrue(actual == expected)

    def test_14(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.parser.RULE_SYNTAX.parse_string(
                '(({"4"} + {"3"} + {"2"} + {"1"}) > 0)', parse_all=True
            ).as_list()
        )
        expected = '((({"1"}+{"2"}+{"3"}+{"4"})>0))'
        self.assertTrue(actual == expected)

    def test_15(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            'IF () THEN ("A"=="")', parse_all=True
        ).as_list()
        expected = [
            ['IF () THEN ', ['"A"', '==', '""']]
        ]
        self.assertTrue(actual == expected)
        
    def test_16(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            'IF ( not("F3".isin(("G1","G3")))) THEN ({"A"}.str.slice(start=2, stop=4).isin(["D1","D3"]))', parse_all=True
        ).as_list()
        expected = [
            'IF',
                ['not', ['"F3"', '.isin', ['(', '"G1"', ',', '"G3"', ')']]],
                'THEN',
                ['{"A"}.str.slice(start=2, stop=4)',
                    '.isin',
                    ['[', '"D1"', ',', '"D3"', ']']]
        ]
        self.assertTrue(actual == expected)
        
    def test_17(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            'if ("C" != "pd.NA") then ( "A" > - 1)', parse_all=True
        ).as_list()
        expected = [
            'if', ['"C"', '!=', '"pd.NA"'], 'then', ['"A"', '>', '-', '1']
        ]
        self.assertTrue(actual == expected)
        
    def test_18(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            'if (0 >min({"C"},{"B"})) then (1 == sum({"A"},{"B"}))', parse_all=True
        ).as_list()
        expected = [
            'if',
                ['0', '>', 'min', ['{"C"}', ',', '{"B"}']],
                'then',
                    ['1', '==', 'sum', ['{"A"}', ',', '{"B"}']]
        ]
        self.assertTrue(actual == expected)
        
    def test_19(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.parser.RULE_SYNTAX.parse_string(
                '(({"4"} + {"3"} + {"2"} * {"1"}) > 0)', parse_all=True
            ).as_list()
        )
        expected = '((({"4"}+{"3"}+{"1"}*{"2"})>0))'
        self.assertTrue(actual == expected)

    def test_20(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.parser.RULE_SYNTAX.parse_string(
                '(({"4"} + {"3"} * {"2"} + {"1"}) > 0)', parse_all=True
            ).as_list()
        )
        expected = '((({"4"}+{"2"}*{"3"}+{"1"})>0))'
        self.assertTrue(actual == expected)

    def test_21(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.parser.RULE_SYNTAX.parse_string(
                '(({"4"} * {"3"} + {"2"} + {"1"}) > 0)', parse_all=True
            ).as_list()
        )
        expected = '((({"3"}*{"4"}+{"2"}+{"1"})>0))'
        self.assertTrue(actual == expected)

    def test_22(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.parser.RULE_SYNTAX.parse_string(
                '({"4"} == {"3"})', parse_all=True
            ).as_list()
        )
        expected = '(({"3"}=={"4"}))'
        self.assertTrue(actual == expected)

    def test_23(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.parser.RULE_SYNTAX.parse_string(
                '({"4"} != {"3"})', parse_all=True
            ).as_list()
        )
        expected = '(({"3"}!={"4"}))'
        self.assertTrue(actual == expected)

    def test_24(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.parser.RULE_SYNTAX.parse_string(
                '({"4"} > {"3"})', parse_all=True
            ).as_list()
        )
        expected = '(({"4"}>{"3"}))'
        self.assertTrue(actual == expected)

    def test_25(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.parser.RULE_SYNTAX.parse_string(
                '(({"4"} > {"3"}) & ({"2"} > {"1"}))', parse_all=True
            ).as_list()
        )
        expected = '((({"2"}>{"1"})&({"4"}>{"3"})))'
        self.assertTrue(actual == expected)

    def test_26(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.parser.RULE_SYNTAX.parse_string(
                '(({"4"} > {"3"}) & ({"2"} == {"1"}))', parse_all=True
            ).as_list()
        )
        expected = '((({"1"}=={"2"})&({"4"}>{"3"})))'
        self.assertTrue(actual == expected)

    def test_27(self):
        actual = ruleminer.flatten_and_sort(
            ruleminer.parser.RULE_SYNTAX.parse_string(
                '(({"4"} > {"3"}) & (({"2"}+{"0"}) == {"1"}))', parse_all=True
            ).as_list()
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

        templates = [{'expression': 'if ({".*"} == ".*") then ({"TP.*"} > 0)'}]
        actual = ruleminer.RuleMiner(templates=templates, data=df).rules
        expected = pd.DataFrame(
                data = [
                    [0, 0, 'if({"Type"}=="life_insurer")then({"TP-life"}>0)','', 5, 0, 1.0, {}],
                    [1, 0, 'if({"Type"}=="non-life_insurer")then({"TP-nonlife"}>0)','', 4, 1, 0.8, {}]], 
                columns = [ruleminer.RULE_ID, 
                ruleminer.RULE_GROUP, 
                ruleminer.RULE_DEF, 
                ruleminer.RULE_STATUS, 
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.ENCODINGS])
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

        templates = [{'expression': '({"Own_funds"} <= quantile({"Own_funds"}, 0.95))'}]
        actual = ruleminer.RuleMiner(templates=templates, data=df,
                                     params = {'evaluate_quantile': True}).rules
        expected = pd.DataFrame(
                data = [
                    [0, 0, 'if () then ({"Own_funds"}<=755.0)', '', 9, 1, 0.9, {}]],
                columns = [ruleminer.RULE_ID, 
                ruleminer.RULE_GROUP, 
                ruleminer.RULE_DEF, 
                ruleminer.RULE_STATUS, 
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.ENCODINGS])
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

        templates = [{'expression': '({"Own_funds"} <= quantile({"Own_funds"}, 0.95))'}]
        actual = ruleminer.RuleMiner(templates=templates, data=df).rules
        expected = pd.DataFrame(
                data = [
                    [0, 0, 'if () then ({"Own_funds"}<=quantile({"Own_funds"},0.95))', '', 9, 1, 0.9, {}]],
                columns = [ruleminer.RULE_ID, 
                ruleminer.RULE_GROUP, 
                ruleminer.RULE_DEF, 
                ruleminer.RULE_STATUS, 
                ruleminer.ABSOLUTE_SUPPORT,
                ruleminer.ABSOLUTE_EXCEPTIONS,
                ruleminer.CONFIDENCE,
                ruleminer.ENCODINGS])
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)
        
    def test_31(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            '(0.05*({"A"}+0.5*{"B"}+{"C"})>0)', parse_all=True
        ).as_list()
        expected = [[['0.05', '*', ['{"A"}', '+', '0.5', '*', '{"B"}', '+', '{"C"}']], '>', '0']]
        self.assertTrue(actual == expected)

    def test_32(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            '(1*(1+0.5*({"A"}+0.5*({"B"}+1)+0.5*({"C"}+1)))>5)', parse_all=True
        ).as_list()
        expected = [['1', '*',
                        [['1', '+', '0.5'],
                        '*',
                        [['{"A"}', '+', '0.5'], '*', ['{"B"}', '+', '1']],
                        '+',
                            ['0.5', '*', ['{"C"}', '+', '1']]],
                            '>',
                                '5']]

        self.assertTrue(actual == expected)
        
    def test_33(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            '0.05*(0.5*(A+1)+0.5*(B+C))', parse_all=True
        ).as_list()
        expected = [['0.05', '*', [['0.5', '*', ['A', '+', '1']], '+', ['0.5', '*', ['B', '+', 'C']]]]]
        self.assertTrue(actual == expected)
        
    def test_34(self):
        actual = ruleminer.parser.RULE_SYNTAX.parse_string(
            '0.05*(A+0.5*(B+1))', parse_all=True
        ).as_list()
        expected = [['0.05', '*', [[['A', '+', '0.5'], '*', ['B', '+', '1']]]]]
        self.assertTrue(actual == expected)
        
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
