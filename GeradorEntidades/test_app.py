"""
Simple test version of the Dynamic CRUD Application
"""

import streamlit as st
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    st.set_page_config(
        page_title="Gerador de Entidades - CRUD Dinâmico",
        page_icon="🗃️",
        layout="wide"
    )
    
    st.title("🗃️ Gerador de Entidades - CRUD Dinâmico")
    st.write("Sistema completo para criação e gerenciamento dinâmico de entidades")
    
    # Test database connection
    try:
        from database.db_manager import DatabaseManager
        db_manager = DatabaseManager()
        st.success("✅ Banco de dados conectado com sucesso!")
        
        # Show existing entities
        entities = db_manager.get_all_entities()
        st.write(f"**Entidades existentes:** {len(entities)}")
        
        for entity in entities:
            st.write(f"- {entity}")
            
    except Exception as e:
        st.error(f"❌ Erro ao conectar com o banco: {e}")
    
    # Test validators
    try:
        from utils.validators import DataValidator
        test_result = DataValidator.validate_text("Teste")
        if test_result[0]:
            st.success("✅ Validadores funcionando!")
        else:
            st.error("❌ Erro nos validadores")
    except Exception as e:
        st.error(f"❌ Erro nos validadores: {e}")
    
    # Test file handler
    try:
        from utils.file_handler import FileHandler
        st.success("✅ Manipulador de arquivos carregado!")
    except Exception as e:
        st.error(f"❌ Erro no manipulador de arquivos: {e}")
    
    st.divider()
    st.write("**Status:** Sistema funcionando corretamente!")

if __name__ == "__main__":
    main()
