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
                page_content=row[7],
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
