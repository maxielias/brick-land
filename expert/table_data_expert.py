import sys
import os
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, MetaData
from sentence_transformers import SentenceTransformer
import openai

class TableSchemaExpert:
    def __init__(self, db_path, table, model_name="gpt-4o-mini", embedding_method='sentence_transformer', embeddings_model='all-MiniLM-L6-v2'):
        self.db_path = db_path
        self.table = table
        self.model = None
        self.model_name = model_name
        self.embedding_method = embedding_method
        self.embeddings_model_name = embeddings_model
        self.embeddings_model = None
        self.engine = None
        self.conn = None
        self.metadata = None

        if embedding_method == 'sentence_transformer':
            self.embeddings_model = SentenceTransformer(embeddings_model)
        elif embedding_method == 'openai':
            openai.api_key = os.getenv('OPENAI_API_KEY')
        else:
            raise ValueError("embedding_method should be 'sentence_transformer' or 'openai'")

    def load_environment_variables(self, env_path):
        load_dotenv(env_path)
        os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2')
        os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT')
        os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')
        # Ensure the API key is loaded
        self.openai_api_key = os.getenv('OPENAI_API_KEY')

    def connect_to_database(self):
        try:
            self.engine = create_engine(f'sqlite:///{self.db_path}')
            self.conn = self.engine.connect()
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.engine)
            print(f"Connected to SQLite database at '{self.db_path}'")
        except Exception as error:
            print(f"Error while connecting to SQLite: {error}")
            self.conn = None
            raise Exception("Failed to establish a database connection")

    def fetch_data_from_table(self):
        query = f"SELECT * FROM {self.table} LIMIT 1;"
        dataframe = pd.read_sql(query, self.conn)
        return dataframe

    def describe_data_attributes(self, df):
        df_head = df.head(1).to_json(orient='records')
        prompt = (
            "Below is a table with information about real estate projects and the properties they have on sale."
            "Each project may be listing more than one apartment, so the table has for each property the data"
            "about the project it belongs to."
            "Return a JSON list with an entry for each column."
            "Provide a description that also adds specific details about the data, taking into account "
            "that it's a database about real estate projects with their properties." 
            "Specially for the description columns, provide a detailed explanation of the data.\n"
            "Each entry should have "
            '{"name": "column name", "description": "column description", "type": "column data type"}'
            f"\n\n{df_head}\n\nJSON:\n"
        )
        self.model = ChatOpenAI(model=self.model_name, openai_api_key=self.openai_api_key)
        res = self.model.predict(prompt)
        attribute_info = json.loads(res)
        print(prompt)
        return attribute_info

    def save_data_as_json(self, data, file_path):
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def close_database_connection(self):
        if self.conn:
            self.conn.close()
            print("SQLite connection is closed")

    def create_and_save_table_schema(self, db_path='data/db/brickland.db', table='properties'):
        self.db_path = db_path
        self.table = table
        self.load_environment_variables('.venv/.env')
        self.connect_to_database()
        latest_data = self.fetch_data_from_table()
        attribute_info = self.describe_data_attributes(latest_data)
        self.save_data_as_json(attribute_info, 'data/raw/attribute_info.json')
        self.close_database_connection()

# # Example usage:
# if __name__ == "__main__":
#     db_path = 'data/db/brickland.db'
#     expert = TableSchemaExpert(db_path=db_path, table="properties", embedding_method='sentence_transformer')
#     expert.load_environment_variables('.venv/.env')

#     expert.connect_to_database()
#     latest_data = expert.fetch_data_from_table()

#     attribute_info = expert.describe_data_attributes(latest_data)
#     print(attribute_info)

    # expert.save_data_as_json(attribute_info, 'data/raw/attribute_info.json')
    # expert.close_database_connection()
 