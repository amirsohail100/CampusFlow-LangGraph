import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from state.StatePipeline import State

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.4,
)

NO_RETRIEVAL_NEEDED = "NO_RETRIEVAL_NEEDED"


def build_retriever(pdf_filename: str):
    """Build a FAISS retriever from a PDF sitting in the data/ folder."""
    pdf_path = os.path.join(DATA_DIR, pdf_filename)
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"Expected '{pdf_filename}' inside the data/ folder but it was not found. "
            f"Place your PDF at: {pdf_path}"
        )

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(documents)

    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 4})


# Retrievers are built the first time they are needed (not at import time)
# so the FastAPI server can still start even if the PDFs are missing.
_academic_retriever = None
_fee_retriever = None


def get_academic_retriever():
    global _academic_retriever
    if _academic_retriever is None:
        _academic_retriever = build_retriever("academics_handbook.pdf")
    return _academic_retriever


def get_fee_retriever():
    global _fee_retriever
    if _fee_retriever is None:
        _fee_retriever = build_retriever("fee_structure.pdf")
    return _fee_retriever


def classifier_node(state: State) -> dict:
    """Look at the latest user message and decide which path to take."""
    last_message = state["messages"][-1].content

    prompt = (
        "Classify the following student query into exactly one category: "
        "'academic', 'fee', or 'general'.\n\n"
        "Use 'academic' for questions about attendance, exams, grading, credits, "
        "promotion, course structure, summer training, or degree requirements.\n"
        "Use 'fee' for questions about tuition, payment, refund, late charges, "
        "scholarships, or any money-related topic.\n"
        "Use 'general' for greetings, casual talk, or anything not related to "
        "the college rules or fee.\n\n"
        f"Query: {last_message}\n\n"
        "Return only one word: academic, fee, or general."
    )

    response = llm.invoke(prompt)
    category = response.content.strip().lower()

    if "academic" in category:
        category = "academic"
    elif "fee" in category:
        category = "fee"
    else:
        category = "general"

    return {"query_type": category}


def academic_rag_node(state: State) -> dict:
    """Retrieve relevant chunks from the academics handbook."""
    query = state["messages"][-1].content
    docs = get_academic_retriever().invoke(query)
    context = "\n\n".join(doc.page_content for doc in docs)
    return {"retrieved_context": context}


def fee_rag_node(state: State) -> dict:
    """Retrieve relevant chunks from the fee structure PDF."""
    query = state["messages"][-1].content
    docs = get_fee_retriever().invoke(query)
    context = "\n\n".join(doc.page_content for doc in docs)
    return {"retrieved_context": context}


def general_node(state: State) -> dict:
    """Answer directly using the LLM's own knowledge, no retrieval needed."""
    return {"retrieved_context": NO_RETRIEVAL_NEEDED}


def response_node(state: State) -> dict:
    """Generate the final answer, personalized using the student's programme."""
    query = state["messages"][-1].content
    programme = state.get("programme", "Unknown")
    context = state["retrieved_context"]

    if context == NO_RETRIEVAL_NEEDED:
        prompt = (
            f"You are a friendly college assistant talking to a {programme} student. "
            f"Answer this question using your own general knowledge:\n\n{query}"
        )
    else:
        prompt = (
            f"You are a college assistant helping a {programme} student. "
            f"Use the following context from the official college documents to answer "
            f"the question accurately. If the context mentions specific figures for "
            f"different programmes, highlight the one relevant to {programme} if possible.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            f"Give a clear, friendly, and precise answer."
        )

    response = llm.invoke(prompt)
    return {"messages": [("ai", response.content.strip())]}


def route_query(state: State) -> str:
    if state["query_type"] == "academic":
        return "academic_rag"
    elif state["query_type"] == "fee":
        return "fee_rag"
    else:
        return "general"
