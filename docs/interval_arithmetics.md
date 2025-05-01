# Interval arithmetics

Ruleminer provides a complete implementation of interval arithmetics when evaluating rules (see for a general description the [Wiki page](https://en.wikipedia.org/wiki/Interval_arithmetic) on Interval Arithmetics). This allows for evaluating rules in the same manner as XBRL validation rules which is based on Interval arithmetics. You can define different interval definitions for different columns. 

## Implementation of interval arithmetics for operators

Comparison operators are evaluated as follows (a and b can be any (nested) mathematical expression following the grammar):

* `==`: `max(UP(a), LB(a)) >= min(UP(b), LB(b)) & min(UP(a), LB(a)) <= max(UP(b), LB(b))`

* `!=`: `max(UP(a), LB(a)) < min(UP(b), LB(b))) | (min(UP(a), LB(a)) > max(UP(b), LB(b))`

* `>`: `min(UP(a), LB(a)) > max(UP(b), LB(b))`

* `>=`: `max(UP(a), LB(a)) >= min(UP(b), LB(b))`

* `<`: `max(UP(a), LB(a)) < min(UP(b), LB(b))`

* `<=`: `min(UP(a), LB(a)) < max(UP(b), LB(b))`

where `UP(x)` is the upper bound of `x`.

## Implementation of mathematical operators

Mathematical operators are evaluated as follows (a and b can be any (nested) mathematical expression following the grammar):

* `LB(a+b)`: `LB(a) + LB(b)`

* `UP(a+b)`: `UP(a) + UP(b)`

* `LB(a-b)`: `LB(a) - UP(b)`

* `UP(a-b)`: `UP(a) - LB(b)`

* `LB(a*b)`: `min(LB(a)*LB(b), UB(a)*LB(b), LB(a)*UB(b), UB(a)*UB(b))`

* `UB(a*b)`: `max(LB(a)*LB(b), UB(a)*LB(b), LB(a)*UB(b), UB(a)*UB(b))`

* `LB(a/b)`: `min(LB(a)/LB(b), UB(a)/LB(b), LB(a)/UB(b), UB(a)/UB(b))`

* `UB(a/b)`: `max(LB(a)/LB(b), UB(a)/LB(b), LB(a)/UB(b), UB(a)/UB(b))`

* `LB(a**b)`: `min(LB(a)**LB(b), UB(a)**LB(b), LB(a)**UB(b), UB(a)**UB(b))`

* `UB(a**b)`: `max(LB(a)**LB(b), UB(a)**LB(b), LB(a)**UB(b), UB(a)**UB(b))`

Note that the plus operator does not change the direction of the tolerance, but the minus operator does change the direction of the tolerance for the right side of the expression, i.e. the lower bound of A - B is calculated by LB(A) - UP(B). This also holds for negative values.

For the multiply and divide operators we need to calculate all possible directions and take the lower or upper bound. This is because A and/or B can be negative. The lower bound of A * B can be either UP(A) * UP(B), UP(A) * LB(B), LB(A) * UP(B), or LB(A), LB(B), depending on the specific values of A and B.

## Using a tolerance definition in ruleminer

You can define tolerances that depend on the values in this way:

```python
params = {
    'tolerance': {
        "default": {
            (  0, 1e3): 1,
            (1e3, 1e6): 2, 
            (1e6, 1e8): 3, 
            (1e8, np.inf): 4
        }
    }
}
```

This means for example that if abs(value) >= 1e3 and < 1e6 then the precision of that value is 2, and so on.

## Using different tolerances for different columns

If you have different tolerances per report of per data point then you can add keys in the form of regexes in the tolerance dictionary. For example the following tolerance definition would use for all columns that start with an "A" zero decimals and for the rest the default tolerance:

```python
params = {
    'tolerance': {
        "A.*": {
            (0, np.inf): 0
        },
        "default": {
            (  0, 1e3): 1,
            (1e3, 1e6): 2, 
            (1e6, 1e8): 3, 
            (1e8, np.inf): 4
        }
    }
}
```

## EIOPA's XBRL tolerance definition

The example above is based on the XBRL tolerance definition (see [EIOPA XBRL Taxonomy Documentation](https://dev.eiopa.europa.eu/Taxonomy/Full/2.8.0/Common/EIOPA_XBRL_Taxonomy_Documentation_2.8.0.pdf).

To describe how it works we use the following example taken from the document mentioned above (page 41). In case of addition of two numbers A and B, where A is interval [A1, A2], and B is interval [B1, B2], the result is interval [A1+B1, A2+B2]. If the interval of the reported numbers overlap with the computed interval the rule is satisfied. An example in C = A + B, where:

* A is reported as 1499 with precision in units (decimals = 0) hence the resulting range is [1498.5, 1499.5];

* B is reported as 1502 with precision in units (decimals = 0) hence the resulting range is [1501.5, 1502.5]; and 

* C is reported as = 3000 with precision in units (decimals = 0) hence the resulting range is [2999.5, 3000.5].

Following the basic operations, the computed tolerance interval for A + B is [1498.5+1501.5, 1499.5+1502.5] = [3000, 3002]. There is an overlap between the interval of C and interval of A + B. As a result the rule is satisfied. If C was reported as 2999, the resulting interval ( with precision in units) would be [2998.5, 2999.5]. With no overlap the rule would not be  satisfied and an exception would be raised.

So to check whether 'A = B' there must be overlap between intervals [A1, A2] and [B1, B2], and that is the case if A2 >= B1 and A1 <= B2. Likewise, for the comparison 'A > B' we check whether A1 > B2 and for the comparison 'A < B' we check whether A2 < B1, and similar for operators <= and >=.

The example can be reproduced in ruleminer in the following way:
```python
df = pd.DataFrame(
    columns=[
        "A",
        "B",
        "C",
    ],
    data=[
        [1499, 1502, 3000],
        [1499, 1500, 2999],
    ],
)
```

And you define the following template:
```python
templates = [{'expression': '({"A"} + {"B"} == {"C"})'}]
```

Then you can run:
```python
r = ruleminer.RuleMiner(templates=templates, data=df, params=params)
```

And r.rules gives you the following output

| id   | definition                                                    | status | abs support | abs exceptions | confidence | encodings |
|------|---------------------------------------------------------------|--------|-------------|----------------|------------|-----------|
| 0    | ```if () then ((({"C"}-0.5*abs({"C"}.apply(__tol__, (...)``` | None   | 1           | 1              | 0.5        | {}        |


Note that the tolerance function is not stored in the formula; the 'tolerance' parameter should be passed every time a Ruleminer object is constructed.

