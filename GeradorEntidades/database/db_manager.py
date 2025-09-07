"""
Database manager for SQLite operations and dynamic table management
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import config

class DatabaseManager:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create metadata table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create metadata table to store entity definitions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entity_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_name TEXT UNIQUE NOT NULL,
                    field_name TEXT NOT NULL,
                    field_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def create_entity(self, entity_name: str, fields: List[Dict[str, str]]) -> bool:
        """
        Create a new entity (table) with specified fields
        
        Args:
            entity_name: Name of the entity/table
            fields: List of dictionaries with 'name' and 'type' keys
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if entity already exists
                if self.entity_exists(entity_name):
                    return False
                
                # Build CREATE TABLE SQL
                field_definitions = []
                field_definitions.append("id INTEGER PRIMARY KEY AUTOINCREMENT")
                
                for field in fields:
                    field_name = field['name'].replace(' ', '_').lower()
                    field_type = config.SUPPORTED_DATA_TYPES[field['type']]
                    field_definitions.append(f"{field_name} {field_type}")
                
                field_definitions.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                
                create_sql = f"CREATE TABLE {entity_name} ({', '.join(field_definitions)})"
                cursor.execute(create_sql)
                
                # Store metadata
                for field in fields:
                    cursor.execute("""
                        INSERT INTO entity_metadata (entity_name, field_name, field_type)
                        VALUES (?, ?, ?)
                    """, (entity_name, field['name'], field['type']))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error creating entity: {e}")
            return False
    
    def entity_exists(self, entity_name: str) -> bool:
        """Check if an entity (table) exists"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=? AND name != 'entity_metadata'
                """, (entity_name,))
                return cursor.fetchone() is not None
        except:
            return False
    
    def get_all_entities(self) -> List[str]:
        """Get list of all created entities"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT entity_name FROM entity_metadata
                    ORDER BY entity_name
                """)
                return [row[0] for row in cursor.fetchall()]
        except:
            return []
    
    def get_entity_fields(self, entity_name: str) -> List[Dict[str, str]]:
        """Get field definitions for an entity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT field_name, field_type FROM entity_metadata
                    WHERE entity_name = ?
                    ORDER BY id
                """, (entity_name,))
                
                fields = []
                for row in cursor.fetchall():
                    fields.append({
                        'name': row[0],
                        'type': row[1]
                    })
                return fields
        except:
            return []
    
    def insert_record(self, entity_name: str, data: Dict[str, Any]) -> bool:
        """Insert a new record into an entity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare field names and values
                field_names = []
                values = []
                placeholders = []
                
                for key, value in data.items():
                    field_name = key.replace(' ', '_').lower()
                    field_names.append(field_name)
                    values.append(value)
                    placeholders.append('?')
                
                sql = f"""
                    INSERT INTO {entity_name} ({', '.join(field_names)})
                    VALUES ({', '.join(placeholders)})
                """
                
                cursor.execute(sql, values)
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error inserting record: {e}")
            return False
    
    def get_all_records(self, entity_name: str) -> pd.DataFrame:
        """Get all records from an entity as DataFrame"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = f"SELECT * FROM {entity_name} ORDER BY id DESC"
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Error getting records: {e}")
            return pd.DataFrame()
    
    def update_record(self, entity_name: str, record_id: int, data: Dict[str, Any]) -> bool:
        """Update a record in an entity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare SET clause
                set_clauses = []
                values = []
                
                for key, value in data.items():
                    field_name = key.replace(' ', '_').lower()
                    set_clauses.append(f"{field_name} = ?")
                    values.append(value)
                
                values.append(record_id)
                
                sql = f"""
                    UPDATE {entity_name} 
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """
                
                cursor.execute(sql, values)
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error updating record: {e}")
            return False
    
    def delete_record(self, entity_name: str, record_id: int) -> bool:
        """Delete a record from an entity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {entity_name} WHERE id = ?", (record_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False
    
    def delete_entity(self, entity_name: str) -> bool:
        """Delete an entire entity (table) and its metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Drop the table
                cursor.execute(f"DROP TABLE IF EXISTS {entity_name}")
                
                # Remove metadata
                cursor.execute("DELETE FROM entity_metadata WHERE entity_name = ?", (entity_name,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting entity: {e}")
            return False
