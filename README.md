# Ki2 Branch Expander

**Ki2 Branch Expander** is a specialized tool for Shogi enthusiasts and developers. It expands and duplicates branches from confluent positions in KI2 format Shogi kifu (game record) files.

## Overview

Many KI2 viewers do not support automatic merging of identical positions (graph view) and instead expect a strict tree structure. In complex kifu with many variations, different paths often lead to the same board position (confluence).

This tool:
1.  Parses KI2 files.
2.  Identifies all reachable positions and their subsequent moves.
3.  Recursively expands the move tree so that every possible path is explicitly represented, even if they pass through identical positions.
4.  Outputs a new KI2 file with fully expanded branches.

## Key Features

-   **SFEN-based Position Identity**: Uses board state, turn, and hand (from SFEN) to accurately identify identical positions regardless of the move sequence taken to reach them.
-   **Full Relative Notation Support**: Correctly handles and generates KI2 relative notations like `右`, `左`, `直`, `寄`, `上`, `引`, and `打`.
-   **Promotion Logic**: Supports `成` (promotion) and `不成` (non-promotion) notation.
-   **Cycle Detection**: Tracks the current path to prevent infinite recursion in case of Sennichite (repetition).
-   **Header Preservation**: Maintains kifu header information such as player names and game titles.
-   **CLI Interface**: Process multiple files easily via command line.

## Requirements

-   Python 3.10 or higher
-   `python-shogi` library

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/maruinen/ki2-branch-expander.git
    cd ki2-branch-expander
    ```

2.  Install the dependencies:
    ```bash
    pip install python-shogi
    ```

## Usage

Run the expander by providing one or more input KI2 files:

```bash
python3 main.py input_file.ki2 [another_file.ki2 ...]
```

-   The tool will generate a new file named `[filename]_expanded.ki2` for each input.
-   If no input files are provided, it defaults to searching for `ShogiSekai.ki2` and `Test1.ki2` in the current directory.

### Example

```bash
python3 main.py my_game.ki2
```
This will create `my_game_expanded.ki2`.

## Project Structure

-   `main.py`: CLI entry point and KI2 formatting logic.
-   `extract_moves.py`: KI2 parsing and move extraction logic.
-   `logic/expander.py`: Core recursive tree expansion and notation generation logic.

## Encoding

This tool handles KI2 files using `cp932` (Shift_JIS) encoding, which is the standard for most Japanese Shogi software.

## Contributing

1.  Create a feature branch: `git checkout -b feature/description`
2.  Implement changes with tests.
3.  Verify all tests pass: `python3 -m unittest discover`
4.  Create a Pull Request with a clear description.
5.  Merge after review/approval.
