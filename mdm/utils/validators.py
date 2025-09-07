import re
from typing import List, Optional, Dict, Any

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class Validators:
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            return True  # Empty email is allowed
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate Brazilian phone number format"""
        if not phone:
            return True  # Empty phone is allowed
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Brazilian phone numbers: 10 or 11 digits
        return len(digits_only) in [10, 11]
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """Validate Brazilian CPF"""
        if not cpf:
            return False
        
        # Remove all non-digit characters
        cpf = re.sub(r'\D', '', cpf)
        
        # CPF must have 11 digits
        if len(cpf) != 11:
            return False
        
        # Check for known invalid CPFs (all same digits)
        if cpf in ['00000000000', '11111111111', '22222222222', '33333333333',
                   '44444444444', '55555555555', '66666666666', '77777777777',
                   '88888888888', '99999999999']:
            return False
        
        # Validate CPF algorithm
        def calculate_digit(cpf_digits, weights):
            total = sum(int(digit) * weight for digit, weight in zip(cpf_digits, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # First verification digit
        first_digit = calculate_digit(cpf[:9], range(10, 1, -1))
        if int(cpf[9]) != first_digit:
            return False
        
        # Second verification digit
        second_digit = calculate_digit(cpf[:10], range(11, 1, -1))
        if int(cpf[10]) != second_digit:
            return False
        
        return True
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        """Validate Brazilian CNPJ"""
        if not cnpj:
            return False
        
        # Remove all non-digit characters
        cnpj = re.sub(r'\D', '', cnpj)
        
        # CNPJ must have 14 digits
        if len(cnpj) != 14:
            return False
        
        # Check for known invalid CNPJs (all same digits)
        if cnpj in ['00000000000000', '11111111111111', '22222222222222',
                    '33333333333333', '44444444444444', '55555555555555',
                    '66666666666666', '77777777777777', '88888888888888',
                    '99999999999999']:
            return False
        
        # Validate CNPJ algorithm
        def calculate_digit(cnpj_digits, weights):
            total = sum(int(digit) * weight for digit, weight in zip(cnpj_digits, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # First verification digit
        first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        first_digit = calculate_digit(cnpj[:12], first_weights)
        if int(cnpj[12]) != first_digit:
            return False
        
        # Second verification digit
        second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        second_digit = calculate_digit(cnpj[:13], second_weights)
        if int(cnpj[13]) != second_digit:
            return False
        
        return True
    
    @staticmethod
    def validate_zip_code(zip_code: str) -> bool:
        """Validate Brazilian ZIP code (CEP)"""
        if not zip_code:
            return True  # Empty ZIP code is allowed
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', zip_code)
        
        # Brazilian ZIP code: 8 digits
        return len(digits_only) == 8
    
    @staticmethod
    def validate_document_number(document_type: str, document_number: str) -> bool:
        """Validate document number based on type"""
        if not document_number:
            return False
        
        document_type = document_type.upper()
        
        if document_type == 'CPF':
            return Validators.validate_cpf(document_number)
        elif document_type == 'CNPJ':
            return Validators.validate_cnpj(document_number)
        else:
            # For other document types, just check if it's not empty
            return len(document_number.strip()) > 0
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate that required fields are present and not empty"""
        errors = []
        
        for field in required_fields:
            value = data.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f"Campo '{field}' é obrigatório")
        
        return errors
    
    @staticmethod
    def validate_client_data(client_data: Dict[str, Any]) -> List[str]:
        """Validate client data"""
        errors = []
        
        # Required fields
        required_fields = ['name', 'document_type', 'document_number']
        errors.extend(Validators.validate_required_fields(client_data, required_fields))
        
        # Email validation
        email = client_data.get('email', '')
        if email and not Validators.validate_email(email):
            errors.append("Formato de email inválido")
        
        # Phone validation
        phone = client_data.get('phone', '')
        if phone and not Validators.validate_phone(phone):
            errors.append("Formato de telefone inválido")
        
        # Document validation
        document_type = client_data.get('document_type', '')
        document_number = client_data.get('document_number', '')
        if document_type and document_number:
            if not Validators.validate_document_number(document_type, document_number):
                errors.append(f"Número de {document_type} inválido")
        
        # ZIP code validation
        zip_code = client_data.get('zip_code', '')
        if zip_code and not Validators.validate_zip_code(zip_code):
            errors.append("Formato de CEP inválido")
        
        return errors
    
    @staticmethod
    def validate_product_data(product_data: Dict[str, Any]) -> List[str]:
        """Validate product data"""
        errors = []
        
        # Required fields
        required_fields = ['code', 'name']
        errors.extend(Validators.validate_required_fields(product_data, required_fields))
        
        # Unit price validation
        unit_price = product_data.get('unit_price')
        if unit_price is not None:
            try:
                price = float(unit_price)
                if price < 0:
                    errors.append("Preço unitário deve ser maior ou igual a zero")
            except (ValueError, TypeError):
                errors.append("Preço unitário deve ser um número válido")
        
        return errors
    
    @staticmethod
    def validate_supplier_data(supplier_data: Dict[str, Any]) -> List[str]:
        """Validate supplier data"""
        errors = []
        
        # Required fields
        required_fields = ['name', 'document_type', 'document_number']
        errors.extend(Validators.validate_required_fields(supplier_data, required_fields))
        
        # Email validation
        email = supplier_data.get('email', '')
        if email and not Validators.validate_email(email):
            errors.append("Formato de email inválido")
        
        # Phone validation
        phone = supplier_data.get('phone', '')
        if phone and not Validators.validate_phone(phone):
            errors.append("Formato de telefone inválido")
        
        # Document validation
        document_type = supplier_data.get('document_type', '')
        document_number = supplier_data.get('document_number', '')
        if document_type and document_number:
            if not Validators.validate_document_number(document_type, document_number):
                errors.append(f"Número de {document_type} inválido")
        
        # ZIP code validation
        zip_code = supplier_data.get('zip_code', '')
        if zip_code and not Validators.validate_zip_code(zip_code):
            errors.append("Formato de CEP inválido")
        
        return errors
    
    @staticmethod
    def format_document_number(document_type: str, document_number: str) -> str:
        """Format document number for display"""
        if not document_number:
            return ""
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', document_number)
        
        document_type = document_type.upper()
        
        if document_type == 'CPF' and len(digits_only) == 11:
            # Format as XXX.XXX.XXX-XX
            return f"{digits_only[:3]}.{digits_only[3:6]}.{digits_only[6:9]}-{digits_only[9:]}"
        elif document_type == 'CNPJ' and len(digits_only) == 14:
            # Format as XX.XXX.XXX/XXXX-XX
            return f"{digits_only[:2]}.{digits_only[2:5]}.{digits_only[5:8]}/{digits_only[8:12]}-{digits_only[12:]}"
        else:
            return document_number
    
    @staticmethod
    def format_phone_number(phone: str) -> str:
        """Format phone number for display"""
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        if len(digits_only) == 10:
            # Format as (XX) XXXX-XXXX
            return f"({digits_only[:2]}) {digits_only[2:6]}-{digits_only[6:]}"
        elif len(digits_only) == 11:
            # Format as (XX) XXXXX-XXXX
            return f"({digits_only[:2]}) {digits_only[2:7]}-{digits_only[7:]}"
        else:
            return phone
    
    @staticmethod
    def format_zip_code(zip_code: str) -> str:
        """Format ZIP code for display"""
        if not zip_code:
            return ""
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', zip_code)
        
        if len(digits_only) == 8:
            # Format as XXXXX-XXX
            return f"{digits_only[:5]}-{digits_only[5:]}"
        else:
            return zip_code
