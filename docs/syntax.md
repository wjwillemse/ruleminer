# Rule grammar

The rule template describes the structure of the rule. Columns and quoted strings in the rule template can contain simple regular expressions.

The syntax of the template follows a grammar defined as follows:

## General rule template format

* a *template* is of the form:
```
if cond_1 then cond_2
```
  or simply a single:
```
cond_1
```

* a *condition* is either a combination of *comparisons* with *logical operators* ('&' and '|') and parenthesis:
```
( comp_1 & comp_2 | comp_3 )
```

or simply a single *comparison*:
```
comp_1
```

* a *comparison* consists of a *term*, a *comparison operator* and a *term*, so::
```
term_1 > term_2
```

## Comparison operators

The following comparison operators are availabe:

* `>=`, `>`, `<=`, `<`, `!=`, `==` 
* `in` 
* `between`
* `match`
* `contains` 

## Terms: numbers, strings, columns, functions

* a `term` can be a `number` (e.g. +3, -4.1, 2.1e-8 and 0.9e10), `quoted string` (a string with single or double quotes), a `column` or a `function of columns`

* a `string` consists of the following characters: a-z A-Z 0-9 _ . , ; ; < > * = + - / \ ? | @ # $ % ^ & ( )

* a `column` is a `string` with braces, so:
```
{"Type"}
```

Here "Type" is the name of the column in the DataFrame with the data

* a `function of columns` is either a prefix operator (min, max, quantile, or abs, in lower or uppercase) on one or more *columns*, and of the form, for example:
```
min(col_1, col_2, col_3)
```
or infix operators with one or more columns:
```
(col_1 + col_2 * col_3)
```

## General mathematical functions

* min

* max

* abs

* sum

## Rounding functions
 
* exact

* round

* floor

* ceil

## Statistical functions

* quantile

* mean

* corr

* std

## String functions

* substr

* split

## Conditional functions

* sumif

* countif

## Functions for external data

* table

## Date and time functions

* days

* months

* years
 