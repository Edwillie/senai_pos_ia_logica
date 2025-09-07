import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from config.database import db_manager

class Client:
    def __init__(self, id: Optional[int] = None, name: str = "", document_type: str = "", 
                 document_number: str = "", email: str = "", phone: str = "", 
                 address: str = "", city: str = "", state: str = "", zip_code: str = "",
                 category: str = "", status: str = "active", created_at: Optional[str] = None,
                 updated_at: Optional[str] = None, created_by: str = "", updated_by: str = ""):
        self.id = id
        self.name = name
        self.document_type = document_type
        self.document_number = document_number
        self.email = email
        self.phone = phone
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.category = category
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.created_by = created_by
        self.updated_by = updated_by
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Client':
        """Create Client instance from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Client instance to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'document_type': self.document_type,
            'document_number': self.document_number,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'category': self.category,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        }
    
    def save(self, user: str) -> int:
        """Save client to database"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.id is None:
                # Insert new client
                cursor.execute('''
                    INSERT INTO clients (name, document_type, document_number, email, phone,
                                       address, city, state, zip_code, category, status, created_by, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.name, self.document_type, self.document_number, self.email, self.phone,
                      self.address, self.city, self.state, self.zip_code, self.category, 
                      self.status, user, user))
                
                self.id = cursor.lastrowid
                
                # Log audit trail
                self._log_audit_trail('INSERT', None, self.to_dict(), user)
                
            else:
                # Update existing client
                old_data = Client.get_by_id(self.id)
                old_dict = old_data.to_dict() if old_data else None
                
                cursor.execute('''
                    UPDATE clients SET name=?, document_type=?, document_number=?, email=?, phone=?,
                                     address=?, city=?, state=?, zip_code=?, category=?, status=?,
                                     updated_by=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (self.name, self.document_type, self.document_number, self.email, self.phone,
                      self.address, self.city, self.state, self.zip_code, self.category,
                      self.status, user, self.id))
                
                # Log audit trail
                self._log_audit_trail('UPDATE', old_dict, self.to_dict(), user)
            
            conn.commit()
            return self.id
    
    @staticmethod
    def get_all(status: Optional[str] = None) -> List['Client']:
        """Get all clients"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("SELECT * FROM clients WHERE status = ? ORDER BY name", (status,))
            else:
                cursor.execute("SELECT * FROM clients ORDER BY name")
            
            rows = cursor.fetchall()
            return [Client.from_dict(dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(client_id: int) -> Optional['Client']:
        """Get client by ID"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
            row = cursor.fetchone()
            
            if row:
                return Client.from_dict(dict(row))
            return None
    
    @staticmethod
    def search(query: str, filters: Optional[Dict[str, str]] = None) -> List['Client']:
        """Search clients with filters"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            sql = "SELECT * FROM clients WHERE 1=1"
            params = []
            
            if query:
                sql += " AND (name LIKE ? OR document_number LIKE ? OR email LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            
            if filters:
                for field, value in filters.items():
                    if value:
                        sql += f" AND {field} = ?"
                        params.append(value)
            
            sql += " ORDER BY name"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [Client.from_dict(dict(row)) for row in rows]
    
    @staticmethod
    def delete(client_id: int, user: str) -> bool:
        """Delete client (soft delete by changing status)"""
        client = Client.get_by_id(client_id)
        if client:
            old_dict = client.to_dict()
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE clients SET status='deleted', updated_by=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (user, client_id))
                
                # Log audit trail
                Client._log_audit_trail_static('DELETE', old_dict, {'status': 'deleted'}, user, client_id)
                
                conn.commit()
                return True
        return False
    
    def _log_audit_trail(self, action: str, old_values: Optional[Dict], new_values: Dict, user: str):
        """Log audit trail for this client"""
        Client._log_audit_trail_static(action, old_values, new_values, user, self.id)
    
    @staticmethod
    def _log_audit_trail_static(action: str, old_values: Optional[Dict], new_values: Dict, user: str, record_id: int):
        """Static method to log audit trail"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_trail (table_name, record_id, action, old_values, new_values, changed_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('clients', record_id, action, 
                  json.dumps(old_values) if old_values else None,
                  json.dumps(new_values),
                  user))
            conn.commit()
    
    @staticmethod
    def get_categories() -> List[str]:
        """Get all unique categories"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM clients WHERE category IS NOT NULL AND category != '' ORDER BY category")
            return [row[0] for row in cursor.fetchall()]
    
    @staticmethod
    def get_count(status: Optional[str] = None) -> int:
        """Get count of clients"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT COUNT(*) FROM clients WHERE status = ?", (status,))
            else:
                cursor.execute("SELECT COUNT(*) FROM clients")
            return cursor.fetchone()[0]
