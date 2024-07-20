import os
from dotenv import load_dotenv, dotenv_values 
load_dotenv('.venv/.env')
from langchain_community.utilities import SQLDatabase

os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2')
os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT')
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')

db = SQLDatabase.from_uri("sqlite:///data/clean/prop_data.db")
# print(db.dialect)
# print(db.get_usable_table_names())
# result = db.run("SELECT * FROM properties LIMIT 10;")
# print(result)

from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)

agent_executor.invoke(
    "Departamento en Villa Crespo de 3 ambientes de menos de 100 m2",
)