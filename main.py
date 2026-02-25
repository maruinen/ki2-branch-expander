import shogi
import sys
import re
import argparse
import os
from extract_moves import extract_moves_from_ki2
from logic.expander import expand_tree
from logic.utils import to_bod
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
        
        # コメントの出力
        for comment in node.get('comments', []):
            lines.append(f"\n*{comment}\n")
        
        traverse(node['branches'], current_depth + 1, True)
        
        for alt_node in current_tree[1:]:
            lines.append(f"\n\n変化：{current_depth}手目\n")
            move_label = "▲" if current_depth % 2 != 0 else "△"
            lines.append(f"{move_label}{alt_node['ki2_str']}")
            
            # 変化の指し手に対するコメント
            for comment in alt_node.get('comments', []):
                lines.append(f"\n*{comment}\n")
                
            traverse(alt_node['branches'], current_depth + 1, False)

    traverse(tree, 1, True)
    # フォーマットの微調整
    text = " ".join(lines).replace(" \n", "\n").replace("\n ", "\n")
    # 連続する改行を整理
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
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
    print(f"Reading and analyzing...")
    move_map, arrival_info = extract_moves_from_ki2(input_file)
    
    if not move_map:
        print(f"No moves extracted from {input_file}. Skipping.")
        return

    # 直前の手が異なる合流ポイントのみを抽出
    initial_sfen = get_board_key(shogi.Board())
    confluence_positions = [
        sfen for sfen, arrivals in arrival_info.items() 
        if len(arrivals) > 1 and sfen != initial_sfen
    ]
    
    print(f"Total unique positions found: {len(arrival_info)}")
    print(f"Number of primary confluence points: {len(confluence_positions)}")
    
    if confluence_positions:
        print("\n--- Primary Confluence Points (Different incoming moves) ---")
        for sfen in confluence_positions:
            board = shogi.Board(sfen)
            side = "先手" if board.turn == shogi.BLACK else "後手"
            print(f"\n[合流局面] 手番: {side}")
            
            # 各到達経路（直前の手）を表示
            for i, (last_move, path) in enumerate(arrival_info[sfen].items(), 1):
                path_str = " ".join(path)
                print(f"  経路 {i}: ... {path_str}")
            
            # 盤面をBOD形式で表示
            print(to_bod(board))
            print("-" * 40)

    print(f"\nExpanding tree branches...")
    board = shogi.Board()
    expanded_tree = expand_tree(board, move_map)
    
    def count_total_moves(tree):
        total = 0
        for node in tree:
            total += 1
            total += count_total_moves(node['branches'])
        return total
    
    print(f"Expansion complete. Total nodes in expanded tree: {count_total_moves(expanded_tree)}")
    
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

def get_board_key(board: shogi.Board) -> str:
    s = board.sfen()
    parts = s.split(' ')
    return " ".join(parts[:3]) + " 1"

def main():
    parser = argparse.ArgumentParser(description="KI2 Branch Expander")
    parser.add_argument("input_files", nargs="*", help="Input KI2 files")
    
    args = parser.parse_args()
    
    files_to_process = args.input_files
    if not files_to_process:
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
