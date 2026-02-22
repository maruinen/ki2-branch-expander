import shogi
from typing import Dict, Set, List, Optional
import re
import collections

ZEN_TO_INT = str.maketrans("１２３４５６７八九", "123456789")
KAN_TO_INT = str.maketrans("一二三四五六七八九", "123456789")

PIECE_TYPE_MAP = {
    '歩': shogi.PAWN, '香': shogi.LANCE, '桂': shogi.KNIGHT, '銀': shogi.SILVER,
    '金': shogi.GOLD, '角': shogi.BISHOP, '飛': shogi.ROOK, '玉': shogi.KING,
    '王': shogi.KING, 'と': shogi.PROM_PAWN, '成香': shogi.PROM_LANCE, 
    '成桂': shogi.PROM_KNIGHT, '成銀': shogi.PROM_SILVER, '馬': shogi.PROM_BISHOP, 
    '龍': shogi.PROM_ROOK, '竜': shogi.PROM_ROOK
}

def parse_ki2_move(board: shogi.Board, move_str: str, last_to_square: Optional[int] = None) -> Optional[shogi.Move]:
    move_str = move_str.strip()
    if not move_str: return None
    move_str = re.sub(r'^[▲△▽▼]', '', move_str).strip()
    if not move_str: return None

    if move_str.startswith('同'):
        to_square = None
        if board.move_stack:
            to_square = board.move_stack[-1].to_square
        elif last_to_square is not None:
            to_square = last_to_square
        
        if to_square is None: return None
        piece_part = move_str[1:].strip()
    else:
        try:
            to_file = int(move_str[0].translate(ZEN_TO_INT))
            to_rank = int(move_str[1].translate(KAN_TO_INT))
            to_square = (to_rank - 1) * 9 + (9 - to_file)
            piece_part = move_str[2:].strip()
        except (ValueError, IndexError):
            return None

    piece_type = None
    relative_part = ""
    for k in sorted(PIECE_TYPE_MAP.keys(), key=len, reverse=True):
        if piece_part.startswith(k):
            piece_type = PIECE_TYPE_MAP[k]
            relative_part = piece_part[len(k):]
            break
    if piece_type is None: return None

    is_promotion_requested = '成' in relative_part and '不成' not in relative_part
    is_not_promotion_requested = '不成' in relative_part
    
    possible_moves = []
    for move in board.legal_moves:
        if move.to_square != to_square: continue
        
        if move.drop_piece_type:
            if move.drop_piece_type == piece_type:
                possible_moves.append(move)
        else:
            actual_piece = board.piece_at(move.from_square)
            if actual_piece is None: continue
            
            match = False
            if actual_piece.piece_type == piece_type:
                if is_promotion_requested:
                    if move.promotion: match = True
                elif is_not_promotion_requested:
                    if not move.promotion: match = True
                else:
                    if piece_type > 8: match = True
                    else: match = True
            elif is_promotion_requested and (actual_piece.piece_type + 8) == piece_type:
                if move.promotion: match = True
            elif piece_type > 8 and (actual_piece.piece_type + 8) == piece_type:
                if move.promotion: match = True
            
            if match:
                possible_moves.append(move)

    if not possible_moves: return None
    if len(possible_moves) == 1: return possible_moves[0]

    is_black = board.turn == shogi.BLACK
    if '打' in relative_part:
        for m in possible_moves:
            if m.drop_piece_type: return m
    
    candidates = [m for m in possible_moves if m.from_square is not None]
    if not candidates: return None
    if len(candidates) == 1: return candidates[0]

    def get_f(sq): return 9 - (sq % 9)
    def get_r(sq): return (sq // 9) + 1
    to_f, to_r = get_f(to_square), get_r(to_square)

    final_candidates = list(candidates)
    vertical_filtered = []
    if '上' in relative_part:
        vertical_filtered = [m for m in final_candidates if (get_r(m.from_square) > to_r if is_black else get_r(m.from_square) < to_r)]
    elif '引' in relative_part:
        vertical_filtered = [m for m in final_candidates if (get_r(m.from_square) < to_r if is_black else get_r(m.from_square) > to_r)]
    elif '寄' in relative_part:
        vertical_filtered = [m for m in final_candidates if get_r(m.from_square) == to_r]
    if vertical_filtered: final_candidates = vertical_filtered
    
    if len(final_candidates) == 1: return final_candidates[0]

    horizontal_filtered = []
    if '直' in relative_part:
        horizontal_filtered = [m for m in final_candidates if get_f(m.from_square) == to_f]
    elif '左' in relative_part:
        relative_to_dest_left = [m for m in final_candidates if (get_f(m.from_square) > to_f if is_black else get_f(m.from_square) < to_f)]
        if relative_to_dest_left: horizontal_filtered = relative_to_dest_left
        else: horizontal_filtered = sorted(final_candidates, key=lambda m: get_f(m.from_square), reverse=is_black)[:1]
    elif '右' in relative_part:
        relative_to_dest_right = [m for m in final_candidates if (get_f(m.from_square) < to_f if is_black else get_f(m.from_square) > to_f)]
        if relative_to_dest_right: horizontal_filtered = relative_to_dest_right
        else: horizontal_filtered = sorted(final_candidates, key=lambda m: get_f(m.from_square), reverse=not is_black)[:1]
    if horizontal_filtered: final_candidates = horizontal_filtered
    
    return final_candidates[0] if final_candidates else None

def get_board_key(board: shogi.Board) -> str:
    s = board.sfen()
    parts = s.split(' ')
    return " ".join(parts[:3])

def extract_moves_from_ki2(file_path: str) -> Dict[str, Dict[str, List[str]]]:
    move_map: Dict[str, Dict[str, List[str]]] = {}
    try:
        with open(file_path, 'r', encoding='cp932', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"Error: {e}"); return {}

    header_patterns = [r'^開始日時：', r'^手合割：', r'^変化：']
    combined_pattern = '|'.join(header_patterns)
    matches = list(re.finditer(combined_pattern, content, re.MULTILINE))
    sections_raw = [content[m.start():(matches[i+1].start() if i+1 < len(matches) else len(content))] for i, m in enumerate(matches)]

    move_pattern = re.compile(r'[▲△▽▼][^▲△▽▼\n\r*]+')
    total_found = 0; total_parsed = 0; errors = 0
    global_registry: Set[tuple[str, Optional[int], int]] = set()
    global_registry.add((shogi.Board().sfen(), None, 0))

    main_sections = []
    variation_sections = []
    for i, s in enumerate(sections_raw):
        if i == 0 or (re.search(r'^手合割：', s, re.MULTILINE) and not re.search(r'^変化[：:]', s, re.MULTILINE)):
            main_sections.append(s)
        else:
            variation_sections.append(s)

    def parse_section(section, is_var, best_p_info=None):
        nonlocal total_found, total_parsed, errors
        if is_var and best_p_info:
            board = shogi.Board(best_p_info[0])
            lts = best_p_info[1]
            curr_cnt = best_p_info[2]
        else:
            board = shogi.Board()
            lts = None
            curr_cnt = 0
            global_registry.add((board.sfen(), None, 0))

        found_moves = [m.strip() for m in move_pattern.findall(section)]
        initial_sfen = board.sfen()
        initial_lts = lts
        last_move_info = None

        for move_str in found_moves:
            total_found += 1
            key = get_board_key(board)
            if key not in move_map: move_map[key] = {}
            move = parse_ki2_move(board, move_str, lts)
            if move:
                total_parsed += 1
                usi = move.usi()
                if usi not in move_map[key]: move_map[key][usi] = []
                lts = move.to_square
                board.push(move)
                last_move_info = (key, usi)
                curr_cnt += 1
                global_registry.add((board.sfen(), lts, curr_cnt))
            else:
                errors += 1
                break
        
        # コメント処理
        tmp_board = shogi.Board(initial_sfen)
        tmp_lts = initial_lts
        last_mi = None
        for line in section.splitlines():
            line = line.strip()
            if line.startswith('*') and last_mi:
                k, u = last_mi
                if k in move_map and u in move_map[k] and line[1:].strip() not in move_map[k][u]:
                    move_map[k][u].append(line[1:].strip())
            elif any(c in line for c in '▲△▽▼'):
                for ms in move_pattern.findall(line):
                    mk = get_board_key(tmp_board)
                    mv = parse_ki2_move(tmp_board, ms, tmp_lts)
                    if mv:
                        tmp_lts = mv.to_square
                        tmp_board.push(mv)
                        last_mi = (mk, mv.usi())
                    else: break

    for s in main_sections: parse_section(s, False)

    pending_vars = variation_sections
    for pass_idx in range(5):
        still_pending = []
        parsed_any = False
        for s in pending_vars:
            found_moves = [m.strip() for m in move_pattern.findall(s)]
            if not found_moves: continue
            var_match = re.search(r'^変化[：:]\s*(\d+)手', s, re.MULTILINE)
            claimed_start_move = int(var_match.group(1)) if var_match else 1
            first_move_str = found_moves[0]
            best_p = None
            max_score = -1
            sorted_registry = sorted(list(global_registry), key=lambda x: abs(x[2] - (claimed_start_move - 1)))
            for sfen, lts, m_count in sorted_registry:
                temp_board = shogi.Board(sfen)
                if parse_ki2_move(temp_board, first_move_str, lts):
                    tb = shogi.Board(sfen)
                    curr_lts = lts
                    pc = 0
                    lookahead_limit = min(len(found_moves), 20)
                    for m_str in found_moves[:lookahead_limit]:
                        move = parse_ki2_move(tb, m_str, curr_lts)
                        if move:
                            curr_lts = move.to_square
                            tb.push(move)
                            pc += 1
                        else: break
                    score = pc / lookahead_limit if lookahead_limit > 0 else 0
                    if score > max_score:
                        max_score = score
                        best_p = (sfen, lts, m_count)
                    if score == 1.0: break
            if max_score > 0:
                parse_section(s, True, best_p)
                parsed_any = True
            else: still_pending.append(s)
        if not still_pending or not parsed_any: break
        pending_sections = still_pending

    print(f"Found: {total_found}, Parsed: {total_parsed}, Errors: {errors}")
    return move_map

if __name__ == "__main__":
    result = extract_moves_from_ki2("ShogiSekai.ki2")
    print(f"Unique positions: {len(result)}")
