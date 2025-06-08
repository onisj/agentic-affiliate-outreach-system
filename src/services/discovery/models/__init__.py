"""
Data Object Model

This package defines the DataObject class for standardized data passing between components,
along with a PlatformType enum for supported platforms.
"""

from .data_object import DataObject, PlatformType

__all__ = [
    "DataObject",
    "PlatformType",
]

__version__ = "1.0.0"