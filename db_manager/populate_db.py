import json
from db_connection import PostgresDB

class PropDb:
    def __init__(self, dbname='brickland', table='properties'):
        self.dbname = dbname
        self.table = table
        self.conn = None
        self.cursor = None

    def connect(self):
        db = PostgresDB(dbname=self.dbname)
        db.connect()
        self.conn = db.get_connection()
        self.cursor = db.cursor

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()

    def delete_table_if_exists(self, table=None):
        if table is None:
            table = self.table
        self.cursor.execute(f'DROP TABLE IF EXISTS {table}')
        self.conn.commit()

    def create_table(self, table=None):
        if table is None:
            table = self.table
        # Create table for properties if it doesn't exist
        self.cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table} (
            prop_url TEXT PRIMARY KEY,
            prop_address TEXT,
            prop_floor TEXT,
            prop_price TEXT,
            prop_m2 TEXT,
            prop_rooms TEXT,
            prop_bedrooms TEXT,
            prop_location TEXT,
            prop_description TEXT,
            prop_images JSONB,
            project_url TEXT,
            project_district TEXT,
            project_address TEXT,
            project_description TEXT,
            project_images JSONB
        )
        ''')
        self.conn.commit()

    def property_exists(self, prop_url, table=None):
        if table is None:
            table = self.table
        self.cursor.execute(f'SELECT 1 FROM {table} WHERE prop_url = %s', (prop_url,))
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
            json.dumps(prop_data.get('prop_images', []), ensure_ascii=False),
            project_data.get('project_url', ''),
            project_data.get('project_district', ''),
            project_data.get('project_address', ''),
            project_data.get('project_description', ''),
            json.dumps(project_data.get('project_images', []), ensure_ascii=False)
        )

        if self.property_exists(prop_data['prop_url']):
            # Update existing property
            self.cursor.execute(f'''
            UPDATE {table}
            SET prop_address = %s, prop_floor = %s, prop_price = %s, prop_m2 = %s, prop_rooms = %s, 
                prop_bedrooms = %s, prop_location = %s, prop_description = %s, prop_images = %s, 
                project_url = %s, project_district = %s, project_address = %s, 
                project_description = %s, project_images = %s
            WHERE prop_url = %s
            ''', (
                prop_data['prop_address'],
                prop_data['prop_floor'],
                prop_data['prop_price'],
                str(prop_data['prop_m2']),
                str(prop_data['prop_rooms']),
                str(prop_data['prop_bedrooms']),
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
            self.cursor.execute(f'''
            INSERT INTO {table} (
                prop_url, prop_address, prop_floor, prop_price, prop_m2, prop_rooms, prop_bedrooms,
                prop_location, prop_description, prop_images, project_url, project_district,
                project_address, project_description, project_images
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', parameters)
        self.conn.commit()

    def import_data(self, json_data, table=None):
        for project in json_data:
            for prop in project['properties']:
                self.insert_or_update_property(project_data=project, prop_data=prop, table=table)

# Usage example
if __name__ == '__main__':
    json_file_path = 'data/raw/argenprop_data.json'
    delete_table = True

    prop_db = PropDb(dbname='brickland')
    prop_db.connect()
    if delete_table:
        prop_db.delete_table_if_exists()
    prop_db.create_table()

    with open(json_file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    prop_db.import_data(json_data)
    prop_db.close()

    print("Data inserted/updated in database successfully!")
