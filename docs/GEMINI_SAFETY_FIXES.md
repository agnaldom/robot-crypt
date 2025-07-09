# Gemini Safety Filter Fixes

This document describes the fixes implemented to handle Gemini API safety filter issues in the Robot-Crypt project.

## Problems Addressed

1. **Safety Filter Blocking**: Gemini's safety filters were blocking legitimate cryptocurrency market analysis
2. **JSON Parsing Errors**: LLM responses contained malformed JSON that couldn't be parsed
3. **Missing Fallback Mechanisms**: No graceful degradation when LLM services fail

## Solutions Implemented

### 1. Configurable Safety Settings

**File**: `src/ai/llm_client.py`

Added configurable safety settings for Gemini API that can be controlled via environment variables:

```python
# Safety settings for Gemini (configurable via environment variables)
self.gemini_safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": os.getenv("GEMINI_SAFETY_HARASSMENT", "BLOCK_ONLY_HIGH")
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH", 
        "threshold": os.getenv("GEMINI_SAFETY_HATE_SPEECH", "BLOCK_ONLY_HIGH")
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": os.getenv("GEMINI_SAFETY_SEXUALLY_EXPLICIT", "BLOCK_ONLY_HIGH")
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": os.getenv("GEMINI_SAFETY_DANGEROUS_CONTENT", "BLOCK_ONLY_HIGH")
    }
]
```

### 2. Automatic Retry with Relaxed Settings

When safety filters block a request, the system now automatically retries with more relaxed settings:

```python
# Try with more relaxed safety settings
relaxed_safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    # ... other categories with BLOCK_NONE
]
```

### 3. Improved JSON Parsing

**File**: `src/ai/llm_client.py`

Added robust JSON parsing with multiple fallback strategies:

- Remove markdown code blocks
- Fix unquoted property names
- Convert single quotes to double quotes
- Remove trailing commas
- Fix boolean values

### 4. Heuristic Fallback Analysis

**File**: `src/ai/news_analyzer.py`

Implemented `_create_fallback_analysis()` method that uses keyword-based heuristics when LLM fails:

```python
def _create_fallback_analysis(self, news_items: List[CryptoNewsItem], symbol: Optional[str]) -> NewsAnalysis:
    """Create fallback analysis using simple heuristics when LLM fails"""
    # Uses keyword matching for sentiment analysis
    positive_keywords = ['bull', 'bullish', 'up', 'surge', 'gain', ...]
    negative_keywords = ['bear', 'bearish', 'down', 'crash', 'loss', ...]
```

### 5. Enhanced Error Handling

Added specific error handling for different failure modes:

- Safety filter blocking
- JSON parsing errors
- Network timeouts
- API rate limiting

## Configuration

### Environment Variables

Add these to your `.env` file to configure Gemini safety settings:

```bash
# Gemini safety settings: BLOCK_NONE, BLOCK_ONLY_HIGH, BLOCK_MEDIUM_AND_ABOVE, BLOCK_LOW_AND_ABOVE
GEMINI_SAFETY_HARASSMENT=BLOCK_ONLY_HIGH
GEMINI_SAFETY_HATE_SPEECH=BLOCK_ONLY_HIGH
GEMINI_SAFETY_SEXUALLY_EXPLICIT=BLOCK_ONLY_HIGH
GEMINI_SAFETY_DANGEROUS_CONTENT=BLOCK_ONLY_HIGH
```

### Safety Threshold Options

- `BLOCK_NONE`: No blocking (most permissive)
- `BLOCK_ONLY_HIGH`: Block only high-risk content
- `BLOCK_MEDIUM_AND_ABOVE`: Block medium and high-risk content
- `BLOCK_LOW_AND_ABOVE`: Block all flagged content (most restrictive)

## Testing

Run the test script to verify the fixes:

```bash
python test_gemini_fixes.py
```

This will test:
1. JSON formatting fixes
2. News analysis with fallback
3. Safety filter handling

## Best Practices

1. **Use Conservative Settings**: Start with `BLOCK_ONLY_HIGH` and adjust as needed
2. **Monitor Logs**: Watch for safety filter warnings in logs
3. **Test Regularly**: Run tests after configuration changes
4. **Fallback Ready**: Ensure fallback analysis provides meaningful results

## Troubleshooting

### Common Issues

1. **Still Getting Blocked**: Try setting safety thresholds to `BLOCK_NONE` for testing
2. **JSON Errors**: Check that prompts are clear about JSON format requirements
3. **Low Confidence**: Fallback analysis will have lower confidence scores (0.3 vs 0.7+)

### Log Messages to Watch For

```
WARNING - Gemini response blocked by safety filters (finish_reason: 2)
INFO - Retrying with relaxed safety settings...
WARNING - Analysis blocked by LLM safety filters
INFO - Fallback heuristic analysis activated
```

## Future Improvements

1. **Machine Learning Fallback**: Train a local model for sentiment analysis
2. **Multi-Provider Routing**: Automatically switch to different LLM providers
3. **Cached Responses**: Cache successful analysis to reduce API calls
4. **Custom Safety Categories**: Define project-specific safety categories

## Dependencies

- `google-generativeai` - Gemini API client
- `asyncio` - Async support
- `json` - JSON parsing
- `re` - Regular expressions for text processing
