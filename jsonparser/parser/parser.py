from jsonparser.primitives import (
    Combinable,
    MatchOneOrMore,
    MatchZeroOrMore,
    MatchCharacter,
    MatchAny,
    MatchAll,
    EndOfText,
    MatchOrDefault,
    MatchKeyword,
    MatchEnd,
    MatchOrRaise as _MatchOrRaise,
)
from typing import Dict, List, Any, Tuple, Optional


class Error(Exception):
    def __init__(self, msg: str, context: str) -> None:
        super().__init__("JSON: %s (``%s'')" % (msg, context))


def MatchOrRaise(matcher: Combinable, msg: str) -> Combinable:
    def E(msg: str, ctx: str) -> Error:
        return Error(msg, ctx)

    return _MatchOrRaise(matcher, E, msg)


class MatchValue(Combinable):
    matchers: List[Combinable] = []

    @classmethod
    def add_matcher(self, matcher: Combinable):
        self.matchers.append(matcher)

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        if len(what) == 0:
            return None
        return MatchAny(*self.matchers).parse(what)


class Helpers:
    class GUARD:
        pass

    wsmatch = MatchZeroOrMore(MatchCharacter(" \r\t\n"))


class MatchDelimiter(Combinable):
    endmatch = MatchEnd()

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        end = self.endmatch.parse(what)
        if end:
            return end
        if what[0] not in "truefalsbo":
            return ("", what)
        return None


class MatchString(Combinable):
    esctab = {
        '"': '"',
        "\\": "\\",
        "/": "/",
        "b": "\b",
        "f": "\f",
        "n": "\n",
        "r": "\r",
        "t": "\t",
    }

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        if what[0] != '"' or len(what) < 2:
            return None
        result = ""
        escaped = False
        try:
            i = 1
            while i < len(what):
                c = what[i]
                if c == '"' and not escaped:
                    return (result, what[i + 1 :])
                elif c == "\\" and not escaped:
                    escaped = True
                elif escaped:
                    escaped = False
                    if c in self.esctab:
                        result += self.esctab[c]
                    elif c == "u":
                        cp = what[i + 1 : i + 1 + 4]
                        try:
                            result += chr(int(cp, 16))
                        except ValueError:
                            raise Error("invalid codepoint", cp)
                        i += 4
                    else:
                        raise Error("unidentified escape", c)
                else:
                    result += c
                i += 1
        except IndexError:
            raise Error("abrupt end of string", what)
        return None


class MatchNumber(Combinable):
    nummatch = MatchOneOrMore(MatchCharacter("0123456789"))

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        _, what = Helpers.wsmatch.parse(what)

        # The implementation here is pretty naive and mostly
        # unnecessarily constructs the string-to-be-atof'd.
        def match_num_chars(where: str) -> str:
            ret = ""
            res = self.nummatch.parse(where)
            if not res:
                raise Error("expecting digits", what)
            n, left = res
            for nc in n:
                ret += nc
            return ret

        try:
            read: int = 0
            sign: int = 1
            if what[read] == "-":
                sign = -1
                read += 1
            num: str = ""
            if what[read] == "0":
                num += "0"
                read += 1
            elif what[read] in "123456789":
                before = match_num_chars(what[read:])
                read += len(before)
                num += before
            else:
                return None

            if read >= len(what):
                return (sign * float(num), what[read:])
            if what[read] == ".":
                num += "."
                read += 1
                after = match_num_chars(what[read:])
                read += len(after)
                num += after
                if read > len(what):
                    raise Error("number missing decimal part", what)
            if read >= len(what):
                return (sign * float(num), what[read:])
            if what[read] in "eE":
                read += 1
                expsign = 1
                if what[read] == "+":
                    read += 1
                    expsign = 1
                elif what[read] == "-":
                    read += 1
                    expsign = -1
                exp = match_num_chars(what[read:])
                read += len(exp)
                res = sign * float(num) * (10 ** (expsign * float(exp)))
                return (res, what[read:])
            return (sign * float(num), what[read:])
        except (IndexError, EndOfText):
            raise Error("abrupt end of number", what)


class MatchObject(Combinable):
    itemmatch = [
        MatchString(),
        Helpers.wsmatch,
        MatchOrRaise(MatchCharacter(":"), "expecting ':'"),
        Helpers.wsmatch,
        MatchOrRaise(MatchValue(), "expecting object value"),
    ]
    match = MatchAll(
        Helpers.wsmatch,
        MatchCharacter("{"),
        Helpers.wsmatch,
        MatchZeroOrMore(
            MatchAll(
                Helpers.wsmatch,
                *itemmatch,
                Helpers.wsmatch,
                MatchCharacter(","),
            )
        ),
        Helpers.wsmatch,
        MatchOrDefault(MatchAll(*itemmatch), Helpers.GUARD),
        Helpers.wsmatch,
        MatchOrRaise(MatchCharacter("}"), "expecting closing '}'"),
    )

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        kv: Dict[str, Any] = {}
        try:
            r = self.match.parse(what)
            if not r:
                return None
            vals, left = r
            if vals[3]:
                for val in vals[3]:
                    kv[val[1]] = val[5]
            if vals[5] != Helpers.GUARD:
                val = vals[5]
                kv[val[0]] = val[4]
            return (kv, left)
        except EndOfText:
            raise Error("sudden end of text when parsing object", what)


class MatchArray(Combinable):
    match = MatchAll(
        Helpers.wsmatch,
        MatchCharacter("["),
        MatchZeroOrMore(
            MatchAll(
                Helpers.wsmatch,
                MatchValue(),
                Helpers.wsmatch,
                MatchCharacter(","),
            )
        ),
        Helpers.wsmatch,
        MatchOrDefault(MatchValue(), Helpers.GUARD),
        Helpers.wsmatch,
        MatchOrRaise(MatchCharacter("]"), "expecting closing ']'"),
    )

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        res: List[Any] = []
        try:
            r = self.match.parse(what)
            if not r:
                return None
            vals, left = r
            if vals[2]:
                for val in vals[2]:
                    res.append(val[1])
            if vals[4] != Helpers.GUARD:
                res.append(vals[4])
            return (res, left)
        except EndOfText:
            raise Error("sudden end of text when parsing array", what)


class MatchBool(Combinable):
    truematch = MatchAll(
        Helpers.wsmatch, MatchKeyword("true", MatchDelimiter())
    )
    falsematch = MatchAll(
        Helpers.wsmatch, MatchKeyword("false", MatchDelimiter())
    )
    match = MatchAny(truematch, falsematch)

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        if len(what) == 0:
            return None
        r = self.match.parse(what)
        if not r:
            return r
        v, left = r
        if v[1][0] == "t":
            res = True
        else:
            res = False
        return (res, left)


class MatchNull(Combinable):
    match = MatchAll(Helpers.wsmatch, MatchKeyword("null", MatchDelimiter()))

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        if len(what) == 0:
            return None
        r = self.match.parse(what)
        if not r:
            return None
        _, left = r
        return (None, left)


class ParseError(Exception):
    def __init__(self, msg):
        super().__init__("JSON parsing error: %s" % msg)


def parse(what: str) -> Optional[Tuple[Any, str]]:
    try:
        r = MatchValue().parse(what)
        if not r:
            raise ParseError("parsing `%s' failed " % what)
        return r
    except Exception as e:
        raise ParseError("parsing `%s' failed: %s" % (what, e))


MatchValue.add_matcher(MatchObject())
MatchValue.add_matcher(MatchNumber())
MatchValue.add_matcher(MatchArray())
MatchValue.add_matcher(MatchString())
MatchValue.add_matcher(MatchBool())
MatchValue.add_matcher(MatchNull())
