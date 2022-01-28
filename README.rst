=========
ruleminer
=========


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

Installation
------------

To install the package::

    pip install ruleminer

To install the package from Github::

    pip install -e git+https://github.com/wjwwillemse/ruleminer.git#egg=ruleminer

To use ruleminer in a project::

    import ruleminer

Usage
-----

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

Calculating metrics
-------------------

Take the rule::

    if ({"Type"} == "life_insurer") then ({"TP-life"} > 0)

With the code::

    templates = [{'expression': 'if ({"Type"} == "life_insurer") then ({"TP-life"} > 0)'}]
    
    r = ruleminer.RuleMiner(templates=templates, data=df)

you can generate the rule metrics of this rule given the data in the DataFrame above (available with r.rules).

.. list-table:: Generated rules (1)
   :widths: 20 40 20 20 20 15 15
   :header-rows: 1

   * - id
     - definition
     - status
     - abs support
     - abs exceptions
     - confidence
     - encodings
   * - 1
     - if ({"Type"} == "life_insurer") then ({"TP-life"} > 0)
     - None
     - 5
     - 0
     - 1
     - {}

There are 5 rows in the data that support this rule. There are no exceptions (i.e. where the if-clause is satisfied, but not the then-clause), so this rule has confidence 1.

Generating rules
----------------

You can define rule templates that contain regular expressions for column names and strings. The package will then generate rules that satisfy the rule template with matching column names and strings from the DataFrame. For example column regex::

    {"T.*"}

will satisfy column names::

    {"Type"}, {"TP-life"}, {"TP-nonlife"}

So, if you apply the following rule ::

    if ({"T.*"} == ".*") then ({"TP.*"} > 0)

then the following rules are generated

.. list-table:: Generated rules (2)
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
     - if ({"Type"} == "non-life_insurer") then ({"TP-nonlife"} > 0)
     - None
     - 4
     - 1
     - 0.8
     - {}
   * - 1
     - if ({"Type"} == "life_insurer") then ({"TP-life"} > 0)
     - None
     - 5
     - 0
     - 1
     - {}

You can use rules without an if-clause, for example::

    {"Assets"} > 0

The metrics for these rules are calculated as if the if-clause is always satisfied.

Parameters
----------

Rule metrics
~~~~~~~~~~~~

Several rule metrics have been proposed in the past. You can add the metrics that you want as a parameter to the ruleminer, i.e.:: 

    params = {'metrics': ['added value', 'abs support', 'abs exceptions', 'confidence']}

    r = ruleminer.RuleMiner(templates=templates, data=df, params=params)

This will produce the desired metrics. Available metrics are:

* abs support (the absolute number of rows that satisfy the rule)

* abs exceptions (the absolute number of rows that do no satisfy the rule)

* confidence

* support

* added value

* casual confidence

* casual support

* conviction

* lift

The default metrics are 'abs support', 'abs exceptions' and 'confidence'.

See for the definitions `Measures for Rules <https://mhahsler.github.io/arules/docs/measures#Measures_for_Rules>`_ from Michael Hahsler.

Metric filters
~~~~~~~~~~~~~~

If you want to select only rules that satisfy a certain metric threshold then you can use

params = {"filter" : {"confidence": 0.75, "abs support": 10}}

The default metric filter is: {"confidence": 0.5, "abs support": 2}

Rule precision
~~~~~~~~~~~~~~

In many situations the equal-operator when used on quantitative data is too strict as small differences can occur that you do no want to consider as exceptions to the rule. For this you can define a decimal parameter inside the params dictionary by this ::

    params={'decimal': 3}

This means that comparisons like::

    A==B

are translated to ::

    abs(A-B) <= 1.5*10**(-decimal)

If no 'decimal' parameter is provided then the absolute difference should be exactly zero.

Evaluating results within rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Suppose you want to use an expression with a quantile::

    ({"Own funds"} <= quantile({"Own funds"}, 0.95))

Then you can choose to evaluate the quantile based on the dataset on which the rules were generated or not with::

    params = {'evaluate_quantile': True}

This would produce the rule ::

    if () then ({"Own funds"}<=755.0)

If you use ::

    params = {'evaluate_quantile': False}

then this would produce ::

    if () then ({"Own funds"}<=quantile({"Own funds"},0.95))

In this case the quantile is re-evaluated each time based when the rule is evaluated and the outcome will depend on the current dataset. 

The default is False (quantiles within rules are not evaluated).

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

and will therefore be pruned from the list if the first rule is already in the list.

Rule template grammar
---------------------

The rule template describes the structure of the rule. Columns and quoted strings in the rule template can contain simple regular expressions.

Examples::

    {"Assets"} > 0

    if ({"Type"} == "life insurer") then ({".*"} > 0)

    if ({".*"} > 0) then (({".*"} == 0) & ({".*"} > 0))

    (({".*"} + {".*"} + {".*"}) == {".*"})

    (min({".*"}, {".*"}) == {".*"})

    ({"Own funds"} <= quantile({"Own funds"}, 0.95))

The syntax of the template follows a grammar defined as follows:

* a *template* is of the form::

    if cond_1 then cond_2

  or simply a single:: 

    cond_1

* a *condition* is either a combination of *comparisons* with *logical operators* ('&' and '|') and parenthesis::

    ( comp_1 & comp_2 | comp_3 )

  or simply a single *comparison*::

    comp_1

* a *comparison* consists of a *term*, a *comparison operator* (>=, >, <=, <, != or ==) and a *term*, so::

    term_1 > term_2

* a *term* can be a *number* (e.g. 3.1415 or 9), *quoted string* (a string with single or double quotes), or a *function of columns*

* a *function of columns* is either a prefix operator (min, max, quantile, or abs, in lower or uppercase) on one or more *columns*, and of the form, for example::

    min(col_1, col_2, col_3)

  or infix operators with one or more columns::

    (col_1 + col_2 * col_3)

* a *column* is a *string* with braces, so::

    {"Type"}

  where "Type" is the name of the column in the DataFrame with the data

* a *string* consists of a-z A-Z 0-9 _ . , ; ; < > * = + - / \ ? | @ # $ % ^ & ( )

Debugging rules
---------------

If you are using this in a Jupyter notebook you can add a the beginning::

    logging.basicConfig(stream=sys.stdout, 
                        format='%(asctime)s %(message)s',
                        level=logging.INFO)

Information about the rule generating process with be displayed in the notebook. Set the debug level to logging.DEBUG is you want more results.
