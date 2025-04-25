#!/usr/bin/env python

"""Tests for `ruleminer` package / logging."""

import unittest
import pandas as pd
import numpy as np
import ruleminer

parameters = {
    "tolerance": {
        "default": {
            (0, np.inf): 0,
        },
    },
    "intermediate_results": ["comparisons"],
}
df = pd.DataFrame(
    [
        ["Test_1", 0.0, 0.5],
        ["Test_2", 1.0, 0.5],
        ["Test_3", 2.0, 0.5],
    ],
    columns=["Name", "A", "B"],
)


class TestLogging(unittest.TestCase):
    """Tests for `ruleminer` package."""

    def test_1(self):
        formulas = ['({"A"}>=1)']
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result", "log"]
            ]
            .values
        )
        expected = [
            ["Test_1", False, "if () then ({0.0 - 1.0 = -1.0} >= [-0.5])"],
            ["Test_2", True, "if () then ({1.0 - 1.0 = 0.0} >= [-0.5])"],
            ["Test_3", True, "if () then ({2.0 - 1.0 = 1.0} >= [-0.5])"],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_2(self):
        formulas = ['({"A"}==1)']
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result", "log"]
            ]
            .values
        )
        expected = [
            ["Test_1", False, "if () then ({0.0 - 1.0 = -1.0} == [-0.5, 0.5])"],
            ["Test_2", True, "if () then ({1.0 - 1.0 = 0.0} == [-0.5, 0.5])"],
            ["Test_3", False, "if () then ({2.0 - 1.0 = 1.0} == [-0.5, 0.5])"],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_3(self):
        formulas = ['({"A"}<=1)']
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result", "log"]
            ]
            .values
        )
        expected = [
            ["Test_1", True, "if () then ({0.0 - 1.0 = -1.0} <= [0.5])"],
            ["Test_2", True, "if () then ({1.0 - 1.0 = 0.0} <= [0.5])"],
            ["Test_3", False, "if () then ({2.0 - 1.0 = 1.0} <= [0.5])"],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_4(self):
        formulas = ['({"A"}=={"B"})']
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result", "log"]
            ]
            .values
        )
        expected = [
            ["Test_1", True, "if () then ({0.0 - 0.5 = -0.5} == [-1.0, 1.0])"],
            ["Test_2", True, "if () then ({1.0 - 0.5 = 0.5} == [-1.0, 1.0])"],
            ["Test_3", False, "if () then ({2.0 - 0.5 = 1.5} == [-1.0, 1.0])"],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_5(self):
        formulas = ['({"A"}<={"B"})']
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result", "log"]
            ]
            .values
        )
        expected = [
            ["Test_1", True, "if () then ({0.0 - 0.5 = -0.5} <= [1.0])"],
            ["Test_2", True, "if () then ({1.0 - 0.5 = 0.5} <= [1.0])"],
            ["Test_3", False, "if () then ({2.0 - 0.5 = 1.5} <= [1.0])"],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_6(self):
        formulas = ['({"A"}>={"B"})']
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result", "log"]
            ]
            .values
        )
        expected = [
            ["Test_1", True, "if () then ({0.0 - 0.5 = -0.5} >= [-1.0])"],
            ["Test_2", True, "if () then ({1.0 - 0.5 = 0.5} >= [-1.0])"],
            ["Test_3", True, "if () then ({2.0 - 0.5 = 1.5} >= [-1.0])"],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_7(self):
        formulas = ['({"A"}>{"B"})']
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result", "log"]
            ]
            .values
        )
        expected = [
            ["Test_1", False, "if () then ({0.0 - 0.5 = -0.5} > [1.0])"],
            ["Test_2", False, "if () then ({1.0 - 0.5 = 0.5} > [1.0])"],
            ["Test_3", True, "if () then ({2.0 - 0.5 = 1.5} > [1.0])"],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])

    def test_8(self):
        formulas = ['({"A"}<{"B"})']
        r = ruleminer.RuleMiner(
            templates=[{"expression": form} for form in formulas],
            params=parameters,
        )
        r = ruleminer.RuleMiner(rules=r.rules, data=df, params=parameters)
        actual = (
            r.results.sort_values(by=["indices"], ignore_index=True)
            .merge(df, how="left", left_on=["indices"], right_index=True)[
                ["Name", "result", "log"]
            ]
            .values
        )
        expected = [
            ["Test_1", False, "if () then ({0.0 - 0.5 = -0.5} < [-1.0])"],
            ["Test_2", False, "if () then ({1.0 - 0.5 = 0.5} < [-1.0])"],
            ["Test_3", False, "if () then ({2.0 - 0.5 = 1.5} < [-1.0])"],
        ]
        self.assertListEqual(list(actual[0]), expected[0])
        self.assertListEqual(list(actual[1]), expected[1])
        self.assertListEqual(list(actual[2]), expected[2])
