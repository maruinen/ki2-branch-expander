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
        to_square = board.move_stack[-1].to_square
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

    is_promotion_requested = '成' in relative_part
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
                    match = True
            elif is_promotion_requested and (actual_piece.piece_type + 8) == piece_type:
                if move.promotion: match = True
            elif piece_type > 8 and (actual_piece.piece_type + 8) == piece_type:
                if not move.promotion: match = True
            
            if match:
                possible_moves.append(move)

    if not possible_moves: return None
    if len(possible_moves) == 1: return possible_moves[0]

    is_black = board.turn == shogi.BLACK
    if '打' in relative_part:
        for m in possible_moves:
            if m.drop_piece_type: return m

    possible_moves_with_from = [m for m in possible_moves if m.from_square is not None]
    if not possible_moves_with_from: return possible_moves[0]
    
    if '右' in relative_part:
        possible_moves_with_from.sort(key=lambda m: m.from_square % 9, reverse=is_black)
    elif '左' in relative_part:
        possible_moves_with_from.sort(key=lambda m: m.from_square % 9, reverse=not is_black)
    elif '上' in relative_part:
        possible_moves_with_from.sort(key=lambda m: m.from_square // 9)
    elif '引' in relative_part or '下' in relative_part:
        possible_moves_with_from.sort(key=lambda m: m.from_square // 9, reverse=True)
    elif '寄' in relative_part:
        possible_moves_with_from.sort(key=lambda m: abs((m.from_square // 9) - (to_square // 9)))
    elif '直' in relative_part:
        for m in possible_moves_with_from:
            if (m.from_square % 9) == (to_square % 9): return m

    return possible_moves_with_from[0]

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

    sections = re.split(r'(?=開始日時|変化：)', content)
    move_pattern = re.compile(r'[▲△▽▼][^▲△▽▼\n\r*]+')
    
    total_found = 0; total_parsed = 0; errors = 0
    main_history: List[str] = [shogi.Board().sfen()]

    for section in sections:
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
            else: continue
        
        for line in section.splitlines():
            line = line.strip()
            if not line or line.startswith('*') or line.startswith('変化：'): continue
            
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
                    errors += 1
                    line_ok = False
                    break
            if not line_ok: break # そのゲームは諦める

    print(f"Found: {total_found}, Parsed: {total_parsed}, Errors: {errors}")
    return move_map

if __name__ == "__main__":
    result = extract_moves_from_ki2("ShogiSekai.ki2")
    print(f"Unique positions: {len(result)}")
