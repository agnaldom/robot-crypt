# Symbol Normalization Fix

## Problem Description

The system was experiencing API errors with symbol formatting, particularly with symbols containing "/" or special characters. The Binance API requires specific symbol formatting and rejects requests with illegal characters in the `symbol` parameter.

## Common Issues Resolved

1. **URL-encoded characters**: `BTC%2FUSDT` → `BTCUSDT`
2. **Forward slashes**: `BTC/USDT` → `BTCUSDT`
3. **Quoted strings**: `"ETHUSDT"` → `ETHUSDT`
4. **Array notation**: `["BNBUSDT"]` → `BNBUSDT`
5. **Special characters**: Control characters, backslashes, tabs, etc.
6. **Mixed case**: `btc/usdt` → `BTCUSDT`
7. **Whitespace**: Leading/trailing spaces removed

## Solution Implemented

### New Functions Added

1. **`normalize_symbol(symbol)`**: Core normalization function
   - Handles URL decoding
   - Removes illegal characters
   - Validates symbol length (3-20 characters)
   - Converts to uppercase
   - Returns normalized symbol or raises `ValueError`

2. **`sanitize_symbol(symbol)`**: Safe wrapper function
   - Calls `normalize_symbol()`
   - Returns `None` on errors instead of raising exceptions
   - Logs errors for debugging

3. **Updated `format_symbol(symbol)`**: Now uses `normalize_symbol()`

### API Integration

All Binance API methods now include symbol validation:

- `get_ticker_price()`
- `get_klines()`
- `create_order()`
- `get_order()`
- `cancel_order()`
- `get_24hr_ticker()`

Both old and new Binance client implementations have been updated.

## Usage Examples

```python
from src.utils.utils import normalize_symbol, sanitize_symbol

# Basic usage
symbol = normalize_symbol("BTC/USDT")  # Returns "BTCUSDT"

# Safe usage (returns None on error)
symbol = sanitize_symbol("invalid/symbol/format")  # Returns None

# Handle problematic input
symbols = [
    "BTC%2FUSDT",     # URL encoded
    '"ETHUSDT"',      # JSON string
    "['BNBUSDT']",    # Array notation
    "BTC/USDT ",      # Trailing space
]

normalized = [sanitize_symbol(s) for s in symbols]
# Returns: ["BTCUSDT", "ETHUSDT", "BNBUSDT", "BTCUSDT"]
```

## Character Handling

### Removed Characters
- Forward slashes (`/`)
- Backslashes (`\`)
- Quotes (`"`, `'`)
- Brackets (`[`, `]`)
- URL encoding (`%22`, `%27`, `%2F`, `%5C`)
- Control characters (`\x00-\x1F`, `\x7F-\x9F`)
- Whitespace (spaces, tabs, newlines)
- All non-alphanumeric characters

### Validation Rules
- Minimum length: 3 characters
- Maximum length: 20 characters
- Only letters and numbers allowed
- Automatically converted to uppercase

## Error Handling

### `normalize_symbol()` Errors
- Raises `ValueError` for invalid input
- Specific error messages for debugging

### `sanitize_symbol()` Safety
- Returns `None` for invalid input
- Logs errors with context
- Never raises exceptions

## Testing

Run the test suite to verify functionality:

```bash
python test_symbol_normalization.py
```

The test covers:
- Basic symbol formatting
- URL encoding scenarios
- Special character handling
- Error cases
- API integration scenarios

## Benefits

1. **Prevents API Errors**: No more "illegal characters in parameter 'symbol'" errors
2. **Robust Input Handling**: Accepts various input formats
3. **Consistent Output**: Always returns proper Binance format
4. **Error Prevention**: Validates symbols before API calls
5. **Debugging Support**: Detailed error logging
6. **Backward Compatible**: Existing code continues to work

## Migration Notes

- Existing `format_symbol()` calls continue to work
- New validation may catch previously unnoticed invalid symbols
- Check logs for any symbols that fail validation
- Use `sanitize_symbol()` for user input that might be invalid

## Files Modified

- `src/utils/utils.py`: Added normalization functions
- `src/api/binance_api.py`: Added validation to all symbol-using methods
- `src/api/binance/client.py`: Added validation to new client methods
- `test_symbol_normalization.py`: Comprehensive test suite

This fix ensures that all symbol parameters sent to the Binance API are properly formatted and contain only valid characters, eliminating the "illegal characters in parameter 'symbol'" errors.
