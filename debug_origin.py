# -*- coding: utf-8 -*-
import shogi
import re
import collections
from extract_moves import parse_ki2_move, get_board_key

def find_sfen_origin(target_sfen):
    with open('ShogiSekai.ki2', 'r', encoding='cp932', errors='replace') as f:
        content = f.read()
    
    header_patterns = [r'^開始日時：', r'^手合割：', r'^変化：']
    combined_pattern = '|'.join(header_patterns)
    matches = list(re.finditer(combined_pattern, content, re.MULTILINE))
    sections = []
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i+1 < len(matches) else len(content)
        sections.append(content[start:end])

    move_pattern = re.compile(r'[▲△▽▼][^▲△▽▼\n\r*]+')
    registry = collections.defaultdict(list)
    registry[0].append((shogi.Board().sfen(), None))

    for i, section in enumerate(sections):
        if not section.strip(): continue
        
        var_match = re.search(r'^変化：(\d+)手', section, re.MULTILINE)
        s_move = int(var_match.group(1)) if var_match else 1
        f_moves = move_pattern.findall(section)
        if not f_moves: continue

        board = None
        last_to_square = None
        if var_match:
            first_move_str = f_moves[0].strip()
            candidates = []
            for sfen, lts in reversed(registry[s_move - 1]):
                temp_board = shogi.Board(sfen)
                if parse_ki2_move(temp_board, first_move_str, lts):
                    candidates.append((sfen, lts))
            
            best_parent = None
            max_parsed = -1
            for sfen, lts in candidates:
                temp_board = shogi.Board(sfen)
                curr_lts = lts
                parsed_count = 0
                for m_str in f_moves:
                    move = parse_ki2_move(temp_board, m_str, curr_lts)
                    if move:
                        curr_lts = move.to_square
                        temp_board.push(move)
                        parsed_count += 1
                    else: break
                if parsed_count > max_parsed:
                    max_parsed = parsed_count
                    best_parent = (sfen, lts)
                if parsed_count == len(f_moves): break
            if best_parent:
                board = shogi.Board(best_parent[0])
                last_to_square = best_parent[1]
        else:
            board = shogi.Board()
            if (board.sfen(), None) not in registry[0]:
                registry[0].append((board.sfen(), None))
        
        if not board: continue
        curr_cnt = s_move - 1
        for m_str in f_moves:
            # Check SFEN BEFORE move
            curr_sfen = board.sfen()
            if curr_sfen.startswith(target_sfen):
                print(f"Target SFEN found BEFORE move at Section {i}, Move {curr_cnt}: {curr_sfen}")
            
            m = parse_ki2_move(board, m_str, last_to_square)
            if m:
                last_to_square = m.to_square
                board.push(m)
                curr_cnt += 1
                
                curr_sfen_after = board.sfen()
                if (curr_sfen_after, last_to_square) not in registry[curr_cnt]:
                    registry[curr_cnt].append((curr_sfen_after, last_to_square))
            else: break

if __name__ == "__main__":
    target = "ln3gknl/1r1sg1sb1/p1pp5/4ppppp/1p7/2PPPP2P/PPBS2PP1/3RGKS2/LN3G1NL"
    find_sfen_origin(target)
