import unittest
import shogi
from logic.expander import get_ki2_move_str, expand_tree
from extract_moves import get_board_key

class TestExpander(unittest.TestCase):
    def test_get_ki2_move_str_basic(self):
        board = shogi.Board()
        # 76-fu (P*7g7f)
        move = shogi.Move.from_usi("7g7f")
        ki2_str = get_ki2_move_str(board, move)
        self.assertEqual(ki2_str, "７六歩")

    def test_get_ki2_move_str_dou(self):
        board = shogi.Board()
        board.push_usi("7g7f")
        board.push_usi("3c3d")
        # 22-kaku-naru (B*8h2b+)
        move = shogi.Move.from_usi("8h2b")
        board.push(move)
        
        # Next move is "Dou" (same square)
        # 22-dou-gin (G*3a2b)
        move_dou = shogi.Move.from_usi("3a2b")
        ki2_str = get_ki2_move_str(board, move_dou)
        self.assertEqual(ki2_str, "同　銀")

    def test_expand_tree_simple(self):
        board = shogi.Board()
        # Mock move_map: { sfen_key: { usi: comments } }
        sfen_start = get_board_key(board)
        move_map = {
            sfen_start: {
                "7g7f": ["Start with pawn"],
                "2g2f": []
            }
        }
        
        tree = expand_tree(board, move_map)
        self.assertEqual(len(tree), 2)
        moves = [t['ki2_str'] for t in tree]
        self.assertIn("７六歩", moves)
        self.assertIn("２六歩", moves)

if __name__ == '__main__':
    unittest.main()
