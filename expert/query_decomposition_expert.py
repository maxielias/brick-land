import os
from dotenv import load_dotenv, dotenv_values
from langchain.output_parsers import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field


class SubQuery(BaseModel):
    """
    Existen tres grandes fuentes de datos:
    1) Tienes acceso a una base de datos de propiedades de pozo.
    2) Tienes acceso a documentación curada sobre artículos donde se analizan las ventajas y deseventajas de comprar de pozo \
    como también se dan consejos sobre como actuar para llevar a cabo la inversión y que errores evitar cometer.
    3) Tienes acceso al modelo de lenguaje que puede responder preguntas sobre la zona donde se encuentra el emprendimiento, \
    sobre la ubicación del inmueble, el barrio, la cercanía a medios de transporte, colegios, etc. \
    La información en la base de datos sobre inmuebles para comprar en emprendimientos de pozo \
    en la Ciudad Autónoma de Buenos Aires (Capital Federal).
    """
    decomposition_query: str = Field(
        ...,
        description="Consulta muy específica que se puede realizar a la base de datos de propiedades de pozo, \
                    documentos curados sobre las ventajas o desventajas de comprar de pozo o sobre las zonas \
                    donde se encuentran los emprendimientos para que responda el modelo de lenguaje.",
    )


class QueryAnalyzer:
    def __init__(self, env_path='.venv/.env'):
        self.load_environment_variables(env_path)
        self.system_message = """
            Eres un experto en convertir preguntas de los usuarios en consultas avanazadas para responder de \
            manera más efectiva a las consultas de clientes que buscan comprar o invertir en un emprendimiento \
            de pozo (inmubles a construir, en construcción o a estrenar) para vivienda permanente o como inversión inmobiliaria. \
            Existen tres grandes fuentes de datos:
            1) Tienes acceso a una base de datos de propiedades de pozo.
            2) Tienes acceso a documentación curada sobre artículos donde se analizan las ventajas y deseventajas de comprar de pozo \
            como también se dan consejos sobre como actuar para llevar a cabo la inversión y que errores evitar cometer.
            3) Tienes acceso al modelo de lenguaje que puede responder preguntas sobre la zona donde se encuentra el emprendimiento, \
            sobre la ubicación del inmueble, el barrio, la cercanía a medios de transporte, colegios, etc.\
            Utilizaras dos estrategias para optimizar las preguntas de los usuarios:
            1) "query decomposition": \
                Realiza la descomposición de consultas. Dada una pregunta del usuario, desglósala en subpreguntas \
                distintas que necesitas responder para poder contestar la pregunta original.
                Si hay siglas o palabras que no conoces, no intentes reformularlas.
                Es importante descomponer la pregunta en partes más pequeñas para poder responderla de manera efectiva. \
                Si es posible, la descomposición debe ser en términos de:
                1) Preguntas específicas de un emprendimiento o departamento: Precio, m2 de un departamento, amenities (pileta, parrilla, sum, etc) \
                servicios del inmueble o edificio y especificaciones del edificio, etc. \
                2) Sugerencias generales sobre cómo comprar un departamento, ventajas y desventajas de comprar de pozo, \
                cuestiones legales y costos relacionados a la compra. \
                Por ejemplo: Los costos de escrituración, los plazos de entrega, los costos de mantenimiento, si es un fideicomiso al costo, \
                si se puede comprar con crédito hipotecario, como suele ser la operatoria de compra, etc.
                3) Preguntas sobre la ubicación del inmueble, el barrio, la cercanía a medios de transporte, colegios, etc. \
                Para cada uno de los 3 puntos anteriores se pueden generar mas de una subdivisión de preguntas. \
            2) "step back prompting": \
                Tomaras una pregunta específica y extraer una pregunta más genérica que llegue a los principios subyacentes \
                necesarios para responder a la pregunta específica. Se le preguntará acerca de los aspectos aclarados en el texto y en la estrategia \
                de "query decomposition". \
            Cada estratefga se ejecutará de manera individual para generar una mayor de robustez en la respuesta.
            Toda la información es para la zona de Capital Federal, Argentina.
            En caso de no poder responder a la pregunta devolver una pregunta más específica para que el cliente pueda responder o responder \
            "Mi conocimiento no me permite responder a esa pregunta en este momento".
        """
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_message),
                ("human", "{question}"),
            ]
        )
        self.llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
        self.llm_with_tools = self.llm.bind_tools([SubQuery])
        self.parser = PydanticToolsParser(tools=[SubQuery])
        self.query_analyzer = self.prompt | self.llm_with_tools | self.parser

    def load_environment_variables(self, env_path):
        load_dotenv(env_path)
        os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2')
        os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT')
        os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')

    def analyze_query(self, question):
        return self.query_analyzer.invoke({"question": question})


# if __name__ == "__main__":
#     analyzer = QueryAnalyzer()
#     question = "¿Cuáles son las ventajas y desventajas de comprar un departamento de pozo?"
#     response = analyzer.analyze_query(question)
#     print(response)
