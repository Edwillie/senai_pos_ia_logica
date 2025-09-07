from typing import List, Dict, Any, Tuple
import difflib
from models.client import Client
from models.product import Product
from models.supplier import Supplier
from models.audit import PotentialDuplicate

class DuplicateDetectionService:
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        if not text1 or not text2:
            return 0.0
        
        # Normalize strings (lowercase, strip whitespace)
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        # Use difflib to calculate similarity ratio
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    @staticmethod
    def normalize_document(document: str) -> str:
        """Normalize document number for comparison"""
        if not document:
            return ""
        
        # Remove common separators and spaces
        return ''.join(filter(str.isalnum, document.lower()))
    
    @staticmethod
    def detect_client_duplicates(threshold: float = 0.8) -> List[PotentialDuplicate]:
        """Detect potential duplicate clients"""
        clients = Client.get_all(status='active')
        duplicates = []
        
        for i, client1 in enumerate(clients):
            for client2 in clients[i+1:]:
                similarity_score = DuplicateDetectionService._calculate_client_similarity(client1, client2)
                
                if similarity_score >= threshold:
                    duplicate = PotentialDuplicate(
                        table_name='clients',
                        record_id_1=client1.id,
                        record_id_2=client2.id,
                        similarity_score=similarity_score,
                        status='pending'
                    )
                    
                    # Check if this duplicate pair already exists
                    if not DuplicateDetectionService._duplicate_exists('clients', client1.id, client2.id):
                        duplicate.save()
                        duplicates.append(duplicate)
        
        return duplicates
    
    @staticmethod
    def detect_product_duplicates(threshold: float = 0.8) -> List[PotentialDuplicate]:
        """Detect potential duplicate products"""
        products = Product.get_all(status='active')
        duplicates = []
        
        for i, product1 in enumerate(products):
            for product2 in products[i+1:]:
                similarity_score = DuplicateDetectionService._calculate_product_similarity(product1, product2)
                
                if similarity_score >= threshold:
                    duplicate = PotentialDuplicate(
                        table_name='products',
                        record_id_1=product1.id,
                        record_id_2=product2.id,
                        similarity_score=similarity_score,
                        status='pending'
                    )
                    
                    # Check if this duplicate pair already exists
                    if not DuplicateDetectionService._duplicate_exists('products', product1.id, product2.id):
                        duplicate.save()
                        duplicates.append(duplicate)
        
        return duplicates
    
    @staticmethod
    def detect_supplier_duplicates(threshold: float = 0.8) -> List[PotentialDuplicate]:
        """Detect potential duplicate suppliers"""
        suppliers = Supplier.get_all(status='active')
        duplicates = []
        
        for i, supplier1 in enumerate(suppliers):
            for supplier2 in suppliers[i+1:]:
                similarity_score = DuplicateDetectionService._calculate_supplier_similarity(supplier1, supplier2)
                
                if similarity_score >= threshold:
                    duplicate = PotentialDuplicate(
                        table_name='suppliers',
                        record_id_1=supplier1.id,
                        record_id_2=supplier2.id,
                        similarity_score=similarity_score,
                        status='pending'
                    )
                    
                    # Check if this duplicate pair already exists
                    if not DuplicateDetectionService._duplicate_exists('suppliers', supplier1.id, supplier2.id):
                        duplicate.save()
                        duplicates.append(duplicate)
        
        return duplicates
    
    @staticmethod
    def _calculate_client_similarity(client1: Client, client2: Client) -> float:
        """Calculate similarity score between two clients"""
        scores = []
        
        # Name similarity (high weight)
        name_score = DuplicateDetectionService.calculate_similarity(client1.name, client2.name)
        scores.append(name_score * 0.4)
        
        # Document number similarity (high weight)
        doc1 = DuplicateDetectionService.normalize_document(client1.document_number)
        doc2 = DuplicateDetectionService.normalize_document(client2.document_number)
        if doc1 and doc2:
            doc_score = 1.0 if doc1 == doc2 else 0.0
            scores.append(doc_score * 0.3)
        
        # Email similarity (medium weight)
        if client1.email and client2.email:
            email_score = DuplicateDetectionService.calculate_similarity(client1.email, client2.email)
            scores.append(email_score * 0.2)
        
        # Phone similarity (low weight)
        if client1.phone and client2.phone:
            phone1 = ''.join(filter(str.isdigit, client1.phone))
            phone2 = ''.join(filter(str.isdigit, client2.phone))
            phone_score = DuplicateDetectionService.calculate_similarity(phone1, phone2)
            scores.append(phone_score * 0.1)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    @staticmethod
    def _calculate_product_similarity(product1: Product, product2: Product) -> float:
        """Calculate similarity score between two products"""
        scores = []
        
        # Code similarity (high weight)
        if product1.code and product2.code:
            code_score = 1.0 if product1.code.lower() == product2.code.lower() else 0.0
            scores.append(code_score * 0.4)
        
        # Name similarity (high weight)
        name_score = DuplicateDetectionService.calculate_similarity(product1.name, product2.name)
        scores.append(name_score * 0.4)
        
        # Description similarity (medium weight)
        if product1.description and product2.description:
            desc_score = DuplicateDetectionService.calculate_similarity(product1.description, product2.description)
            scores.append(desc_score * 0.2)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    @staticmethod
    def _calculate_supplier_similarity(supplier1: Supplier, supplier2: Supplier) -> float:
        """Calculate similarity score between two suppliers"""
        scores = []
        
        # Name similarity (high weight)
        name_score = DuplicateDetectionService.calculate_similarity(supplier1.name, supplier2.name)
        scores.append(name_score * 0.4)
        
        # Document number similarity (high weight)
        doc1 = DuplicateDetectionService.normalize_document(supplier1.document_number)
        doc2 = DuplicateDetectionService.normalize_document(supplier2.document_number)
        if doc1 and doc2:
            doc_score = 1.0 if doc1 == doc2 else 0.0
            scores.append(doc_score * 0.3)
        
        # Email similarity (medium weight)
        if supplier1.email and supplier2.email:
            email_score = DuplicateDetectionService.calculate_similarity(supplier1.email, supplier2.email)
            scores.append(email_score * 0.2)
        
        # Contact person similarity (low weight)
        if supplier1.contact_person and supplier2.contact_person:
            contact_score = DuplicateDetectionService.calculate_similarity(supplier1.contact_person, supplier2.contact_person)
            scores.append(contact_score * 0.1)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    @staticmethod
    def _duplicate_exists(table_name: str, record_id_1: int, record_id_2: int) -> bool:
        """Check if a duplicate pair already exists in the database"""
        from config.database import db_manager
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM potential_duplicates 
                WHERE table_name = ? AND 
                      ((record_id_1 = ? AND record_id_2 = ?) OR 
                       (record_id_1 = ? AND record_id_2 = ?))
            ''', (table_name, record_id_1, record_id_2, record_id_2, record_id_1))
            
            return cursor.fetchone()[0] > 0
    
    @staticmethod
    def get_duplicate_details(duplicate: PotentialDuplicate) -> Tuple[Any, Any]:
        """Get the actual records for a potential duplicate"""
        if duplicate.table_name == 'clients':
            record1 = Client.get_by_id(duplicate.record_id_1)
            record2 = Client.get_by_id(duplicate.record_id_2)
        elif duplicate.table_name == 'products':
            record1 = Product.get_by_id(duplicate.record_id_1)
            record2 = Product.get_by_id(duplicate.record_id_2)
        elif duplicate.table_name == 'suppliers':
            record1 = Supplier.get_by_id(duplicate.record_id_1)
            record2 = Supplier.get_by_id(duplicate.record_id_2)
        else:
            return None, None
        
        return record1, record2
    
    @staticmethod
    def merge_records(duplicate: PotentialDuplicate, keep_record_id: int, user: str) -> bool:
        """Merge two duplicate records, keeping one and deleting the other"""
        try:
            if duplicate.table_name == 'clients':
                # Keep the selected record, delete the other
                delete_id = duplicate.record_id_2 if keep_record_id == duplicate.record_id_1 else duplicate.record_id_1
                Client.delete(delete_id, user)
            
            elif duplicate.table_name == 'products':
                delete_id = duplicate.record_id_2 if keep_record_id == duplicate.record_id_1 else duplicate.record_id_1
                Product.delete(delete_id, user)
            
            elif duplicate.table_name == 'suppliers':
                delete_id = duplicate.record_id_2 if keep_record_id == duplicate.record_id_1 else duplicate.record_id_1
                Supplier.delete(delete_id, user)
            
            # Mark duplicate as resolved
            duplicate.status = 'merged'
            duplicate.reviewed_by = user
            duplicate.save()
            
            return True
        
        except Exception as e:
            print(f"Error merging records: {e}")
            return False
    
    @staticmethod
    def mark_as_not_duplicate(duplicate: PotentialDuplicate, user: str) -> bool:
        """Mark a potential duplicate as not a duplicate"""
        try:
            duplicate.status = 'not_duplicate'
            duplicate.reviewed_by = user
            duplicate.save()
            return True
        except Exception as e:
            print(f"Error marking as not duplicate: {e}")
            return False
    
    @staticmethod
    def run_all_duplicate_detection(threshold: float = 0.8) -> Dict[str, int]:
        """Run duplicate detection for all entity types"""
        results = {
            'clients': 0,
            'products': 0,
            'suppliers': 0
        }
        
        # Detect client duplicates
        client_duplicates = DuplicateDetectionService.detect_client_duplicates(threshold)
        results['clients'] = len(client_duplicates)
        
        # Detect product duplicates
        product_duplicates = DuplicateDetectionService.detect_product_duplicates(threshold)
        results['products'] = len(product_duplicates)
        
        # Detect supplier duplicates
        supplier_duplicates = DuplicateDetectionService.detect_supplier_duplicates(threshold)
        results['suppliers'] = len(supplier_duplicates)
        
        return results
