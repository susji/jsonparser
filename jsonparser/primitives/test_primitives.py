import unittest
from typing import Any, Optional, Tuple
from jsonparser.primitives import *


class ParserTest(unittest.TestCase):
    def test_character(self):
        left = "abc "
        g = MatchCharacter
        for c in left:
            n, left = g(c).parse(left)
            self.assertEqual(n, c)

    def test_zero_or_more(self):
        left = "abbcccz"
        for m in ("a", "bb", "ccc", "z"):
            mz = MatchZeroOrMore(MatchCharacter(m[0]))
            n, left = mz.parse(left)
            self.assertEqual(len(n), len(m))
            for nn in n:
                self.assertEqual(nn, m[0])

    def test_zero_or_more_none(self):
        mz = MatchZeroOrMore(MatchCharacter("z"))
        n, left = mz.parse("a")
        self.assertTrue(not n or len(n) == 0)
        self.assertEqual(left, "a")

    def test_one_or_more(self):
        left = "abbcccz"
        for m in ("a", "bb", "ccc", "z"):
            mo = MatchOneOrMore(MatchCharacter(m[0]))
            n, left = mo.parse(left)
            self.assertEqual(len(n), len(m))
            for nn in n:
                self.assertEqual(nn, m[0])

    def test_one_or_more_fail(self):
        left = "aaab"
        for MatchOrRaise, what in ((True, "aaa"), (False, "z")):
            mc = MatchCharacter(what[0])
            mo = MatchOneOrMore(mc)
            if MatchOrRaise:
                n, left = mo.parse(left)
                self.assertEqual(type(n), list)
            else:
                self.assertFalse(mo.parse(left))

    def test_one_or_more_multi(self):
        left = "abc" + "abc" + "abz"
        mo = MatchOneOrMore(
            MatchAll(
                MatchCharacter("a"),
                MatchAll(
                    MatchCharacter("b"),
                    MatchOr(MatchCharacter("c"), MatchCharacter("z")),
                ),
            )
        )
        nodes, left = mo.parse(left)
        self.assertEqual(left, "")
        self.assertEqual(len(nodes), 3)

    def test_or(self):
        left = "ab"
        mo = MatchOr(MatchCharacter("a"), MatchCharacter("b"))
        m1, left = mo.parse(left)
        self.assertEqual(left, "b")
        self.assertEqual(m1, "a")
        m2, left = mo.parse(left)
        self.assertEqual(left, "")
        self.assertEqual(m2, "b")

    def test_and(self):
        left = "ab"
        mo = MatchAll(MatchCharacter("a"), MatchCharacter("b"))
        m, left = mo.parse(left)
        self.assertEqual(left, "")
        self.assertEqual(m, ["a", "b"])

    def test_any(self):
        left = "abc"
        mo = MatchAny(
            MatchCharacter("a"), MatchCharacter("b"), MatchCharacter("c")
        )
        for cur in left:
            res, left = mo.parse(left)

    def test_any_negative(self):
        left = "abz"
        mo = MatchAny(
            MatchCharacter("a"), MatchCharacter("b"), MatchCharacter("c")
        )
        for i, c in enumerate(left):
            r = mo.parse(left)
            if c in "ab":
                self.assertTrue(r)
                n, left = r
                self.assertEqual(n, c)
            else:
                self.assertFalse(r)

    def test_n(self):
        left = "aaaaa"
        m = MatchN(len(left), MatchCharacter("a"))
        r, left = m.parse(left)
        self.assertEqual(left, "")
        self.assertEqual(r, ["a"] * 5)

    def test_n_neg(self):
        left = "aaaaa"
        with self.assertRaises(EndOfText):
            MatchN(len(left) + 1, MatchCharacter("a")).parse(left)

    def test_chain(self):
        left = "abcde"
        m = MatchAll(
            MatchCharacter("a"),
            MatchCharacter("b"),
            MatchCharacter("c"),
            MatchCharacter("d"),
        )
        val, left = m.parse(left)
        self.assertEqual(left, "e")
        self.assertEqual(val, ["a", "b", "c", "d"])

    def test_or_default(self):
        left = "ab"
        m = MatchOrDefault(MatchCharacter("a"), "NOMATCH")
        first, left = m.parse(left)
        self.assertEqual(first, "a")
        second, left = m.parse(left)
        self.assertEqual(second, "NOMATCH")
        self.assertEqual(left, "b")

    def test_keyword(self):
        left = "avainsana"
        n, left = MatchKeyword(left, []).parse(left)
        self.assertEqual(left, "")
        self.assertEqual(n, "avainsana")

    class TestDelimiter(Combinable):
        def parse(self, what: str) -> Optional[Tuple[Any, str]]:
            if what[0] in ",{}[] \t\n":
                return ("", what)
            return None

    def test_keywords(self):
        one = "eka"
        two = "toka"
        left = "%s %s" % (one, two)
        first, left = MatchKeyword(one, self.TestDelimiter()).parse(left)
        self.assertEqual(left, " %s" % two)
        self.assertEqual(first, one)

        second, left = MatchKeyword(two, self.TestDelimiter()).parse(left[1:])
        self.assertEqual(left, "")
        self.assertEqual(second, two)

    def test_keywords_neg(self):
        self.assertFalse(
            MatchKeyword("eka", self.TestDelimiter()).parse("ekatoka")
        )

    def test_end(self):
        self.assertTrue(MatchEnd().parse(""))
        self.assertFalse(MatchEnd().parse(" "))

    class TestException(Exception):
        pass

    def E(self, msg: str, context: str) -> Exception:
        return self.TestException()

    def test_or_raise(self):
        m = MatchOrRaise(MatchCharacter("a"), self.E, "throwing hard")
        with self.assertRaises(self.TestException):
            m.parse("b")
        self.assertTrue(m.parse("a"))
