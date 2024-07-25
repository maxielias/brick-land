import os
import sqlite3
from dotenv import load_dotenv
from langchain.chains import create_sql_query_chain
from langchain_openai import OpenAI  # Ensure you have the correct LLM setup for LangChain
from sqlalchemy import create_engine, MetaData
from langchain_community.utilities import SQLDatabase  # Import the correct utility from langchain_community

class QueryTranslator:
    def __init__(self, dbname='brickland.db'):
        self.db_path = os.path.abspath(os.path.join('data', 'db'))
        self.dbname = os.path.join(self.db_path, dbname)
        self.engine = None
        self.metadata = None
        self.db = None
        print(f"Database path: {self.dbname}")

    def load_environment_variables(self, env_path):
        load_dotenv(env_path)
        os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2')
        os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT')
        os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')

    def connect(self):
        try:
            self.engine = create_engine(f'sqlite:///{self.dbname}')
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.engine)
            self.db = SQLDatabase(engine=self.engine)  # Create SQLDatabase object
            print(f"Connection to SQLite database '{self.dbname}' established")
        except Exception as error:
            print(f"Error while connecting to SQLite: {error}")
            self.engine = None
            raise Exception("Failed to establish a database connection")

    def close(self):
        if self.engine:
            self.engine.dispose()
            print("SQLite connection is closed")

    def query_data(self, question):
        llm = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        chain = create_sql_query_chain(llm=llm, db=self.db)
        response = chain.invoke({"question": question})
        return response

# # Usage example
# if __name__ == '__main__':
#     query_translator = QueryTranslator(dbname='brickland.db')
#     try:
#         query_translator.load_environment_variables('.venv/.env')
#         query_translator.connect()
#         query = query_translator.query_data("How many projects are in the database?")
#         print(query)
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     finally:
#         query_translator.close()
