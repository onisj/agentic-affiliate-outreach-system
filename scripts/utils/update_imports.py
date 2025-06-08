#!/usr/bin/env python3
import os
import re
from pathlib import Path

def update_imports(directory: str):
    """Update import statements in all Python files."""
    # Patterns to replace
    patterns = [
        (r'from\s+app\.services\.', 'from services.'),
        (r'from\s+app\.services\s+import', 'from services import'),
        (r'import\s+app\.services\.', 'import services.'),
        (r'import\s+app\.services\s+as', 'import services as')
    ]
    
    # Walk through directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                update_file_imports(file_path, patterns)

def update_file_imports(file_path: str, patterns: list):
    """Update import statements in a single file."""
    try:
        # Read file
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Apply patterns
        new_content = content
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, new_content)
            
        # Write back if changes were made
        if new_content != content:
            with open(file_path, 'w') as f:
                f.write(new_content)
            print(f"Updated imports in {file_path}")
            
    except Exception as e:
        print(f"Error updating {file_path}: {str(e)}")

if __name__ == '__main__':
    # Update imports in src directory
    src_dir = Path(__file__).parent.parent.parent / 'src'
    update_imports(str(src_dir))
    
    # Update imports in tests directory
    tests_dir = Path(__file__).parent.parent.parent / 'tests'
    update_imports(str(tests_dir))
    
    # Update imports in scripts directory
    scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
    update_imports(str(scripts_dir)) 