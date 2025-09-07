import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from config.database import db_manager

class Product:
    def __init__(self, id: Optional[int] = None, code: str = "", name: str = "", 
                 description: str = "", category: str = "", unit_price: Optional[float] = None,
                 unit_of_measure: str = "", supplier_id: Optional[int] = None, 
                 status: str = "active", created_at: Optional[str] = None,
                 updated_at: Optional[str] = None, created_by: str = "", updated_by: str = ""):
        self.id = id
        self.code = code
        self.name = name
        self.description = description
        self.category = category
        self.unit_price = unit_price
        self.unit_of_measure = unit_of_measure
        self.supplier_id = supplier_id
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.created_by = created_by
        self.updated_by = updated_by
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Create Product instance from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Product instance to dictionary"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'unit_price': self.unit_price,
            'unit_of_measure': self.unit_of_measure,
            'supplier_id': self.supplier_id,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        }
    
    def save(self, user: str) -> int:
        """Save product to database"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.id is None:
                # Insert new product
                cursor.execute('''
                    INSERT INTO products (code, name, description, category, unit_price,
                                        unit_of_measure, supplier_id, status, created_by, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.code, self.name, self.description, self.category, self.unit_price,
                      self.unit_of_measure, self.supplier_id, self.status, user, user))
                
                self.id = cursor.lastrowid
                
                # Log audit trail
                self._log_audit_trail('INSERT', None, self.to_dict(), user)
                
            else:
                # Update existing product
                old_data = Product.get_by_id(self.id)
                old_dict = old_data.to_dict() if old_data else None
                
                cursor.execute('''
                    UPDATE products SET code=?, name=?, description=?, category=?, unit_price=?,
                                      unit_of_measure=?, supplier_id=?, status=?,
                                      updated_by=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (self.code, self.name, self.description, self.category, self.unit_price,
                      self.unit_of_measure, self.supplier_id, self.status, user, self.id))
                
                # Log audit trail
                self._log_audit_trail('UPDATE', old_dict, self.to_dict(), user)
            
            conn.commit()
            return self.id
    
    @staticmethod
    def get_all(status: Optional[str] = None) -> List['Product']:
        """Get all products"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("SELECT * FROM products WHERE status = ? ORDER BY name", (status,))
            else:
                cursor.execute("SELECT * FROM products ORDER BY name")
            
            rows = cursor.fetchall()
            return [Product.from_dict(dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(product_id: int) -> Optional['Product']:
        """Get product by ID"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            
            if row:
                return Product.from_dict(dict(row))
            return None
    
    @staticmethod
    def get_by_code(code: str) -> Optional['Product']:
        """Get product by code"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE code = ?", (code,))
            row = cursor.fetchone()
            
            if row:
                return Product.from_dict(dict(row))
            return None
    
    @staticmethod
    def search(query: str, filters: Optional[Dict[str, str]] = None) -> List['Product']:
        """Search products with filters"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            sql = "SELECT * FROM products WHERE 1=1"
            params = []
            
            if query:
                sql += " AND (name LIKE ? OR code LIKE ? OR description LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            
            if filters:
                for field, value in filters.items():
                    if value:
                        sql += f" AND {field} = ?"
                        params.append(value)
            
            sql += " ORDER BY name"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [Product.from_dict(dict(row)) for row in rows]
    
    @staticmethod
    def delete(product_id: int, user: str) -> bool:
        """Delete product (soft delete by changing status)"""
        product = Product.get_by_id(product_id)
        if product:
            old_dict = product.to_dict()
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE products SET status='deleted', updated_by=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (user, product_id))
                
                # Log audit trail
                Product._log_audit_trail_static('DELETE', old_dict, {'status': 'deleted'}, user, product_id)
                
                conn.commit()
                return True
        return False
    
    def _log_audit_trail(self, action: str, old_values: Optional[Dict], new_values: Dict, user: str):
        """Log audit trail for this product"""
        Product._log_audit_trail_static(action, old_values, new_values, user, self.id)
    
    @staticmethod
    def _log_audit_trail_static(action: str, old_values: Optional[Dict], new_values: Dict, user: str, record_id: int):
        """Static method to log audit trail"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_trail (table_name, record_id, action, old_values, new_values, changed_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('products', record_id, action, 
                  json.dumps(old_values) if old_values else None,
                  json.dumps(new_values),
                  user))
            conn.commit()
    
    @staticmethod
    def get_categories() -> List[str]:
        """Get all unique categories"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category")
            return [row[0] for row in cursor.fetchall()]
    
    @staticmethod
    def get_units_of_measure() -> List[str]:
        """Get all unique units of measure"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT unit_of_measure FROM products WHERE unit_of_measure IS NOT NULL AND unit_of_measure != '' ORDER BY unit_of_measure")
            return [row[0] for row in cursor.fetchall()]
    
    @staticmethod
    def get_count(status: Optional[str] = None) -> int:
        """Get count of products"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT COUNT(*) FROM products WHERE status = ?", (status,))
            else:
                cursor.execute("SELECT COUNT(*) FROM products")
            return cursor.fetchone()[0]
    
    def get_supplier_name(self) -> Optional[str]:
        """Get supplier name for this product"""
        if self.supplier_id:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM suppliers WHERE id = ?", (self.supplier_id,))
                row = cursor.fetchone()
                return row[0] if row else None
        return None
