# GEMINI.md

## Project Overview
**Ki2 Branch Expander** is a tool designed to expand and duplicate branches from confluent positions in KI2 shogi files. It's specifically built for KI2 viewers that do not support automatic merging of identical positions (graph view), ensuring that every possible path is explicitly represented in the move tree.

## Main Technologies
- **Language**: Python 3.10+
- **Library**: `python-shogi` (for board simulation and move validation)

## Project Structure
- `main.py`: The primary CLI entry point for processing KI2 files.
- `extract_moves.py`: Contains logic to parse KI2 files and build a mapping of positions to their subsequent moves.
- `logic/expander.py`: Core logic for recursively expanding the move tree while avoiding infinite loops (Sennichite).
- `analyze_confluence.py`: A diagnostic tool to report on the number of confluent positions in a given KI2 file.

## Building and Running
1. **Install dependencies**:
   ```bash
   pip install python-shogi
   ```
2. **Run the expander**:
   ```bash
   python3 main.py [INPUT_FILE ...]
   ```
   Where `[INPUT_FILE ...]` refers to one or more KI2 files to process. If no input files are provided, it defaults to processing `ShogiSekai.ki2` and `Test1.ki2` if they exist in the current directory.
   The tool will output `[INPUT_FILE]_expanded.ki2` for each input file.

   **Example**:
   ```bash
   python3 main.py my_game.ki2 another_game.ki2
   ```
   This will process `my_game.ki2` and `another_game.ki2`, generating `my_game_expanded.ki2` and `another_game_expanded.ki2`.

## Testing
Run the test suite using `unittest`:
```bash
python3 -m unittest discover tests
```

## Development Conventions
- **SFEN-based Identity**: Positions are identified using the board, turn, and hand components of the SFEN string (ignoring move count).
- **Encoding**: KI2 files are typically handled using `cp932` (Shift_JIS).
- **Cycle Detection**: The expander tracks the current path to prevent infinite recursion during tree expansion.

## Development Workflow
1. Create a feature branch: `git checkout -b feature/description`
2. Implement changes with tests
3. Verify all tests pass: `pytest` or `python3 -m unittest discover`
4. Create a Pull Request(PR) with clear description
5. Merge after review/approval

## Tooling
- We have the `gh` command (GitHub CLI) installed and available.
- Use `gh pr create` to create pull requests from the command line.

