import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from config.database import db_manager

class Supplier:
    def __init__(self, id: Optional[int] = None, name: str = "", document_type: str = "", 
                 document_number: str = "", email: str = "", phone: str = "", 
                 address: str = "", city: str = "", state: str = "", zip_code: str = "",
                 category: str = "", contact_person: str = "", status: str = "active", 
                 created_at: Optional[str] = None, updated_at: Optional[str] = None, 
                 created_by: str = "", updated_by: str = ""):
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
        self.contact_person = contact_person
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.created_by = created_by
        self.updated_by = updated_by
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Supplier':
        """Create Supplier instance from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Supplier instance to dictionary"""
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
            'contact_person': self.contact_person,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        }
    
    def save(self, user: str) -> int:
        """Save supplier to database"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.id is None:
                # Insert new supplier
                cursor.execute('''
                    INSERT INTO suppliers (name, document_type, document_number, email, phone,
                                         address, city, state, zip_code, category, contact_person,
                                         status, created_by, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.name, self.document_type, self.document_number, self.email, self.phone,
                      self.address, self.city, self.state, self.zip_code, self.category,
                      self.contact_person, self.status, user, user))
                
                self.id = cursor.lastrowid
                
                # Log audit trail
                self._log_audit_trail('INSERT', None, self.to_dict(), user)
                
            else:
                # Update existing supplier
                old_data = Supplier.get_by_id(self.id)
                old_dict = old_data.to_dict() if old_data else None
                
                cursor.execute('''
                    UPDATE suppliers SET name=?, document_type=?, document_number=?, email=?, phone=?,
                                       address=?, city=?, state=?, zip_code=?, category=?, contact_person=?,
                                       status=?, updated_by=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (self.name, self.document_type, self.document_number, self.email, self.phone,
                      self.address, self.city, self.state, self.zip_code, self.category,
                      self.contact_person, self.status, user, self.id))
                
                # Log audit trail
                self._log_audit_trail('UPDATE', old_dict, self.to_dict(), user)
            
            conn.commit()
            return self.id
    
    @staticmethod
    def get_all(status: Optional[str] = None) -> List['Supplier']:
        """Get all suppliers"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("SELECT * FROM suppliers WHERE status = ? ORDER BY name", (status,))
            else:
                cursor.execute("SELECT * FROM suppliers ORDER BY name")
            
            rows = cursor.fetchall()
            return [Supplier.from_dict(dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(supplier_id: int) -> Optional['Supplier']:
        """Get supplier by ID"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
            row = cursor.fetchone()
            
            if row:
                return Supplier.from_dict(dict(row))
            return None
    
    @staticmethod
    def search(query: str, filters: Optional[Dict[str, str]] = None) -> List['Supplier']:
        """Search suppliers with filters"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            sql = "SELECT * FROM suppliers WHERE 1=1"
            params = []
            
            if query:
                sql += " AND (name LIKE ? OR document_number LIKE ? OR email LIKE ? OR contact_person LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"])
            
            if filters:
                for field, value in filters.items():
                    if value:
                        sql += f" AND {field} = ?"
                        params.append(value)
            
            sql += " ORDER BY name"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [Supplier.from_dict(dict(row)) for row in rows]
    
    @staticmethod
    def delete(supplier_id: int, user: str) -> bool:
        """Delete supplier (soft delete by changing status)"""
        supplier = Supplier.get_by_id(supplier_id)
        if supplier:
            old_dict = supplier.to_dict()
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE suppliers SET status='deleted', updated_by=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (user, supplier_id))
                
                # Log audit trail
                Supplier._log_audit_trail_static('DELETE', old_dict, {'status': 'deleted'}, user, supplier_id)
                
                conn.commit()
                return True
        return False
    
    def _log_audit_trail(self, action: str, old_values: Optional[Dict], new_values: Dict, user: str):
        """Log audit trail for this supplier"""
        Supplier._log_audit_trail_static(action, old_values, new_values, user, self.id)
    
    @staticmethod
    def _log_audit_trail_static(action: str, old_values: Optional[Dict], new_values: Dict, user: str, record_id: int):
        """Static method to log audit trail"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_trail (table_name, record_id, action, old_values, new_values, changed_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('suppliers', record_id, action, 
                  json.dumps(old_values) if old_values else None,
                  json.dumps(new_values),
                  user))
            conn.commit()
    
    @staticmethod
    def get_categories() -> List[str]:
        """Get all unique categories"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM suppliers WHERE category IS NOT NULL AND category != '' ORDER BY category")
            return [row[0] for row in cursor.fetchall()]
    
    @staticmethod
    def get_count(status: Optional[str] = None) -> int:
        """Get count of suppliers"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT COUNT(*) FROM suppliers WHERE status = ?", (status,))
            else:
                cursor.execute("SELECT COUNT(*) FROM suppliers")
            return cursor.fetchone()[0]
    
    def get_products_count(self) -> int:
        """Get count of products for this supplier"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products WHERE supplier_id = ? AND status = 'active'", (self.id,))
            return cursor.fetchone()[0]
    
    @staticmethod
    def get_for_dropdown() -> List[Dict[str, Any]]:
        """Get suppliers formatted for dropdown selection"""
        suppliers = Supplier.get_all(status='active')
        return [{'id': s.id, 'name': s.name} for s in suppliers]
