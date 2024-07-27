import sqlite3
import os

class QueryAgent:
    def __init__(self, db_path='data/db', dbname='brickland.db'):
        self.db_path = db_path
        self.dbname = dbname
        self.full_db_path = os.path.join(self.db_path, self.dbname)
        self.conn = None
        self.cursor = None
        # print(f"Database path: {self.full_db_path}")

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.full_db_path)
            self.cursor = self.conn.cursor()
            # print(f"Connection to SQLite database '{self.full_db_path}' established")
        except sqlite3.Error as error:
            print(f"Error while connecting to SQLite: {error}")
            self.conn = None
            self.cursor = None
            raise Exception("Failed to establish a database connection")

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()
            # print("SQLite connection is closed")

    def execute_queries(self, queries):
        results = []
        for query in queries:
            try:
                # print(f"Executing query: {query}")
                self.cursor.execute(query)
                result = self.cursor.fetchall()
                results.append(result)
                # print(f"Query result: {result}")
            except sqlite3.Error as error:
                print(f"Error executing query '{query}': {error}")
                results.append(None)
        return results

# if __name__ == "__main__":
#     query_agent = QueryAgent()
#     query_agent.connect()
#     queries = [
#         "SELECT * FROM properties WHERE prop_rooms = 2 AND prop_location LIKE '%Palermo%' AND CAST(prop_price AS REAL) < 200000 LIMIT 5"
#     ]
#     results = query_agent.execute_queries(queries)
#     print(results)
#     query_agent.close()