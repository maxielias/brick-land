import os
from dotenv import load_dotenv
import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from query_decomposition_expert import QueryAnalyzer
from query_router_expert import QueryRouter
from query_translator_expert import QueryTranslator
from query_agent import QueryAgent
from langchain_openai import ChatOpenAI

class ExpertAssistant:
    def __init__(self):
        self.db_path = 'data/db'
        self.dbname = 'brickland.db'
        self.env_path = '.venv/.env'
        self.load_environment_variables(self.env_path)
        self.embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.query_analyzer = QueryAnalyzer()
        self.query_router = QueryRouter()
        self.query_translator = QueryTranslator()
        self.query_agent = QueryAgent(db_path=self.db_path, dbname=self.dbname)  # Initialize the QueryAgent
        self.llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # self.table_data_expert = TableSchemaExpert()

    def load_environment_variables(self, env_path):
        load_dotenv(env_path)
        os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2')
        os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT')
        os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')

    def create_sub_questions(self, user_query):
        sub_queries = self.query_analyzer.analyze_query(user_query)
        return sub_queries
    
    def get_transformed_question(self, sub_queries):
        transformed_question = self.query_analyzer.transform_queries_to_string(sub_queries)
        return transformed_question
    
    def query_source(self, sub_queries):
        query_source_list = []
        for sub_query in sub_queries:
            data_source = self.query_router.analyze_query(sub_query)
            query_source_list.append({'question': sub_query, 'source': data_source})
        return query_source_list

    def load_schema(self, query_source_list):
        if any(e for e in [item for sublist in [d['source'].datasource for d in query_source_list] 
                           for item in sublist] if 'properties_table' in e):
            try:
                with open('data/raw/attribute_info_properties.json', 'r') as json_file:
                    table_metadata = json.load(json_file)
                print("Found Table Schema Metadata")
                return table_metadata
            except FileNotFoundError:
                print("Table Schema Metadata Not Found")
                return None
            
    def translate_query(self, query_source_list, table_schema):
        try:
            translated_queries = []
            if table_schema is None:
                return None
            for query in query_source_list:
                if isinstance(query['source'].datasource, list):
                    cond_true = any(e for e in query['source'].datasource if 'properties_table' in e) 
                if query['source'].datasource == 'properties_table' or cond_true:
                    sub_query = query['question'].decomposition_query
                    translated_query = self.query_translator.query_data(sub_query)
                    translated_queries.append(translated_query)
            return translated_queries
        except Exception as e:
            # print(f"Error translating query: {e}")
            return None
    
    def general_advice_query(self, query_source_list):
        general_advice_context = []
        for query in query_source_list:
            cond_true = False
            if isinstance(query['source'].datasource, list):
                cond_true = any(e for e in query['source'].datasource if 'pdf_docs' in e)
            if query['source'].datasource == 'pdf_docs' or cond_true:
                sub_query = query['question'].decomposition_query
                chroma_db = Chroma(persist_directory="./chroma_db", embedding_function=self.embedding_model)
                for query in sub_query:
                    docs = chroma_db.similarity_search(query)
                    if isinstance(docs, list):
                        for doc in docs:
                            general_advice_context.append(doc)
                    else:
                        general_advice_context.append(docs)
        return general_advice_context

    def create_prompt(self, user_query, transformed_questions, translated_queries, general_adivice_context,
                      query_results):
        context = (
        "You are an expert assistant in helping potential property buyers or investors, find a project or property that fits"
        "their preferences. "
        "You have access to a database of real state pojects in the following states: "
        "pre-construction, to be finished within a few months or years, or brand new. "
        "Each project may have several apartments or properties for sale. "
        "All properties are located in Buenos Aires City (Ciudad Autónoma de Buenos Aires or Capital Federal)"
        "For general purpose questions, not related to the speficifications of the project or propoerty, "
        "there are curated documents about the advantages and disadvantages of buying such properties, advice about"
        "buying off-plan, as well as advice on how to carry out the investment and what mistakes to avoid. "
        "You can also answer questions about the area where the project is located, the location of the property, "
        "the neighborhood, proximity to transportation, schools, etc."
        )
        template = (
            f"Expert context:\n{context}\n\n"
            f"Answer original question (in Spanish):\n{user_query}\n\n"
            f"with the following translated question (in English):\n{user_query}\n\n"
            f"Make use of decomposed questions:\n{transformed_questions}\n\n"
            f"That will be translated into the following queries:\n{translated_queries}\n\n"
            f"Query Results:\n{query_results}\n\n"
            f"If query result is None and translated queries is empty or None, provide general advice \n"
            f"and/or if the question is not related to the specifications of the project or property, you can provide general advice.\n"
            f"If possible, create a list of all the key concepts and add important information keeping in mind the"
            f"General Advice Context:\n{general_adivice_context}\n\n"
            f"Answer the above questions with the provided information."
            f"In case there are multiple properties that meet the criteria, provide a list including the url of the property and/or project."
            f"Provide the answer in Spanish in the case of a question in English."
            f"Remeber to provide the answer in a professional manner."
            f"Merge the answers into a single response."
        )
        return template

    def process_user_query(self, user_query):
        sub_queries = self.create_sub_questions(user_query)
        transformed_questions = self.get_transformed_question(sub_queries)
        list_of_sources = self.query_source(sub_queries)
        table_schema = self.load_schema(list_of_sources)
        translated_queries = self.translate_query(list_of_sources, table_schema)
        general_advice_context = self.general_advice_query(list_of_sources)
        try:
            self.query_agent.connect()
            query_results = self.query_agent.execute_queries(translated_queries)
            self.query_agent.close()
        except Exception as e:
            translated_queries = "NO specific queries about a praticular project or property"
            query_results = "NO specific queries about a praticular project or property"
        if translated_queries is None:
            translated_queries = "NO specific queries about a praticular project or property"
            query_results = "NO specific queries about a praticular project or property"
        prompt = self.create_prompt(user_query, transformed_questions, translated_queries, general_advice_context,
                      query_results)
        response = self.llm.predict(prompt)
        return response

if __name__ == '__main__':
    expert = ExpertAssistant()
    user_query = ("Que tengo que saber para comprar un departamento de pozo en Buenos Aires?")
    response = expert.process_user_query(user_query)
    print(response)
