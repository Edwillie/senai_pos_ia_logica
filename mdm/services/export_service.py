import pandas as pd
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
import csv
from models.client import Client
from models.product import Product
from models.supplier import Supplier
from models.audit import AuditTrail

class ExportService:
    
    @staticmethod
    def export_clients_to_csv() -> bytes:
        """Export all active clients to CSV"""
        clients = Client.get_all(status='active')
        
        # Convert to list of dictionaries
        data = []
        for client in clients:
            client_dict = client.to_dict()
            # Remove internal fields
            client_dict.pop('id', None)
            client_dict.pop('created_at', None)
            client_dict.pop('updated_at', None)
            client_dict.pop('created_by', None)
            client_dict.pop('updated_by', None)
            data.append(client_dict)
        
        # Create DataFrame and convert to CSV
        df = pd.DataFrame(data)
        
        # Rename columns to Portuguese
        column_mapping = {
            'name': 'Nome',
            'document_type': 'Tipo Documento',
            'document_number': 'Número Documento',
            'email': 'Email',
            'phone': 'Telefone',
            'address': 'Endereço',
            'city': 'Cidade',
            'state': 'Estado',
            'zip_code': 'CEP',
            'category': 'Categoria',
            'status': 'Status'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Convert to CSV bytes
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        return output.getvalue().encode('utf-8')
    
    @staticmethod
    def export_products_to_csv() -> bytes:
        """Export all active products to CSV"""
        products = Product.get_all(status='active')
        
        # Convert to list of dictionaries with supplier names
        data = []
        for product in products:
            product_dict = product.to_dict()
            # Remove internal fields
            product_dict.pop('id', None)
            product_dict.pop('created_at', None)
            product_dict.pop('updated_at', None)
            product_dict.pop('created_by', None)
            product_dict.pop('updated_by', None)
            
            # Add supplier name instead of ID
            supplier_name = product.get_supplier_name()
            product_dict['supplier_name'] = supplier_name
            product_dict.pop('supplier_id', None)
            
            data.append(product_dict)
        
        # Create DataFrame and convert to CSV
        df = pd.DataFrame(data)
        
        # Rename columns to Portuguese
        column_mapping = {
            'code': 'Código',
            'name': 'Nome',
            'description': 'Descrição',
            'category': 'Categoria',
            'unit_price': 'Preço Unitário',
            'unit_of_measure': 'Unidade de Medida',
            'supplier_name': 'Fornecedor',
            'status': 'Status'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Convert to CSV bytes
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        return output.getvalue().encode('utf-8')
    
    @staticmethod
    def export_suppliers_to_csv() -> bytes:
        """Export all active suppliers to CSV"""
        suppliers = Supplier.get_all(status='active')
        
        # Convert to list of dictionaries
        data = []
        for supplier in suppliers:
            supplier_dict = supplier.to_dict()
            # Remove internal fields
            supplier_dict.pop('id', None)
            supplier_dict.pop('created_at', None)
            supplier_dict.pop('updated_at', None)
            supplier_dict.pop('created_by', None)
            supplier_dict.pop('updated_by', None)
            data.append(supplier_dict)
        
        # Create DataFrame and convert to CSV
        df = pd.DataFrame(data)
        
        # Rename columns to Portuguese
        column_mapping = {
            'name': 'Nome',
            'document_type': 'Tipo Documento',
            'document_number': 'Número Documento',
            'email': 'Email',
            'phone': 'Telefone',
            'address': 'Endereço',
            'city': 'Cidade',
            'state': 'Estado',
            'zip_code': 'CEP',
            'category': 'Categoria',
            'contact_person': 'Pessoa de Contato',
            'status': 'Status'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Convert to CSV bytes
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        return output.getvalue().encode('utf-8')
    
    @staticmethod
    def export_audit_trail_to_csv(limit: int = 1000) -> bytes:
        """Export audit trail to CSV"""
        audit_records = AuditTrail.get_all(limit=limit)
        
        # Convert to list of dictionaries
        data = []
        for record in audit_records:
            audit_dict = record.to_dict()
            # Remove JSON fields for CSV export
            audit_dict.pop('old_values', None)
            audit_dict.pop('new_values', None)
            data.append(audit_dict)
        
        # Create DataFrame and convert to CSV
        df = pd.DataFrame(data)
        
        # Rename columns to Portuguese
        column_mapping = {
            'id': 'ID',
            'table_name': 'Tabela',
            'record_id': 'ID do Registro',
            'action': 'Ação',
            'changed_by': 'Alterado Por',
            'changed_at': 'Data/Hora'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Convert to CSV bytes
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        return output.getvalue().encode('utf-8')

class ImportService:
    
    @staticmethod
    def import_clients_from_csv(file_content: bytes, user: str) -> Dict[str, Any]:
        """Import clients from CSV file"""
        try:
            # Read CSV content
            content = file_content.decode('utf-8')
            df = pd.read_csv(io.StringIO(content))
            
            # Map Portuguese columns back to English
            column_mapping = {
                'Nome': 'name',
                'Tipo Documento': 'document_type',
                'Número Documento': 'document_number',
                'Email': 'email',
                'Telefone': 'phone',
                'Endereço': 'address',
                'Cidade': 'city',
                'Estado': 'state',
                'CEP': 'zip_code',
                'Categoria': 'category',
                'Status': 'status'
            }
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Validate required columns
            required_columns = ['name', 'document_type', 'document_number']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'message': f'Colunas obrigatórias ausentes: {", ".join(missing_columns)}',
                    'imported': 0,
                    'errors': []
                }
            
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Create client object
                    client = Client(
                        name=str(row.get('name', '')).strip(),
                        document_type=str(row.get('document_type', '')).strip(),
                        document_number=str(row.get('document_number', '')).strip(),
                        email=str(row.get('email', '')).strip() if pd.notna(row.get('email')) else '',
                        phone=str(row.get('phone', '')).strip() if pd.notna(row.get('phone')) else '',
                        address=str(row.get('address', '')).strip() if pd.notna(row.get('address')) else '',
                        city=str(row.get('city', '')).strip() if pd.notna(row.get('city')) else '',
                        state=str(row.get('state', '')).strip() if pd.notna(row.get('state')) else '',
                        zip_code=str(row.get('zip_code', '')).strip() if pd.notna(row.get('zip_code')) else '',
                        category=str(row.get('category', '')).strip() if pd.notna(row.get('category')) else '',
                        status=str(row.get('status', 'active')).strip()
                    )
                    
                    # Validate required fields
                    if not client.name or not client.document_number:
                        errors.append(f'Linha {index + 2}: Nome e Número do Documento são obrigatórios')
                        continue
                    
                    # Save client
                    client.save(user)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f'Linha {index + 2}: {str(e)}')
            
            return {
                'success': True,
                'message': f'{imported_count} clientes importados com sucesso',
                'imported': imported_count,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao processar arquivo: {str(e)}',
                'imported': 0,
                'errors': []
            }
    
    @staticmethod
    def import_products_from_csv(file_content: bytes, user: str) -> Dict[str, Any]:
        """Import products from CSV file"""
        try:
            # Read CSV content
            content = file_content.decode('utf-8')
            df = pd.read_csv(io.StringIO(content))
            
            # Map Portuguese columns back to English
            column_mapping = {
                'Código': 'code',
                'Nome': 'name',
                'Descrição': 'description',
                'Categoria': 'category',
                'Preço Unitário': 'unit_price',
                'Unidade de Medida': 'unit_of_measure',
                'Fornecedor': 'supplier_name',
                'Status': 'status'
            }
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Validate required columns
            required_columns = ['code', 'name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'message': f'Colunas obrigatórias ausentes: {", ".join(missing_columns)}',
                    'imported': 0,
                    'errors': []
                }
            
            imported_count = 0
            errors = []
            
            # Get suppliers for lookup
            suppliers = {s.name: s.id for s in Supplier.get_all(status='active')}
            
            for index, row in df.iterrows():
                try:
                    # Find supplier ID if supplier name is provided
                    supplier_id = None
                    if pd.notna(row.get('supplier_name')) and row.get('supplier_name'):
                        supplier_name = str(row.get('supplier_name')).strip()
                        supplier_id = suppliers.get(supplier_name)
                    
                    # Parse unit price
                    unit_price = None
                    if pd.notna(row.get('unit_price')):
                        try:
                            unit_price = float(row.get('unit_price'))
                        except (ValueError, TypeError):
                            unit_price = None
                    
                    # Create product object
                    product = Product(
                        code=str(row.get('code', '')).strip(),
                        name=str(row.get('name', '')).strip(),
                        description=str(row.get('description', '')).strip() if pd.notna(row.get('description')) else '',
                        category=str(row.get('category', '')).strip() if pd.notna(row.get('category')) else '',
                        unit_price=unit_price,
                        unit_of_measure=str(row.get('unit_of_measure', '')).strip() if pd.notna(row.get('unit_of_measure')) else '',
                        supplier_id=supplier_id,
                        status=str(row.get('status', 'active')).strip()
                    )
                    
                    # Validate required fields
                    if not product.code or not product.name:
                        errors.append(f'Linha {index + 2}: Código e Nome são obrigatórios')
                        continue
                    
                    # Save product
                    product.save(user)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f'Linha {index + 2}: {str(e)}')
            
            return {
                'success': True,
                'message': f'{imported_count} produtos importados com sucesso',
                'imported': imported_count,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao processar arquivo: {str(e)}',
                'imported': 0,
                'errors': []
            }
    
    @staticmethod
    def import_suppliers_from_csv(file_content: bytes, user: str) -> Dict[str, Any]:
        """Import suppliers from CSV file"""
        try:
            # Read CSV content
            content = file_content.decode('utf-8')
            df = pd.read_csv(io.StringIO(content))
            
            # Map Portuguese columns back to English
            column_mapping = {
                'Nome': 'name',
                'Tipo Documento': 'document_type',
                'Número Documento': 'document_number',
                'Email': 'email',
                'Telefone': 'phone',
                'Endereço': 'address',
                'Cidade': 'city',
                'Estado': 'state',
                'CEP': 'zip_code',
                'Categoria': 'category',
                'Pessoa de Contato': 'contact_person',
                'Status': 'status'
            }
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Validate required columns
            required_columns = ['name', 'document_type', 'document_number']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'message': f'Colunas obrigatórias ausentes: {", ".join(missing_columns)}',
                    'imported': 0,
                    'errors': []
                }
            
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Create supplier object
                    supplier = Supplier(
                        name=str(row.get('name', '')).strip(),
                        document_type=str(row.get('document_type', '')).strip(),
                        document_number=str(row.get('document_number', '')).strip(),
                        email=str(row.get('email', '')).strip() if pd.notna(row.get('email')) else '',
                        phone=str(row.get('phone', '')).strip() if pd.notna(row.get('phone')) else '',
                        address=str(row.get('address', '')).strip() if pd.notna(row.get('address')) else '',
                        city=str(row.get('city', '')).strip() if pd.notna(row.get('city')) else '',
                        state=str(row.get('state', '')).strip() if pd.notna(row.get('state')) else '',
                        zip_code=str(row.get('zip_code', '')).strip() if pd.notna(row.get('zip_code')) else '',
                        category=str(row.get('category', '')).strip() if pd.notna(row.get('category')) else '',
                        contact_person=str(row.get('contact_person', '')).strip() if pd.notna(row.get('contact_person')) else '',
                        status=str(row.get('status', 'active')).strip()
                    )
                    
                    # Validate required fields
                    if not supplier.name or not supplier.document_number:
                        errors.append(f'Linha {index + 2}: Nome e Número do Documento são obrigatórios')
                        continue
                    
                    # Save supplier
                    supplier.save(user)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f'Linha {index + 2}: {str(e)}')
            
            return {
                'success': True,
                'message': f'{imported_count} fornecedores importados com sucesso',
                'imported': imported_count,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao processar arquivo: {str(e)}',
                'imported': 0,
                'errors': []
            }
