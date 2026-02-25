import unittest
import shogi
from extract_moves import parse_ki2_move

class TestParser(unittest.TestCase):
    def test_parse_ki2_move_basic(self):
        board = shogi.Board()
        # 76-fu
        move = parse_ki2_move(board, "▲７六歩")
        self.assertIsNotNone(move)
        self.assertEqual(move.usi(), "7g7f")

    def test_parse_ki2_move_dou(self):
        board = shogi.Board()
        board.push_usi("7g7f")
        board.push_usi("3c3d")
        board.push_usi("8h2b") # B*8h2b+
        
        # △同銀 (G*3a2b)
        move = parse_ki2_move(board, "△同　銀")
        self.assertIsNotNone(move)
        self.assertEqual(move.usi(), "3a2b")

    def test_parse_ki2_move_promote(self):
        board = shogi.Board()
        board.push_usi("7g7f")
        board.push_usi("3c3d")
        # ▲22-kaku-naru
        move = parse_ki2_move(board, "▲２二角成")
        self.assertIsNotNone(move)
        self.assertEqual(move.usi(), "8h2b+")
        self.assertTrue(move.promotion)

if __name__ == '__main__':
    unittest.main()
