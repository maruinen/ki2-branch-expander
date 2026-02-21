# -*- coding: utf-8 -*-
import shogi
import re
import collections
from extract_moves import parse_ki2_move, get_board_key

def debug():
    with open('ShogiSekai.ki2', 'r', encoding='cp932', errors='replace') as f:
        content = f.read()

    sections = re.split(r'(?=開始日時|手合割：|変化：)', content)
    move_pattern = re.compile(r'[▲△▽▼][^▲△▽▼\n\r*]+')
    
    registry = collections.defaultdict(list)
    registry[0].append(shogi.Board().sfen())

    for i, section in enumerate(sections):
        if not section.strip(): continue
        
        start_move = 1
        var_match = re.search(r'変化：(\d+)手', section)
        if var_match:
            start_move = int(var_match.group(1))
            parent_sfen = None
            first_move_match = move_pattern.search(section)
            if first_move_match:
                first_move_str = first_move_match.group(0).strip()
                
                if i == 146:
                    print(f"--- Debugging Section {i} ---")
                    print(f"Start move: {start_move}, First move: {first_move_str}")
                    print(f"Registry[{start_move-1}] size: {len(registry[start_move-1])}")
                
                for sfen in reversed(registry[start_move - 1]):
                    temp_board = shogi.Board(sfen)
                    move = parse_ki2_move(temp_board, first_move_str)
                    if i == 146:
                        # Print some info about each candidate
                        pass
                    if move:
                        parent_sfen = sfen
                        break
            
            if parent_sfen:
                board = shogi.Board(parent_sfen)
            else:
                if i == 146:
                    print(f"Failed to find parent for Section {i}")
                continue
        else:
            board = shogi.Board()

        # Process moves and update registry
        current_move_count = start_move - 1
        found_moves = move_pattern.findall(section)
        for move_str in found_moves:
            move = parse_ki2_move(board, move_str)
            if move:
                board.push(move)
                current_move_count += 1
                sfen = board.sfen()
                if sfen not in registry[current_move_count]:
                    registry[current_move_count].append(sfen)
            else:
                break

if __name__ == "__main__":
    debug()
