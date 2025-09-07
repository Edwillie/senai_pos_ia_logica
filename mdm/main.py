import streamlit as st
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import db_manager
from services.auth_service import AuthService, show_login_form
from pages.dashboard import show_dashboard
from pages.clients import show_clients_page
from pages.products import show_products_page
from pages.suppliers import show_suppliers_page
from pages.duplicates import show_duplicates_page
from utils.helpers import UIHelpers

# Page configuration
st.set_page_config(
    page_title="Sistema MDM - Gerenciamento de Dados Mestres",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2e86ab 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        text-align: center;
    }
    
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .status-active { color: #28a745; }
    .status-inactive { color: #dc3545; }
    .status-pending { color: #ffc107; }
</style>
""", unsafe_allow_html=True)

def initialize_app():
    """Initialize the application"""
    # Create default admin user if no users exist
    if db_manager.create_default_user():
        st.info("👤 Usuário administrador padrão criado: admin/admin123")

def show_sidebar():
    """Show sidebar navigation"""
    with st.sidebar:
        st.markdown("### 🏢 Sistema MDM")
        st.markdown("---")
        
        # User info
        if AuthService.is_logged_in():
            user = AuthService.get_current_user()
            st.markdown(f"**Usuário:** {user['username']}")
            st.markdown(f"**Função:** {user['role'].title()}")
            st.markdown("---")
            
            # Navigation menu
            pages = {
                "📊 Dashboard": "dashboard",
                "👥 Clientes": "clients", 
                "📦 Produtos": "products",
                "🏭 Fornecedores": "suppliers",
                "🔍 Duplicatas": "duplicates"
            }
            
            # Admin-only pages
            if AuthService.is_admin():
                pages["👤 Usuários"] = "users"
                pages["📋 Auditoria"] = "audit"
            
            # Page selection
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 'dashboard'
            
            for page_name, page_key in pages.items():
                if st.button(page_name, key=page_key, use_container_width=True):
                    st.session_state.current_page = page_key
                    st.rerun()
            
            st.markdown("---")
            
            # Settings and logout
            if st.button("🔑 Alterar Senha", use_container_width=True):
                st.session_state.current_page = 'change_password'
                st.rerun()
            
            if st.button("🚪 Sair", use_container_width=True):
                AuthService.logout_user()

def show_main_content():
    """Show main content based on current page"""
    if not AuthService.is_logged_in():
        show_login_form()
        return
    
    current_page = st.session_state.get('current_page', 'dashboard')
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Sistema de Gerenciamento de Dados Mestres (MDM)</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Route to appropriate page
    if current_page == 'dashboard':
        show_dashboard()
    elif current_page == 'clients':
        show_clients_page()
    elif current_page == 'products':
        show_products_page()
    elif current_page == 'suppliers':
        show_suppliers_page()
    elif current_page == 'duplicates':
        show_duplicates_page()
    elif current_page == 'users':
        from services.auth_service import show_user_management
        show_user_management()
    elif current_page == 'audit':
        from pages.audit import show_audit_page
        show_audit_page()
    elif current_page == 'change_password':
        from services.auth_service import show_change_password
        show_change_password()
    else:
        st.error("Página não encontrada")

def main():
    """Main application function"""
    try:
        # Initialize app
        initialize_app()
        
        # Show sidebar
        show_sidebar()
        
        # Show main content
        show_main_content()
        
    except Exception as e:
        st.error(f"Erro na aplicação: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()
