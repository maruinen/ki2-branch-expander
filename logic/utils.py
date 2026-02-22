import shogi

def to_bod(board: shogi.Board) -> str:
    """
    shogi.Board オブジェクトを柿木BOD形式の文字列に変換する。
    """
    lines = []
    
    # 後手の持駒
    gote_hand = []
    for piece_type in reversed(shogi.PIECE_TYPES):
        count = board.pieces_in_hand[shogi.WHITE].get(piece_type, 0)
        if count > 0:
            name = shogi.PIECE_JAPANESE_SYMBOLS[piece_type]
            count_str = {1: "", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九"}.get(count, str(count))
            gote_hand.append(f"{name}{count_str}")
    
    lines.append(f"後手の持駒：{'　'.join(gote_hand) if gote_hand else 'なし'}")
    lines.append("  ９ ８ ７ ６ ５ ４ ３ ２ １")
    lines.append("+---------------------------+")
    
    kanji_nums = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
    
    for y in range(1, 10):
        row = "|"
        for x in range(9, 0, -1):
            square = (y - 1) * 9 + (9 - x)
            piece = board.piece_at(square)
            if piece:
                symbol = shogi.PIECE_JAPANESE_SYMBOLS[piece.piece_type]
                prefix = "v" if piece.color == shogi.WHITE else " "
                row += f"{prefix}{symbol}"
            else:
                row += " ・"
        row += f"|{kanji_nums[y]}"
        lines.append(row)
        
    lines.append("+---------------------------+")
    
    # 先手の持駒
    sente_hand = []
    for piece_type in reversed(shogi.PIECE_TYPES):
        count = board.pieces_in_hand[shogi.BLACK].get(piece_type, 0)
        if count > 0:
            name = shogi.PIECE_JAPANESE_SYMBOLS[piece_type]
            count_str = {1: "", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九"}.get(count, str(count))
            sente_hand.append(f"{name}{count_str}")
            
    lines.append(f"先手の持駒：{'　'.join(sente_hand) if sente_hand else 'なし'}")
    # 手数は move_stack のサイズ
    lines.append(f"手数＝{len(board.move_stack)}    まで")
    
    return "\n".join(lines)
