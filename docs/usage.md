# Usage

To use ruleminer in a project:

```python
import ruleminer
```

After installation you can use the functions in the package in for
example a Jupyter notebook.

Examples below are based the following dataset.

| Name      | Type      | Assets | TP-nonlife | TP-nonlife | Own funds | Excess |
|-----------|-----------|--------|------------|------------|-----------|--------|
| Insurer 1 | life      | 1000   | 800        | 0          | 200       | 200    |
| Insurer 2 | non-life  | 4000   | 0          | 3200       | 800       | 800    |
| Insurer 3 | non-life  | 800    | 0          | 700        | 100       | 100    |
| Insurer 4 | life      | 2500   | 1800       | 0          | 700       | 700    |
| Insurer 5 | non-lifer | 2100   | 0          | 2200       | 200       | 200    |
| Insurer 6 | life      | 9000   | 8800       | 0          | 200       | 200    |
| Insurer 7 | non-life  | 9000   | 0          | 8800       | 200       | 200    |
| Insurer 8 | life      | 9000   | 8800       | 0          | 200       | 200    |
| Insurer 9 | non-life  | 9000   | 8800       | 0          | 200       | 200    |
| Insurer 10| life      | 9000   | 0          | 8800       | 200       | 199.99 |

## Calculating metrics

Take the rule

```
if ({"Type"} == "life") then ({"TP-life"} > 0)
```

This rule says: if an insurer reports for column "Type" (noted by the curved brackets) the value "life" then the value of the column "TP-life" should be higher than zero. 

With the code

```python
templates = [{'expression': 'if ({"Type"} == "life") then ({"TP-life"} > 0)'}]

r = ruleminer.RuleMiner(templates=templates, data=df)
```

you can generate the rule metrics of this rule given the data in the DataFrame above (available with r.rules).

| id   | definition                                             | status | abs support | abs exceptions | confidence | encodings |
|------|--------------------------------------------------------|--------|-------------|----------------|------------|-----------|
| 0    | if ({"Type"} == "life") then ({"TP-life"} > 0) | None   | 5           | 0              | 1          | {}        |

There are 5 rows in the data that support this rule. There are no exceptions (i.e. where the if-clause is satisfied, but not the then-clause), so this rule has confidence 1.

## Generating rules

You can define rule templates that contain regular expressions for column names and strings. The package will then generate rules that satisfy the rule template with matching column names and strings from the DataFrame. For example column regex:
```
{"T.*"}
```

will satisfy column names:
```
{"Type"}, {"TP-life"}, {"TP-nonlife"}
```

So, if you apply the following rule:
```
if ({"T.*"} == ".*") then ({"TP.*"} > 0)
```

then the following rules are generated

| id   | definition                                                    | status | abs support | abs exceptions | confidence | encodings |
|------|---------------------------------------------------------------|--------|-------------|----------------|------------|-----------|
| 0    | if ({"Type"} == "non-life") then ({"TP-nonlife"} > 0) | None   | 4           | 1              | 0.8        | {}        |
| 1    | if ({"Type"} == "life") then ({"TP-life"} > 0)        | None   | 5           | 0              | 1          | {}        |

You can use rules without an if-clause, for example:
```
{"Assets"} > 0
```

The metrics for these rules are calculated as if the if-clause is always satisfied.

## Rule examples

The following rules can be applied to the data above:
```
{"Assets"} > 0

if ({"Type"} == ".*") then ({".*"} > 0)

if ({".*"} > 0) then (({".*"} == 0) & ({".*"} > 0))

(({".*"} + {".*"} + {".*"}) == {".*"})

(min({".*"}, {".*"}) == {".*"})

({"Own funds"} <= quantile({"Own funds"}, 0.95))

(substr({"Type"}, 0, 1) in ["a", "b"])
```

## Parameters

### Rule metrics

Several rule metrics have been proposed in the past. You can add the metrics that you want as a parameter to the ruleminer, i.e.:

```python
params = {'metrics': ['added value', 'abs support', 'abs exceptions', 'confidence']}

r = ruleminer.RuleMiner(templates=templates, data=df, params=params)
```

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

* rule power factor

The default metrics are 'abs support', 'abs exceptions' and 'confidence'.

See for the definitions `Measures for Rules <https://mhahsler.github.io/arules/docs/measures#Measures_for_Rules>`_ from Michael Hahsler.

### Metric filters

If you want to select only rules that satisfy a certain metric threshold then you can use:
```python
params = {"filter" : {"confidence": 0.75, "abs support": 10}}
```

The default metric filter is: {"confidence": 0.5, "abs support": 2}

### Rule precision

In many situations the equal-operator when used on quantitative data is too strict as small differences can occur that you do no want to consider as exceptions to the rule. For this you can define a decimal parameter inside the params dictionary by this:

```python
params={'decimal': 3}
```

This means that comparisons like:
```
A==B
```

are translated to:
```
abs(A-B) <= 1.5*10**(-decimal)
```

If no 'decimal' parameter is provided then the absolute difference should be exactly zero.

### Rule results

Add the following parameters to the parameter dictionary to specify the output:

* 'output_confirmations': a boolean to specify whether the indices of the data that satisfy a rule should be returned (default=True)
* 'output_exceptions': a boolean to specify whether the indicesof the data that do not satisfy a rule should be returned (default=True)
* 'output_not_applicable': a boolean to specify whether the indices of the data to which a rule does not apply (i.e. where the antecedent is not true) should be returned (default=False)

## Evaluating results within rules

Suppose you want to use an expression with a quantile:
```
({"Own funds"} <= quantile({"Own funds"}, 0.95))
```

Then you can choose to evaluate the quantile based on the dataset on which the rules were generated or not with:
```python
params = {'evaluate_statistics': True}
```

This would produce the rule:
```
if () then ({"Own funds"}<=755.0)
```

If you use:
```python
params = {'evaluate_statistics': False}
```

then this would produce:
```
if () then ({"Own funds"}<=quantile({"Own funds"},0.95))
```

In this case the quantile is re-evaluated each time based when the rule is evaluated and the outcome will depend on the current dataset. 

The default is False (quantiles within rules are not evaluated).

## Rule pruning

By using regex in column names, it will sometimes happen that rules are identical to other rules, except that they have a different ordering of columns. For example:
```
max({"TP life"}, {"TP nonlife"})
```

is identical to:
```
max({"TP nonlife"}, {"TP life"})
```

The generated rules are therefore pruned to delete the identical rules from the generated list of rules.

* a==b is identical to b==a
* a!=b is identical to b!=a
* min(a, b) is identical to min(b, a)
* max(a, b) is identical to max(b, a)
* a+b is identical to b+a
* a*b is identical to b*a

These identities are applied recursively in rules. So the rule:
```
(({"4"}>{"3"}) & (({"2"}+{"1"})=={"0"}))
```

is identical to:
```
((({"1"}+{"2"})=={"0"}) & ({"4"}>{"3"}))
```

and will therefore be pruned from the list if the first rule is already in the list.

## Debugging rules

If you are using this in a Jupyter notebook you can add a the beginning::

    logging.basicConfig(stream=sys.stdout, 
                        format='%(asctime)s %(message)s',
                        level=logging.DEBUG)

Information about the rule generating process with be displayed in the notebook. Set the debug level to logging.INFO is you want less results.

