#!/usr/bin/env python3
import sys
from pprint import pprint
from typing import List
from jsonparser.parser import parse

lines: List[str] = []
for line in sys.stdin:
    lines.append(line.strip())

left = "".join(lines)
try:
    while left:
        val, left = parse(left)
        pprint(val)
except Exception as e:
    print(e)
