# ruleminer

[![Documentation](https://readthedocs.org/projects/ruleminer/badge)](https://ruleminer.readthedocs.io/en/latest/)
[![image](https://img.shields.io/pypi/v/ruleminer.svg)](https://pypi.python.org/pypi/ruleminer)
[![image](https://img.shields.io/pypi/pyversions/ruleminer.svg)](https://pypi.python.org/pypi/ruleminer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Python package to discover association rules in Pandas DataFrames. 

This package implements the code of the paper [Discovering and ranking validation rules in supervisory data](https://github.com/wjwillemse/ruleminer/tree/main/docs/paper.pdf).

*   Free software: MIT/X license

*   Documentation: <https://ruleminer.readthedocs.io/en/latest>.

## Features

Here is what the package does:

* Discover human-readable validation rules using rule templates with regular expressions

* Evaluate rules using interval arithmetics

* Calculate association rules metrics

Available functions: available functions: min, max, abs, quantile, sum, substr, split, count, sumif, countif, mean, std, exact, corr, round, floor, ceil, table

Available metrics: available metrics: abs support, abs exceptions, confidence, support, added value, casual confidence, casual support, conviction, lift and rule power factor

Here are some examples of rule templates with regexes with which you can generate validation rules:

  - *if ({"Type"} == ".*") then ({".*"} > 0)*

  - *if ({".*"} > 0) then (({".*"} == 0) & ({".*"} > 0))*

  - *(({".*"} + {".*"} + {".*"}) == {".*"})*

  - *({"Own funds"} <= quantile({"Own funds"}, 0.95))*

  - *(substr({"Type"}, 0, 1) in ["a", "b"])*

The first template generates (with the dataset described in the Usage section) rules like

  - *if ({"Type"} == "non-life_insurer") then ({"TP-nonlife"} > 0)*
  - *if ({"Type"} == "life_insurer") then ({"TP-life"} > 0)*

These generated validation rules can then be used to validate new datasets.

## Contributors

* Willem Jan Willemse <https://codeberg.org/wjwillemse>
