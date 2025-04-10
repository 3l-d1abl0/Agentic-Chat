# Agentic RAG (Retrieval-Augmented Generation)

A powerful chatbot application built with Streamlit that combines RAG capabilities using Agno-agi framework, PostgreSQL for persistence, and Qdrant for vector storage.

## Features

- 🤖 Interactive chat interface powered by GPT models
- 📚 Document-based question answering using RAG
- 💾 Persistent chat history using PostgreSQL
- 🔍 Vector search capabilities with Qdrant
- 🌐 Web search integration using DuckDuckGo
- 🧠 Autonomous agent with memory and knowledge base

## Prerequisites

- Python 3.8+
- PostgreSQL
- Qdrant vector database
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AgenticChat
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:

   export your apena ai key
```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

4. Configure database connections:

- Setup your pgVector Database, for example: 
```bash
docker run -d \
  -e POSTGRES_DB=ai \
  -e POSTGRES_USER=ai \
  -e POSTGRES_PASSWORD=ai \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -v pgvolume:/var/lib/postgresql/data \
  -p 5532:5432 \
  --name pgvector \
  phidata/pgvector:16
```
- As per above config PostgreSQL should be running on `localhost:5532` with database `ai` and user/password as `ai/ai` (Customize a per you need)

- Setup your Qdrant db, for example:
```bash
docker run -d -p 6333:6333 --name qdrantdb qdrant/qdrant
```
- Qdrant should be running on `localhost:6333`

## Usage

1. Start the Streamlit application:
```bash
streamlit run streamlit_app.py --server.headless true
```

2. Open your browser and navigate to the provided URL (typically `http://localhost:8501`)

3. Upload documents and start asking questions!

## Project Structure

- `streamlit_app.py`: Main application file with Streamlit UI and database connection checks
- `agno_agent.py`: Agent configuration and setup using the Agno framework
- Database Components:
  - PostgreSQL: Stores chat history and agent sessions
  - Qdrant: Vector database for document embeddings

## Features in Detail

### Chat Interface
- Real-time chat interaction
- Persistent chat history across sessions
- Markdown support for formatted responses

### RAG Capabilities
- Document retrieval using vector similarity
- Integration with OpenAI embeddings
- Configurable number of retrieved documents (currently set to 3)

### Agent Features
- Session management
- User memory creation
- Conversation summarization
- Web search capabilities
- Knowledge base integration


