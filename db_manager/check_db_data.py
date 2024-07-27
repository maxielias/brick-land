import sqlite3
import os

class PropDbViewer:
    def __init__(self, dbname='brickland.db', table='properties'):
        self.db_path = os.path.abspath(os.path.join('data', 'db'))
        self.dbname = os.path.join(self.db_path, dbname)
        self.table = table
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.dbname)
            self.cursor = self.conn.cursor()
            print(f"Connection to SQLite database '{self.dbname}' established")
        except sqlite3.Error as error:
            print(f"Error while connecting to SQLite: {error}")
            self.conn = None
            self.cursor = None

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()
            print("SQLite connection is closed")

    def view_data(self, table=None):
        if table:
            self.table = table
        if self.cursor:
            try:
                self.cursor.execute(f"SELECT * FROM {self.table} LIMIT 5")
                rows = self.cursor.fetchall()
                if rows:
                    for row in rows:
                        print(row)
                else:
                    print(f"No data found in table '{self.table}'")
            except sqlite3.Error as error:
                print(f"Error while querying the database: {error}")

# Usage example
if __name__ == '__main__':
    prop_db_viewer = PropDbViewer(dbname='brickland.db')
    try:
        prop_db_viewer.connect()
        prop_db_viewer.view_data()
        prop_db_viewer.view_data(table='prop_images_href')
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        prop_db_viewer.close()
