# AGENTS.md - Development Guidelines for booksi

This file contains guidelines and commands for agentic coding agents working in the booksi repository.

## Project Overview

booksi is a Python-based web scraping and data processing tool that extracts, processes, and analyzes adult entertainment listings from websites. The main components include:

- **booksi.py**: Main entry point for data processing pipeline
- **gallib.py**: Core library with HTML parsing, data manipulation, and utility functions
- **pyGals.py**: Web scraping script using wget for data collection
- **booksi.test.py**: Test suite for validation

## Build/Lint/Test Commands

### Running the Application
```bash
# Main data processing pipeline
python booksi.py [options]

# Options:
# -h  Show help
# -v  Verbose output
# -ci Use CSV import instead of HTML analysis (faster for testing)
# -s  Show statistics

# Web scraping data collection
python pyGals.py [options]

# Options:
# -h  Show help
# -i  Include images
# -a  Anal only filtering
# -l  Local tar storage
# -f  Local folder storage
# -t  Test mode (limits to 10 items)
```

### Testing
```bash
# Run specific test file
python booksi.test.py

# Run with verbose output
python -v booksi.test.py

# Test individual functions (example pattern)
python -c "import gallib as gl; print(gl.prune_items('./data', test_mode=True))"
```

### Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Current dependencies:
# - pandas
# - beautifulsoup4
# - tqdm
# - wcwidth
```

## Code Style Guidelines

### Import Organization
```python
# Standard library imports first
import os
import sys
import shutil
from datetime import datetime, timedelta
from collections import defaultdict

# Third-party imports next
import pandas as pd
from bs4 import BeautifulSoup as soup
from tqdm import tqdm
import wcwidth

# Local imports last
import gallib as gl
```

### Naming Conventions
- **Functions**: snake_case (e.g., `prune_items`, `getlastdir`)
- **Variables**: snake_case (e.g., `dir_path`, `lastdir`, `pdall`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `TEST_MODE`, `DEFAULT_PATH`)
- **Classes**: PascalCase (rare in this codebase)
- **File names**: snake_case for Python files (e.g., `booksi.py`, `gallib.py`)

### Type Hints
The codebase doesn't use type hints consistently, but when adding new code:
```python
from typing import List, Dict, Optional, Union

def prune_items(path: str, test_mode: bool = True) -> int:
    # Function implementation
```

### Error Handling
```python
# Use try-except blocks for file operations
try:
    file_handle = open(filename, "r")
    return file_handle
except FileNotFoundError:
    print(f"The file {filename} does not exist!")
    return None

# Use conditional checks for data validation
if not os.path.exists(csv_file):
    print(f"CSV file not found: {csv_file}")
    return None
```

### String Formatting
```python
# Use f-strings for new code
print(f"Processing {count} items in {directory}")

# Existing code uses .format() or % - maintain consistency when modifying
print("     New{0} {1} : Upd{0} {2}".format(old, len(new_sids), len(changed_sids)))
```

### Function Documentation
```python
def function_name(param1: type, param2: type = default) -> return_type:
    """
    Brief description of what the function does.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (optional)
    
    Returns:
        Description of return value
    
    Raises:
        ExceptionType: When error occurs
    """
```

## Data Processing Patterns

### DataFrame Operations
```python
# Standard pattern for data processing
df = pd.DataFrame(data)
df = df.fillna("")  # Replace NaN with empty string
df = df.sort_values(by=["column"], ascending=True)
df = df.groupby(["key_columns"], as_index=False).max()

# Filtering patterns
df = df[~df["column"].str.contains(pattern, na=False)]
df = df[(df["col1"] == "✓") & (df["col2"] == "✓")]
```

### HTML Parsing with BeautifulSoup
```python
from bs4 import BeautifulSoup as soup

# Standard parsing pattern
page_soup = soup(html_content, "html.parser")
elements = page_soup.findAll("div", {"class": "item-class", "data-type": "listing"})

for element in elements:
    text_content = element.find("h4").get_text(strip=True)
    # Process element
```

### File Operations
```python
# Safe file reading
with open(file_path, "r") as file:
    content = file.read()

# Safe file writing
os.makedirs(directory_path, exist_ok=True)
with open(file_path, "w") as file:
    file.write(content)
```

## Configuration Management

### Config File Format (gals.conf)
```ini
[section_name]
key1=value1
key2=value2

[variables]
# Comments are supported
GalsinPage=23
html0=https://example.com/
```

### Reading Config Files
```python
variables = {}
variables_section = False
with open("config.conf", "r") as config_file:
    for line in config_file:
        line = line.strip()
        if line == "[variables]":
            variables_section = True
            continue
        if variables_section and line and not line.startswith("#"):
            key, value = map(str.strip, line.split("=", 1))
            variables[key] = value
```

## Progress Reporting

### Using tqdm for Progress Bars
```python
from tqdm import tqdm

# For file operations
files = os.listdir(directory)
progress_bar = tqdm(total=len(files), desc="Processing", bar_format="{l_bar}", ncols=80)
for file in files:
    # Process file
    progress_bar.update(1)
progress_bar.close()

# For data processing
items = data_list
desc = f"✓ {category}: {len(items)}"
progress_bar = tqdm(total=len(items), desc=desc, bar_format="{l_bar}", ncols=80)
```

## Testing Guidelines

### Test File Structure
```python
# booksi.test.py
import os
import gallib as gl
import pandas as pd

def test_function_name():
    # Test implementation
    expected_result = "expected"
    actual_result = function_under_test()
    assert actual_result == expected_result

# Integration tests
def test_data_processing_pipeline():
    # Test end-to-end functionality
    pass
```

### Running Single Tests
```bash
# Test specific function
python -c "import gallib as gl; result = gl.prune_items('./data', test_mode=True); print(result)"

# Test with sample data
python -c "import pandas as pd; df = pd.read_csv('sample.csv'); print(df.head())"
```

## Security and Data Handling

### Input Validation
```python
# Validate file paths
if not os.path.exists(file_path):
    raise FileNotFoundError(f"File not found: {file_path}")

# Sanitize user input
import re
pattern = re.compile(r"^[a-zA-Z0-9_-]+$")
if not pattern.match(user_input):
    raise ValueError("Invalid input format")
```

### Data Privacy
- Never log or print sensitive personal information
- Use test_mode flags for development
- Sanitize data before output to HTML/CSV

## Performance Considerations

### Memory Management
```python
# Use generators for large datasets
def process_large_file(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            yield process_line(line)

# Optimize DataFrame operations
df = df[required_columns_only]  # Select needed columns early
df = df.astype({'column': 'int32'})  # Use appropriate data types
```

### Caching Patterns
```python
# Cache expensive operations
import functools

@functools.lru_cache(maxsize=128)
def expensive_function(param):
    # Expensive computation
    return result
```

## Common Utilities

### Directory Operations
```python
# Get latest directory
def getlastdir(dir_path):
    directories = [d for d in os.listdir(dir_path) 
                  if os.path.isdir(os.path.join(dir_path, d))]
    return os.path.join(dir_path, sorted(directories, reverse=True)[0])
```

### String Cleaning
```python
# Clean and normalize strings
def clean_string(text):
    if pd.isna(text):
        return ""
    return str(text).strip()
```

## Git Workflow

### Commit Message Style
```
feat: add new data processing feature
fix: resolve HTML parsing issue
refactor: optimize DataFrame operations
test: add unit tests for gallib functions
docs: update AGENTS.md guidelines
```

### Branch Naming
- `feature/dataset-processing`
- `bugfix/html-parsing`
- `refactor/performance-optimization`

## Environment Setup

### Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python booksi.py -v -s
```

### Production Considerations
- Use absolute paths for file operations
- Implement proper logging instead of print statements
- Add error recovery mechanisms
- Monitor memory usage for large datasets