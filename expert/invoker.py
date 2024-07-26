import os
from dotenv import load_dotenv
import json
from query_decomposition_expert import QueryAnalyzer
from query_router_expert import QueryRouter
from query_translator_expert import QueryTranslator
# from table_data_expert import TableSchemaExpert

class ExpertAssistant:
    def __init__(self):
        self.db_path = 'data/db/brickland.db'
        self.env_path = '.venv/.env'
        self.load_environment_variables(self.env_path)
        self.query_analyzer = QueryAnalyzer()
        self.query_router = QueryRouter()
        self.query_translator = QueryTranslator()
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
    
    def query_source(self, sub_queries):
        query_source_list = []
        for sub_query in sub_queries:
            data_source = self.query_router.analyze_query(sub_query)
            query_source_list.append({'question': sub_query, 'source': data_source})
        return query_source_list

    def load_schema(self, query_source_list):
        if any(e for e in [item for sublist in [d['source'].datasource for d in list_of_sources] 
                           for item in sublist] if 'properties_table' in e):
            try:
                with open('data/raw/attribute_info.json', 'r') as json_file:
                    table_metadata = json.load(json_file)
                print("Found Table Schema Metadata")
                return table_metadata
            except FileNotFoundError:
                print("Table Schema Metadata Not Found")
                return None

    def create_prompt(self, user_query):
        sub_queries = self.create_sub_questions(user_query)
        self.process_user_query(sub_queries)

# Template for the expert assistant
# template = """
# Eres un asistente experto en ayudar a compradores o inversores de propiedades. Tienes acceso a una base de datos 
# de propiedades de pozo en la Ciudad Autónoma de Buenos Aires (Capital Federal) y documentación curada sobre artículos 
# donde se analizan las ventajas y desventajas de comprar de pozo, así como consejos sobre cómo llevar a cabo la inversión 
# y qué errores evitar. También puedes responder preguntas sobre la zona donde se encuentra el emprendimiento, 
# la ubicación del inmueble, el barrio, la cercanía a medios de transporte, colegios, etc. 

# Dada una pregunta del usuario, desglósala en sub-preguntas distintas que necesitas responder para poder contestar 
# la pregunta original. La descomposición debe ser en términos de:
# 1) Preguntas específicas de un emprendimiento o departamento: Precio, m2 de un departamento, amenities (pileta, parrilla, sum, etc), 
# servicios del inmueble o edificio y especificaciones del edificio, etc.
# 2) Sugerencias generales sobre cómo comprar un departamento, ventajas y desventajas de comprar de pozo, 
# cuestiones legales y costos relacionados a la compra. Por ejemplo: Los costos de escrituración, los plazos de entrega, 
# los costos de mantenimiento, si es un fideicomiso al costo, si se puede comprar con crédito hipotecario, 
# cómo suele ser la operatoria de compra, etc.
# 3) Preguntas sobre la ubicación del inmueble, el barrio, la cercanía a medios de transporte, colegios, etc.

# Toda la información es para la zona de Capital Federal, Argentina.
# """

if __name__ == '__main__':
    expert = ExpertAssistant()
    user_query = "Estoy buscando un departamento en Palermo de 2 ambientes que salga menos de 200 mil dólares en una zona cerca al subte,"
    "ofrece financiamiento?"
    sub_queries = expert.create_sub_questions(user_query)
    list_of_sources = expert.query_source(sub_queries)
    table_schema = expert.load_schema(list_of_sources)
    print(sub_queries, list_of_sources, table_schema, sep='\n')
