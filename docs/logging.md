# Logging of intermediate results

Ruleminer can return logs of intermediate values of rule evaluations in the output. The results of all numerical comparisons within rules are logged in the `log`-column of the results DataFrame by adding this to the parameters:

```python
params = {
    'intermediate_results': ['comparisons', 'statistics']
}
```
## Simple numerical logging

For comparisons that do not involve interval arithmetics the following logging is included in the results. Suppose you have the following condition: `A == B`, where `A` and `B` can be mathematical expressions. The format of the logging then is:

`({A} == {B})`

For other comparison operators the logging is likewise.

## Interval logging

For comparisons that involve interval arithmetics the following logging is included in the results. Suppose you have the following condition: `A == B`, where `A` and `B` can be mathematical expressions. The format of the logging then is:

`({A - B = diff} == [lower_bound, upper_bound])`

The comparison is satisfied if the difference between `A` and `B` is within the interval `[lower_bound, upper_bound`], where the interval depends on the expressions of `A` and `B`, the tolerance definition and the specific values of the data points.

For other comparison operators the logging is likewise.

## Statistics logging

