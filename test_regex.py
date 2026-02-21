# -*- coding: utf-8 -*-
import re

# New proposed pattern
move_pattern = re.compile(r'[▲△▽▼][^▲△▽▼\n\r*]+')

test_lines = [
    "▲７六歩  △３四歩  ▲２六歩  △４四歩  ▲４八銀  △４二飛",
    "▲３三角成 △同　飛  ▲３六歩",
    "▲ ４八銀  △　４二飛", # Spaces after symbols
    "▲７六歩 *comment on line",
    "変化：36手",
]

for line in test_lines:
    moves = move_pattern.findall(line)
    print(f"Line: {repr(line)}")
    print(f"Moves: {[m.strip() for m in moves]}")
    print("-" * 20)
