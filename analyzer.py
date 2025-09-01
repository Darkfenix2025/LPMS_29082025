import os
import sys
from pathlib import Path
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import Ollama
from langchain.chains import RetrievalQA

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using OCR if necessary."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            page_text = page.get_text()
            if not page_text.strip():  # If no text, use OCR
                pix = page.get_pixmap()
                img = Image.open(pix.tobytes())
                page_text = pytesseract.image_to_string(img)
            text += page_text + "\n"
        doc.close()
        return text
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        return ""

def extract_text_from_txt(txt_path):
    """Extract text from TXT file."""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading TXT {txt_path}: {e}")
        return ""

def extract_text_from_document(doc_path):
    """Extract text from document (PDF or TXT)."""
    if doc_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(doc_path)
    elif doc_path.lower().endswith('.txt'):
        return extract_text_from_txt(doc_path)
    else:
        print("Unsupported file type.")
        return ""

def load_vector_db(db_name):
    """Load existing vector database."""
    persist_directory = f"vector_databases/{db_name}"
    if not os.path.exists(persist_directory):
        print(f"Vector database '{db_name}' not found.")
        return None
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    return vectorstore

def analyze_demand(doc_path, db_name):
    """Analyze a new demand document."""
    if not os.path.exists(doc_path):
        print("Document does not exist.")
        return

    print("Extracting text from document...")
    demand_text = extract_text_from_document(doc_path)
    if not demand_text.strip():
        print("No text extracted from document.")
        return

    vectorstore = load_vector_db(db_name)
    if not vectorstore:
        return

    print("Searching for similar cases...")
    # Embed the demand text
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    demand_embedding = embeddings.embed_query(demand_text)

    # Search for similar documents
    similar_docs = vectorstore.similarity_search_by_vector(demand_embedding, k=5)
    summaries = [doc.page_content[:500] + "..." for doc in similar_docs]

    # Generate prompt
    prompt = f"""Eres un estratega legal. He recibido esta nueva demanda: {demand_text[:2000]}...

Mi base de datos de casos anteriores similares indica que las estrategias exitosas fueron:
{chr(10).join(f"- {summary}" for summary in summaries)}

Basado en todo esto, redacta un análisis preliminar de la demanda, identifica sus puntos fuertes y débiles, y sugiere 3 posibles líneas de defensa."""

    # Use Ollama
    llm = Ollama(model="mistral-small:22b")  # Assuming llama2 is installed
    response = llm(prompt)
    print("\n=== Análisis de la Demanda ===")
    print(response)

def analyze_question(question, db_name):
    """Analyze an open question."""
    vectorstore = load_vector_db(db_name)
    if not vectorstore:
        return

    print("Searching for relevant information...")
    # Use RetrievalQA for question answering
    llm = Ollama(model="mistral-small:22b")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
    )
    response = qa_chain.run(question)
    print("\n=== Respuesta ===")
    print(response)

def main():
    print("=== Jurisprudential Analyzer ===")
    print("Select mode:")
    print("1. Análisis de Demanda")
    print("2. Pregunta Abierta")
    mode = input("Enter mode (1 or 2): ").strip()

    if mode == "1":
        doc_path = input("Enter the path to the new document (PDF or TXT): ").strip()
        db_name = input("Enter the name of the vector database: ").strip()
        analyze_demand(doc_path, db_name)
    elif mode == "2":
        question = input("Enter your question: ").strip()
        db_name = input("Enter the name of the vector database: ").strip()
        analyze_question(question, db_name)
    else:
        print("Invalid mode.")
        sys.exit(1)

if __name__ == "__main__":
    main()