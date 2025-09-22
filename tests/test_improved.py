"""
Test script for improved arXiv downloading functions.
Import this into your Jupyter notebook to test the improved functions.
"""

from utils import search_arxiv_simple, arxiv_to_faiss

def test_improved_download():
    """Test the improved download functionality with a small number of papers."""
    
    print("Testing improved arXiv download with error handling...")
    
    # Test with just 3 papers to avoid overwhelming the server
    search = search_arxiv_simple("transformer", max_results=3)
    
    print("Starting download...")
    db = arxiv_to_faiss(search=search, max_papers=3)
    
    if db is not None:
        print(f"✅ Success! Database created with {db.index.ntotal} vectors")
        return db
    else:
        print("❌ Failed to create database")
        return None

# You can run this in your notebook:
# from test_improved import test_improved_download
# db = test_improved_download()