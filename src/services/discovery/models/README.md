Created a `DataObject` class to standardize data passing between components. This will help ensure consistent data structure and type safety across the system. Let me create that file:

I've created the `DataObject` class with the following features:

1. **Platform Type Enum**: Defines supported platforms (LinkedIn, Twitter, YouTube, TikTok, Instagram, Reddit, Generic)

2. **Required Fields**:
   - `platform`: The platform the data was scraped from
   - `timestamp`: When the data was collected (defaults to current UTC time)
   - `url`: The URL that was scraped

3. **Optional Fields**:
   - `data`: The actual scraped data
   - `metadata`: Additional metadata about the scraping process
   - `error`: Error message if scraping failed

4. **Utility Methods**:
   - `to_dict()`: Convert to dictionary
   - `from_dict()`: Create from dictionary
   - `is_valid()`: Check if the data is valid
   - Getters for all fields
   - Methods to update/merge data and metadata
   - String representations

5. **Pydantic Integration**:
   - Uses Pydantic for data validation
   - Custom JSON encoders for datetime
   - Field descriptions for documentation

This standardized data object will help ensure:
- Consistent data structure across components
- Type safety through Pydantic validation
- Easy serialization/deserialization
- Clear error handling
- Metadata tracking for monitoring and debugging