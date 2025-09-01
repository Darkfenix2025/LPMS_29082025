import os
import sys
from pathlib import Path
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
import chromadb

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

def process_files(root_folder):
    """Recursively process files in the folder."""
    corpus = ""
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            file_path = Path(root) / file
            if file.lower().endswith('.pdf'):
                text = extract_text_from_pdf(str(file_path))
            elif file.lower().endswith('.txt'):
                text = extract_text_from_txt(str(file_path))
            else:
                continue
            corpus += text + "\n"
    return corpus

def create_vector_db(corpus, db_name):
    """Create and save vector database."""
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(corpus)

    # Create embeddings
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create ChromaDB
    persist_directory = f"vector_databases/{db_name}"
    os.makedirs(persist_directory, exist_ok=True)

    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    vectorstore.persist()
    print(f"Vector database '{db_name}' created successfully in {persist_directory}")

def main():
    print("=== Jurisprudential Indexer ===")
    root_folder = input("Enter the path to the root folder containing documents: ").strip()
    if not os.path.exists(root_folder):
        print("Folder does not exist.")
        sys.exit(1)

    db_name = input("Enter the name for the vector database: ").strip()
    if not db_name:
        print("Database name cannot be empty.")
        sys.exit(1)

    print("Processing files...")
    corpus = process_files(root_folder)
    if not corpus.strip():
        print("No text extracted from files.")
        sys.exit(1)

    print("Creating vector database...")
    create_vector_db(corpus, db_name)
    print("Indexing complete.")

if __name__ == "__main__":
    main()