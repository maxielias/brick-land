import os
from dotenv import load_dotenv
from langchain.chains import create_sql_query_chain
from langchain_openai import OpenAI  # Ensure you have the correct LLM setup for LangChain
from langchain_community.utilities import SQLDatabase  # Import the correct utility from langchain_community
import json

class QueryTranslator:
    def __init__(self, db_path='data/db', dbname='brickland.db'):
        self.db_path = db_path
        self.dbname = dbname
        self.full_db_path = os.path.join(self.db_path, self.dbname)
        self.db_conn = SQLDatabase.from_uri(f"sqlite:///{self.full_db_path}")
        self.table_schema = None
        # print(f"Database path: {self.full_db_path}")

    def load_environment_variables(self, env_path):
        load_dotenv(env_path)
        os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2')
        os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT')
        os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')

    def load_table_schema(self, schema_path):
        with open(schema_path, 'r') as schema_file:
            self.table_schema = json.load(schema_file)
        # print("Table schema loaded successfully")

    def query_data(self, question):
        llm = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        self.table_schema = self.load_table_schema('data/raw/attribute_info_properties.json') or []
        schema_description = "\n".join(
            [f"{col['name']}: {col['description']}" for col in self.table_schema]
        )

        # Create a prompt that includes the schema description and examples
        prompt = (
            f"You are an SQL query generator. Use the following table schema to generate a precise SQL query.\n\n"
            f"Table Schema:\n{schema_description}\n\n"
            f"Examples:\n"
            f"1. User Question: 'Estoy buscando un departamento en Palermo de 2 ambientes que salga menos de 200 mil dólares en una zona cerca al subte, ofrece financiamiento?'\n"
            f"   SQL Query: SELECT * FROM properties WHERE prop_location LIKE '%Palermo%' AND prop_rooms = 2 AND CAST(prop_price AS REAL) < 200000 AND prop_description LIKE '%subte%' AND prop_description LIKE '%financiamiento%';\n\n"
            f"2. User Question: 'Quiero encontrar un departamento en Recoleta que tenga 3 habitaciones y esté en un piso alto.'\n"
            f"   SQL Query: SELECT * FROM properties WHERE prop_location LIKE '%Recoleta%' AND prop_bedrooms = 3 AND CAST(prop_floor AS INTEGER) > 5;\n\n"
            f"3. User Question: 'Estoy buscando un departamento que sea un monoambiente en cualquier zona de la ciudad.'\n"
            f"   SQL Query: SELECT * FROM properties WHERE (prop_rooms IS NULL OR prop_rooms = 'nan' OR prop_bedrooms IS NULL OR prop_bedrooms = 'nan') AND (LOWER(prop_url) LIKE '%monoambiente%' OR LOWER(prop_description) LIKE '%monoambiente%');\n\n"
            f"User Question:\n{question}\n\n"
            f"Generate the SQL query based on the user question and the table schema. Use functions like CAST to convert data types if necessary, wherever you need to extract a value from a string. Use LIKE to match a pattern in a string column rather than finding the exact value, for example in searching for a location or a name.\n"
            f"If the user does not provide a specific value, it does not matter, but remember to bring a limit of 5.\n"
            f"Always return the prop_url and project_url columns in the query, as they are essential for the user to access the property and the project information.\n"
            f"For the price, if it's 'nan', assume average price of properties with similar location, rooms and floor, else average of properties selected in the query, but do not change the 'nan' value in the database."
        )

        chain = create_sql_query_chain(llm=llm, db=self.db_conn)
        response = chain.invoke({"question": prompt})
        return response

# # Usage example
# if __name__ == '__main__':
#     query_translator = QueryTranslator(dbname='brickland.db')
#     try:
#         query_translator.load_environment_variables('.venv/.env')
#         query_translator.load_table_schema('data/raw/attribute_info_properties.json')  # Load schema from JSON
#         query = query_translator.query_data("Estoy buscando un departamento en Palermo de 2 ambientes que salga menos de 200 mil dólares "
#                                             "en una zona cerca al subte, ofrece financiamiento?")
#         print(query)
#     except Exception as e:
#         print(f"An error occurred: {e}")
