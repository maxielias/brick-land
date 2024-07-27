import json
import sqlite3
import os

class PropDb:
    def __init__(self, dbname='brickland.db', table='properties'):
        self.db_path = os.path.abspath(os.path.join('data', 'db'))
        os.makedirs(self.db_path, exist_ok=True)
        self.dbname = os.path.join(self.db_path, dbname)
        self.table = table
        self.images_table = 'prop_images_href'
        self.conn = None
        self.cursor = None
        print(f"Database path: {self.dbname}")

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.dbname)
            self.cursor = self.conn.cursor()
            print(f"Connection to SQLite database '{self.dbname}' established")
        except sqlite3.Error as error:
            print(f"Error while connecting to SQLite: {error}")
            self.conn = None
            self.cursor = None
            raise Exception("Failed to establish a database connection")

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()
            print("SQLite connection is closed")

    def create_tables(self):
        self.cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {self.table} (
            prop_url TEXT PRIMARY KEY,
            prop_address TEXT,
            prop_floor TEXT,
            prop_price TEXT,
            prop_m2 TEXT,
            prop_rooms TEXT,
            prop_bedrooms TEXT,
            prop_location TEXT,
            prop_description TEXT,
            project_url TEXT,
            project_district TEXT,
            project_address TEXT,
            project_description TEXT
        )
        ''')
        
        self.cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {self.images_table} (
            prop_url TEXT,
            project_url TEXT,
            prop_images TEXT,
            project_images TEXT,
            FOREIGN KEY(prop_url) REFERENCES {self.table}(prop_url),
            FOREIGN KEY(project_url) REFERENCES {self.table}(project_url)
        )
        ''')
        self.conn.commit()

    def property_exists(self, prop_url, table=None):
        if table is None:
            table = self.table
        self.cursor.execute(f'SELECT 1 FROM {table} WHERE prop_url = ?', (prop_url,))
        return self.cursor.fetchone() is not None

    def insert_or_update_property(self, project_data, prop_data, table=None):
        if table is None:
            table = self.table
        if prop_data is None:
            return None
        parameters = (
            prop_data.get('prop_url'),
            prop_data.get('prop_address', ''),
            prop_data.get('prop_floor', ''),
            prop_data.get('prop_price', ''),
            str(prop_data.get('prop_m2', 'nan')),
            str(prop_data.get('prop_rooms', 'nan')),
            str(prop_data.get('prop_bedrooms', 'nan')),
            prop_data.get('prop_location', ''),
            prop_data.get('prop_description', 'nan'),
            project_data.get('project_url', ''),
            project_data.get('project_district', ''),
            project_data.get('project_address', ''),
            project_data.get('project_description', '')
        )

        image_parameters = (
            prop_data.get('prop_url'),
            project_data.get('project_url', ''),
            json.dumps(prop_data.get('prop_images', []), ensure_ascii=False),
            json.dumps(project_data.get('project_images', []), ensure_ascii=False)
        )

        if self.property_exists(prop_data['prop_url'], table):
            self.cursor.execute(f'''
            UPDATE {table}
            SET prop_address = ?, prop_floor = ?, prop_price = ?, prop_m2 = ?, prop_rooms = ?, 
                prop_bedrooms = ?, prop_location = ?, prop_description = ?, 
                project_url = ?, project_district = ?, project_address = ?, 
                project_description = ?
            WHERE prop_url = ?
            ''', parameters)
            
            self.cursor.execute(f'''
            UPDATE {self.images_table}
            SET project_url = ?, prop_images = ?, project_images = ?
            WHERE prop_url = ?
            ''', image_parameters)
        else:
            self.cursor.execute(f'''
            INSERT INTO {table} (
                prop_url, prop_address, prop_floor, prop_price, prop_m2, prop_rooms, prop_bedrooms,
                prop_location, prop_description, project_url, project_district,
                project_address, project_description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', parameters)
            
            self.cursor.execute(f'''
            INSERT INTO {self.images_table} (
                prop_url, project_url, prop_images, project_images
            ) VALUES (?, ?, ?, ?)
            ''', image_parameters)
        self.conn.commit()

    def import_data(self, json_data, table=None):
        for project in json_data:
            for prop in project['properties']:
                self.insert_or_update_property(project_data=project, prop_data=prop, table=table)

if __name__ == '__main__':
    json_file_path = 'data/raw/argenprop_data.json'
    
    prop_db = PropDb(dbname='brickland.db')
    try:
        prop_db.connect()
        prop_db.create_tables()

        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        prop_db.import_data(json_data)
        print("Data inserted/updated in database successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        prop_db.close()
