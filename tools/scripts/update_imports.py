#!/usr/bin/env python3
import os
import re
from pathlib import Path

def update_imports(directory: str):
    """
    Recursively update import statements from 'services.*' and 'tasks.*' to 'app.services.*' and 'app.tasks.*'
    in all Python files within the given directory.
    """
    # Regular expressions to match import statements
    import_patterns = [
        # services -> app.services
        (r'from\s+services\.', 'from app.services.'),
        (r'import\s+services\.', 'import app.services.'),
        (r'from\s+services\s+import', 'from app.services import'),
        (r'import\s+services\s+as', 'import app.services as'),
        # tasks -> app.tasks
        (r'from\s+tasks\.', 'from app.tasks.'),
        (r'import\s+tasks\.', 'import app.tasks.'),
        (r'from\s+tasks\s+import', 'from app.tasks import'),
        (r'import\s+tasks\s+as', 'import app.tasks as'),
    ]
    
    # Get all Python files in the directory and its subdirectories
    python_files = Path(directory).rglob('*.py')
    
    for file_path in python_files:
        # Skip files in virtual environment or other special directories
        if any(x in str(file_path) for x in ['venv', '.git', '__pycache__', 'migrations']):
            continue
            
        try:
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if the file contains any 'services.' or 'tasks.' imports
            needs_update = any(re.search(pattern, content) for pattern, _ in import_patterns)
            
            if needs_update:
                print(f"Updating imports in: {file_path}")
                
                # Replace the imports
                updated_content = content
                for pattern, replacement in import_patterns:
                    updated_content = re.sub(pattern, replacement, updated_content)
                
                # Write the updated content back to the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                print(f"✓ Updated imports in: {file_path}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

if __name__ == "__main__":
    # Get the project root directory (assuming this script is in the scripts directory)
    project_root = Path(__file__).parent.parent
    
    print("Starting import path updates...")
    update_imports(str(project_root))
    print("Import path updates completed!") 