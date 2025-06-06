# Utilities

This directory contains utility modules and helper functions used across the application.

## Contents

- `base_script.py`: Base class for command-line scripts
- Other utility modules

## Usage

### Base Script

The `base_script.py` module provides a base class for command-line scripts:

```python
from utils.base_script import BaseScript

class MyScript(BaseScript):
    def run(self):
        # Script implementation
        pass

if __name__ == "__main__":
    MyScript().run()
```

## Adding New Utilities

When adding new utility modules:
1. Keep them focused and single-purpose
2. Add proper documentation
3. Include unit tests
4. Update this README with usage examples