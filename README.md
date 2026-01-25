# booksi

A Python-based web scraping and data processing tool that extracts, processes, and analyzes adult entertainment listings from websites.

## Overview

booksi automates the collection and processing of listing data from websites, providing clean CSV and HTML output for analysis. The system consists of:

- **Data Collection**: Web scraping using wget with configurable options
- **Data Processing**: HTML parsing, data extraction, and CSV generation
- **Analysis**: Statistical reporting and HTML table generation

## Installation

1. Clone the repository:
```bash
git clone git@github.com:flabbrgastr/booksusi.git
cd booksusi
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure scraping settings in `gals.conf`

## Usage

### Web Scraping
```bash
# Basic scraping
python pyGals.py

# With options
python pyGals.py -i    # Include images
python pyGals.py -a    # Anal only filtering
python pyGals.py -t    # Test mode (limits to 10 items)
python pyGals.py -l    # Local tar storage
python pyGals.py -f    # Local folder storage
```

### Data Processing
```bash
# Process HTML data and generate outputs
python booksi.py

# With options
python booksi.py -v     # Verbose output
python booksi.py -ci    # Use CSV import instead of HTML analysis
python booksi.py -s     # Show statistics
```

### Testing
```bash
# Run test suite
python booksi.test.py

# Test individual functions
python -c "import gallib as gl; print(gl.prune_items('./data', test_mode=True))"
```

## Configuration

Edit `gals.conf` to customize:
- Target URLs and scraping parameters
- Number of listings per page
- Storage locations and retention periods

Example configuration:
```ini
[variables]
GalsinPage=23
html0=https://example.com/service/
html2=/?&city=wien&page=
N=+15
```

## Output

The system generates:
- `all.csv`: Cleaned and processed data
- `all.html`: Interactive HTML table with sorting
- Statistical summaries and analytics

## Development

See `AGENTS.md` for detailed development guidelines, coding standards, and testing procedures.

## Git Setup

For first-time setup:

```bash
# Generate SSH key
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Add SSH key to agent
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_rsa

# Copy public key and add to GitHub
clip < ~/.ssh/id_rsa.pub

# Test connection
ssh -T git@github.com

# Initialize repository
git init
git remote add origin git@github.com:flabbrgastr/booksusi.git
git fetch

# Check available branches
git branch -v -a
```
