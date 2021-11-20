# jsonparser

This is a simple JSON parser done as a parser combinator exercise. Notably, the
present approach is incredibly slow with CPython: `benchmark.py` displays a
difference of three orders of magnitude. With `pypy3`, this reduces to two. This
is probably explained by the sheer amount of nested function calls when the
parsing grammar is described with nesting combinators.