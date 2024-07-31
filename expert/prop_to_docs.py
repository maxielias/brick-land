import sqlite3
from dotenv import load_dotenv
import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter

class RealEstateDataTransformer:
    def __init__(self, db_path='data/db/brickland.db', chroma_db_path='data/db', table_name='properties', env_path='.venv/.env', collection_name='properties_to_docs'):
        self.db_path = db_path
        self.env_path = env_path
        self.chroma_db_path = chroma_db_path
        self.table_name = table_name
        self.collection_name = collection_name
        self.load_environment_variables(env_path)
        self.embedding_model = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

    def load_environment_variables(self, env_path):
        load_dotenv(env_path)
        os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2')
        os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT')
        os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')
        os.environ['TAVILY_API_KEY'] = os.getenv('TAVILY_API_KEY')

    def fetch_all_rows(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.table_name}")
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        documents = []
        for row in rows:
            doc = dict(zip(column_names, row))
            documents.append(doc)
        conn.close()
        return documents

    def transform_to_docs(self, rows):
        docs = []
        metadata = []
        for row in rows:
            doc = f"{row['prop_description']} {row['project_description']}"
            m = {
                "prop_url": row["prop_url"],
                "prop_address": row["prop_address"],
                "prop_floor": row["prop_floor"],
                "prop_price": row["prop_price"],
                "prop_m2": row["prop_m2"],
                "prop_rooms": row["prop_rooms"],
                "prop_bedrooms": row["prop_bedrooms"],
                "prop_location": row["prop_location"],
                "project_url": row["project_url"],
                "project_district": row["project_district"],
                "project_address": row["project_address"],
                "project_description": row["project_description"],
            }
            docs.append(doc)
            metadata.append(m)
        return metadata, docs

    def load_to_chroma(self, metadata, docs, embedding_function, persist_directory):
        if embedding_function is None:
            embedding_function = self.embedding_model
        if persist_directory is None:
            persist_directory = self.db_path
        db = Chroma.from_texts(metadatas=metadata, texts=docs, embedding=embedding_function, persist_directory=persist_directory)

    def run(self):
        rows = self.fetch_all_rows()
        metadata, docs = self.transform_to_docs(rows)
        self.load_to_chroma(metadata, docs, self.embedding_model, self.chroma_db_path)

if __name__ == "__main__":
    transformer = RealEstateDataTransformer()
    transformer.run()
    print("Properties table to vector store conversion completed.")
