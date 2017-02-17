'''
PhysPy is a SymPy-based Python library for calculating error percentage for
measured values.
'''

from collections import Iterable, namedtuple as _
import math

import sympy as sym

from ._abs import Abs

class Value:
    '''
    An abstract class that represents either measured or dependent value.

    **Note**: PhysPy values override arithmetic operators (`+`, `-`, `*`, `/`, `**`) and `abs` function.
    '''

    def __init__(self):
        raise NotImplementedError

    def approx(self):
        '''
        Calculate the average value.
        '''
        raise NotImplementedError

    def apply(self, fn):
        '''
        Apply a function to the value.
        
        **Note**: the passed function must operate with SymPy values, not any Python objects.
        '''
        raise NotImplementedError

    def absolute_error(self, probability):
        '''
        Calculate the absolute error.
        '''
        raise NotImplementedError

    def show(self, probability, unicode=False):
        '''
        Show the average value and error percentage in readable format.
        '''
        symbol = '\u00b1' if unicode else '+/-'
        return '{0} {1} {2} ({3}%)'.format(
            _round(self.approx(), 2),
            symbol,
            _round(self.absolute_error(probability), 2),
            _round(self.relative_error(probability) * 100, 1),
        )
    
    def relative_error(self, probability):
        '''
        Calculate the relative error.
        '''
        return abs(self.absolute_error(probability) / self.approx())

    def __add__(self, other):
        return DependentValue(get_symbol(self) + get_symbol(other), values(self, other))

    def __sub__(self, other):
        return DependentValue(get_symbol(self) - get_symbol(other), values(self, other))

    def __mul__(self, other):
        return DependentValue(get_symbol(self) * get_symbol(other), values(self, other))

    def __truediv__(self, other):
        return DependentValue(get_symbol(self) / get_symbol(other), values(self, other))

    def __pow__(self, other):
        return DependentValue(get_symbol(self) ** get_symbol(other), values(self, other))

    def __neg__(self):
        return DependentValue(-get_symbol(self), values(self))

    def __abs__(self):
        return self.apply(Abs)

class NamedValue(Value):
    '''
    Named measured value.
    '''
    def __init__(self, name, values, ierr):
        self.values = values
        self.name = name
        self.symbol = sym.Symbol(name)
        self.ierr = ierr

    def approx(self):
        return sum(self.values) / len(self.values)

    def rmsd(self):
        '''
        Calculate root-mean-square deviation.
        '''
        a = self.approx()
        n = len(self.values)
        if n > 1:
            return math.sqrt(
                sum((v - a)**2 for v in self.values) / (n * (n - 1)) 
            )
        return 0

    def random_error(self, probability):
        return self.rmsd() * coef(probability, len(self.values))

    def absolute_error(self, probability):
        return math.sqrt(self.random_error(probability)**2 + self.ierr**2)
    
    def name(self, name):
        return NamedValue(name, self.values)

    def apply(self, fn):
        return DependentValue(fn(self.symbol), [self])

class DependentValue(Value):
    def __init__(self, symbol, values):
        self.symbol = symbol
        self.values = [v for v in values if isinstance(v, NamedValue)]

    def approx(self):
        d = {}
        for v in self.values:
            d[v.name] = v.approx()
        return self.symbol.evalf(subs=d)

    def absolute_error(self, probability):
        ds = []
        for v in self.values:
            subs = {}

            for v_ in self.values:
                subs[v_.name] = v_.approx()

            diff = sym.diff(self.symbol, v.symbol)

            ds.append(
                (diff.evalf(subs=subs) * v.absolute_error(probability))**2
            )

        return math.sqrt(sum(ds))

    def apply(self, fn):
        return DependentValue(fn(get_symbol(self)), self.values)

def _round(x, n):
    if x < 0:
        return - _round(abs(x), n)
    if x == 0:
        return 0
    return round(x, int(-math.log(x, 10)) + n)

def each(fn, lst):
    return [fn(i, e) for (i, e) in enumerate(lst)]

def each_lazy(fn, lst):
    return (fn(i, e) for (i, e) in enumerate(lst))

each.lazy = each_lazy

def mapvalue(name, values, ierr):
    res = []
    for (i, v) in enumerate(values):
        res.append(value(name.format(i=i), v, ierr))
    return res

def mapvalue_lazy(name, values, ierr):
    for(i, v) in enumerate(values):
        yield value(name.format(i=i), v, ierr)

mapvalue.lazy = mapvalue_lazy

def coef(probability, n):
    # TODO: calculate Student coef for **any** probability
    return {
        (2, .95): 12.7,
        (3, .95): 4.3,
        (4, .95): 3.2,
        (5, .95): 2.8,
        (6, .95): 2.6,
        (7, .95): 2.4,
        (8, .95): 2.4,
        (9, .95): 2.3,
        (10, .95): 2.3,
        (15, .95): 2.1,
        (20, .95): 2.1,
        (100, .95): 2.0,
    }[n, probability]

def value(name, value, ierr):
    '''
    Construct a `NamedValue` from values list and instrument drift.
    '''

    if isinstance(value, NamedValue):
        return NamedValue(name, value.values, ierr)
    if isinstance(value, Iterable):
        return NamedValue(name, value, ierr)
    return NamedValue(name, [value], ierr)

def constant(name, value):
    '''
    Construct a constant `NamedValue`.
    '''

    return NamedValue(name, [value], 0)

def val(name, values, ierr):
    '''
    Create a global variable that refers to a `NamedValue`.
    '''

    from inspect import currentframe
    frame = currentframe().f_back

    v = value(name, values, ierr)

    try:
        frame.f_globals[v.name] = v
    finally:
        del frame

    return v

def const(name, value):
    '''
    Create a global variable that refers to a constant `NamedValue`.
    '''

    from inspect import currentframe
    frame = currentframe().f_back

    v = constant(name, value)

    try:
        frame.f_globals[v.name] = v
    finally:
        del frame

    return v

def values(*args):
    res = []
    for v in args:
        if isinstance(v, NamedValue):
            res.append(v)
        elif isinstance(v, DependentValue):
            for v_ in v.values:
                res.append(v_)
    return res

def get_symbol(value):
    if isinstance(value, valalue):
        return value.symbol
    return value

def get_value(value):
    if isinstance(value, Value):
        return value.approx()
    return value
