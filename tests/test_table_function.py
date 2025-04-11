#!/usr/bin/env python

"""Tests for table function"""

import unittest
import pandas as pd
import ruleminer


class TestRuleminer(unittest.TestCase):
    """Tests for table function"""

    def test_1(self):
        external_data = pd.DataFrame(
            {
                "a": [1, 2],
                "b": [20, 30],
                "c": [True, False],
            }
        )
        parameters = {
            "tolerance": {
                "default": None,
            },
            "tables": {"external_data": external_data},
        }
        formulas = ['([{"A"}, {"B"}] in TABLE("external_data", ["a", "b"]))']
        df = pd.DataFrame(
            [
                ["Test_1", 1, 20, 0],
                ["Test_2", 1, 1, 0],
                ["Test_3", 2, 30, 1],
            ],
            columns=["Name", "A", "B", "C"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then (pd.concat([{"A"},{"B"}], axis=1).apply(tuple, axis=1).isin(_table_external_data[["a","b"]].apply(tuple, axis=1)))'
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
            ["Test_3", True],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_2(self):
        external_data = pd.DataFrame(
            {
                "a": ["entity_a", "entity_b"],
            }
        )
        parameters = {
            "tolerance": {
                "default": None,
            },
            "tables": {"external_data": external_data},
        }
        formulas = ['([{"A"}] in TABLE("external_data", ["a"]))']
        df = pd.DataFrame(
            [
                ["Test_1", "entity_a", "life"],
                ["Test_2", "entity_b", "non-life"],
                ["Test_3", "entity_c", "non-life"],
            ],
            columns=["Name", "A", "B"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then (pd.concat([{"A"}], axis=1).apply(tuple, axis=1).isin(_table_external_data[["a"]].apply(tuple, axis=1)))'
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

    def test_3(self):
        external_data = pd.DataFrame(
            {
                "a": ["entity_a", "entity_b"],
                "b": ["life", "non-life"],
            }
        )
        parameters = {
            "tolerance": {
                "default": None,
            },
            "tables": {"external_data": external_data},
        }
        formulas = ['([{"A"}, {"B"}] in TABLE("external_data", ["a", "b"]))']
        df = pd.DataFrame(
            [
                ["Test_1", "entity_a", "life"],
                ["Test_2", "entity_a", "non-life"],
                ["Test_3", "entity_b", "non-life"],
            ],
            columns=["Name", "A", "B"],
        )
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        expected = 'if () then (pd.concat([{"A"},{"B"}], axis=1).apply(tuple, axis=1).isin(_table_external_data[["a","b"]].apply(tuple, axis=1)))'
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
            ["Test_3", True],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])
