# Data Object Model

## Overview

The Data Object Model is a Python package that defines the `DataObject` class to standardize data passing between components in scraping and analysis pipelines. The `DataObject` class ensures a consistent data structure, type safety, and robust error handling across the system. It includes a `PlatformType` enum to specify supported social media platforms and generic websites, and leverages Pydantic for data validation and serialization.

The `DataObject` class was created to provide a unified way to handle scraped data, ensuring compatibility and reliability across different components. It supports a variety of platforms and includes utility methods for easy data manipulation, serialization, and validation.

## Features

- **Standardized Data Structure**: The `DataObject` class provides a consistent format for scraped data, including platform, timestamp, URL, data, metadata, and error fields.
- **Platform Support**: The `PlatformType` enum supports LinkedIn, Twitter, YouTube, TikTok, Instagram, Reddit, and generic websites.
- **Data Validation**: Leverages Pydantic for type-safe data validation and serialization.
- **Flexible Data Manipulation**: Methods to update, merge, and retrieve data and metadata.
- **Error Handling**: Tracks and reports scraping errors with optional error messages.
- **Serialization**: Supports conversion to and from dictionaries with JSON-compatible datetime encoding.
- **Metadata Tracking**: Allows adding metadata for monitoring and debugging purposes.

### Why DataObject?

The `DataObject` class was designed to address the need for a standardized data structure in scraping pipelines. Its key benefits include:

- **Consistent Data Structure**: Ensures all components use the same data format, reducing integration issues.
- **Type Safety**: Pydantic validation enforces correct data types and structures.
- **Easy Serialization/Deserialization**: Simplifies data exchange between components and storage systems.
- **Clear Error Handling**: Captures and reports errors to facilitate debugging.
- **Metadata Tracking**: Supports monitoring and debugging by storing additional context about the scraping process.


## Dependencies

The package relies on the following Python libraries:

- `pydantic`
- `typing`


## Usage

### Importing Modules

```python
from data_object_model import DataObject, PlatformType
```

### Example: Creating a DataObject

```python
from data_object_model import DataObject, PlatformType
from datetime import datetime

# Create a DataObject instance
data_obj = DataObject(
    platform=PlatformType.LINKEDIN,
    url="https://www.linkedin.com/in/example-profile",
    data={
        "name": "John Doe",
        "headline": "Software Engineer"
    },
    metadata={
        "scraper_version": "1.0",
        "request_id": "abc123"
    }
)

# Add metadata
data_obj.add_metadata("scraped_by", "MyScraper")

# Update data
data_obj.update_data("location", "San Francisco")

# Check validity
print(data_obj.is_valid())  # True

# Convert to dictionary
print(data_obj.to_dict())

# String representation
print(data_obj)
```

### Example: Handling Errors

```python
# Create a DataObject with an error
data_obj = DataObject(
    platform=PlatformType.TWITTER,
    url="https://twitter.com/invalid-profile",
    error="Profile not found"
)

# Check validity
print(data_obj.is_valid())  # False

# Get error message
print(data_obj.get_error())  # "Profile not found"
```

## Modules

### data_object.py
Defines the `DataObject` class and `PlatformType` enum. The `DataObject` class includes:

1. **Platform Type Enum**:
   - Defines supported platforms: LinkedIn, Twitter, YouTube, TikTok, Instagram, Reddit, Generic.

2. **Required Fields**:
   - `platform`: The platform the data was scraped from (type: `PlatformType`).
   - `timestamp`: When the data was collected (defaults to current UTC time, type: `datetime`).
   - `url`: The URL that was scraped (type: `str`).

3. **Optional Fields**:
   - `data`: The actual scraped data (type: `Dict[str, Any]`, default: empty dict).
   - `metadata`: Additional metadata about the scraping process (type: `Dict[str, Any]`, default: empty dict).
   - `error`: Error message if scraping failed (type: `Optional[str]`, default: None).

4. **Utility Methods**:
   - `to_dict()`: Convert the `DataObject` to a dictionary.
   - `from_dict()`: Create a `DataObject` from a dictionary.
   - `is_valid()`: Check if the data is valid (no error and non-empty data).
   - Getters: `get_platform()`, `get_timestamp()`, `get_url()`, `get_data()`, `get_metadata()`, `get_error()`.
   - Modifiers: `set_error()`, `add_metadata()`, `update_data()`, `merge_data()`, `merge_metadata()`.
   - String representations: `__str__()` and `__repr__()` for concise and detailed output.

5. **Pydantic Integration**:
   - Uses Pydantic for robust data validation and serialization.
   - Custom JSON encoders for datetime fields (ISO format).
   - Field descriptions for better documentation and introspection.

## Configuration

No additional configuration is required. The `DataObject` class uses Pydantic's default configuration, with custom JSON encoding for datetime fields.

## Error Handling

The `DataObject` class includes an `error` field to store error messages if scraping fails. The `is_valid()` method checks for the absence of errors and the presence of data, making it easy to verify the integrity of the object.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

