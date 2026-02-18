import shogi
from typing import Dict, Set, List, Optional
import re

def get_ki2_move_str(board: shogi.Board, move: shogi.Move) -> str:
    """
    python-shogiのMoveオブジェクトをKI2形式の文字列に変換する。
    """
    # python-shogiの内部インデックス (0=9a, 1=8a, ..., 80=1i)
    # file = 9 - (index % 9)
    # rank = (index // 9) + 1
    
    to_file = 9 - (move.to_square % 9)
    to_rank = (move.to_square // 9) + 1
    
    ZEN_NUM = "　１２３４５６７８９"
    KAN_NUM = "　一二三四五六七八九"
    
    if board.move_stack and board.move_stack[-1].to_square == move.to_square:
        to_str = "同　"
    else:
        to_str = f"{ZEN_NUM[to_file]}{KAN_NUM[to_rank]}"
    
    # 駒種
    if move.drop_piece_type:
        piece_type = move.drop_piece_type
    else:
        piece_type = board.piece_at(move.from_square).piece_type
    
    PIECE_MAP = {
        shogi.PAWN: '歩', shogi.LANCE: '香', shogi.KNIGHT: '桂', shogi.SILVER: '銀',
        shogi.GOLD: '金', shogi.BISHOP: '角', shogi.ROOK: '飛', shogi.KING: '玉',
        shogi.PROM_PAWN: 'と', shogi.PROM_LANCE: '成香', shogi.PROM_KNIGHT: '成桂',
        shogi.PROM_SILVER: '成銀', shogi.PROM_BISHOP: '馬', shogi.PROM_ROOK: '龍'
    }
    
    piece_str = PIECE_MAP.get(piece_type, '?')
    
    if move.promotion:
        piece_str += "成"
            
    return f"{to_str}{piece_str}"

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
