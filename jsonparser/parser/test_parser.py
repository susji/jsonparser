import unittest
from jsonparser.parser import *


class TestParser(unittest.TestCase):
    def test_string(self):
        m = "this is a simple string"
        p = MatchString()
        n, left = p.parse('"%s"' % m)
        self.assertEqual(left, "")
        self.assertEqual(n, m)

    def test_string_utf8(self):
        p = MatchString()
        n, left = p.parse('"%s"' % "abc\u0394e")
        self.assertEqual(left, "")
        self.assertEqual(n, "abcΔe")

    def test_string_escaped(self):
        m = r"this is an escaped \"string\""
        p = MatchString()
        n, left = p.parse('"%s"' % m)
        self.assertEqual(left, "")
        self.assertEqual(type(n), str)
        self.assertEqual(m.replace("\\", ""), n)

    def test_number_int(self):
        m = "123456"
        p = MatchNumber()
        n, left = p.parse(m)
        self.assertEqual(type(n), float)
        self.assertAlmostEqual(float(m), n)
        self.assertEqual(left, "")

    def test_number_float(self):
        m = "123456.789"
        p = MatchNumber()
        n, left = p.parse(m)
        self.assertEqual(type(n), float)
        self.assertAlmostEqual(float(m), n)
        self.assertEqual(left, "")

    def test_number_float_neg(self):
        m = "-654.321"
        p = MatchNumber()
        n, left = p.parse(m)
        self.assertEqual(type(n), float)
        self.assertAlmostEqual(float(m), n)
        self.assertEqual(left, "")

    def test_number_exp(self):
        n, left = MatchNumber().parse("123.15e5")
        self.assertEqual(left, "")
        self.assertAlmostEqual(n, 123.15e5)

    def test_number_exp_neg(self):
        n, left = MatchNumber().parse("321.51e-5")
        self.assertEqual(left, "")
        self.assertAlmostEqual(n, 321.51e-5)

    def test_number_broken(self):
        with self.assertRaises(Error):
            MatchNumber().parse("123.")

    def test_bool(self):
        m = [("true", True, True), ("false", False, True), ("ei", 0, False)]
        p = MatchBool()
        for left, exp, shouldwork in m:
            got = p.parse(left)
            self.assertEqual(not not got, shouldwork)
            if shouldwork:
                n, left = got
                self.assertEqual(left, "")
                self.assertEqual(exp, n)

    def test_null(self):
        m = [("null", True), ("muu", False)]
        p = MatchNull()
        for left, exp in m:
            got = p.parse(left)
            self.assertEqual(not not got, exp)
            if exp:
                val, left = got
                self.assertEqual(left, "")
                self.assertEqual(val, None)

    def test_object(self):
        m = '{ "test" : 123 }'
        p = MatchObject()
        n, left = p.parse(m)
        self.assertEqual(left, "")
        self.assertEqual(n, {"test": 123.0})

    def test_object_empty(self):
        n, left = MatchObject().parse("{}")
        self.assertEqual(left, "")
        self.assertEqual(n, {})

    def test_object_nested(self):
        m = '{ "first": { "second": 321 }}'
        p = MatchObject()
        n, left = p.parse(m)
        self.assertEqual(left, "")
        self.assertEqual(n, {"first": {"second": 321}})

    def test_array(self):
        m = '[ "eka", "toka", { "kolmas": 3, "neljas": [ false, null ] } ]'
        n, left = MatchArray().parse(m)
        self.assertEqual(left, "")
        self.assertEqual(
            n, ["eka", "toka", {"kolmas": 3, "neljas": [False, None]}]
        )

    def test_array_empty(self):
        n, left = MatchArray().parse("  [   ]")
        self.assertEqual(left, "")
        self.assertEqual(n, [])

    def test_object_broken(self):
        with self.assertRaises(Error):
            MatchObject().parse('{ "jotain" ')

    def test_array_broken(self):
        with self.assertRaises(Error):
            MatchArray().parse("[ 1")
