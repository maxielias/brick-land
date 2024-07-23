import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from db_manager.db_connection import PostgresDB
from sentence_transformers import SentenceTransformer
import openai

class TableSchemaExpert:
    def __init__(self, db_name, table, model_name="gpt-4", embedding_method='sentence_transformer', embeddings_model='all-MiniLM-L6-v2'):
        self.db = PostgresDB(dbname=db_name)
        self.model = ChatOpenAI(model=model_name)
        self.table = table
        self.embedding_method = embedding_method
        self.embeddings_model_name = embeddings_model
        self.embeddings_model = None

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

    def connect_to_database(self):
        self.db.connect()

    def fetch_data_from_table(self):
        query = f"SELECT * FROM {self.table} LIMIT 1;"  # Fetch only the first row
        self.db.cursor.execute(query)
        rows = self.db.cursor.fetchall()
        colnames = [desc[0] for desc in self.db.cursor.description]
        dataframe = pd.DataFrame(rows, columns=colnames)
        return dataframe

    def describe_data_attributes(self, dataframe):
        dataframe_head = dataframe.head(1).to_json(orient='records')  # Ensure we are processing only the first row
        prompt = (
            "Below is a table with information about hotel rooms. "
            "Return a JSON list with an entry for each column."
            "Below is a table with information about hotel rooms.\n"
            "Provide a description that also adds specific details about the data, taking into account "
            "that it's a database about real state projects with their properties." 
            "Specially for the description columns, provide a detailed explanation of the data.\n"
            "Each entry should have "
            '{"name": "column name", "description": "column description", "type": "column data type"}'
            f"\n\n{dataframe_head}\n\nJSON:\n"
        )
        res = self.model.predict(prompt)
        attribute_info = json.loads(res)
        print(prompt)
        return attribute_info

    def save_data_as_json(self, data, file_path):
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def close_database_connection(self):
        self.db.close()

# Example usage:
if __name__ == "__main__":
    expert = TableSchemaExpert(db_name="brickland", table="properties", embedding_method='sentence_transformer')
    expert.load_environment_variables('.env')

    expert.connect_to_database()
    latest_price = expert.fetch_data_from_table()

    attribute_info = expert.describe_data_attributes(latest_price)
    print(attribute_info)

    expert.save_data_as_json(attribute_info, 'data/raw/attribute_info.json')
    expert.close_database_connection()
