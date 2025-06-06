#!/usr/bin/env python3
"""
Base Script Class

This module provides a base class for all scripts with common functionality:
- Configuration management
- Logging setup
- Error handling
- Database session management
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from database.session import get_db
from config.settings import settings

class BaseScript:
    def __init__(self, script_name: str):
        self.script_name = script_name
        self._setup_logging()
        self.logger = logging.getLogger(script_name)

    def _setup_logging(self):
        """Configure logging for the script."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f"logs/{self.script_name}.log")
            ]
        )

    @contextmanager
    def get_db_session(self):
        """Get a database session with automatic cleanup."""
        session = next(get_db())
        try:
            yield session
        finally:
            session.close()

    def run(self):
        """Main execution method to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement run()")

    def handle_error(self, error: Exception):
        """Handle script errors consistently."""
        self.logger.error(f"Error in {self.script_name}: {str(error)}", exc_info=True)
        sys.exit(1)

    def main(self):
        """Entry point for the script."""
        try:
            self.run()
        except Exception as e:
            self.handle_error(e) 