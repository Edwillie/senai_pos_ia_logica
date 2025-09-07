import bcrypt
import streamlit as st
from typing import Optional, Dict, Any
from config.database import db_manager

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, password_hash, role, is_active 
                FROM users 
                WHERE username = ? AND is_active = 1
            ''', (username,))
            
            user = cursor.fetchone()
            
            if user and AuthService.verify_password(password, user['password_hash']):
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'is_active': user['is_active']
                }
            
            return None
    
    @staticmethod
    def create_user(username: str, password: str, role: str = 'user') -> bool:
        """Create a new user"""
        try:
            password_hash = AuthService.hash_password(password)
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password_hash, role)
                    VALUES (?, ?, ?)
                ''', (username, password_hash, role))
                
                conn.commit()
                return True
        except Exception:
            return False
    
    @staticmethod
    def change_password(username: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = AuthService.authenticate_user(username, old_password)
        if user:
            try:
                new_hash = AuthService.hash_password(new_password)
                
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE users SET password_hash = ? WHERE username = ?
                    ''', (new_hash, username))
                    
                    conn.commit()
                    return True
            except Exception:
                return False
        return False
    
    @staticmethod
    def get_all_users() -> list:
        """Get all users (admin only)"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, role, is_active, created_at 
                FROM users 
                ORDER BY username
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def toggle_user_status(user_id: int) -> bool:
        """Toggle user active status"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET is_active = NOT is_active WHERE id = ?
                ''', (user_id,))
                
                conn.commit()
                return True
        except Exception:
            return False
    
    @staticmethod
    def is_logged_in() -> bool:
        """Check if user is logged in"""
        return 'user' in st.session_state and st.session_state.user is not None
    
    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """Get current logged in user"""
        if AuthService.is_logged_in():
            return st.session_state.user
        return None
    
    @staticmethod
    def get_current_username() -> str:
        """Get current username or 'system' if not logged in"""
        user = AuthService.get_current_user()
        return user['username'] if user else 'system'
    
    @staticmethod
    def is_admin() -> bool:
        """Check if current user is admin"""
        user = AuthService.get_current_user()
        return user and user.get('role') == 'admin'
    
    @staticmethod
    def login_user(user: Dict[str, Any]):
        """Login user (set session state)"""
        st.session_state.user = user
    
    @staticmethod
    def logout_user():
        """Logout user (clear session state)"""
        if 'user' in st.session_state:
            del st.session_state.user
        st.rerun()
    
    @staticmethod
    def require_auth():
        """Decorator/function to require authentication"""
        if not AuthService.is_logged_in():
            st.error("⚠️ Você precisa fazer login para acessar esta página.")
            st.stop()
    
    @staticmethod
    def require_admin():
        """Decorator/function to require admin privileges"""
        AuthService.require_auth()
        if not AuthService.is_admin():
            st.error("⚠️ Você precisa de privilégios de administrador para acessar esta página.")
            st.stop()

def show_login_form():
    """Show login form"""
    st.title("🔐 Login - Sistema MDM")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            if username and password:
                user = AuthService.authenticate_user(username, password)
                if user:
                    AuthService.login_user(user)
                    st.success(f"Bem-vindo, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
            else:
                st.error("Por favor, preencha todos os campos.")
    
    # Show default credentials info
    st.info("""
    **Credenciais padrão:**
    - Usuário: admin
    - Senha: admin123
    """)

def show_user_management():
    """Show user management interface (admin only)"""
    AuthService.require_admin()
    
    st.subheader("👥 Gerenciamento de Usuários")
    
    # Create new user
    with st.expander("➕ Criar Novo Usuário"):
        with st.form("create_user_form"):
            new_username = st.text_input("Nome de Usuário")
            new_password = st.text_input("Senha", type="password")
            new_role = st.selectbox("Função", ["user", "admin"])
            
            if st.form_submit_button("Criar Usuário"):
                if new_username and new_password:
                    if AuthService.create_user(new_username, new_password, new_role):
                        st.success(f"Usuário '{new_username}' criado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao criar usuário. Nome de usuário pode já existir.")
                else:
                    st.error("Por favor, preencha todos os campos.")
    
    # List existing users
    users = AuthService.get_all_users()
    
    if users:
        st.subheader("Usuários Existentes")
        
        for user in users:
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            
            with col1:
                st.write(f"**{user['username']}**")
            
            with col2:
                st.write(user['role'])
            
            with col3:
                status = "✅ Ativo" if user['is_active'] else "❌ Inativo"
                st.write(status)
            
            with col4:
                if user['username'] != 'admin':  # Don't allow disabling admin user
                    if st.button(f"Toggle", key=f"toggle_{user['id']}"):
                        if AuthService.toggle_user_status(user['id']):
                            st.rerun()
            
            with col5:
                st.write(user['created_at'][:10] if user['created_at'] else '')

def show_change_password():
    """Show change password form"""
    AuthService.require_auth()
    
    st.subheader("🔑 Alterar Senha")
    
    with st.form("change_password_form"):
        current_password = st.text_input("Senha Atual", type="password")
        new_password = st.text_input("Nova Senha", type="password")
        confirm_password = st.text_input("Confirmar Nova Senha", type="password")
        
        if st.form_submit_button("Alterar Senha"):
            if current_password and new_password and confirm_password:
                if new_password != confirm_password:
                    st.error("A nova senha e a confirmação não coincidem.")
                elif len(new_password) < 6:
                    st.error("A nova senha deve ter pelo menos 6 caracteres.")
                else:
                    username = AuthService.get_current_username()
                    if AuthService.change_password(username, current_password, new_password):
                        st.success("Senha alterada com sucesso!")
                    else:
                        st.error("Senha atual incorreta.")
            else:
                st.error("Por favor, preencha todos os campos.")
