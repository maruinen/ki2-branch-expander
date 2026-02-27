# GEMINI.md (Updated)

## 1. プロジェクトの目的
**Ki2 Branch Expander** は、合流した局面（同じ局面が異なる手順で現れる場合）を検出し、その局面から続く指し手をすべての経路に対して展開（複製）することで、再生アプリがグラフ表示（自動合流）をサポートしていなくても全分岐を表示可能にする。

## 2. 核心アーキテクチャ（2フェーズ・パス）
1.  **第一パス（収集）**: `extract_moves.py`
    - 元のKI2ファイルを走査し、すべての出現局面（SFENキー）とその局面から指された「次の手（USI形式）」の集合を構築。
    - メインラインだけでなく「変化：」で始まるすべての分岐を独立した手順としてシミュレートし、盤面状態の正確さを維持。
    - 相対表記（右、左、上、引、寄、直）を部分的にサポート。
2.  **第二パス（展開）**: `logic/expander.py`
    - 初期局面から `move_map` を用いて再帰的にツリーを構築。
    - 異なる手順でも同じ局面（SFEN）にたどり着けば、その局面以降のすべての分岐を再度展開。
    - 循環（千日手）は `path_history` により検出して停止。

## 3. 実装上の注意点
- **文字コード**: 出力は `cp932` (Shift_JIS) を推奨（将棋ソフトとの互換性のため）。
- **指し手のパース**: 指し手の抽出とパースを分離し、`legal_moves` から候補を絞り込む手法を採用。
- **デバッグ**: `Total moves found` と `Successfully parsed` の比率を監視し、パース失敗による盤面同期ずれを検知。

## 4. プログラム構成
- `main.py`: CLIエントリポイント。ファイルヘッダーの維持と複数ファイルのバッチ処理。
- `extract_moves.py`: KI2パーサーと局面ハッシュマップ生成。
- `logic/expander.py`: ツリー展開とKI2文字列生成（`get_ki2_move_str` を含む）。

## 5. テクニカル・インサイト
- **KI2形式の分岐（変化）に関する制約**:
    - **空行の必要性**: 棋譜再生アプリとの互換性のため、`変化：` で始まる行の直前には必ず空行を挿入する必要がある。
    - **改行の挿入**: 分岐ブロックにおいて、手数を示す行（例：`変化：X手目`）の直後は改行（LFまたはCRLF）が必要である。

## 6. Technical Insights (Updated)
- **KI2 Relative Notation**: Implemented a cascading filter for Right, Left, Straight, Up, Down (引), and Yoru (寄).
  - Black: Right = smaller file, Up = smaller rank.
  - White: Right = larger file, Up = larger rank.
- **Board Copying**: `shogi.Board` objects lack a `.copy()` method. Use `shogi.Board(board.sfen())` to clone a board state.
- **USI Promotion**: Move USI strings for promotion moves include a `+` suffix (e.g., `7g7f+`). Ensure this is accounted for in test expectations.
- **Testing**: Use USI-based board setups in unit tests to avoid dependency on external `.ki2` files.
## 7. 最新のテクニカル・インサイト (2026-02-27)

### パースとロジックの堅牢化
- **決定論的パースの原則**: 将棋の棋譜表記（KI2）は一意であるべき。確率的なスコアリングや先読み推測を排除し、幾何学的なルール（右・左・上・引など）に基づいた一意な移動元特定ロジックを実装。
- **変化セクションの親局面特定**: 「変化：n手」の親局面は、直前のセクションを遡り、最初に n-1 手目が存在するセクションの局面として一意に特定可能。セクションごとの局面履歴を保持することで正確な分岐を実現。
- **相対表記の厳密な定義**: 「右」は、目的地に行ける駒の中で最も右にある駒（先手：筋の最小値、後手：筋の最大値）を指す。

### 合流局面の分析
- **合流ポイントの定義**: True Confluence は、同じ局面（SFEN）に「異なる直前の指し手」で到達した瞬間に発生する。
- **分析レポート機能**: 合流局面ごとに、そこに至る複数の経路（直前3手）と盤面状態（BOD形式）を出力することで、ツリーの複雑性を視認可能にした。

### ライブラリ・形式への対応
- **BOD (柿木板) 形式**: 診断・デバッグ用に SFEN から BOD 形式への変換ユーティリティ (`logic/utils.py`) を実装。
- **python-shogi の手札管理**: `board.pieces_in_hand[color][type]` または `Counter` を使用。SFEN は `shogi.Board` 初期化のために最低4〜6要素が必要。
- **コメントの継承**: 指し手に紐付いたコメント（`*` 行）をパース時に保持し、ブランチ展開時にも各ノードに正しく引き継ぐ仕組みを導入。

## 8. Technical Insights (Session Summary: GitHub Actions & Core Logic Review)

### GitHub Actions Integration
- **Automation:** Successfully integrated Gemini-powered workflows for issue triaging and PR reviews.
- **Workflow Repository:** Utilizing standard templates from `google-github-actions/run-gemini-cli` to maintain consistency across projects.

### Core Logic Reinforcement
- **Position Identity:** Reconfirmed that positions must be identified using SFEN (board, turn, hand), ignoring move count, to accurately detect and expand confluent branches.
- **Encoding Management:** Strict adherence to `cp932` (Shift_JIS) for both input and output is mandatory for compatibility with Shogi ecosystem tools.
- **Infinite Recursion Prevention:** The expansion algorithm uses path history tracking to detect and break cycles (Sennichite), ensuring termination in complex game trees.
