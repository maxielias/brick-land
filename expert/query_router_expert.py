import os
from dotenv import load_dotenv, dotenv_values
from langchain.output_parsers import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Literal
from query_decomposition_expert import QueryAnalyzer


class Router(BaseModel):
    """
    There are three main sources of data:
    1) You have access to a database of properties under construction, just finished, or about to be constructed, or pre-sale.
    2) You have access to curated documentation on articles that analyze the advantages and disadvantages of buying properties under construction, as well as provide advice on how to proceed with the investment and what mistakes to avoid.
    3) You have access to a language model and web search tools that can answer questions about the area where the development is located, including the location of the property, the neighborhood, proximity to transportation, schools, etc.
    The information in the database is about properties available for purchase in developments under construction in the Autonomous City of Buenos Aires (Capital Federal).
    """
    datasource: List[Literal["properties_table", "pdf_docs", "llm_expertise"]] = Field(
        ...,
        description="Given the question from the user choose the most relevant data source to answer the question.",
    )


class QueryRouter:
    def __init__(self, env_path='.venv/.env'):
        self.load_environment_variables(env_path)
        self.system_message = """
            Es un experto en decidir las mejores fuentes de datos para las preguntas del usuario. \
            Si es más de una pregunta estarán separadas por "\n".
            Las consultas de clientes deben estar dirigidas a comprar o invertir en un emprendimiento \
            de pozo (inmubles a construir, en construcción o a estrenar) para vivienda permanente o como inversión inmobiliaria. \
            Existen tres grandes fuentes de datos:
            1) Tienes acceso a una base de datos de propiedades de pozo.
            2) Tienes acceso a documentación curada sobre artículos donde se analizan las ventajas y desventajas de comprar de pozo \
            como también se dan consejos sobre como actuar para llevar a cabo la inversión y que errores evitar cometer.
            3) Tienes acceso al modelo de lenguaje que puede responder preguntas sobre la zona donde se encuentra el emprendimiento, \
            sobre la ubicación del inmueble, el barrio, la cercanía a medios de transporte, colegios, parques, etc. \
            En caso de que la pregunta no se refiera específicamente a la descripción de un inmueble, \
            o datos particulares del proyecto (precio, dirección, piso, servicios comunes, ammenities, financiación específica que ofrece ese proyecto o inmueble), \
            o conjunto de proyectos o inmuebles que devuelva al experto, no incluir la fuente de datos de la base de datos. \
            Por Ejemplo: \
            - ¿Cuáles son las ventajas y desventajas de comprar un departamento de pozo en Palermo? \
            - ¿Es seguro el barrio de Boedo? \
            - ¿Cuál es la cercanía a medios de transporte en Palermo? \
            - ¿Cuál es la cercanía de los departamentos de 2 ambientes en Palermo a medios de transporte y colegios?
            - ¿Como se paga un departamento de pozo?
            En caso de no encontrar una fuente de datos relevante, se proporcionará una respuesta vacía.
        """
        """
        He is an expert in deciding the best data sources for user questions.
        If there is more than one question, they will be separated by "\n".
        Client inquiries should be directed towards buying or investing in a development under construction (properties to be built, under construction, or newly built) for permanent residence or as a real estate investment.
        There are three main sources of data:
            1) You have access to a database of properties under construction.
            2) You have access to curated documentation on articles that analyze the advantages and disadvantages of buying properties under construction, as well as provide advice on how to proceed with the investment and what mistakes to avoid.
            3) You have access to a language model and web search agent that can answer questions about the area where the development is located, including the location of the property, the neighborhood, proximity to transportation, schools, parks, etc.
        If the question does not specifically refer to the description of a property, or particular project data (price, address, floor, common services, amenities, specific financing offered by that project or property), or a set of projects or properties returned to the expert, do not include the database as a data source.
        For Example:
            - What are the advantages and disadvantages of buying an off-plan apartment in Palermo?
            - Is the Boedo neighborhood safe?
            - What is the proximity to transportation in Palermo?
            - What is the proximity of 2-room apartments in Palermo to transportation and schools?
            - How do you pay for an off-plan apartment?
        If no relevant data source is found, an empty response will be provided.
        """
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_message),
                ("human", "{question}"),
            ]
        )
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.structured_llm = self.llm.with_structured_output(Router)
        self.query_router = self.prompt | self.structured_llm

    def load_environment_variables(self, env_path):
        load_dotenv(env_path)
        os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2')
        os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT')
        os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')

    def analyze_query(self, question):
        return self.query_router.invoke({"question": question})


# if __name__ == "__main__":
#     question = "Sugerime un departamento en Palermo de 2 ambientes con pileta y parrilla. \
#         Me conviene comprar si no conozco a la desarrolladora inmobiliaria? Es segura la zona?"
#     query_analyzer = QueryAnalyzer()
#     query_router = QueryRouter()
#     queries = query_analyzer.analyze_query(question)
#     print(queries)
#     response = query_analyzer.transform_queries_to_string(queries=queries)
#     data_sources = query_router.analyze_query(response)
#     print(data_sources)
