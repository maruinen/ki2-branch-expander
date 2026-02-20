import shogi
from typing import Dict, Set, List, Optional
import re

ZEN_TO_INT = str.maketrans("１２３４５６７八九", "123456789")
KAN_TO_INT = str.maketrans("一二三四五六七八九", "123456789")

PIECE_TYPE_MAP = {
    '歩': shogi.PAWN, '香': shogi.LANCE, '桂': shogi.KNIGHT, '銀': shogi.SILVER,
    '金': shogi.GOLD, '角': shogi.BISHOP, '飛': shogi.ROOK, '玉': shogi.KING,
    '王': shogi.KING, 'と': shogi.PROM_PAWN, '成香': shogi.PROM_LANCE, 
    '成桂': shogi.PROM_KNIGHT, '成銀': shogi.PROM_SILVER, '馬': shogi.PROM_BISHOP, 
    '龍': shogi.PROM_ROOK, '竜': shogi.PROM_ROOK
}

def parse_ki2_move(board: shogi.Board, move_str: str) -> Optional[shogi.Move]:
    move_str = move_str.strip()
    if not move_str: return None
    move_str = re.sub(r'^[▲△▽▼]', '', move_str).strip()
    if not move_str: return None

    if move_str.startswith('同'):
        if not board.move_stack: return None
        last_move = board.move_stack[-1]
        to_square = last_move.to_square
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
    # 長い名前から順にマッチング（成香など）
    for k in sorted(PIECE_TYPE_MAP.keys(), key=len, reverse=True):
        if piece_part.startswith(k):
            piece_type = PIECE_TYPE_MAP[k]
            relative_part = piece_part[len(k):]
            break
    if piece_type is None:
        return None

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
            # 駒の種類が一致するか、成る前の駒が指定されている場合を考慮
            if actual_piece.piece_type == piece_type:
                if is_promotion_requested:
                    if move.promotion: match = True
                elif is_not_promotion_requested:
                    if not move.promotion: match = True
                else:
                    # 成駒が指定された場合は、すでに成っている駒のみ
                    if piece_type > 8:
                        match = True
                    else:
                        # 生駒が指定された場合、成る手と成らない手の両方が候補
                        match = True
            elif is_promotion_requested and (actual_piece.piece_type + 8) == piece_type:
                if move.promotion: match = True
            elif piece_type > 8 and (actual_piece.piece_type + 8) == piece_type:
                # 「成銀」と指定されて、銀が成る場合
                if move.promotion: match = True
            
            if match:
                possible_moves.append(move)

    if not possible_moves:
        return None
    if len(possible_moves) == 1: return possible_moves[0]

    # 相対表記の処理
    is_black = board.turn == shogi.BLACK
    
    # 打が指定されている場合は、まずそれを優先
    if '打' in relative_part:
        for m in possible_moves:
            if m.drop_piece_type: return m
    
    # 盤上の駒からの移動に限定
    candidates = [m for m in possible_moves if m.from_square is not None]
    if not candidates: return None # 指し手が見つからない
    if len(candidates) == 1: return candidates[0] # 曖昧性がない

    # 相対位置判定のための補助関数
    def get_file(sq): return 9 - (sq % 9)
    def get_rank(sq): return (sq // 9) + 1

    to_f = get_file(to_square)
    to_r = get_rank(to_square)

    final_candidates = list(candidates) # Make a copy to filter

    # 1. 垂直方向の属性でフィルタ (上, 引, 寄)
    vertical_filtered = []
    if '上' in relative_part:
        vertical_filtered = [m for m in final_candidates if (get_rank(m.from_square) > to_r if is_black else get_rank(m.from_square) < to_r)]
    elif '引' in relative_part:
        vertical_filtered = [m for m in final_candidates if (get_rank(m.from_square) < to_r if is_black else get_rank(m.from_square) > to_r)]
    elif '寄' in relative_part:
        vertical_filtered = [m for m in final_candidates if get_rank(m.from_square) == to_r]

    if vertical_filtered:
        final_candidates = vertical_filtered
    
    if len(final_candidates) == 1: return final_candidates[0]
    if not final_candidates: return possible_moves[0] # Fallback if vertical filter eliminates everything

    # 2. 水平方向の属性でフィルタ (直, 左, 右)
    horizontal_filtered = []
    if '直' in relative_part:
        horizontal_filtered = [m for m in final_candidates if get_file(m.from_square) == to_f]
    elif '左' in relative_part:
        # Option 1: Relative to destination file
        # Black: from_f > to_f
        # White: from_f < to_f
        relative_to_dest_left = [m for m in final_candidates if (get_file(m.from_square) > to_f if is_black else get_file(m.from_square) < to_f)]
        if relative_to_dest_left:
            horizontal_filtered = relative_to_dest_left
        else:
            # Option 2: Relative to other pieces (leftmost of remaining)
            # Black: file 9 is left, so larger get_file value is "more left"
            # White: file 1 is left, so smaller get_file value is "more left"
            horizontal_filtered = sorted(final_candidates, key=lambda m: get_file(m.from_square), reverse=is_black)[:1]

    elif '右' in relative_part:
        # Option 1: Relative to destination file
        # Black: from_f < to_f
        # White: from_f > to_f
        relative_to_dest_right = [m for m in final_candidates if (get_file(m.from_square) < to_f if is_black else get_file(m.from_square) > to_f)]
        if relative_to_dest_right:
            horizontal_filtered = relative_to_dest_right
        else:
            # Option 2: Relative to other pieces (rightmost of remaining)
            # Black: file 1 is right, so smaller get_file value is "more right"
            # White: file 9 is right, so larger get_file value is "more right"
            horizontal_filtered = sorted(final_candidates, key=lambda m: get_file(m.from_square), reverse=not is_black)[:1] # Corrected sorting

    if horizontal_filtered:
        final_candidates = horizontal_filtered
    
    if final_candidates:
        return final_candidates[0]
    
    return possible_moves[0]

def get_board_key(board: shogi.Board) -> str:
    s = board.sfen()
    parts = s.split(' ')
    return " ".join(parts[:3])

def extract_moves_from_ki2(file_path: str) -> Dict[str, Set[str]]:
    move_map: Dict[str, Set[str]] = {}
    try:
        with open(file_path, 'r', encoding='cp932', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"Error: {e}"); return {}

    sections = re.split(r'(?=開始日時|手合割：|変化：)', content)
    # より厳密な指し手パターン（空記号の後のスペースを許容）
    move_pattern = re.compile(r'[▲△▽▼][ \t]*[^▲△▽▼\n\r* \t]+[ \t]*')
    
    total_found = 0; total_parsed = 0; errors = 0
    main_history: List[str] = [shogi.Board().sfen()]

    for section_idx, section in enumerate(sections):
        if not section.strip(): continue
        
        board = shogi.Board()
        is_variation = False
        start_move = 1
        
        var_match = re.search(r'変化：(\d+)手', section)
        if var_match:
            is_variation = True
            start_move = int(var_match.group(1))
            if start_move <= len(main_history):
                board = shogi.Board(main_history[start_move - 1])
            else:
                continue
        
        for line_idx, line in enumerate(section.splitlines()):
            line = line.strip()
            if not line or line.startswith('*') or line.startswith('変化：'): continue
            
            # 手合割などのヘッダー行をスキップ
            if any(h in line for h in ['開始日時', '終了日時', '手合割', '先手', '後手', '棋戦']):
                continue

            found_moves = move_pattern.findall(line)
            line_ok = True
            for move_str in found_moves:
                total_found += 1
                key = get_board_key(board)
                if key not in move_map: move_map[key] = set()
                
                move = parse_ki2_move(board, move_str)
                if move:
                    total_parsed += 1
                    move_map[key].add(move.usi())
                    board.push(move)
                    if not is_variation:
                        if len(board.move_stack) >= len(main_history):
                            main_history.append(board.sfen())
                        else:
                            main_history[len(board.move_stack)] = board.sfen()
                else:
                    print(f"Failed to parse move: '{move_str.strip()}' at pos {key} (Section {section_idx}, Line {line_idx})")
                    errors += 1
                    line_ok = False
                    break
            if not line_ok: break 

    print(f"Found: {total_found}, Parsed: {total_parsed}, Errors: {errors}")
    return move_map

if __name__ == "__main__":
    result = extract_moves_from_ki2("ShogiSekai.ki2")
    print(f"Unique positions: {len(result)}")