"""
Data validation utilities for different field types
"""

from datetime import datetime
from typing import Any, Tuple
import re

class DataValidator:
    @staticmethod
    def validate_text(value: Any) -> Tuple[bool, str, Any]:
        """Validate text field"""
        if value is None or value == "":
            return True, "", ""
        
        try:
            str_value = str(value).strip()
            return True, "", str_value
        except Exception as e:
            return False, f"Erro ao converter para texto: {e}", None
    
    @staticmethod
    def validate_integer(value: Any) -> Tuple[bool, str, Any]:
        """Validate integer field"""
        if value is None or value == "":
            return True, "", None
        
        try:
            # Handle string input
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    return True, "", None
            
            int_value = int(float(value))  # Convert via float to handle "123.0"
            return True, "", int_value
        except (ValueError, TypeError):
            return False, f"'{value}' não é um número inteiro válido", None
    
    @staticmethod
    def validate_decimal(value: Any) -> Tuple[bool, str, Any]:
        """Validate decimal/float field"""
        if value is None or value == "":
            return True, "", None
        
        try:
            # Handle string input
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    return True, "", None
                # Replace comma with dot for Brazilian decimal format
                value = value.replace(',', '.')
            
            float_value = float(value)
            return True, "", float_value
        except (ValueError, TypeError):
            return False, f"'{value}' não é um número decimal válido", None
    
    @staticmethod
    def validate_date(value: Any) -> Tuple[bool, str, Any]:
        """Validate date field"""
        if value is None or value == "":
            return True, "", None
        
        try:
            # If it's already a datetime object
            if isinstance(value, datetime):
                return True, "", value.strftime('%Y-%m-%d')
            
            # If it's a string, try to parse it
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    return True, "", None
                
                # Try different date formats
                date_formats = [
                    '%Y-%m-%d',      # 2023-12-25
                    '%d/%m/%Y',      # 25/12/2023
                    '%d-%m-%Y',      # 25-12-2023
                    '%Y/%m/%d',      # 2023/12/25
                    '%d/%m/%y',      # 25/12/23
                    '%d-%m-%y'       # 25-12-23
                ]
                
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(value, fmt)
                        return True, "", parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                
                return False, f"'{value}' não é uma data válida. Use formatos como: DD/MM/AAAA, AAAA-MM-DD", None
            
            return False, f"'{value}' não é uma data válida", None
            
        except Exception as e:
            return False, f"Erro ao validar data: {e}", None
    
    @staticmethod
    def validate_boolean(value: Any) -> Tuple[bool, str, Any]:
        """Validate boolean field"""
        if value is None or value == "":
            return True, "", None
        
        try:
            # Handle different boolean representations
            if isinstance(value, bool):
                return True, "", value
            
            if isinstance(value, str):
                value = value.strip().lower()
                if value == "":
                    return True, "", None
                
                true_values = ['true', 'verdadeiro', 'sim', 's', '1', 'yes', 'y']
                false_values = ['false', 'falso', 'não', 'nao', 'n', '0', 'no']
                
                if value in true_values:
                    return True, "", True
                elif value in false_values:
                    return True, "", False
                else:
                    return False, f"'{value}' não é um valor booleano válido. Use: Sim/Não, True/False, 1/0", None
            
            if isinstance(value, (int, float)):
                return True, "", bool(value)
            
            return False, f"'{value}' não é um valor booleano válido", None
            
        except Exception as e:
            return False, f"Erro ao validar booleano: {e}", None
    
    @staticmethod
    def validate_field(field_type: str, value: Any) -> Tuple[bool, str, Any]:
        """
        Validate a field based on its type
        
        Args:
            field_type: The type of the field (from config.SUPPORTED_DATA_TYPES keys)
            value: The value to validate
            
        Returns:
            Tuple of (is_valid, error_message, converted_value)
        """
        validators = {
            "Texto": DataValidator.validate_text,
            "Número Inteiro": DataValidator.validate_integer,
            "Número Decimal": DataValidator.validate_decimal,
            "Data": DataValidator.validate_date,
            "Booleano": DataValidator.validate_boolean
        }
        
        validator = validators.get(field_type)
        if not validator:
            return False, f"Tipo de campo não suportado: {field_type}", None
        
        return validator(value)
    
    @staticmethod
    def validate_record(fields: list, data: dict) -> Tuple[bool, list, dict]:
        """
        Validate an entire record against field definitions
        
        Args:
            fields: List of field definitions with 'name' and 'type'
            data: Dictionary of field values
            
        Returns:
            Tuple of (is_valid, error_messages, validated_data)
        """
        errors = []
        validated_data = {}
        
        for field in fields:
            field_name = field['name']
            field_type = field['type']
            value = data.get(field_name)
            
            is_valid, error_msg, converted_value = DataValidator.validate_field(field_type, value)
            
            if not is_valid:
                errors.append(f"{field_name}: {error_msg}")
            else:
                validated_data[field_name] = converted_value
        
        return len(errors) == 0, errors, validated_data
