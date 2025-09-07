"""
File import/export utilities for CSV and Excel files
"""

import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Tuple
import io
from utils.validators import DataValidator

class FileHandler:
    @staticmethod
    def export_to_csv(df: pd.DataFrame, filename: str = None) -> bytes:
        """Export DataFrame to CSV format"""
        try:
            # Convert DataFrame to CSV bytes
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_bytes = csv_buffer.getvalue().encode('utf-8-sig')
            return csv_bytes
        except Exception as e:
            st.error(f"Erro ao exportar CSV: {e}")
            return None
    
    @staticmethod
    def export_to_excel(df: pd.DataFrame, filename: str = None) -> bytes:
        """Export DataFrame to Excel format"""
        try:
            # Convert DataFrame to Excel bytes
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Dados')
            excel_bytes = excel_buffer.getvalue()
            return excel_bytes
        except Exception as e:
            st.error(f"Erro ao exportar Excel: {e}")
            return None
    
    @staticmethod
    def read_uploaded_file(uploaded_file) -> Tuple[bool, str, pd.DataFrame]:
        """
        Read uploaded CSV or Excel file
        
        Returns:
            Tuple of (success, error_message, dataframe)
        """
        try:
            if uploaded_file is None:
                return False, "Nenhum arquivo foi enviado", pd.DataFrame()
            
            file_extension = uploaded_file.name.lower().split('.')[-1]
            
            if file_extension == 'csv':
                # Try different encodings for CSV
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding='latin-1')
                    except UnicodeDecodeError:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding='cp1252')
                        
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file)
            else:
                return False, f"Formato de arquivo não suportado: {file_extension}", pd.DataFrame()
            
            # Clean column names (remove extra spaces)
            df.columns = df.columns.str.strip()
            
            return True, "", df
            
        except Exception as e:
            return False, f"Erro ao ler arquivo: {str(e)}", pd.DataFrame()
    
    @staticmethod
    def validate_import_data(df: pd.DataFrame, entity_fields: List[Dict[str, str]]) -> Tuple[bool, List[str], pd.DataFrame]:
        """
        Validate imported data against entity field definitions
        
        Args:
            df: DataFrame with imported data
            entity_fields: List of field definitions
            
        Returns:
            Tuple of (success, error_messages, validated_dataframe)
        """
        errors = []
        validated_rows = []
        
        # Check if required columns exist
        expected_columns = [field['name'] for field in entity_fields]
        missing_columns = []
        
        for col in expected_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            errors.append(f"Colunas obrigatórias não encontradas: {', '.join(missing_columns)}")
            return False, errors, pd.DataFrame()
        
        # Validate each row
        for index, row in df.iterrows():
            row_errors = []
            validated_row = {}
            
            for field in entity_fields:
                field_name = field['name']
                field_type = field['type']
                value = row.get(field_name)
                
                # Skip NaN values
                if pd.isna(value):
                    value = None
                
                is_valid, error_msg, converted_value = DataValidator.validate_field(field_type, value)
                
                if not is_valid:
                    row_errors.append(f"Linha {index + 2}, {field_name}: {error_msg}")
                else:
                    validated_row[field_name] = converted_value
            
            if row_errors:
                errors.extend(row_errors)
            else:
                validated_rows.append(validated_row)
        
        # Create validated DataFrame
        if validated_rows:
            validated_df = pd.DataFrame(validated_rows)
        else:
            validated_df = pd.DataFrame()
        
        success = len(errors) == 0
        return success, errors, validated_df
    
    @staticmethod
    def prepare_export_dataframe(df: pd.DataFrame, entity_fields: List[Dict[str, str]]) -> pd.DataFrame:
        """
        Prepare DataFrame for export by formatting columns properly
        """
        try:
            export_df = df.copy()
            
            # Remove system columns if they exist
            system_columns = ['id', 'created_at']
            for col in system_columns:
                if col in export_df.columns:
                    export_df = export_df.drop(columns=[col])
            
            # Format columns based on field types
            field_type_map = {field['name']: field['type'] for field in entity_fields}
            
            for col in export_df.columns:
                if col in field_type_map:
                    field_type = field_type_map[col]
                    
                    if field_type == "Data":
                        # Format dates for better readability
                        export_df[col] = pd.to_datetime(export_df[col], errors='coerce').dt.strftime('%d/%m/%Y')
                    elif field_type == "Booleano":
                        # Convert boolean to readable format
                        export_df[col] = export_df[col].map({True: 'Sim', False: 'Não', None: ''})
                    elif field_type == "Número Decimal":
                        # Format decimals
                        export_df[col] = export_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "")
            
            return export_df
            
        except Exception as e:
            st.error(f"Erro ao preparar dados para exportação: {e}")
            return df
    
    @staticmethod
    def get_sample_template(entity_fields: List[Dict[str, str]]) -> pd.DataFrame:
        """
        Generate a sample template DataFrame for import
        """
        sample_data = {}
        
        for field in entity_fields:
            field_name = field['name']
            field_type = field['type']
            
            if field_type == "Texto":
                sample_data[field_name] = ["Exemplo de texto"]
            elif field_type == "Número Inteiro":
                sample_data[field_name] = [123]
            elif field_type == "Número Decimal":
                sample_data[field_name] = [123.45]
            elif field_type == "Data":
                sample_data[field_name] = ["25/12/2023"]
            elif field_type == "Booleano":
                sample_data[field_name] = ["Sim"]
            else:
                sample_data[field_name] = [""]
        
        return pd.DataFrame(sample_data)
