import json
import sqlite3
import os

class PropDb:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        # Connect to SQLite database (or create it if it doesn't exist)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.close()

    def create_table(self):
        # Create table for properties if it doesn't exist
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            prop_url TEXT PRIMARY KEY,
            prop_address TEXT,
            prop_floor TEXT,
            prop_price TEXT,
            prop_m2 INTEGER,
            prop_rooms INTEGER,
            prop_bedrooms INTEGER,
            prop_location TEXT,
            prop_description TEXT,
            prop_images TEXT,
            project_url TEXT,
            project_district TEXT,
            project_address TEXT,
            project_description TEXT,
            project_images TEXT
        )
        ''')
        self.conn.commit()

    def property_exists(self, prop_url):
        self.cursor.execute('SELECT 1 FROM properties WHERE prop_url = ?', (prop_url,))
        return self.cursor.fetchone() is not None

    def insert_or_update_property(self, project_data, prop_data):
        if prop_data is None:
            return None
        parameters = (
            prop_data.get('prop_url'),
            prop_data.get('prop_address', ''),
            prop_data.get('prop_floor', ''),
            prop_data.get('prop_price', ''),
            prop_data.get('prop_m2', 0),
            prop_data.get('prop_rooms', 0),
            prop_data.get('prop_bedrooms', 0),
            prop_data.get('prop_location', ''),
            prop_data.get('prop_description', 'nan'),
            json.dumps(prop_data.get('prop_images', []), ensure_ascii=False),
            project_data.get('project_url', ''),
            project_data.get('project_district', ''),
            project_data.get('project_address', ''),
            project_data.get('project_description', ''),
            json.dumps(project_data.get('project_images', []), ensure_ascii=False)
        )

        if self.property_exists(prop_data['prop_url']):
            # Update existing property
            self.cursor.execute('''
            UPDATE properties
            SET prop_address = ?, prop_floor = ?, prop_price = ?, prop_m2 = ?, prop_rooms = ?, 
                prop_bedrooms = ?, prop_location = ?, prop_description = ?, prop_images = ?, 
                project_url = ?, project_district = ?, project_address = ?, 
                project_description = ?, project_images = ?
            WHERE prop_url = ?
            ''', (
                prop_data['prop_address'],
                prop_data['prop_floor'],
                prop_data['prop_price'],
                prop_data['prop_m2'],
                prop_data['prop_rooms'],
                prop_data['prop_bedrooms'],
                prop_data['prop_location'],
                prop_data['prop_description'] if prop_data['prop_description'] else 'nan',
                json.dumps(prop_data['prop_images'], ensure_ascii=False),
                project_data['project_url'],
                project_data['project_district'],
                project_data['project_address'],
                project_data['project_description'],
                json.dumps(project_data['project_images'], ensure_ascii=False),
                prop_data['prop_url']
            ))
        else:
            # Insert new property
            self.cursor.execute('''
            INSERT INTO properties (
                prop_url, prop_address, prop_floor, prop_price, prop_m2, prop_rooms, prop_bedrooms,
                prop_location, prop_description, prop_images, project_url, project_district,
                project_address, project_description, project_images
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', parameters)
        self.conn.commit()


    def import_data(self, json_data):
        for project in json_data:
            for prop in project['properties']:
                self.insert_or_update_property(project_data=project, prop_data=prop)

# Usage example
if __name__ == '__main__':
    db_path = 'data/clean/prop_data.db'
    json_file_path = 'data/raw/argenprop_data.json'

    with open(json_file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    prop_db = PropDb(db_path)
    prop_db.connect()
    prop_db.create_table()
    prop_db.import_data(json_data)
    prop_db.close()

    print("Data inserted/updated in database successfully!")
