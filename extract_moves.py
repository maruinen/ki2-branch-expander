import shogi
from typing import Dict, Set, List, Optional, Tuple
import re

ZEN_TO_INT = str.maketrans("１２３４５６７八九", "123456789")
KAN_TO_INT = str.maketrans("一二三四五六七八九", "123456789")

# 駒名マップ（1文字・2文字両方に対応）
PIECE_TYPE_MAP = {
    '歩': shogi.PAWN, '香': shogi.LANCE, '桂': shogi.KNIGHT, '銀': shogi.SILVER,
    '金': shogi.GOLD, '角': shogi.BISHOP, '飛': shogi.ROOK, '玉': shogi.KING,
    '王': shogi.KING, 'と': shogi.PROM_PAWN, '成香': shogi.PROM_LANCE, 
    '成桂': shogi.PROM_KNIGHT, '成銀': shogi.PROM_SILVER, '馬': shogi.PROM_BISHOP, 
    '龍': shogi.PROM_ROOK, '竜': shogi.PROM_ROOK,
    '全': shogi.PROM_SILVER, '圭': shogi.PROM_KNIGHT, '杏': shogi.PROM_LANCE,
    '个': shogi.PROM_PAWN
}

def parse_ki2_move(board: shogi.Board, move_str: str, last_to_square: Optional[int] = None) -> Optional[shogi.Move]:
    move_str = move_str.strip()
    if not move_str: return None
    # 先手・後手の記号を除去
    move_str = re.sub(r'^[▲△▽▼＋]', '', move_str).strip()
    if not move_str: return None

    # 1. 目的地 (to_square) の特定
    if move_str.startswith(('同', '〃')):
        to_square = board.move_stack[-1].to_square if board.move_stack else last_to_square
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

    # 2. 駒種と相対表記・成フラグの分離
    piece_type = None
    relative_part = ""
    # 長い駒名から順にマッチング
    for k in sorted(PIECE_TYPE_MAP.keys(), key=len, reverse=True):
        if piece_part.startswith(k):
            piece_type = PIECE_TYPE_MAP[k]
            relative_part = piece_part[len(k):]
            break
    if piece_type is None: return None

    is_prom = '成' in relative_part and '不成' not in relative_part
    is_not_prom = '不成' in relative_part
    
    # 3. 合法手からの絞り込み
    candidates = []
    for move in board.legal_moves:
        if move.to_square != to_square: continue
        
        if move.drop_piece_type:
            if move.drop_piece_type == piece_type:
                candidates.append(move)
        else:
            p = board.piece_at(move.from_square)
            # 盤上の駒が指定された駒種と一致するか
            if p.piece_type == piece_type:
                # 符号に「成」「不成」がある場合はそれに従う。指定がない場合は「不成」とする（生駒の場合）
                if is_prom:
                    if move.promotion: candidates.append(move)
                elif is_not_prom:
                    if not move.promotion: candidates.append(move)
                else:
                    # 既に成っている駒が動く場合は promotion は常に False (python-shogiの仕様)
                    # 生駒が動く場合は、指定がなければ不成
                    if not move.promotion: candidates.append(move)
            # 駒が成る場合 (例: 符号が「龍」で、盤上に「飛」がある)
            elif (p.piece_type + 8) == piece_type:
                if move.promotion:
                    candidates.append(move)

    if not candidates: return None
    if len(candidates) == 1: return candidates[0]

    # 4. 相対表記による決定論的な絞り込み (実績あるロジック)
    is_black = board.turn == shogi.BLACK
    
    if '打' in relative_part:
        for m in candidates:
            if m.drop_piece_type: return m

    # 盤上の駒からの移動に限定
    board_candidates = [m for m in candidates if not m.drop_piece_type]
    if not board_candidates: return None
    if len(board_candidates) == 1: return board_candidates[0]

    def get_f(sq): return 9 - (sq % 9)
    def get_r(sq): return (sq // 9) + 1
    to_f, to_r = get_f(to_square), get_r(to_square)

    # 垂直方向 (上, 引, 寄)
    if any(x in relative_part for x in ('上', '行', '入')):
        board_candidates = [m for m in board_candidates if (get_r(m.from_square) > to_r if is_black else get_r(m.from_square) < to_r)]
    elif '引' in relative_part:
        board_candidates = [m for m in board_candidates if (get_r(m.from_square) < to_r if is_black else get_r(m.from_square) > to_r)]
    elif '寄' in relative_part:
        board_candidates = [m for m in board_candidates if get_r(m.from_square) == to_r]

    if len(board_candidates) == 1: return board_candidates[0]

    # 水平方向 (右, 左, 直)
    # 「右」は、そこに行ける駒の中で最も右にある（先手なら1筋寄り、後手なら9筋寄り）
    if '右' in relative_part:
        val = min if is_black else max
        f_val = val(get_f(m.from_square) for m in board_candidates)
        board_candidates = [m for m in board_candidates if get_f(m.from_square) == f_val]
    elif '左' in relative_part:
        val = max if is_black else min
        f_val = val(get_f(m.from_square) for m in board_candidates)
        board_candidates = [m for m in board_candidates if get_f(m.from_square) == f_val]
    elif '直' in relative_part:
        board_candidates = [m for m in board_candidates if get_f(m.from_square) == to_f]

    return board_candidates[0] if board_candidates else None

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

    # セクション分割（開始日時、手合割、変化）
    header_patterns = [r'^開始日時：', r'^手合割：', r'^変化[：:]']
    combined_pattern = '|'.join(header_patterns)
    matches = list(re.finditer(combined_pattern, content, re.MULTILINE))
    
    sections_raw = []
    if not matches:
        sections_raw = [content]
    else:
        for i in range(len(matches)):
            start = matches[i].start()
            end = matches[i+1].start() if i+1 < len(matches) else len(content)
            sections_raw.append(content[start:end])

    move_pattern = re.compile(r'[▲△▽▼＋][^▲△▽▼\n\r*＋]+')
    
    # section_idx -> { move_count -> (sfen, last_to_square) }
    # move_count 0 は初期局面
    histories: Dict[int, Dict[int, Tuple[str, Optional[int]]]] = {}

    total_found = 0; total_parsed = 0; errors = 0

    for idx, section in enumerate(sections_raw):
        if not section.strip(): continue
        
        var_match = re.search(r'^変化[：:]\s*(\d+)手', section, re.MULTILINE)
        if var_match:
            n = int(var_match.group(1))
            # 親セクションを一意に特定するルール:
            # 直前のセクションから遡り、最初に n-1 手目が存在するセクションを採用
            parent_idx = -1
            for prev_idx in range(idx - 1, -1, -1):
                if prev_idx in histories and (n - 1) in histories[prev_idx]:
                    parent_idx = prev_idx
                    break
            
            if parent_idx == -1:
                # 警告を出すが続行
                print(f"Warning: Section {idx} (Variation {n}手) parent not found.")
                continue
            
            parent_sfen, parent_lts = histories[parent_idx][n - 1]
            board = shogi.Board(parent_sfen)
            last_to = parent_lts
            start_move_count = n - 1
        else:
            # メインライン
            board = shogi.Board()
            last_to = None
            start_move_count = 0
        
        # 履歴の初期化
        histories[idx] = {start_move_count: (board.sfen(), last_to)}
        
        last_move_info = None
        curr_cnt = start_move_count

        # セクション内の指し手をパース
        lines = section.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('変化'): continue
            
            if line.startswith('*'):
                if last_move_info:
                    k, u = last_move_info
                    if k in move_map and u in move_map[k]:
                        if line[1:].strip() not in move_map[k][u]:
                            move_map[k][u].append(line[1:].strip())
                continue
            
            if any(h in line for h in ['開始日時', '終了日時', '手合割', '先手', '後手', '棋戦']):
                continue

            moves_in_line = move_pattern.findall(line)
            for m_str in moves_in_line:
                total_found += 1
                key = get_board_key(board)
                if key not in move_map: move_map[key] = {}
                
                move = parse_ki2_move(board, m_str, last_to)
                if move:
                    total_parsed += 1
                    usi = move.usi()
                    if usi not in move_map[key]: move_map[key][usi] = []
                    
                    last_to = move.to_square
                    board.push(move)
                    last_move_info = (key, usi)
                    curr_cnt += 1
                    histories[idx][curr_cnt] = (board.sfen(), last_to)
                else:
                    errors += 1
                    # print(f"Error in Section {idx}: {m_str.strip()} at move {curr_cnt+1}")
                    board = None # このセクションの解析を中断
                    break
            if board is None: break

    print(f"Found: {total_found}, Parsed: {total_parsed}, Errors: {errors}")
    return move_map

if __name__ == "__main__":
    import sys
    file = sys.argv[1] if len(sys.argv) > 1 else "ShogiSekai.ki2"
    result = extract_moves_from_ki2(file)
    print(f"Unique positions: {len(result)}")
