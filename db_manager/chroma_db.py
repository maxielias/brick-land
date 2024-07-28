import os
import fitz  # PyMuPDF
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_text_splitters import CharacterTextSplitter

class VectorDBManager:
    def __init__(self, pdf_directory='data/processed/pdf_files', db_directory='data/db/chroma_db', chunk_size=500, overlap_size=125):
        self.pdf_directory = pdf_directory
        self.db_directory = db_directory
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
    def get_all_pdf_files(self, pdf_directory=None):
        if pdf_directory is None:
            pdf_directory = self.pdf_directory
        pdf_files = []
        for root, dirs, files in os.walk(pdf_directory):
            for file in files:
                if file.endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        return pdf_files
    
    def text_loader(self, doc):
        try:
            with fitz.open(doc) as pdf_document:
                text = ""
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    text += page.get_text()
            return text
        except Exception as e:
            print(f"Error loading {doc}: {e}")
            return ""
    
    def split_text(self, text):
        text_splitter = CharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.overlap_size)
        return text_splitter.split_text(text)
    
    def load_to_chroma(self, chunks, embedding_function, persist_directory):
        if embedding_function is None:
            embedding_function = self.embedding_model
        if persist_directory is None:
            persist_directory = self.db_directory
        db = Chroma.from_texts(texts=chunks, embedding=embedding_function, persist_directory=persist_directory)

    def process_and_save_chunks(self):
        list_of_pdfs = self.get_all_pdf_files()
        doc_chunks_to_chroma = []
        for doc in list_of_pdfs:
            text = self.text_loader(doc)
            if text:
                splits = self.split_text(text)
                doc_chunks_to_chroma.extend(splits)
                self.load_to_chroma(splits, self.embedding_model, self.db_directory)
        return doc_chunks_to_chroma

if __name__ == "__main__":
    vector_db_manager = VectorDBManager()
    doc_chunks_to_chroma = vector_db_manager.process_and_save_chunks()
