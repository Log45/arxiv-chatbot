# chatbot_app.py

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from utils import search_arxiv_simple, arxiv_to_faiss, generate_session_id, client
import os

# --- Streamlit UI ---
st.set_page_config(page_title="ArXiv Chatbot", layout="wide")
st.title("ArXiv Chatbot")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None
if "session_id" not in st.session_state:
    st.session_state.session_id = generate_session_id()
if "papers_loaded" not in st.session_state:
    st.session_state.papers_loaded = False
if "current_search" not in st.session_state:
    st.session_state.current_search = None

# Function to create QA chain from search results
def create_qa_chain(search_results, max_papers=10):
    """Create a QA chain from arXiv search results."""
    try:
        
        db = arxiv_to_faiss(search=search_results, max_papers=max_papers)
            
        if db is None:
            st.error("Failed to create database from papers.")
            return None
            
        retriever = db.as_retriever()
        llm = ChatOpenAI(temperature=0)
        ### Langchain RAG documentation: https://python.langchain.com/v0.2/docs/tutorials/qa_chat_history/
        # Contextualize question
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        # Answer question
        system_prompt = (
            "You are an assistant for question-answering tasks relating to research papers. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. "
            "\n\n"
            "{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        # Statefully manage chat history
        store = {}

        def get_session_history(session_id: str) -> BaseChatMessageHistory:
            if session_id not in store:
                store[session_id] = ChatMessageHistory()
            return store[session_id]

        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

        return conversational_rag_chain, db
        
    except Exception as e:
        st.error(f"Error creating QA chain: {str(e)}")
        return None, None

# Create tabs
tab1, tab2 = st.tabs(["Search ArXiv", "Chat"])

# Tab 1: Search ArXiv (First tab - landing page)
with tab1:
    st.header("Search and Download Papers")
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Enter search query:", 
            placeholder="e.g., quantum machine learning, transformer models, etc.",
            key="search_input"
        )
    
    with col2:
        max_results = st.slider("Max papers:", min_value=1, max_value=500, value=10)
    
    # Search button
    if st.button("Search Papers", type="primary"):
        if search_query:
            with st.spinner("Searching arXiv..."):
                try:
                    search = search_arxiv_simple(search_query, max_results)
                    st.session_state.current_search = search
                    
                    # Display search results
                    st.success(f"Found papers for: '{search_query}'")
                    
                    # Show papers that will be downloaded
                    st.subheader("Papers to be downloaded:")
                    paper_list = []
                    for i, result in enumerate(client.results(search), 1):
                        paper_info = f"{i}. **{result.title}**\n   - Authors: {', '.join(author.name for author in result.authors)}\n   - Published: {result.published.strftime('%Y-%m-%d')}"
                        paper_list.append(paper_info)
                    
                    for paper in paper_list:
                        st.markdown(paper)
                    
                    # Download and create QA chain
                    
                    qa_chain, db = create_qa_chain(search, max_results)
                    
                    if qa_chain is not None:
                        st.session_state.qa_chain = qa_chain
                        st.session_state.papers_loaded = True
                        st.session_state.messages = []  # Clear previous chat
                        st.success(f"Successfully loaded {max_results} papers! You can now chat about them.")
                        
                        # Show database info
                        if db:
                            st.info(f"Database contains {db.index.ntotal} text chunks")
                    else:
                        st.error("Failed to initialize chat with the papers.")
                            
                except Exception as e:
                    st.error(f"Error searching papers: {str(e)}")
        else:
            st.warning("Please enter a search query")
    
    # Show current status
    if st.session_state.papers_loaded:
        st.success("Papers are loaded and ready for chat!")
        if st.button("Load New Papers"):
            st.session_state.papers_loaded = False
            st.session_state.qa_chain = None
            st.session_state.messages = []
            st.rerun()
    else:
        st.info("🔍 Search for papers above to get started!")

# Tab 2: Chat Interface
with tab2:
    st.header("Chat with Research Papers")
    
    if not st.session_state.papers_loaded:
        st.warning("No papers loaded yet. Please search for papers in the 'Search ArXiv' tab first.")
        st.info("Tip: Go to the first tab to search and download papers, then come back here to chat!")
    else:
        # Create a container for the chat messages
        chat_container = st.container()
        
        # Display chat history in the container
        with chat_container:
            # Add some spacing at the top
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Display existing messages
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            # Add some spacing before the input
            st.markdown("<br>", unsafe_allow_html=True)

        # Handle user input (this will appear at the bottom)
        if prompt := st.chat_input("Ask me anything about the research papers..."):
            # Add user message to chat
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Process the response
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.qa_chain.invoke(
                        {"input": prompt}, 
                        config={"configurable": {"session_id": st.session_state.session_id}}
                    )
                    print(response)
                    print(response["answer"])
                except Exception as e:
                    response = {"answer": f"Sorry, I encountered an error: {str(e)}"}
            
            

            # Add assistant response to chat
            st.chat_message("assistant").markdown(response["answer"])
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
            # Display sources as formatted text below the response, as a chat message
            if "context" in response and response["context"]:
                sources_md = "##### References used:\n"
                for i, doc in enumerate(response["context"], 1):
                    source_path = doc.metadata.get("source", "Unknown")
                    filename = source_path.split("\\")[-1].split("/")[-1]
                    snippet = doc.page_content[:300].replace('\n', ' ') + "..."
                    sources_md += f"**{i}. `{filename}`**\n\n> {snippet}\n\n"
                st.chat_message("assistant").markdown(sources_md)
                st.session_state.messages.append({"role": "assistant", "content": sources_md})
            
            # Rerun to update the display
            st.rerun()
