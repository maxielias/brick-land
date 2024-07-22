import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
load_dotenv('.venv/.env')

class PostgresDB:
    def __init__(self, dbname):
        self.connection = None
        self.cursor = None
        self.dbname = dbname

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD'),
                host=os.getenv('POSTGRES_HOST'),
                port=os.getenv('POSTGRES_PORT')
            )
            self.cursor = self.connection.cursor()
            print("Connection to PostgreSQL established")
        except Exception as error:
            print("Error while connecting to PostgreSQL", error)
            self.connection = None
            self.cursor = None

    def create_database_if_not_exists(self, dbname):
        if self.cursor:
            try:
                self.cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{dbname}'")
                exists = self.cursor.fetchone()
                if not exists:
                    self.cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
                    self.connection.commit()
                    print(f"Database '{dbname}' created successfully")
                else:
                    print(f"Database '{dbname}' already exists")
            except Exception as error:
                print("Error while checking/creating database", error)

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("PostgreSQL connection is closed")

    def get_connection(self):
        if self.connection:
            return self.connection
        else:
            print("No active connection")
            return None

    def main(self, dbname=None):
        self.connect()
        if dbname is None:
            dbname = self.dbname
        if self.get_connection():
            self.create_database_if_not_exists(dbname)
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            self.connection.commit()
