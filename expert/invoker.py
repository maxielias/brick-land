import os
from dotenv import load_dotenv, dotenv_values
load_dotenv('.venv/.env')
import sqlite3
from langchain.schema import Document
from pydantic import BaseModel, Field
from typing import List, Optional

class DatabaseLoader:
    def __init__(self, db_path):
        self.db_path = db_path

    def load(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM properties")
        rows = cursor.fetchall()
        conn.close()

        documents = []
        for row in rows:
            doc = Document(
                page_content=row[7],  # assuming 'prop_description' is the 8th column
                metadata={
                    "address": row[0],
                    "floor": row[1],
                    "price": row[2],
                    "m2": row[3],
                    "rooms": row[4],
                    "bedrooms": row[5],
                    "location": row[6],
                    "images": row[8],
                    "project_url": row[9],
                    "project_district": row[10],
                    "project_address": row[11],
                    "project_description": row[12],
                    "project_images": row[13],
                    "prop_url": row[14]
                }
            )
            documents.append(doc)
        return documents

    def update_property(self, prop_url, **kwargs):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Construct the update query dynamically based on provided keyword arguments
        columns = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        values.append(prop_url)

        cursor.execute(f"UPDATE properties SET {columns} WHERE prop_url = ?", values)
        conn.commit()
        conn.close()

class PropertySearch(BaseModel):
    """
    Search over the properties database for a property that matches the given criteria. Data is in Spanish.
    """
    prop_url: Optional[str] = Field(None, description="URL of the property")
    prop_address: Optional[str] = Field(None, description="Address of the property")
    prop_floor: Optional[str] = Field(None, description="Floor of the property")
    prop_price: Optional[float] = Field(None, description="Price of the property")
    prop_m2_price: Optional[float] = Field(None, description="Price per square meter of the property which is the total\
                                           price divided by the covered square meters of the property,\
                                           plus half of the semi-covered and uncovered meters")
    prop_location: Optional[str] = Field(None, description="Location of the property")
    prop_ammenities: Optional[List[str]] = Field(None, description="Ammenities of the property in the building")
    prop_description: Optional[str] = Field(None, description="Description of the property")
    prop_data: Optional[List[str]] = Field(None, description="Data of all the services included in the property")
    project_district: Optional[str] = Field(None, description="District of the project")
    project_address: Optional[str] = Field(None, description="Address of the project")

os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2')
os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT')
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')

db_loader = DatabaseLoader('data/clean/prop_data.db')
docs = db_loader.load()

# Example update
# db_loader.update_property('some_prop_url', prop_price=500000, prop_m2=80)

context_prop = 'este va a ser el contexto de las propiedades en capital'
context_advice = 'este va a ser el contexto de los consejos para comprar propiedades en pozo'
context_district = 'este va a ser el contexto de los barrios de capital'

template = """
Sos un asistente virtual experto en propiedades inmobiliarias. Debes asistir a tus clientes a invertir o comprar propiedades en pozo a la venta.
Para ello, debes responder a las preguntas que te hagan tus clientes de manera clara y concisa.
La pregunta es la siguiente: {question}

Es importante descomponer la pregunta en partes más pequeñas para poder responderla de manera efectiva.
Si es posible, la descomposición debe ser en términos de:

1) Detalles sobre la propiedad que desea adquirir el cliente. Utiliza el contexto {context_prop} para proporcionar información relevante.
   Ejemplos: "busco un departamento de 2 ambientes en Palermo", "quiero comprar un monoambiente con balcón en Belgrano",
   "estoy interesado en un 3 ambientes luminoso de 70 m2 en Villa Crespo", "me gustaría adquirir un dúplex en Caballito".

2) Consejos o sugerencias sobre compra/negociación, adquisición de propiedades en pozo, etc., dentro del contexto de la pregunta.
   Utiliza el contexto {context_advice} para ofrecer recomendaciones útiles y prácticas.

3) Detalles sobre la ubicación de la propiedad. Utiliza el contexto {context_district} para proporcionar información relevante sobre la zona.
   Ejemplos: "¿Qué tal es la seguridad en la zona?", "¿Cómo es la infraestructura y los servicios en el barrio?",
   "¿Qué tipo de demografía tiene el área?"

4) Análisis Comparativo: Proporciona comparaciones con propiedades similares en diferentes barrios o ciudades para dar una mejor perspectiva.

5) Información de Financiamiento: Proporciona información sobre opciones de financiamiento, tasas de interés actuales, y consejos sobre cómo obtener el mejor trato.

6) Seguridad y Calidad de Vida: Proporciona información sobre la seguridad del barrio y la calidad de vida, como proximidad a parques, centros comerciales, escuelas, y transporte público.

En caso de que no sea posible descomponer la pregunta en estas partes, responde a la pregunta de la mejor manera posible,
utilizando la cantidad de descomposiciones que sean factibles, ya sea 1, 2 o 3, siendo una la mínima, que significa responder solo a la pregunta directamente.

Recuerda siempre ofrecer información precisa, relevante y útil para el cliente.
"""
