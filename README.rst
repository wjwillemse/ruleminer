=========
ruleminer
=========


.. image:: https://img.shields.io/pypi/v/ruleminer.svg
        :target: https://pypi.python.org/pypi/ruleminer

.. image:: https://img.shields.io/travis/wjwillemse/ruleminer.svg
        :target: https://travis-ci.com/wjwillemse/ruleminer

.. image:: https://readthedocs.org/projects/ruleminer/badge/?version=latest
        :target: https://ruleminer.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/wjwillemse/ruleminer/shield.svg
     :target: https://pyup.io/repos/github/wjwillemse/ruleminer/
     :alt: Updates

**DISCLAIMER - BETA PHASE**

*This package is currently in a beta phase.*

Python package to discover association rules in Pandas DataFrames.

Installation
------------

To install the package::

    pip install ruleminer

To install the package from Github::

    pip install -e git+https://github.com/wjwwillemse/ruleminer.git#egg=ruleminer

To use ruleminer in a project::

    import ruleminer

Examples
--------

.. list-table:: Some insurance undertakings data
   :widths: 25 25 20 20 20 20 20
   :header-rows: 1

   * - Name
     - Type
     - Assets
     - TP-life
     - TP-nonlife
     - Own funds
     - Excess
   * - Insurer 1
     - life insurer
     - 1000
     - 800
     - 0
     - 200
     - 200
   * - Insurer 2
     - non-life insurer
     - 4000
     - 0
     - 3200
     - 800
     - 800
   * - Insurer 3
     - non-life insurer
     - 800
     - 0
     - 700
     - 100
     - 100
   * - Insurer 4
     - life insurer
     - 2500
     - 1800
     - 0
     - 700
     - 700
   * - Insurer 5
     - non-life insurer
     - 2100
     - 0
     - 2200
     - 200
     - 200
   * - Insurer 6
     - life insurer
     - 9000
     - 8800
     - 0
     - 200
     - 200
   * - Insurer 7
     - non-life insurer
     - 9000
     - 0
     - 8800
     - 200
     - 200
   * - Insurer 8
     - life insurer
     - 9000
     - 8800
     - 0
     - 200
     - 200
   * - Insurer 9
     - non-life insurer
     - 9000
     - 8800
     - 0
     - 200
     - 200
   * - Insurer 10
     - life insurer
     - 9000
     - 0
     - 8800
     - 200
     - 199.99

Generating rules
----------------

The expression::

    templates = [{'expression': 'if ({"T.*"} == ".*") then ({"TV.*"} > 0)'}]
    r = ruleminer.RuleMiner(templates=templates, data=df)

will generated the following rules (available with r.rules)

.. list-table:: Generated rules
   :widths: 20 40 20 20 20 15 15
   :header-rows: 1

   * - id
     - definition
     - status
     - abs support
     - abs exceptions
     - confidence
     - encodings
   * - 0
     - if ({"Type"} == "non-life_insurer") then ({"TV-nonlife"} > 0)
     - None
     - 4
     - 1
     - 0.8
     - {}
   * - 1
     - if ({"Type"} == "life_insurer") then ({"TV-life"} > 0)
     - None
     - 5
     - 0
     - 1
     - {}

You can define so-called rule templates that contain regular expressions for column names and strings. The package  will then generate rules that satisfy the rule template with matching column names and strings from the data DataFrame. For example, given the data DataFrame above, column regex::

    {"T.*"}

will satisfy column names::

    {"Type"}, {"TP-life"}, {"TP-nonlife"}


Rule pruning
------------

By using regex in column names, it will sometimes happen that rules are identical to other rules, except that they have a different ordering of columns. For example::

    max({"TP life"}, {"TP nonlife"})

is identical to::

    max({"TP nonlife"}, {"TP life"})

The generated rules are therefore pruned to delete the identical rules from the generated list of rules.

* a==b is identical to b==a
* a!=b is identical to b!=a
* min(a, b) is identical to min(b, a)
* max(a, b) is identical to max(b, a)
* a+b is identical to b+a
* a*b is identical to b*a

These identities are applied recursively in rules. So the rule::

    (({"4"}>{"3"}) & (({"2"}+{"1"})=={"0"}))

is identical to::

    ((({"1"}+{"2"})=={"0"}) & ({"4"}>{"3"}))

and will therefore be pruned from the list if the latter rule is already in the list.

Rule template grammar
---------------------

The rule template describes the structure of the rule. Columns and quoted strings in the rule template can contain simple regular expressions.

Examples::

    {"Assets"} > 0

    if ({"Type"} == "life insurer") then ({".*"} > 0)

    if ({".*"} > 0) then (({".*"} == 0) & ({".*"} > 0))

The syntax of the template follows a grammar defined as follows:

* a *template* is of the form::

    if cond_1 then cond_2

  or simply a single:: 

    cond_1

* a *condition* is either a combination of *comparisons* with *logical operators* ('&', 'and', '|', 'or') and parenthesis::

    ( comp_1 & comp_2 | comp_3 )

  or simply a single *comparison*::

    comp_1

* a *comparison* consists of a *term*, a *comparison operator* (>=, >, <=, <, != or ==) and a *term*, so::

    term_1 > term_2

* a *term* can be a *number* (e.g. 3.1415 or 9), *quoted string* (a string with single or double quotes), or a *function of columns*

* a *function of columns* is either a prefix operator (min, max, abs or sum, in lower or uppercase) on one or more *columns*, and of the form, for example::

    min(col_1, col_2, col_3)

  or infix operators with one or more columns::

    (col_1 + col_2 * col_3)

* a *column* is a *string* with braces, so::

    {"Type"}

  where "Type" is the name of the column in the DataFrame with the data

* a *string* consists of a-z A-Z 0-9 _ . , * +

