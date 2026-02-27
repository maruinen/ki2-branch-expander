# 設計詳細 (Design Document)

このドキュメントでは、Ki2 Branch Expander の核心となるアルゴリズムと内部データ構造について詳述します。

## データ構造

### 局面ハッシュマップ
- **構造**: `dict[str, set[shogi.Move]]`
- **キー**: 局面の SFEN 文字列（盤面、手番、持駒のみを抽出）。
- **値**: その局面から指されたことがある全ての「次の手」の集合。
- **目的**: 異なる経路から到達した同一局面において、既知のすべての分岐を網羅するために使用します。

## 処理プロセス

1. **第一パス（収集フェーズ）**
   - 入力 KI2 をパースし、出現するすべての局面と、そこから指された手をハッシュマップに記録します。
2. **第二パス（再構築フェーズ）**
   - ルート局面から再帰的に探索を開始します。
   - 各局面において、ハッシュマップに登録されている「すべての指し手」を分岐として書き出します。
   - **千日手対策**: 現在の探索パス（ルートからの局面履歴）を保持し、同一経路内で局面が重複した場合は、その指し手での探索を打ち切ります。

## 主要コンポーネント
- `extract_moves.py`: KI2 ファイルを走査し、局面ハッシュマップを構築する責務。
- `logic/expander.py`: ハッシュマップと `python-shogi` のシミュレーションを用いて、新しい指し手ツリーを再帰的に生成する責務。

詳細な使い方は [README.md](README.md) を参照してください。

---
## Historical Technical Insights
*This section contains a log of technical insights gathered over time. It serves as a historical reference.*

### テクニカル・インサイト
- **KI2形式の分岐（変化）に関する制約**:
    - **空行の必要性**: 棋譜再生アプリとの互換性のため、`変化：` で始まる行の直前には必ず空行を挿入する必要がある。
    - **改行の挿入**: 分岐ブロックにおいて、手数を示す行（例：`変化：X手目`）の直後は改行（LFまたはCRLF）が必要である。

### Technical Insights (Updated)
- **KI2 Relative Notation**: Implemented a cascading filter for Right, Left, Straight, Up, Down (引), and Yoru (寄).
  - Black: Right = smaller file, Up = smaller rank.
  - White: Right = larger file, Up = larger rank.
- **Board Copying**: `shogi.Board` objects lack a `.copy()` method. Use `shogi.Board(board.sfen())` to clone a board state.
- **USI Promotion**: Move USI strings for promotion moves include a `+` suffix (e.g., `7g7f+`). Ensure this is accounted for in test expectations.
- **Testing**: Use USI-based board setups in unit tests to avoid dependency on external `.ki2` files.
### 最新のテクニカル・インサイト (2026-02-27)

#### パースとロジックの堅牢化
- **決定論的パースの原則**: 将棋の棋譜表記（KI2）は一意であるべき。確率的なスコアリングや先読み推測を排除し、幾何学的なルール（右・左・上・引など）に基づいた一意な移動元特定ロジックを実装。
- **変化セクションの親局面特定**: 「変化：n手」の親局面は、直前のセクションを遡り、最初に n-1 手目が存在するセクションの局面として一意に特定可能。セクションごとの局面履歴を保持することで正確な分岐を実現。
- **相対表記の厳密な定義**: 「右」は、目的地に行ける駒の中で最も右にある駒（先手：筋の最小値、後手：筋の最大値）を指す。

#### 合流局面の分析
- **合流ポイントの定義**: True Confluence は、同じ局面（SFEN）に「異なる直前の指し手」で到達した瞬間に発生する。
- **分析レポート機能**: 合流局面ごとに、そこに至る複数の経路（直前3手）と盤面状態（BOD形式）を出力することで、ツリーの複雑性を視認可能にした。

#### ライブラリ・形式への対応
- **BOD (柿木板) 形式**: 診断・デバッグ用に SFEN から BOD 形式への変換ユーティリティ (`logic/utils.py`) を実装。
- **python-shogi の手札管理**: `board.pieces_in_hand[color][type]` または `Counter` を使用。SFEN は `shogi.Board` 初期化のために最低4〜6要素が必要。
- **コメントの継承**: 指し手に紐付いたコメント（`*` 行）をパース時に保持し、ブランチ展開時にも各ノードに正しく引き継ぐ仕組みを導入。

### Technical Insights (Session Summary: GitHub Actions & Core Logic Review)

#### GitHub Actions Integration
- **Automation:** Successfully integrated Gemini-powered workflows for issue triaging and PR reviews.
- **Workflow Repository:** Utilizing standard templates from `google-github-actions/run-gemini-cli` to maintain consistency across projects.

#### Core Logic Reinforcement
- **Position Identity:** Reconfirmed that positions must be identified using SFEN (board, turn, hand), ignoring move count, to accurately detect and expand confluent branches.
- **Encoding Management:** Strict adherence to `cp932` (Shift_JIS) for both input and output is mandatory for compatibility with Shogi ecosystem tools.
- **Infinite Recursion Prevention:** The expansion algorithm uses path history tracking to detect and break cycles (Sennichite), ensuring termination in complex game trees.

