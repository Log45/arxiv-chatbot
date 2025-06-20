# Improved arXiv Paper Downloader

This project provides improved functions for downloading arXiv papers with proper error handling, retry logic, and rate limiting to prevent connection reset errors.

## Problem Solved

The original code was encountering `ConnectionResetError` when trying to download many papers at once from arXiv. This happens because:

1. **Rate Limiting**: arXiv has rate limits to prevent server overload
2. **Connection Limits**: Too many simultaneous connections can cause the server to reset connections
3. **No Error Handling**: The original code didn't handle network errors gracefully

## Solution

The improved functions include:

- **Retry Logic**: Automatic retry with exponential backoff
- **Rate Limiting**: Delays between downloads to respect server limits
- **Error Handling**: Graceful handling of network errors
- **Progress Tracking**: Clear feedback on download progress
- **Configurable Limits**: Control how many papers to download

## Files

- `utils.py`: Contains all the improved functions
- `main.py`: Example script showing how to use the functions
- `test_improved.py`: Test script for Jupyter notebooks
- `test.ipynb`: Original notebook (for reference)

## Usage

### Option 1: Run the main script
```bash
python main.py
```

### Option 2: Use in Jupyter notebook
```python
# Import the improved functions
from utils import search_arxiv_simple, arxiv_to_faiss

# Create a search
search = search_arxiv_simple("transformer", max_results=10)

# Download and create FAISS database (limit to 5 papers)
db = arxiv_to_faiss(search=search, max_papers=5)
```

### Option 3: Use the test function
```python
from test_improved import test_improved_download
db = test_improved_download()
```

## Key Improvements

1. **`download_paper_with_retry()`**: Downloads a single paper with retry logic
2. **`save_arxiv_results()`**: Downloads multiple papers with error handling
3. **`arxiv_to_documents()`**: Processes downloaded papers into documents
4. **`arxiv_to_faiss()`**: Creates FAISS database from documents

## Configuration

You can adjust these parameters:

- `max_papers`: Maximum number of papers to download (default: 10)
- `max_retries`: Number of retry attempts per paper (default: 3)
- `delay`: Base delay between downloads in seconds (default: 2.0)

## Example Output

```
Testing improved arXiv download with error handling...
Starting download...
Successfully downloaded: Attention Is All You Need
Successfully downloaded: BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
Successfully downloaded: GPT-2: Language Models are Unsupervised Multitask Learners
Successfully downloaded 3 out of 3 papers
Successfully loaded 3 documents from directory
Split into 45 chunks
✅ Success! Database created with 45 vectors
```

## Troubleshooting

If you still encounter issues:

1. **Reduce `max_papers`**: Try downloading fewer papers at once
2. **Increase `delay`**: Add more time between downloads
3. **Check internet connection**: Ensure stable network connection
4. **Try different search terms**: Some papers might not be available

## Dependencies

Make sure you have these packages installed:
```bash
pip install arxiv langchain faiss-cpu sentence-transformers pypdf
```

