#!/usr/bin/env python3
"""
Main script demonstrating improved arXiv downloading with error handling.
"""

from utils import search_arxiv_simple, arxiv_to_faiss

def main():
    """Main function to demonstrate the improved arXiv downloading."""
    
    print("Starting arXiv paper download with improved error handling...")
    
    # Create a search for transformer papers (limit to 5 for testing)
    search = search_arxiv_simple("transformer", max_results=5)
    
    # Convert to FAISS database with max 5 papers
    print("Downloading and processing papers...")
    db = arxiv_to_faiss(search=search, max_papers=5)
    
    if db is not None:
        print(f"Successfully created FAISS database!")
        print(f"Database contains {db.index.ntotal} vectors")
    else:
        print("Failed to create FAISS database.")

if __name__ == "__main__":
    main()
