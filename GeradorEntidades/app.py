"""
Main Streamlit application for Dynamic CRUD Entity Generator
"""

import streamlit as st
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pages import entity_creator, data_manager, import_export
import config

def main():
    """Main application function"""
    
    # Page configuration
    st.set_page_config(
        page_title=config.APP_TITLE,
        page_icon=config.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown(f"""
    <div class="main-header">
        <h1>{config.APP_ICON} {config.APP_TITLE}</h1>
        <p>Sistema completo para criação e gerenciamento dinâmico de entidades</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🧭 Navegação")
        
        # Navigation menu
        page = st.radio(
            "Selecione uma página:",
            options=[
                "🏠 Início",
                "🏗️ Criar Entidade", 
                "📊 Gerenciar Dados",
                "📁 Importar/Exportar"
            ],
            index=0
        )
        
        st.divider()
        
        # Quick stats
        st.subheader("📈 Estatísticas Rápidas")
        
        try:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
            entities = db_manager.get_all_entities()
            
            st.metric("Entidades Criadas", len(entities))
            
            # Count total records across all entities
            total_records = 0
            for entity in entities:
                df = db_manager.get_all_records(entity)
                total_records += len(df)
            
            st.metric("Total de Registros", total_records)
            
            if entities:
                st.write("**Entidades:**")
                for entity in entities[:5]:  # Show first 5
                    records_count = len(db_manager.get_all_records(entity))
                    st.write(f"• {entity} ({records_count} registros)")
                
                if len(entities) > 5:
                    st.write(f"... e mais {len(entities) - 5} entidades")
        
        except Exception as e:
            st.error("Erro ao carregar estatísticas")
        
        st.divider()
        
        # Help section
        with st.expander("❓ Ajuda"):
            st.write("""
            **Como usar o sistema:**
            
            1. **Criar Entidade**: Defina uma nova tabela com campos personalizados
            2. **Gerenciar Dados**: Adicione, edite e visualize registros
            3. **Importar/Exportar**: Trabalhe com arquivos CSV/Excel
            
            **Tipos de dados suportados:**
            - Texto
            - Número Inteiro
            - Número Decimal
            - Data
            - Booleano (Sim/Não)
            """)
        
        # About section
        with st.expander("ℹ️ Sobre"):
            st.write("""
            **Gerador de Entidades v1.0**
            
            Sistema desenvolvido em Python com:
            - Streamlit (Interface)
            - SQLite (Banco de dados)
            - Pandas (Manipulação de dados)
            
            Desenvolvido para Windows 11
            """)
    
    # Main content area
    if page == "🏠 Início":
        show_home_page()
    elif page == "🏗️ Criar Entidade":
        entity_creator.show_entity_creator()
    elif page == "📊 Gerenciar Dados":
        data_manager.show_data_manager()
    elif page == "📁 Importar/Exportar":
        import_export.show_import_export()

def show_home_page():
    """Display the home page"""
    
    # Welcome section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("👋 Bem-vindo ao Gerador de Entidades!")
        st.write("""
        Este sistema permite criar e gerenciar entidades (tabelas) de forma dinâmica, 
        sem necessidade de programação. Você pode:
        
        - **Criar entidades personalizadas** com campos de diferentes tipos
        - **Gerenciar dados** com operações completas de CRUD
        - **Importar e exportar** dados em formatos CSV e Excel
        - **Validar dados** automaticamente conforme os tipos definidos
        """)
    
    with col2:
        st.image("https://via.placeholder.com/300x200/667eea/ffffff?text=CRUD+System", 
                caption="Sistema CRUD Dinâmico")
    
    st.divider()
    
    # Quick start guide
    st.header("🚀 Guia de Início Rápido")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="info-box">
        <h4>1️⃣ Criar Entidade</h4>
        <p>Comece criando uma nova entidade definindo seus campos e tipos de dados.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-box">
        <h4>2️⃣ Adicionar Dados</h4>
        <p>Use a página de gerenciamento para adicionar registros à sua entidade.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="info-box">
        <h4>3️⃣ Importar/Exportar</h4>
        <p>Trabalhe com arquivos CSV/Excel para importar ou exportar seus dados.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Features overview
    st.header("✨ Funcionalidades Principais")
    
    features = [
        {
            "icon": "🏗️",
            "title": "Criação Dinâmica de Entidades",
            "description": "Crie tabelas personalizadas com campos de diferentes tipos sem programação."
        },
        {
            "icon": "📊",
            "title": "Gerenciamento Completo de Dados",
            "description": "Visualize, adicione, edite e exclua registros com interface intuitiva."
        },
        {
            "icon": "📁",
            "title": "Importação e Exportação",
            "description": "Trabalhe com arquivos CSV e Excel com validação automática de dados."
        },
        {
            "icon": "✅",
            "title": "Validação Automática",
            "description": "Validação de tipos de dados em tempo real para garantir integridade."
        },
        {
            "icon": "🔍",
            "title": "Busca e Filtros",
            "description": "Encontre rapidamente os dados que precisa com ferramentas de busca."
        },
        {
            "icon": "💾",
            "title": "Armazenamento Local",
            "description": "Dados salvos localmente em SQLite, sem necessidade de servidor externo."
        }
    ]
    
    for i in range(0, len(features), 2):
        col1, col2 = st.columns(2)
        
        with col1:
            feature = features[i]
            st.markdown(f"""
            <div class="metric-container">
            <h4>{feature['icon']} {feature['title']}</h4>
            <p>{feature['description']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        if i + 1 < len(features):
            with col2:
                feature = features[i + 1]
                st.markdown(f"""
                <div class="metric-container">
                <h4>{feature['icon']} {feature['title']}</h4>
                <p>{feature['description']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()
    
    # System status
    st.header("🔧 Status do Sistema")
    
    try:
        from database.db_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.success("✅ Banco de Dados")
            st.write("SQLite conectado")
        
        with col2:
            entities = db_manager.get_all_entities()
            st.info(f"📊 {len(entities)} Entidades")
            st.write("Criadas no sistema")
        
        with col3:
            total_records = 0
            for entity in entities:
                df = db_manager.get_all_records(entity)
                total_records += len(df)
            st.info(f"📝 {total_records} Registros")
            st.write("Total de dados")
        
        with col4:
            st.success("🚀 Sistema Ativo")
            st.write("Pronto para uso")
    
    except Exception as e:
        st.error(f"❌ Erro no sistema: {e}")
    
    # Call to action
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="success-box" style="text-align: center;">
        <h3>🎯 Pronto para começar?</h3>
        <p>Use o menu lateral para navegar pelas funcionalidades do sistema!</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
