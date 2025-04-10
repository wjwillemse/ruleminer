# Experimental class for floats with lower and upper tolerance bounds

import numpy as np

class FloatWithTolerance:

    def __init__(
        self, 
        value, 
        upper_bound=None,
        lower_bound=None,
        key="default", 
        tolerances={
            "default": {
                (  0, 1e3): 1,
                (1e3, 1e6): 2, 
                (1e6, 1e8): 3, 
                (1e8, np.inf): 4
            }
        }
    ):
        """ """
        self.value = value
        if upper_bound is None:
            self.upper_bound = self._tol(value, tolerances.get(key))
        else:
            self.upper_bound = upper_bound
        if lower_bound is None:
            self.lower_bound = -self._tol(value, tolerances.get(key))
        else:
            self.lower_bound = lower_bound

    def __repr__(self):
        return str(self.value)+" ("+str(self.lower_bound)+", "+str(self.upper_bound)+")"

    def __str__(self):
        return self.__repr()

    def _tol(self, value, tolerance_def):
        for ((start, end)), decimals in tolerance_def.items():
            if abs(value) >= start and abs(value) < end:
                return 0.5 * 10 ** (decimals)

    def __add__(self, other):
        """ """
        return FloatWithTolerance(
            value=self.value+other.value,
            upper_bound=self.upper_bound + other.upper_bound,
            lower_bound=self.lower_bound + other.lower_bound,
        )

    def __minus__(self, other):
        """ """
        return FloatWithTolerance(
            value=self.value-other.value,
            upper_bound=self.upper_bound + other.upper_bound,
            lower_bound=self.lower_bound + other.lower_bound,
        )

    def __mul__(self, other):
        return FloatWithTolerance(
            value=self.value * other.value,
            upper_bound=np.max(
                [
                    self.upper_bound * other.upper_bound,
                    self.upper_bound * other.lower_bound,
                    self.lower_bound * other.upper_bound,
                    self.lower_bound * other.lower_bound
                ]
            ),
            lower_bound=np.min(
                [
                    self.upper_bound * other.upper_bound,
                    self.upper_bound * other.lower_bound,
                    self.lower_bound * other.upper_bound,
                    self.lower_bound * other.lower_bound
                ]
            ),
        )

    def __truediv__(self, other):
        return FloatWithTolerance(
            value=self.value / other.value,
            upper_bound=np.max(
                [
                    self.upper_bound / other.upper_bound,
                    self.upper_bound / other.lower_bound,
                    self.lower_bound / other.upper_bound,
                    self.lower_bound / other.lower_bound
                ]
            ),
            lower_bound=np.min(
                [
                    self.upper_bound / other.upper_bound,
                    self.upper_bound / other.lower_bound,
                    self.lower_bound / other.upper_bound,
                    self.lower_bound / other.lower_bound
                ]
            ),
        )

    def __floordiv__(self, other):
        return FloatWithTolerance(
            value=self.value // other.value,
            upper_bound=np.max(
                [
                    self.upper_bound // other.upper_bound,
                    self.upper_bound // other.lower_bound,
                    self.lower_bound // other.upper_bound,
                    self.lower_bound // other.lower_bound
                ]
            ),
            lower_bound=np.min(
                [
                    self.upper_bound // other.upper_bound,
                    self.upper_bound // other.lower_bound,
                    self.lower_bound // other.upper_bound,
                    self.lower_bound // other.lower_bound
                ]
            ),
        )

    def __abs__(self, other):
        pass

    def __mod__(self, other):
        pass

    def __divmod__(self, other):
        pass

    def __pow__(self, other):
        pass

    def __ceil__(self, other):
        pass

    def __floor__(self, other):
        pass

    def __round__(self, other):
        pass

    def __floordiv__(self, other):
        pass

    def __eq__(self, other):
        pass

    def __ne__(self, other):
        pass

    def __ge__(self, other):
        pass

    def __gt__(self, other):
        pass

    def __le__(self, other):
        pass

    def __lt__(self, other):
        pass

    def __neg__(self, other):
        pass

    def __pos__(self, other):
        pass

    def __str__(self, other):
        pass

