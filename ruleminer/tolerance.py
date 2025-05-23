# Experimental class for series, floats with lower and upper tolerance bounds

import numpy as np
import pandas as pd

default_tolerances = {
    "default": {(0, 1e3): 1, (1e3, 1e6): 2, (1e6, 1e8): 3, (1e8, np.inf): 4}
}


def _tol(value, tolerance_def):
    if isinstance(value, Interval):
        return value
    else:
        if tolerance_def is None:
            return value
        else:
            for ((start, end)), decimals in tolerance_def.items():
                if abs(value) >= start and abs(value) < end:
                    return 0.5 * 10 ** (decimals)
            raise Exception(
                "tolerance definition not found for value "
                + str(value)
                + " in "
                + tolerance_def
            )


class Interval(tuple):
    def __init__(self, x):
        """ """
        return tuple.__init__(x)

    def __add__(self, other):
        """ """
        if isinstance(other, Interval):
            self = Interval(
                [
                    self[0] + other[0],
                    self[1] + other[1],
                ],
            )
            return self
        else:
            self = Interval(
                [
                    self[0] + other,
                    self[1] + other,
                ]
            )
            return self

    def __radd__(self, other):
        """ """
        return self.__add__(other)

    def __sub__(self, other):
        """ """
        if isinstance(other, Interval):
            return Interval(
                [
                    self[0] - other[0],
                    self[1] - other[1],
                ]
            )
        else:
            return Interval(
                [
                    self[0] - other,
                    self[1] - other,
                ]
            )

    def __mul__(self, other):
        if isinstance(other, Interval):
            return Interval(
                [
                    min(
                        [
                            self[0] * other[0],
                            self[1] * other[0],
                            self[0] * other[1],
                            self[1] * other[1],
                        ]
                    ),
                    max(
                        [
                            self[0] * other[0],
                            self[1] * other[0],
                            self[0] * other[1],
                            self[1] * other[1],
                        ]
                    ),
                ]
            )
        else:
            return Interval(
                [
                    min(
                        [
                            self[0] * other,
                            self[1] * other,
                        ]
                    ),
                    max(
                        [
                            self[0] * other,
                            self[1] * other,
                        ]
                    ),
                ]
            )

    def __rmul__(self, other):
        """ """
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, Interval):
            return Interval(
                [
                    min(
                        [
                            self[0] / other[0],
                            self[1] / other[0],
                            self[0] / other[1],
                            self[1] / other[1],
                        ]
                    ),
                    max(
                        [
                            self[0] / other[0],
                            self[1] / other[0],
                            self[0] / other[1],
                            self[1] / other[1],
                        ]
                    ),
                ]
            )
        else:
            return Interval(
                [
                    min(
                        [
                            self[0] / other,
                            self[1] / other,
                        ]
                    ),
                    max(
                        [
                            self[0] / other,
                            self[1] / other,
                        ]
                    ),
                ]
            )

    def __floordiv__(self, other):
        if isinstance(other, Interval):
            return Interval(
                [
                    min(
                        [
                            self[0] // other[0],
                            self[1] // other[0],
                            self[0] // other[1],
                            self[1] // other[1],
                        ]
                    ),
                    max(
                        [
                            self[0] // other[0],
                            self[1] // other[0],
                            self[0] // other[1],
                            self[1] // other[1],
                        ]
                    ),
                ]
            )
        else:
            return Interval(
                [
                    min(
                        [
                            self[0] // other,
                            self[1] // other,
                        ]
                    ),
                    max(
                        [
                            self[0] // other,
                            self[1] // other,
                        ]
                    ),
                ]
            )

    def __pow__(self, other):
        if isinstance(other, Interval):
            return Interval(
                [
                    min(
                        [
                            self[0] ** other[0],
                            self[1] ** other[0],
                            self[0] ** other[1],
                            self[1] ** other[1],
                        ]
                    ),
                    max(
                        [
                            self[0] ** other[0],
                            self[1] ** other[0],
                            self[0] ** other[1],
                            self[1] ** other[1],
                        ]
                    ),
                ]
            )
        else:
            return Interval(
                [
                    min(
                        [
                            self[0] ** other,
                            self[1] ** other,
                        ]
                    ),
                    max(
                        [
                            self[0] ** other,
                            self[1] ** other,
                        ]
                    ),
                ]
            )

    def __eq__(self, other):
        return (self[1] >= other[0]) & (self[0] <= other[1])

    def __ne__(self, other):
        return ~((self[1] >= other[0]) & (self[0] <= other[1]))

    def __ge__(self, other):
        return self[1] >= other[0]

    def __gt__(self, other):
        return self[0] > other[1]

    def __le__(self, other):
        return self[0] <= other[1]

    def __lt__(self, other):
        return self[1] < other[0]

    def __abs__(self):
        return Interval(
            [
                # min of abs(upper) and abs(lower), except if lower < 0 and upper > 0
                # (then the result should be 0)
                min(
                    [
                        abs(self[0]),
                        abs(self[1]),
                    ]
                )
                if not (self[0] < 0 and self[1] > 0)
                else 0,
                # max of abs(upper) and abs(lower)
                max(
                    [
                        abs(self[0]),
                        abs(self[1]),
                    ]
                ),
            ]
        )

    def __pos__(self):
        return Interval([self[0], self[1]])

    def __neg__(self):
        return Interval([-self[1], -self[0]])

    # def __mod__(self, other):
    #     pass

    # def __divmod__(self, other):
    #     pass

    # def __ceil__(self, other):
    #     pass

    # def __floor__(self, other):
    #     pass

    # def __round__(self, other):
    #     pass


class SeriesWithTolerance(pd.Series):
    # add property to retain original data
    _metadata = ["original_data"]

    def __init__(self, *args, **kwargs):
        """ """
        # retain the original data within the object
        self.original_data = kwargs.get("data", *args)
        # change values to intervals before creating the series
        kwargs["data"] = [
            Interval(
                [
                    value - _tol(value, default_tolerances["default"]),
                    value + _tol(value, default_tolerances["default"]),
                ]
            )
            if not isinstance(value, Interval)
            else value
            for value in kwargs.get("data", *args)
        ]
        super().__init__(**kwargs)

    def __eq__(self, other):
        """ """
        res = self.values == other.values
        return res

    def __ne__(self, other):
        """ """
        return self.values != other.values

    def __ge__(self, other):
        """ """
        return self.values >= other.values

    def __gt__(self, other):
        """ """
        return self.values > other.values

    def __le__(self, other):
        """ """
        return self.values <= other.values

    def __lt__(self, other):
        """ """
        return self.values < other.values

    @property
    def _constructor(self):
        return SeriesWithTolerance

    @property
    def _constructor_expanddim(self):
        return DataFrameWithTolerance


class DataFrameWithTolerance(pd.DataFrame):
    # add property to retain original data
    _metadata = ["original_data"]

    def __init__(self, *args, **kwargs):
        """ """
        # retain the original data within the object
        self.original_data = kwargs.get("data", *args)
        # change values to intervals before creating the series
        kwargs["data"] = [
            [
                Interval(
                    [
                        value - _tol(value, default_tolerances["default"]),
                        value + _tol(value, default_tolerances["default"]),
                    ]
                )
                if not isinstance(value, Interval)
                else value
                for value in column
            ]
            for column in kwargs.get("data", *args)
        ]
        super().__init__(**kwargs)

    @property
    def _constructor(self):
        return DataFrameWithTolerance

    @property
    def _constructor_sliced(self):
        return SeriesWithTolerance
