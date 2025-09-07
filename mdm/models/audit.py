import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from config.database import db_manager

class AuditTrail:
    def __init__(self, id: Optional[int] = None, table_name: str = "", record_id: int = 0,
                 action: str = "", old_values: Optional[str] = None, new_values: Optional[str] = None,
                 changed_by: str = "", changed_at: Optional[str] = None):
        self.id = id
        self.table_name = table_name
        self.record_id = record_id
        self.action = action
        self.old_values = old_values
        self.new_values = new_values
        self.changed_by = changed_by
        self.changed_at = changed_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditTrail':
        """Create AuditTrail instance from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert AuditTrail instance to dictionary"""
        return {
            'id': self.id,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'action': self.action,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'changed_by': self.changed_by,
            'changed_at': self.changed_at
        }
    
    def get_old_values_dict(self) -> Optional[Dict[str, Any]]:
        """Parse old_values JSON string to dictionary"""
        if self.old_values:
            try:
                return json.loads(self.old_values)
            except json.JSONDecodeError:
                return None
        return None
    
    def get_new_values_dict(self) -> Optional[Dict[str, Any]]:
        """Parse new_values JSON string to dictionary"""
        if self.new_values:
            try:
                return json.loads(self.new_values)
            except json.JSONDecodeError:
                return None
        return None
    
    def get_changes(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed changes between old and new values"""
        old_dict = self.get_old_values_dict() or {}
        new_dict = self.get_new_values_dict() or {}
        
        changes = {}
        
        # Check for modified fields
        for key in new_dict:
            if key in old_dict:
                if old_dict[key] != new_dict[key]:
                    changes[key] = {
                        'old': old_dict[key],
                        'new': new_dict[key],
                        'type': 'modified'
                    }
            else:
                changes[key] = {
                    'old': None,
                    'new': new_dict[key],
                    'type': 'added'
                }
        
        # Check for removed fields
        for key in old_dict:
            if key not in new_dict:
                changes[key] = {
                    'old': old_dict[key],
                    'new': None,
                    'type': 'removed'
                }
        
        return changes
    
    @staticmethod
    def get_all(table_name: Optional[str] = None, record_id: Optional[int] = None,
                limit: int = 100, offset: int = 0) -> List['AuditTrail']:
        """Get audit trail records with optional filters"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            sql = "SELECT * FROM audit_trail WHERE 1=1"
            params = []
            
            if table_name:
                sql += " AND table_name = ?"
                params.append(table_name)
            
            if record_id:
                sql += " AND record_id = ?"
                params.append(record_id)
            
            sql += " ORDER BY changed_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [AuditTrail.from_dict(dict(row)) for row in rows]
    
    @staticmethod
    def get_by_record(table_name: str, record_id: int) -> List['AuditTrail']:
        """Get audit trail for a specific record"""
        return AuditTrail.get_all(table_name=table_name, record_id=record_id)
    
    @staticmethod
    def get_recent_changes(limit: int = 50) -> List['AuditTrail']:
        """Get recent changes across all tables"""
        return AuditTrail.get_all(limit=limit)
    
    @staticmethod
    def get_user_activity(username: str, limit: int = 50) -> List['AuditTrail']:
        """Get activity for a specific user"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM audit_trail 
                WHERE changed_by = ? 
                ORDER BY changed_at DESC 
                LIMIT ?
            ''', (username, limit))
            
            rows = cursor.fetchall()
            return [AuditTrail.from_dict(dict(row)) for row in rows]
    
    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """Get audit trail statistics"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) FROM audit_trail")
            total_records = cursor.fetchone()[0]
            
            # Records by table
            cursor.execute('''
                SELECT table_name, COUNT(*) as count 
                FROM audit_trail 
                GROUP BY table_name 
                ORDER BY count DESC
            ''')
            by_table = dict(cursor.fetchall())
            
            # Records by action
            cursor.execute('''
                SELECT action, COUNT(*) as count 
                FROM audit_trail 
                GROUP BY action 
                ORDER BY count DESC
            ''')
            by_action = dict(cursor.fetchall())
            
            # Records by user
            cursor.execute('''
                SELECT changed_by, COUNT(*) as count 
                FROM audit_trail 
                GROUP BY changed_by 
                ORDER BY count DESC
                LIMIT 10
            ''')
            by_user = dict(cursor.fetchall())
            
            # Recent activity (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) 
                FROM audit_trail 
                WHERE changed_at >= datetime('now', '-7 days')
            ''')
            recent_activity = cursor.fetchone()[0]
            
            return {
                'total_records': total_records,
                'by_table': by_table,
                'by_action': by_action,
                'by_user': by_user,
                'recent_activity': recent_activity
            }
    
    @staticmethod
    def cleanup_old_records(days_to_keep: int = 365) -> int:
        """Clean up old audit records (older than specified days)"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM audit_trail 
                WHERE changed_at < datetime('now', '-{} days')
            '''.format(days_to_keep))
            
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count

class PotentialDuplicate:
    def __init__(self, id: Optional[int] = None, table_name: str = "", record_id_1: int = 0,
                 record_id_2: int = 0, similarity_score: float = 0.0, status: str = "pending",
                 reviewed_by: Optional[str] = None, reviewed_at: Optional[str] = None,
                 created_at: Optional[str] = None):
        self.id = id
        self.table_name = table_name
        self.record_id_1 = record_id_1
        self.record_id_2 = record_id_2
        self.similarity_score = similarity_score
        self.status = status
        self.reviewed_by = reviewed_by
        self.reviewed_at = reviewed_at
        self.created_at = created_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PotentialDuplicate':
        """Create PotentialDuplicate instance from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PotentialDuplicate instance to dictionary"""
        return {
            'id': self.id,
            'table_name': self.table_name,
            'record_id_1': self.record_id_1,
            'record_id_2': self.record_id_2,
            'similarity_score': self.similarity_score,
            'status': self.status,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at,
            'created_at': self.created_at
        }
    
    def save(self) -> int:
        """Save potential duplicate to database"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.id is None:
                cursor.execute('''
                    INSERT INTO potential_duplicates (table_name, record_id_1, record_id_2, 
                                                    similarity_score, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.table_name, self.record_id_1, self.record_id_2, 
                      self.similarity_score, self.status))
                
                self.id = cursor.lastrowid
            else:
                cursor.execute('''
                    UPDATE potential_duplicates 
                    SET status=?, reviewed_by=?, reviewed_at=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (self.status, self.reviewed_by, self.id))
            
            conn.commit()
            return self.id
    
    @staticmethod
    def get_pending(table_name: Optional[str] = None) -> List['PotentialDuplicate']:
        """Get pending duplicate reviews"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if table_name:
                cursor.execute('''
                    SELECT * FROM potential_duplicates 
                    WHERE status = 'pending' AND table_name = ?
                    ORDER BY similarity_score DESC
                ''', (table_name,))
            else:
                cursor.execute('''
                    SELECT * FROM potential_duplicates 
                    WHERE status = 'pending'
                    ORDER BY similarity_score DESC
                ''')
            
            rows = cursor.fetchall()
            return [PotentialDuplicate.from_dict(dict(row)) for row in rows]
    
    @staticmethod
    def get_count(status: Optional[str] = None) -> int:
        """Get count of potential duplicates"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT COUNT(*) FROM potential_duplicates WHERE status = ?", (status,))
            else:
                cursor.execute("SELECT COUNT(*) FROM potential_duplicates")
            return cursor.fetchone()[0]
