"""
Configuration file for the Dynamic CRUD Application
"""

import os

# Database configuration
DATABASE_PATH = "entities.db"

# Supported data types for entity fields
SUPPORTED_DATA_TYPES = {
    "Texto": "TEXT",
    "Número Inteiro": "INTEGER", 
    "Número Decimal": "REAL",
    "Data": "DATE",
    "Booleano": "BOOLEAN"
}

# File upload configuration
MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls']

# Application settings
APP_TITLE = "Gerador de Entidades - CRUD Dinâmico"
APP_ICON = "🗃️"
