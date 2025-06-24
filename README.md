# ArXiv Chatbot: Interactive Research Assistant

ArXiv Chatbot is a Streamlit-based research assistant that allows you to search, download, and interactively chat about arXiv papers using advanced language models. The app provides a user-friendly interface for exploring research topics, asking questions, and viewing source documents for each answer.

## Features

- **Search arXiv**: Find papers by topic or keyword directly from the app.
- **Download & Index**: Download selected papers and build a searchable vector database.
- **Chat with Papers**: Ask questions about the papers and get answers with references to the original documents.
- **Source Transparency**: Every answer includes clear references to the documents used.
- **Robust Downloading**: Improved error handling, retry logic, and rate limiting for reliable paper downloads.

## Quick Start

### 1. Run with Docker (Recommended)

```bash
docker build -t arxiv-chatbot .
docker run -p 8501:8501 arxiv-chatbot
```
Then open [http://localhost:8501](http://localhost:8501) in your browser.

### 2. Run Locally

Make sure you have Python 3.12 and all dependencies installed:
```bash
pip install -r requirements.txt
streamlit run chat.py
```

## Usage

1. **Search for Papers**: Enter a topic or keywords in the "Search ArXiv" tab.
2. **Download & Index**: Select the number of papers to download and initialize the chat.
3. **Chat**: Switch to the "Chat" tab and ask questions about the downloaded papers. Each answer will include references to the source documents.

## Next Steps

- Add a UI interface for advanced ArXiv search to combine and ignore multiple queries based on arXiv API documentation. 
- Add a an option to create a new chat, which creates a new database and chat log with a unique session id, creating separation from past context.
- Deploy to Google Cloud or Azure.
- Add an upload option for papers from local machine.

## Advanced: Programmatic Paper Downloading

The project also includes improved utilities for downloading and processing arXiv papers with robust error handling. These can be used independently in scripts or notebooks.

```python
from utils import search_arxiv_simple, arxiv_to_faiss

search = search_arxiv_simple("transformer", max_results=10)
db = arxiv_to_faiss(search=search, max_papers=5)
```

## Configuration

You can adjust these parameters in the code or UI:
- `max_papers`: Maximum number of papers to download (default: 10)
- `max_retries`: Number of retry attempts per paper (default: 3)
- `delay`: Base delay between downloads in seconds (default: 2.0)

## Troubleshooting

- If downloads fail, try reducing `max_papers` or increasing `delay`.
- Ensure a stable internet connection.
- Some papers may not be available for download.

## Dependencies

All dependencies are listed in `requirements.txt`. Key packages include:
- `streamlit`
- `arxiv`
- `langchain`
- `faiss-cpu`
- `sentence-transformers`
- `pypdf`

## Credits

- Built with [Streamlit](https://streamlit.io/), [LangChain](https://python.langchain.com/), and [arXiv](https://arxiv.org/).


