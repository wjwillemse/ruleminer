=========
ruleminer
=========

.. image:: https://readthedocs.org/projects/ruleminer/badge/?version=latest
        :alt: ReadTheDocs
        :target: https://ruleminer.readthedocs.io/en/latest/

.. image:: https://img.shields.io/pypi/v/ruleminer.svg
        :target: https://pypi.python.org/pypi/ruleminer

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
        :target: https://opensource.org/licenses/MIT
        :alt: License: MIT

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
        :target: https://github.com/psf/black
        :alt: Code style: black


**DISCLAIMER - BETA PHASE**

*This package is currently in a beta phase.*

Python package to discover association rules in Pandas DataFrames. 

This package implements the code of the paper `Discovering and ranking validation rules in supervisory data <https://github.com/wjwillemse/ruleminer/tree/main/docs/paper.pdf>`_.

Here is what the package does:

* Generate human-readable validation rules using rule templates containing regular expressions and a Pandas DataFrame dataset

  - available functions: min, max, abs, quantile, sum, substr, split, count, sumif and countif
  - including parameters for metric filters and rule precisions (including XBRL tolerances)

* Evaluate rules and calculate association rules metrics

  - available metrics: abs support, abs exceptions, confidence, support, added value, casual confidence, casual support, conviction, lift and rule power factor

Here are some examples of rule templates with regexes with which you can generate validation rules:

- if ({"Type"} == ".*") then ({".*"} > 0)

- if ({".*"} > 0) then (({".*"} == 0) & ({".*"} > 0))

- (({".*"} + {".*"} + {".*"}) == {".*"})

- ({"Own funds"} <= quantile({"Own funds"}, 0.95))

- (substr({"Type"}, 0, 1) in ["a", "b"])

The first template generates (with the dataset described in the Usage section) rules like

- if ({"Type"} == "non-life_insurer") then ({"TP-nonlife"} > 0)
- if ({"Type"} == "life_insurer") then ({"TP-life"} > 0)

These generated validation rules can then be used to validate new datasets.
