import arxiv
import markitdown
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from langchain.llms import OpenAIChat
from langchain.document_loaders import DirectoryLoader
from langchain_core.documents import Document
from typing import List, Dict, Union, Any
import os
import time
import random
from urllib.error import HTTPError, URLError
from urllib.request import urlretrieve
import traceback
from pathlib import Path

# Global client
client = arxiv.Client()

def search_arxiv_simple(query: str, max_results: int = 10, prefix: str = "all") -> arxiv.Search:
    """Function to search arxiv for a simple query including only one prefix. 

    Args:
        query (str): String of plaintext to search for. 
        max_results (int, optional): Max number of results to return. Defaults to 10.
        prefix (str, optional): Prefix to determine what to search for. Defaults to "all".
                                Options: "all", "ti", "au", "cat", "jr", "abs", "rn", "co"

    Returns:
        arxiv.Search: Representation of the search query query.
    """
    query = f'{prefix}:"{query}"'
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending,
    )
    return search

def search_arxiv_advanced(queries: List[str], ignore_list: List[str] = [], max_results: int = 10) -> arxiv.Search:
    """Function to do an advanced search of arxiv. Queries are ANDed together, ignore_list is ORed together.
    Queries and ignore_list MUST INCLUDE PREFIXES. 

    Args:
        queries (List[str]): List of formatted queries to AND together.
        ignore_list (List[str]): List of formatted queries to ignore.
        max_results (int, optional): Max number of results to return. Defaults to 10.

    Returns:
        arxiv.Search: Representation of the search query query.
    """
    query = " AND ".join(queries)
    if ignore_list:
        ignore_query = " OR ".join(ignore_list)
        query = f"({query}) ANDNOT ({ignore_query})"
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending,
    )
    return search

def download_paper_with_retry(result, output_dir: str, max_retries: int = 3, delay: float = 2.0) -> bool:
    """Download a single paper with retry logic and error handling.
    
    Args:
        result: arXiv result object
        output_dir: Directory to save the paper
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        bool: True if download successful, False otherwise
    """
    # Set the PDF URL
    result.pdf_url = result.__str__().replace("abs", "pdf")
    
    for attempt in range(max_retries):
        try:
            # Add random delay to avoid rate limiting
            time.sleep(delay + random.uniform(0, 1))
            
            # Download the PDF
            downloaded_path = result.download_pdf(output_dir)
            print(f"Successfully downloaded: {result.title}")
            return True
            
        except (HTTPError, URLError, ConnectionResetError, OSError) as e:
            print(f"Attempt {attempt + 1} failed for '{result.title}': {str(e)}")
            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Waiting {wait_time:.2f} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"Failed to download '{result.title}' after {max_retries} attempts")
                return False
    
    return False

def save_arxiv_results(search: arxiv.Search, output_dir: str, max_papers: int = 10) -> List[str]:
    """Function to save the results of an arxiv search to a directory with error handling.
    
    Args:
        search (arxiv.Search): Search to save the results of.
        output_dir (str): Directory to save the results to.
        max_papers (int): Maximum number of papers to download.
        
    Returns:
        List[str]: List of successfully downloaded paper filenames
    """
    downloaded_files = []
    paper_count = 0
    
    for result in client.results(search):
        if paper_count >= max_papers:
            break
            
        if download_paper_with_retry(result, output_dir):
            downloaded_files.append(result.title)
            paper_count += 1
        else:
            print(f"Skipping paper: {result.title}")
    
    print(f"Successfully downloaded {len(downloaded_files)} out of {max_papers} papers")
    return downloaded_files

def initialize_db(documents: List[Document], embeddings: HuggingFaceEmbeddings) -> FAISS:
    """Function to initialize a FAISS database from a list of documents.
    
    Args:
        documents (List[Document]): List of documents to add to the database.
        embeddings (HuggingFaceEmbeddings): Embeddings to use for the database.
    """
    db = FAISS.from_documents(documents, embeddings)
    return db
        
def arxiv_to_documents(search: arxiv.Search, max_papers: int = 10) -> List[Document]:
    """Function to convert an arxiv search to a list of documents.
    
    Args:
        search (arxiv.Search): Search to convert to documents.
        max_papers (int): Maximum number of papers to download and process.
    """
    output_dir = "./papers"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir) 
    
    # Download papers with error handling
    try:
        downloaded_files = save_arxiv_results(search, output_dir, max_papers)
    except Exception as e:
        print(f"Error downloading papers: {traceback.format_exc()}")
        downloaded_files = []
    
    if not downloaded_files and not len(os.listdir(output_dir)):
        print("No papers were successfully downloaded. Returning empty document list.")
        return []
    
    # Load documents from the downloaded papers
    try:
        directory_loader = DirectoryLoader(path=os.path.relpath(output_dir), glob='*.pdf')
        docs = directory_loader.load()
        print(f"Successfully loaded {len(docs)} documents from directory")
        
        # Split into smaller chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        documents = text_splitter.split_documents(docs)
        print(f"Split into {len(documents)} chunks")
        
        return documents
    except Exception as e:
        print(f"Error loading documents: {str(e)}")
        return []

def arxiv_to_faiss(search: arxiv.Search, max_papers: int = 10) -> FAISS:
    """Function to convert an arxiv search to a FAISS database.
    
    Args:
        search (arxiv.Search): Search to convert to a FAISS database.
        max_papers (int): Maximum number of papers to download and process.
    """
    documents = arxiv_to_documents(search, max_papers)
    
    if not documents:
        print("No documents to process. Returning None.")
        return None
    
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = initialize_db(documents, embeddings)
    return db
