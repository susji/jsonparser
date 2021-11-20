from abc import ABC, abstractmethod
from typing import Any, List, Iterable, Tuple, Optional, Callable


class Combinable(ABC):
    @abstractmethod
    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        pass


class EndOfText(Exception):
    pass


class MatchOr(Combinable):
    def __init__(self, first: Combinable, second: Combinable) -> None:
        self.first = first
        self.second = second

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        res = self.first.parse(what)
        if res:
            return res
        return self.second.parse(what)


class MatchCharacter(Combinable):
    def __init__(self, match: str) -> None:
        self.match = match

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        try:
            if what[0] in self.match:
                return (what[0], what[1:])
            return None
        except IndexError:
            raise EndOfText()


class MatchZeroOrMore(Combinable):
    def __init__(self, matcher: Combinable) -> None:
        self.matcher = matcher

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        matched: List[Any] = None
        mp = self.matcher.parse
        while True:
            if len(what) == 0:
                break
            res = mp(what)
            if not res:
                break
            node, what = res
            if not matched:
                matched = []
            matched.append(node)
        return (matched, what)


class MatchOneOrMore(Combinable):
    def __init__(self, matcher: Combinable) -> None:
        self.wrapped = MatchZeroOrMore(matcher)

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        res = self.wrapped.parse(what)
        if not res:
            return None
        matches, what = res
        if not matches or len(matches) == 0:
            return None
        return (matches, what)


class MatchAny(Combinable):
    def __init__(self, *args: Combinable) -> None:
        if len(args) == 0:
            raise RuntimeError("MatchAny without any matchers")
        self.matchers: Iterable[Combinable] = args

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        for matcher in self.matchers:
            res = matcher.parse(what)
            if res:
                return res
        return None


class MatchN(Combinable):
    def __init__(self, n: int, matcher: Combinable) -> None:
        self.n = n
        self.matcher = matcher

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        left: str = what
        res: List[Combinable] = []
        for _ in range(self.n):
            r = self.matcher.parse(left)
            if not r:
                return None
            n, left = r
            res.append(n)
        return (res, left)


class MatchAll(Combinable):
    def __init__(self, *args: Combinable) -> None:
        if len(args) == 0:
            raise RuntimeError("MatchArgs without any matchers")
        self.matchers: Iterable[Combinable] = args

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        left: str = what
        res: List[Any] = []
        for m in self.matchers:
            r = m.parse(left)
            if not r:
                return None
            n, left = r
            res.append(n)
        return (res, left)


class MatchOrDefault(Combinable):
    def __init__(self, matcher: Combinable, default: Any) -> None:
        self.matcher = matcher
        self.default = default

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        r = self.matcher.parse(what)
        if not r:
            return (self.default, what)
        return r


class MatchEnd(Combinable):
    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        if len(what) == 0:
            return ("", "")
        return None


class MatchKeyword(Combinable):
    def __init__(self, keyword: str, delimiter: Combinable) -> None:
        self.matcher = MatchAll(
            *[MatchCharacter(c) for c in keyword],
            MatchOr(MatchEnd(), delimiter)
        )

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        r = self.matcher.parse(what)
        if not r:
            return None
        kw, left = r
        return ("".join(kw), left)


class MatchOrRaise(Combinable):
    def __init__(
        self, matcher: Combinable, e: Callable[[str, str], Exception], msg: str
    ) -> None:
        self.matcher = matcher
        self.e = e
        self.msg = msg

    def parse(self, what: str) -> Optional[Tuple[Any, str]]:
        r = self.matcher.parse(what)
        if not r:
            raise self.e(self.msg, what)
        return r
