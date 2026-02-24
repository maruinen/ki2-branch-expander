import os
import re
import sys

def bundle():
    files = [
        'extract_moves.py',
        'logic/expander.py',
        'logic/utils.py',
        'main.py'
    ]
    
    output_file = 'ki2_expander_portable.py'
    
    all_content = []
    all_imports = set()
    
    # Local imports to remove
    local_imports = [
        r'from extract_moves import .*',
        r'from logic\.expander import .*',
        r'from logic\.utils import .*',
        r'import extract_moves',
        r'import logic\.expander',
        r'import logic\.utils'
    ]
    
    for file_path in files:
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found.")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        content_lines = []
        for line in lines:
            # Collect non-local imports
            if line.startswith('import ') or line.startswith('from '):
                is_local = False
                for pattern in local_imports:
                    if re.match(pattern, line):
                        is_local = True
                        break
                if not is_local:
                    all_imports.add(line.strip())
                continue
            
            # Remove __main__ block except for main.py
            if 'if __name__ == "__main__":' in line and file_path != 'main.py':
                break
            
            content_lines.append(line)
            
        all_content.append(f"\n# --- Content from {file_path} ---\n")
        all_content.extend(content_lines)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#!/usr/bin/env python3\n")
        f.write("# Ki2 Branch Expander - Portable Version\n\n")
        f.write("\n".join(sorted(list(all_imports))))
        f.write("\n\n")
        
        # Add dependency check
        f.write("import sys\ntry:\n    import shogi\nexcept ImportError:\n")
        f.write("    print('Error: python-shogi is not installed.')\n")
        f.write("    print('Please run: pip install python-shogi')\n")
        f.write("    sys.exit(1)\n\n")
        
        f.writelines(all_content)

    print(f"Successfully bundled into {output_file}")

if __name__ == "__main__":
    bundle()
