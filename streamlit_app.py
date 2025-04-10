import psycopg
import streamlit as st
from qdrant_client import QdrantClient
from agno.agent import Agent
from agno.utils.log import logger
from agno.knowledge.pdf import PDFReader
from agno.knowledge.text import TextReader
from agno.knowledge.csv import CSVReader
from agno_agent import get_rag_agent
from typing import List
from agno.document import Document
from agno.document.reader.website_reader import WebsiteReader



def check_postgres_connection():
    try:

        #postgresql://username:password@host:port/database
        pg_db_url = "postgresql://ai:ai@localhost:5532/ai"

        connection = psycopg.connect(pg_db_url)
        
        cursor = connection.cursor()# Create a cursor object
        cursor.execute("SELECT version();") # Execute a test query
        result = cursor.fetchone()
        print(f"Can connect PostgreSQL: {result[0]}")
        cursor.close()
        connection.close()
        return True

    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return False

def check_qdrant_connection():
    try:

        host = 'localhost'
        port = 6333
        
        # Initialize Qdrant client
        client = QdrantClient(host=host, port=port)
        collections = client.get_collections() # Test connection with a basic operation
        print(collections)
        print("Connected to Qdrant DB.")
        return True

    except Exception as e:
        print(f"Error connecting to Qdrant DB: {e}")
        return False

def get_file_reader(file_type: str):
    readers = { "pdf": PDFReader(), "csv": CSVReader(), "txt": TextReader() }
    return readers.get(file_type.lower(), None)

def sidebar_model_options():
    model_options = {
        "o3-mini": "openai:o3-mini",
        "o3-mini": "openai:gpt-3.5-turbo",
        "gpt-4o": "openai:gpt-4o",
        "gpt-4-turbo": "openai:gpt-4-turbo"
    }
    selected_model = st.sidebar.selectbox(
        "Select a model",
        options=list(model_options.keys()),
        index=0,
        key="model_selector",
    )
    if st.session_state.get("model_id") != selected_model:
        st.session_state["model_id"] = selected_model

    return selected_model

def sidebar_knowledge_base(rag_agent):
    uploaded_file = st.sidebar.file_uploader("Add a Document (.pdf, .csv, or .txt)", key="file_upload")
    if uploaded_file:
        file_type = uploaded_file.name.split(".")[-1].lower()
        reader = get_file_reader(file_type)
        if reader:
            docs = reader.read(uploaded_file)
            rag_agent.knowledge.load_documents(docs, upsert=True)

def sidebar_knowledge_base_url(rag_agent):    
    
    if "loaded_urls" not in st.session_state:
        st.session_state.loaded_urls = set()

    if "loaded_urls" not in st.session_state:
        st.session_state.loaded_urls = set()
    
    input_url = st.sidebar.text_input("Add URL to Knowledge Base")
    if input_url and input_url not in st.session_state.loaded_urls:
        alert = st.sidebar.info("Processing URLs...", icon="ℹ️")
        scraper = WebsiteReader(max_links=2, max_depth=1)
        docs: List[Document] = scraper.read(input_url)
        if docs:
            rag_agent.knowledge.load_documents(docs, upsert=True)
            st.session_state.loaded_urls.add(input_url)
            st.sidebar.success("URL added to knowledge base")
        else:
            st.sidebar.error("Could not process the provided URL")
        alert.empty()
    else:
        if input_url:
            st.sidebar.info("URL already loaded in knowledge base")

def sidebar_session_history(rag_agent):
    # Session Management
    if rag_agent.storage:
        
        stored_sessions = rag_agent.storage.get_all_sessions()

        # Get session names if available, otherwise use IDs
        session_options = []
        for session in stored_sessions:

            #print(dir(session))

            session_name = ( session.session_data.get("session_name", None) if session.session_data else None )
            display_name = session_name if session_name else session.session_id
            session_options.append({"id": session.session_id, "display": display_name})

        chosen_session = st.sidebar.selectbox("Session ID", options=[opt["display"] for opt in session_options])
        print(chosen_session)
        #Find the selected session ID
        selected_session_id = next(
            s["id"] for s in session_options if s["display"] == chosen_session
        )
        if selected_session_id != st.session_state.get("rag_agent_session_id"):
            st.session_state["rag_agent"] = get_rag_agent(model_id=model_id, session_id=selected_session_id)
            st.session_state["rag_agent_session_id"] = selected_session_id
            st.rerun()

def page_setup():
    st.set_page_config(page_title="Agentic RAG", page_icon="🐧", layout="wide")
    st.header('Agentic RAG')

    st.sidebar.markdown("Built using [Agno-agi](https://github.com/agno-agi/agno/)")

def initialize_agent(model_id: str):

    if "rag_agent" not in st.session_state or st.session_state["rag_agent"] is None:
        logger.info(f"########## Creating {model_id} Agent ##########")
        agent: Agent = get_rag_agent(
            model_id=model_id, session_id=st.session_state.get("rag_agent_session_id")
        )
        st.session_state["rag_agent"] = agent
        st.session_state["rag_agent_session_id"] = agent.session_id

    return st.session_state["rag_agent"]


def run_app(rag_agent):

    logger.info(f"########## Setting up Streamlit ##########")
    # Initialize session_state["history"] before accessing it for chat history
    if "history" not in st.session_state:
        st.session_state["history"] = []

    print("Memory Runs: ",rag_agent.memory.runs)
    print("LOAD SESSIONS: ", rag_agent.load_session())

    # Load chat history from memory, if Present in memory and not present in state history
    logger.info(f"########## Loading chat history ##########")
    if rag_agent.memory and not st.session_state["history"]:
        logger.debug("Loading chat history!")
        logger.debug(rag_agent.memory.messages)
        st.session_state["history"] = [
            {"role": message.role, "content": message.content} for message in rag_agent.memory.messages
        ]
    elif not st.session_state["history"]:#If session chat history is still empty
        logger.debug("No chat history found")
        st.session_state["history"] = [{"role": "agent", "content": "Upload a doc and ask me questions..."}]

    # Handle user input and generate responses
    if prompt := st.chat_input("Ask a question:"):
        st.session_state["history"].append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            agent_response = rag_agent.run(prompt)
            print('AGENT RESPONSE: ', agent_response.content)
            st.session_state["history"].append({"role": "assistant", "content": agent_response.content})

    # Display chat history
    for message in st.session_state["history"]:

        if message["role"] in ["user", "assistant"]:
            if message["content"] is not None:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # if message["role"] == "system":
        #     continue
        # with st.chat_message(message["role"]):
        #     st.write(message["content"])

    sidebar_knowledge_base(rag_agent)

    sidebar_knowledge_base_url(rag_agent)

    sidebar_session_history(rag_agent)
    



if __name__ == "__main__":

    #1. Check if can connect to Postgres
    if not check_postgres_connection():
        exit(1)

    #2. Check if can connect to Qdrant 
    if not check_qdrant_connection():
        exit(1)

    page_setup()

    model_id = sidebar_model_options()

    # Initialize the agent
    rag_agent = initialize_agent(model_id)

    run_app(rag_agent)