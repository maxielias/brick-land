from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from psycopg2 import sql 
import openai
import os
from dotenv import load_dotenv
from db_connection import PostgresDB

# Load environment variables
load_dotenv('.venv/.env')
os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2')
os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT')
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')

class DescriptionEmbedder:
    def __init__(self, dbname, table, embedding_method='sentence_transformer', embeddings_model='all-MiniLM-L6-v2'):
        self.dbname = dbname
        self.table = table
        self.embedding_method = embedding_method
        self.embeddings_model = embeddings_model
        self.conn = None
        self.cursor = None

        if embedding_method == 'sentence_transformer':
            self.embeddings_model = SentenceTransformer(embeddings_model)
        elif embedding_method == 'openai':
            openai.api_key = os.environ['OPENAI_API_KEY']
        else:
            raise ValueError("embedding_method should be 'sentence_transformer' or 'openai'")

    def connect(self):
        db = PostgresDB(dbname=self.dbname)
        db.connect()
        self.conn = db.get_connection()
        self.cursor = db.cursor

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()

    def fetch_query(self, table='properties'):
        self.cursor.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(table)))
        return self.cursor.fetchall()

    def combine_descriptions(self, query):
        description = [(c[8] if c[8].lower().startswith('departamento') else 'Departamento con ' + c[8]) + '. Pertenece a ' + c[13] for c in query]
        return description

    def index_query(self, query):
        return [q[0] for q in query]

    def generate_embeddings(self, descriptions):
        if self.embedding_method == 'sentence_transformer':
            embeddings = self.embeddings_model.encode(descriptions, convert_to_tensor=False)
        elif self.embedding_method == 'openai':
            embeddings = [openai.Embedding.create(input=desc, model='text-embedding-ada-002')['data'][0]['embedding'] for desc in descriptions]
        return embeddings

    def ensure_column_exists(self, table=None):
        if table is None:
            table = self.table
        self.cursor.execute(f'''
            ALTER TABLE {table} 
            ADD COLUMN IF NOT EXISTS description_embeddings VECTOR(1536);  -- Change 1536 to the appropriate dimension
        ''')
        self.conn.commit()

    def update_table_with_embeddings(self, index_list, embeddings):
        for idx, embedding in tqdm(zip(index_list, embeddings), total=len(index_list)):
            embedding_str = ','.join(map(str, embedding))
            self.cursor.execute(
                sql.SQL('UPDATE {} SET description_embeddings = %s WHERE prop_url = %s').format(sql.Identifier(self.table)),
                (embedding_str, idx)
            )
        self.conn.commit()

    def run(self):
        self.ensure_column_exists()
        query = self.fetch_query()
        descriptions = self.combine_descriptions(query)
        embeddings = self.generate_embeddings(descriptions)
        index_list = self.index_query(query)
        self.update_table_with_embeddings(index_list, embeddings)


# Usage example
if __name__ == '__main__':
    
    description_embedder = DescriptionEmbedder(dbname='brickland', table='properties',
                                               embedding_method='sentence_transformer')
    description_embedder.connect()
    description_embedder.run()
    description_embedder.close()
    print("Embeddings created and updated successfully!")
