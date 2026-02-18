import shogi
import sys
import re
import argparse
import os
from extract_moves import extract_moves_from_ki2
from logic.expander import expand_tree
from typing import List, Dict

def format_as_ki2_text(tree: List[Dict]) -> str:
    """
    ツリー構造をKI2のテキスト形式に整形する。
    """
    lines = []
    
    def traverse(current_tree: List[Dict], current_depth: int, is_main: bool):
        if not current_tree:
            return
        
        node = current_tree[0]
        move_label = "▲" if current_depth % 2 != 0 else "△"
        lines.append(f"{move_label}{node['ki2_str']}")
        
        traverse(node['branches'], current_depth + 1, True)
        
        for alt_node in current_tree[1:]:
            lines.append(f"\n\n変化：{current_depth}手目\n")
            move_label = "▲" if current_depth % 2 != 0 else "△"
            lines.append(f"{move_label}{alt_node['ki2_str']}")
            traverse(alt_node['branches'], current_depth + 1, False)

    traverse(tree, 1, True)
    text = " ".join(lines).replace(" \n", "\n").replace("\n ", "\n")
    return text

def get_ki2_header(file_path: str) -> str:
    """
    元のKI2ファイルからヘッダー情報を抽出する。
    """
    header_lines = []
    try:
        with open(file_path, 'r', encoding='cp932', errors='replace') as f:
            for line in f:
                stripped = line.strip()
                if not stripped: continue
                # 指し手らしき文字が含まれない行をヘッダーとみなす
                if not (stripped.startswith('▲') or stripped.startswith('△') or stripped.startswith('変化：')):
                    header_lines.append(stripped)
                else:
                    break
    except:
        pass
    return "\n".join(header_lines)

def process_file(input_file: str):
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}_expanded{ext}"
    
    print(f"--- Processing {input_file} ---")
    print(f"Reading...")
    move_map = extract_moves_from_ki2(input_file)
    
    if not move_map:
        print(f"No moves extracted from {input_file}. Skipping.")
        return

    print(f"Expanding branches from {len(move_map)} positions...")
    board = shogi.Board()
    expanded_tree = expand_tree(board, move_map)
    
    print(f"Generating KI2 output...")
    header = get_ki2_header(input_file)
    ki2_text = format_as_ki2_text(expanded_tree)
    
    final_output = header + "\n\n" + ki2_text
    
    try:
        with open(output_file, 'w', encoding='cp932', errors='replace') as f:
            f.write(final_output)
        print(f"Done! Saved to {output_file}")
    except Exception as e:
        print(f"Error saving file: {e}")

def main():
    parser = argparse.ArgumentParser(description="KI2 Branch Expander")
    parser.add_argument("input_files", nargs="*", help="Input KI2 files (defaults to ShogiSekai.ki2 and Test1.ki2 if not provided)")
    
    args = parser.parse_args()
    
    files_to_process = args.input_files
    if not files_to_process:
        # デフォルトのファイル
        for f in ["ShogiSekai.ki2", "Test1.ki2"]:
            if os.path.exists(f):
                files_to_process.append(f)
    
    if not files_to_process:
        print("No input files found.")
        return

    for f in files_to_process:
        process_file(f)

if __name__ == "__main__":
    main()
