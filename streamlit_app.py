import psycopg
import streamlit as st
from qdrant_client import QdrantClient
from agno.agent import Agent
from agno.utils.log import logger
from agno.knowledge.pdf import PDFReader
from agno.knowledge.text import TextReader
from agno.knowledge.csv import CSVReader
from agno_agent import get_auto_rag_agent

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

def sidebar_knowledge_base(rag_agent):
    uploaded_file = st.sidebar.file_uploader("Add a Document (.pdf, .csv, or .txt)", key="file_upload")
    if uploaded_file:
        file_type = uploaded_file.name.split(".")[-1].lower()
        reader = get_file_reader(file_type)
        if reader:
            docs = reader.read(uploaded_file)
            rag_agent.knowledge.load_documents(docs, upsert=True)

    # if st.sidebar.button("Clear Knowledge Base"):
    #     rag_agent.knowledge.vector_db.delete()
    #     st.sidebar.success("Knowledge base cleared")

def page_setup():
    st.set_page_config(page_title="Autonomous RAG", page_icon="🐧")
    st.header('Autonomous RAG')

    st.sidebar.markdown("Built using [Agno-agi](https://github.com/agno-agi/agno/)")

def initialize_agent(model_id: str):

    if "rag_agent" not in st.session_state or st.session_state["rag_agent"] is None:
        logger.info(f"---*--- Creating {model_id} Agent ---*---")
        agent: Agent = get_auto_rag_agent(
            model_id=model_id, session_id=st.session_state.get("rag_agent_session_id")
        )
        st.session_state["rag_agent"] = agent
        st.session_state["rag_agent_session_id"] = agent.session_id

    return st.session_state["rag_agent"]


def run_app(rag_agent):

    # Initialize session_state["history"] before accessing it for chat history
    if "history" not in st.session_state:
        st.session_state["history"] = []

    # Load chat history from memory
    if rag_agent.memory and not st.session_state["history"]:
        logger.debug("Loading chat history!")
        st.session_state["history"] = [
            {"role": message.role, "content": message.content} for message in rag_agent.memory.messages
        ]
    elif not st.session_state["history"]:#If session chat history is still empty
        logger.debug("No chat history found")
        st.session_state["history"] = [{"role": "agent", "content": "Upload a doc and ask me questions..."}]

        # Handle user input and generate responses
    if prompt := st.chat_input("Ask a question:"):
        st.session_state["history"].append({"role": "user", "content": prompt})
        with st.chat_message("agent"):
            agent_response = rag_agent.run(prompt)
            st.session_state["history"].append({"role": "agent", "content": agent_response.content})

        # Display chat history
    for message in st.session_state["history"]:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.write(message["content"])

    sidebar_knowledge_base(rag_agent)



if __name__ == "__main__":

    #1. Check if can connect to Postgres
    if not check_postgres_connection():
        exit(1)

    #2. Check if can connect to Qdrant 
    if not check_qdrant_connection():
        exit(1)

    page_setup()

    # Initialize the agent
    rag_agent = initialize_agent("gpt-3.5-turbo")

    run_app(rag_agent)