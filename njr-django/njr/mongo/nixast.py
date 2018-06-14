"""
The nix ast, everything in here is derived from the :class:`Expr` class.
"""

from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

class Expr:
    """The basic nix expression. Is the base of all asts."""

    def match(self, cases, *args, **kwargs):
        """ Given a dictionary of cases expression, run the correct
        case with the content of the data structure. This is essentially
        pattern matching.
        """
        try:
            case = cases[self.matchname]
        except LookupError:
            return cases["default"](self, *args, **kwargs)
        else:
            return case(
                self,
                *[getattr(self, name) for name in self._fields], *args, **kwargs)

    def visit(self, visitor, *args, **kwargs):
        """ Given a visitor, run the correct case with the content of the data
        structure. This is essentially pattern matching.
        """
        try:
            case = getattr(visitor, self.matchname)
        except AttributeError:
            return getattr(visitor, "default")(visitor, self, *args, **kwargs)
        else:
            fields = [getattr(self, name) for name in self._fields]
            return case(
                self,
                *fields,
                *args,
                **kwargs
            )

    def __str__(self):
        return dumps(self)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

class Number (Expr, namedtuple("number", "inner")):
    """A nix number. """
    matchname = "number"

class String (Expr, namedtuple("string", "inner")):
    """A nix string. """
    matchname = "string"

class Attrset (Expr, namedtuple("attrset", "inner")):
    """A nix attrset. """
    matchname = "attrset"

Attrset.empty = Attrset({})

class _Ident (Expr, namedtuple("ident", "data")):
    """A identifier, should not be used in ast, only to be used with recursive
    functions"""
    matchname = "ident"

class List (Expr, namedtuple("list", "inner")):
    """A nix list. """
    matchname = "list"

class Fun (Expr, namedtuple("fun", "inner")):
    """ Fun is the nix function. The body argument is a python function.
    """
    matchname = "fun"

class App (Expr, namedtuple("fun", "function arg")):
    """ Fun is a nix application. """
    matchname = "app"

class Lookup(Expr, namedtuple("lookup", "attrset attrpath")):
    """Lookup is the attribute lookup operator in nix. """
    matchname = "lookup"

class Import(Expr, namedtuple("imp", "filename")):
    """Import is the primitive that can import files"""
    matchname = "imp"

class Let(Expr, namedtuple('let', "env body")):
    """Let is an let expression in nix. """
    matchname = "let"


from functools import partial

class UnboundExpr:
    """ An expression that needs extra information to be expressed completely.
    """

    def __init__(self, function, depends = None):
        self.function = function
        if depends is None:
            depends = parameter_names(function)
        self.depends = depends

    def required(self):
         return set(self.depends)

    def injectify(self, **kwargs):
        """Like inject, but calls nixify on all the arguments"""
        try:
            return self.inject(**{k: nixify(v) for k,v in kwargs.items()})
        except Exception as e:
            raise e

    def inject(self, **kwargs):
        """Enables the user to inject a value in the environment"""
        depends = { d for d in self.depends if d not in kwargs }

        unbound = set()
        bound = {}

        for k, v in kwargs.items():
            if isinstance(v, UnboundExpr):
                unbound.add(k)
                depends |= v.required()
            else:
                bound[k] = v

        inj_args = sorted(depends - unbound)

        def injection (*args):
            dct = {k: v for k, v in zip(inj_args, args)}
            inj_locals = dict(dct, **bound)

            left = set(unbound)
            while left:
                rest = set()
                for k in left:
                    b = kwargs[k]
                    if set(b.depends).issubset(inj_locals):
                        inj_locals[k] = b.function.__call__(
                            *[inj_locals[d] for d in b.depends]
                        )
                    else:
                        rest.add(k)
                if left == rest:
                    raise Exception("Cycle in dependencies, or dependencies unfulfilled: "
                                    + str(b.depends))
                else:
                    left = rest

            return self.function.__call__(*[inj_locals[d] for d in self.depends])

        return UnboundExpr(injection, inj_args)

    def bind(self, env={}):
        if not env:
            return self.function()
        else:
            return Let(env, self)

    def __call__(self, **kwargs):
        """ An injection followed by an empty bind"""
        return self.inject(**kwargs).bind()

    def normalform(self):
        """ Calls the function with the depends names """
        return self.function(*[_Ident(n) for n in self.depends]);

    def __str__(self):
        return str(self.normalform())

    def __eq__(self, other):
        if isinstance(other, UnboundExpr):
            return self.normalform() == other.normalform()
        else:
            return false

    def __repr__(self):
        return repr(self.normalform())

    def __hash__(self):
        return hash(self.normalform())

def random_ident():
    import random 
    return _Ident("id{:08x}".format(random.randrange(2 **64)))

def nixexpr(fn):
    """ Nix expr helper, makes a function that has nix dependencies into a
    nix bound expression.
    """
    if not callable(fn):
        return UnboundExpr(lambda: fn)
    return UnboundExpr(fn)


from functools import partial

def fun(function):
    params = parameter_names(function)
    if len(params) > 1:
        return Fun(lambda x: fun(partial(function, x)))
    else:
        return Fun(function)

def app(f, *args):
    for arg in args:
        f = App(f, arg)
    return f

def lookup(pkg, subpkg):
    """Nix expression to perform an attribute lookup"""
    subpkgs = subpkg.split(".")
    n = Lookup(pkg, subpkgs[0])
    for sub in subpkgs[1:]:
        n = Lookup(n, sub)
    return n

def nixify(value):
    """Takes a python value and deeply converts it into a nix expression."""
    import numbers
    if isinstance(value, Expr):
        return value
    if isinstance(value, dict):
        return Attrset({k:nixify(v) for k, v in value.items()})
    if isinstance(value, list):
        return List([nixify(v) for v in value])
    if isinstance(value, str):
        return String(value)
    if isinstance(value, numbers.Number):
        return Number(value)
    if isinstance(value, bool):
        return Boolean(value)
    if isinstance(value, UnboundExpr):
        return value
    if callable(value):
        return fun(value)
    raise TypeError("Can't convert %s to a nixexpr" % type(value))


BUILTINS = _Ident("builtins")


def lookup(pkg, *subpkgs):
    """Nix expression to perform an attribute lookup"""
    for subpkg in subpkgs:
        subs = subpkg.split(".")
        for sub in subs:
            pkg = Lookup(pkg, sub)
    return pkg


def dump(expr, fp, **kwargs):
    """dump is equivalent to json.dump, but with nix, and less options."""
    Dump(fp, kwargs.get("seperators", ("=", ";"))).accept(expr, set())

def dumps(obj, **kwargs):
    """Like dump but dumps to a string instead of a file"""
    from io import StringIO
    fp = StringIO()
    dump(obj, fp, **kwargs)
    return fp.getvalue()

def fixpoint(fun, _set):
    result = set()
    tmpset = set()
    while _set:
        for e in _set:
            tmpset |= fun(e)
            result.add(e)
        _set = tmpset - result
    return result

class Dump:

    def __init__(self, fp, seperators):
        self.fp = fp
        self.seperators = seperators

    def accept(self, e, ctx):
        if e is None:
            return self.default(e)
        return e.visit(self, ctx)

    def write(self, string):
        self.fp.write(string)

    def fun (self, e, body, ctx):
        base, *rest = parameter_names(body)
        var = unique_in(base, ctx)
        self.write("(")
        self.write(var)
        self.write(": ")
        self.accept(body(_Ident(var)), set([var, *ctx]))
        self.write(")")

    def app (self, e, function, arg, ctx):
        self.write("(")
        self.accept(function, ctx)
        self.write(" ")
        self.accept(arg, ctx)
        self.write(")")

    def ident (self, e, name, ctx):
        self.write(name)

    def imp (self, e, filename, ctx):
        self.write("import ")
        self.write(filename)

    def lookup (self, e, attrset, attrpath, ctx):
        self.accept(attrset, ctx)
        self.write(".")
        self.write(attrpath)

    def attrset (self, e, attrset, ctx):
        self.write("{");
        for key in sorted(attrset):
            self.write(key)
            self.write(self.seperators[0])
            self.accept(attrset[key], ctx)
            self.write(self.seperators[1])
        self.write("}");

    def let (self, e, env, body, ctx):
        ctx = set(ctx)
        vrs = {}

        def validate_keys(key):
            if not key in env:
                raise ValueError("%r not in environment: %s" % (key, list(env)))
            vrs[key] = unique_in(key, ctx);
            ctx.add(vrs[key])
            return env[key].required()

        keys = fixpoint(validate_keys, body.required())

        def accept_in_env(innerbody):
            self.accept(innerbody.inject(**{
                k: _Ident(v) for k,v in vrs.items()
            }).bind(), ctx)

        if keys:
            self.write("(let ")
            for key in sorted(keys):
                self.write(vrs[key])
                self.write(self.seperators[0])
                accept_in_env(env[key])
                self.write(self.seperators[1])
            self.write(" in ")
        accept_in_env(body)
        if keys:
            self.write(")")

    def list (self, e, list, ctx):
        self.write("[");
        try:
            fst, *rest = list;
        except ValueError:
            pass
        else:
            self.accept(fst, ctx);
            for val in rest:
                self.write(" ")
                self.accept(val, ctx);
        self.write("]");

    def string (self, e, string, ctx):
        self.write('"')
        self.write(string)
        self.write('"')

    def number (self, e, num, ctx):
        self.write(str(num));

    def boolean (self, e, boolean, ctx):
        self.write("true" if boolean else "false");

    def default (self, e):
        self.write("??");

def parameter_names(fn):
    import inspect
    sig = inspect.signature(fn)
    return list(sig.parameters)

def unique_in(base, set):
    i = 0
    var = base
    while var in set:
        var = base + str(i);
        i += 1
    return var
