import shogi
from typing import Dict, Set, List, Optional
import re

def get_ki2_move_str(board: shogi.Board, move: shogi.Move) -> str:
    """
    python-shogiのMoveオブジェクトをKI2形式の文字列に変換する。
    相対表記（上、引、寄、右、左、直、打）および「不成」をサポート。
    """
    to_file = 9 - (move.to_square % 9)
    to_rank = (move.to_square // 9) + 1
    
    ZEN_NUM = "　１２３４５６７８９"
    KAN_NUM = "　一二三四五六七八九"
    
    if board.move_stack and board.move_stack[-1].to_square == move.to_square:
        to_str = "同　"
    else:
        to_str = f"{ZEN_NUM[to_file]}{KAN_NUM[to_rank]}"
    
    if move.drop_piece_type:
        piece_type = move.drop_piece_type
    else:
        from_piece = board.piece_at(move.from_square)
        piece_type = from_piece.piece_type
    
    PIECE_MAP = {
        shogi.PAWN: '歩', shogi.LANCE: '香', shogi.KNIGHT: '桂', shogi.SILVER: '銀',
        shogi.GOLD: '金', shogi.BISHOP: '角', shogi.ROOK: '飛', shogi.KING: '玉',
        shogi.PROM_PAWN: 'と', shogi.PROM_LANCE: '成香', shogi.PROM_KNIGHT: '成桂',
        shogi.PROM_SILVER: '成銀', shogi.PROM_BISHOP: '馬', shogi.PROM_ROOK: '龍'
    }
    
    piece_str = PIECE_MAP.get(piece_type, '?')
    
    # 相対表記の判定
    relative_str = ""
    
    # 同じ種類の駒が同じ目的地に行けるか（移動のみ）
    board_candidates = []
    for m in board.legal_moves:
        if m.to_square == move.to_square and not m.drop_piece_type:
            p = board.piece_at(m.from_square)
            if p.piece_type == piece_type:
                if m.from_square not in board_candidates:
                    board_candidates.append(m.from_square)

    if move.drop_piece_type:
        if board_candidates:
            relative_str = "打"
    else:
        if len(board_candidates) > 1:
            is_black = board.turn == shogi.BLACK
            from_sq = move.from_square
            
            def get_f(sq): return 9 - (sq % 9)
            def get_r(sq): return (sq // 9) + 1
            
            from_f, from_r = get_f(from_sq), get_r(from_sq)
            to_f, to_r = get_f(move.to_square), get_r(move.to_square)
            
            v_pos = ""
            if from_r > to_r: v_pos = "上" if is_black else "引"
            elif from_r < to_r: v_pos = "引" if is_black else "上"
            else: v_pos = "寄"
            
            h_pos = ""
            if from_f == to_f: h_pos = "直"
            elif from_f > to_f: h_pos = "左" if is_black else "右"
            else: h_pos = "右" if is_black else "左"
            
            if piece_type in [shogi.PAWN, shogi.LANCE, shogi.KNIGHT, shogi.SILVER, shogi.GOLD, shogi.PROM_PAWN, shogi.PROM_LANCE, shogi.PROM_KNIGHT, shogi.PROM_SILVER]:
                if h_pos == "直":
                    relative_str = v_pos + h_pos
                else:
                    relative_str = h_pos + v_pos
            else:
                relative_str = v_pos
                # 垂直方向で区別できなければ水平方向も追加
                v_others = [sq for sq in board_candidates if sq != from_sq]
                can_distinguish_v = all( ((get_r(sq) > to_r) != (from_r > to_r)) or ((get_r(sq) < to_r) != (from_r < to_r)) or ((get_r(sq) == to_r) != (from_r == to_r)) for sq in v_others)
                if not can_distinguish_v:
                    relative_str = h_pos + v_pos

    # 成・不成
    if move.promotion:
        piece_str += "成"
    else:
        can_promote = False
        for m in board.legal_moves:
            if m.from_square == move.from_square and m.to_square == move.to_square and m.promotion:
                can_promote = True
                break
        if can_promote:
            piece_str += "不成"
            
    return f"{to_str}{piece_str}{relative_str}"

def expand_tree(
    board: shogi.Board, 
    move_map: Dict[str, Set[str]], 
    path_history: Set[str] = None
) -> List[Dict]:
    """
    局面ハッシュマップを元に、再帰的に全分岐を展開したツリー構造を生成する。
    """
    if path_history is None:
        path_history = set()

    from extract_moves import get_board_key
    sfen_key = get_board_key(board)

    if sfen_key in path_history:
        return []

    next_moves_usi = move_map.get(sfen_key, set())
    if not next_moves_usi:
        return []

    new_path_history = path_history | {sfen_key}
    tree = []

    # 決定論的な出力のためソート
    for move_usi in sorted(list(next_moves_usi)):
        move = shogi.Move.from_usi(move_usi)
        ki2_val = get_ki2_move_str(board, move)
        
        board.push(move)
        branches = expand_tree(board, move_map, new_path_history)
        board.pop()
        
        tree.append({
            'move': move,
            'branches': branches,
            'ki2_str': ki2_val
        })
        
    return tree
