from sympy.core import S, Add, Mul, sympify, Symbol, Dummy
from sympy.core.exprtools import factor_terms
from sympy.core.function import (Function, Derivative, ArgumentIndexError,
    AppliedUndef)
from sympy.core.numbers import pi
from sympy.functions.elementary.miscellaneous import sqrt
from sympy.functions.elementary.piecewise import Piecewise
from sympy.core.expr import Expr
from sympy.core.relational import Eq
from sympy.core.logic import fuzzy_not
from sympy.functions.elementary.exponential import exp, exp_polar
from sympy.functions.elementary.trigonometric import atan2
from sympy.functions.elementary.complexes import *

class Abs(Function):

    is_real = True
    is_negative = False
    unbranched = True

    def fdiff(self, argindex=1):
        if argindex == 1:
            return sign(self.args[0])
        else:
            raise ArgumentIndexError(self, argindex)

    @classmethod
    def eval(cls, arg):
        from sympy.simplify.simplify import signsimp
        from sympy.core.function import expand_mul

        if hasattr(arg, '_eval_Abs'):
            obj = arg._eval_Abs()
            if obj is not None:
                return obj
        if not isinstance(arg, Expr):
            raise TypeError("Bad argument type for Abs(): %s" % type(arg))
        # handle what we can
        arg = signsimp(arg, evaluate=False)
        if arg.is_Mul:
            known = []
            unk = []
            for t in arg.args:
                tnew = cls(t)
                if tnew.func is cls:
                    unk.append(tnew.args[0])
                else:
                    known.append(tnew)
            known = Mul(*known)
            unk = cls(Mul(*unk), evaluate=False) if unk else S.One
            return known*unk
        if arg is S.NaN:
            return S.NaN
        if arg.is_Pow:
            base, exponent = arg.as_base_exp()
            if base.is_real:
                if exponent.is_integer:
                    if exponent.is_even:
                        return arg
                    if base is S.NegativeOne:
                        return S.One
                    if base.func is cls and exponent is S.NegativeOne:
                        return arg
                    return Abs(base)**exponent
                if base.is_nonnegative:
                    return base**re(exponent)
                if base.is_negative:
                    return (-base)**re(exponent)*exp(-S.Pi*im(exponent))
                return
        if isinstance(arg, exp):
            return exp(re(arg.args[0]))
        if isinstance(arg, AppliedUndef):
            return
        if arg.is_Add and arg.has(S.Infinity, S.NegativeInfinity):
            if any(a.is_infinite for a in arg.as_real_imag()):
                return S.Infinity
        if arg.is_zero:
            return S.Zero
        if arg.is_nonnegative:
            return arg
        if arg.is_nonpositive:
            return -arg
        if arg.is_imaginary:
            arg2 = -S.ImaginaryUnit * arg
            if arg2.is_nonnegative:
                return arg2
        # reject result if all new conjugates are just wrappers around
        # an expression that was already in the arg
        conj = arg.conjugate()
        new_conj = conj.atoms(conjugate) - arg.atoms(conjugate)
        if new_conj and all(arg.has(i.args[0]) for i in new_conj):
            return
        if arg != conj and arg != -conj:
            ignore = arg.atoms(Abs)
            abs_free_arg = arg.xreplace({i: Dummy(real=True) for i in ignore})
            unk = [a for a in abs_free_arg.free_symbols if a.is_real is None]
            if not unk or not all(conj.has(conjugate(u)) for u in unk):
                return sqrt(expand_mul(arg*conj))

    def _eval_is_integer(self):
        if self.args[0].is_real:
            return self.args[0].is_integer

    def _eval_is_nonzero(self):
        return fuzzy_not(self._args[0].is_zero)

    def _eval_is_zero(self):
        return self._args[0].is_zero

    def _eval_is_positive(self):
        is_z = self.is_zero
        if is_z is not None:
            return not is_z

    def _eval_is_rational(self):
        if self.args[0].is_real:
            return self.args[0].is_rational

    def _eval_is_even(self):
        if self.args[0].is_real:
            return self.args[0].is_even

    def _eval_is_odd(self):
        if self.args[0].is_real:
            return self.args[0].is_odd

    def _eval_is_algebraic(self):
        return self.args[0].is_algebraic

    def _eval_power(self, exponent):
        if self.args[0].is_real and exponent.is_integer:
            if exponent.is_even:
                return self.args[0]**exponent
            elif exponent is not S.NegativeOne and exponent.is_Integer:
                return self.args[0]**(exponent - 1)*self
        return

    def _eval_nseries(self, x, n, logx):
        direction = self.args[0].leadterm(x)[0]
        s = self.args[0]._eval_nseries(x, n=n, logx=logx)
        when = Eq(direction, 0)
        return Piecewise(
            ((s.subs(direction, 0)), when),
            (sign(direction)*s, True),
        )

    def _sage_(self):
        import sage.all as sage
        return sage.abs_symbolic(self.args[0]._sage_())

    def _eval_derivative(self, x):
        #if self.args[0].is_real or self.args[0].is_imaginary:
        #    return Derivative(self.args[0], x, evaluate=True) \
        #        * sign(conjugate(self.args[0]))
        #return (re(self.args[0]) * Derivative(re(self.args[0]), x,
        #    evaluate=True) + im(self.args[0]) * Derivative(im(self.args[0]),
        #        x, evaluate=True)) / Abs(self.args[0])
        return self.args[0].diff(x)

    def _eval_rewrite_as_Heaviside(self, arg):
        # Note this only holds for real arg (since Heaviside is not defined
        # for complex arguments).
        from sympy import Heaviside
        if arg.is_real:
            return arg*(Heaviside(arg) - Heaviside(-arg))

    def _eval_rewrite_as_Piecewise(self, arg):
        if arg.is_real:
            return Piecewise((arg, arg >= 0), (-arg, True))

    def _eval_rewrite_as_sign(self, arg):
        from sympy import sign
        return arg/sign(arg)