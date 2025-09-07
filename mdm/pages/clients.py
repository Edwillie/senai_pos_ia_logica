import streamlit as st
from typing import Optional
from models.client import Client
from services.auth_service import AuthService
from services.export_service import ExportService, ImportService
from utils.validators import Validators
from utils.helpers import UIHelpers, FormHelpers, DataHelpers

def show_clients_page():
    """Show clients management page"""
    st.header("👥 Gerenciamento de Clientes")
    
    # Check authentication
    AuthService.require_auth()
    
    # Action tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Listar", "➕ Cadastrar", "📥 Importar", "📊 Relatórios"])
    
    with tab1:
        show_clients_list()
    
    with tab2:
        show_client_form()
    
    with tab3:
        show_import_clients()
    
    with tab4:
        show_clients_reports()

def show_clients_list():
    """Show list of clients with search and filters"""
    st.subheader("📋 Lista de Clientes")
    
    # Search and filters
    filters = UIHelpers.create_search_filters('clients')
    
    # Get clients based on filters
    if filters.get('query') or any(v for k, v in filters.items() if k != 'query'):
        clients = Client.search(
            query=filters.get('query', ''),
            filters={k: v for k, v in filters.items() if k != 'query' and v}
        )
    else:
        clients = Client.get_all(status='active')
    
    if clients:
        # Convert to display format
        client_data = []
        for client in clients:
            client_data.append({
                'ID': client.id,
                'Nome': client.name,
                'Documento': f"{client.document_type}: {Validators.format_document_number(client.document_type, client.document_number)}",
                'Email': client.email or '-',
                'Telefone': Validators.format_phone_number(client.phone) or '-',
                'Cidade': client.city or '-',
                'Categoria': client.category or '-',
                'Status': UIHelpers.create_status_badge(client.status)
            })
        
        # Pagination
        paginated = DataHelpers.paginate_data(client_data, page_size=10)
        
        # Display info
        st.info(f"Mostrando {paginated['showing_from']}-{paginated['showing_to']} de {paginated['total_items']} clientes")
        
        # Display table
        for i, client in enumerate(paginated['data']):
            with st.expander(f"👤 {client['Nome']} - {client['Documento']}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Email:** {client['Email']}")
                    st.write(f"**Telefone:** {client['Telefone']}")
                    st.write(f"**Cidade:** {client['Cidade']}")
                    st.write(f"**Categoria:** {client['Categoria']}")
                
                with col2:
                    if st.button("✏️ Editar", key=f"edit_client_{client['ID']}"):
                        st.session_state.edit_client_id = client['ID']
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Excluir", key=f"delete_client_{client['ID']}"):
                        if UIHelpers.create_confirmation_dialog(
                            f"Tem certeza que deseja excluir o cliente '{client['Nome']}'?",
                            f"delete_client_{client['ID']}"
                        ):
                            if Client.delete(client['ID'], AuthService.get_current_username()):
                                UIHelpers.show_success_message("Cliente excluído com sucesso!")
                                st.rerun()
                            else:
                                UIHelpers.show_error_message("Erro ao excluir cliente.")
        
        # Export button
        st.markdown("---")
        if st.button("📥 Exportar Clientes (CSV)", use_container_width=True):
            csv_data = ExportService.export_clients_to_csv()
            st.download_button(
                "⬇️ Download CSV",
                csv_data,
                f"clientes_{st.session_state.get('export_timestamp', 'export')}.csv",
                "text/csv"
            )
    
    else:
        st.info("Nenhum cliente encontrado.")
        if st.button("➕ Cadastrar Primeiro Cliente"):
            st.session_state.current_tab = 1
            st.rerun()

def show_client_form(client_id: Optional[int] = None):
    """Show client creation/editing form"""
    # Check if editing existing client
    edit_client_id = st.session_state.get('edit_client_id')
    if edit_client_id:
        client_id = edit_client_id
        st.session_state.edit_client_id = None  # Clear after use
    
    if client_id:
        st.subheader("✏️ Editar Cliente")
        client = Client.get_by_id(client_id)
        if not client:
            UIHelpers.show_error_message("Cliente não encontrado.")
            return
    else:
        st.subheader("➕ Cadastrar Novo Cliente")
        client = Client()
    
    # Form
    with st.form("client_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nome *", value=client.name)
            
            document_type = st.selectbox(
                "Tipo de Documento *",
                options=["CPF", "CNPJ", "RG", "Passaporte"],
                index=["CPF", "CNPJ", "RG", "Passaporte"].index(client.document_type) if client.document_type else 0
            )
            
            document_number = FormHelpers.create_document_input(
                "Número do Documento *",
                document_type,
                client.document_number
            )
            
            email = FormHelpers.create_email_input("Email", client.email)
            
            phone = FormHelpers.create_phone_input("Telefone", client.phone)
            
            category = st.text_input("Categoria", value=client.category)
        
        with col2:
            address = st.text_area("Endereço", value=client.address)
            
            city = st.text_input("Cidade", value=client.city)
            
            state = st.selectbox(
                "Estado",
                options=["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
                        "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", 
                        "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"],
                index=0 if not client.state else ["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
                        "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", 
                        "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"].index(client.state)
            )
            
            zip_code = FormHelpers.create_zip_code_input("CEP", client.zip_code)
            
            status = st.selectbox(
                "Status",
                options=["active", "inactive"],
                index=0 if client.status == "active" else 1,
                format_func=lambda x: "Ativo" if x == "active" else "Inativo"
            )
        
        # Form buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit = st.form_submit_button("💾 Salvar", use_container_width=True)
        
        with col2:
            cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if cancel:
            if 'edit_client_id' in st.session_state:
                del st.session_state.edit_client_id
            st.rerun()
        
        if submit:
            # Validate form data
            form_data = {
                'name': name,
                'document_type': document_type,
                'document_number': document_number,
                'email': email,
                'phone': phone,
                'address': address,
                'city': city,
                'state': state,
                'zip_code': zip_code,
                'category': category,
                'status': status
            }
            
            errors = Validators.validate_client_data(form_data)
            
            if errors:
                for error in errors:
                    UIHelpers.show_error_message(error)
            else:
                # Update client object
                client.name = name
                client.document_type = document_type
                client.document_number = document_number
                client.email = email
                client.phone = phone
                client.address = address
                client.city = city
                client.state = state
                client.zip_code = zip_code
                client.category = category
                client.status = status
                
                try:
                    # Save client
                    client.save(AuthService.get_current_username())
                    
                    if client_id:
                        UIHelpers.show_success_message("Cliente atualizado com sucesso!")
                    else:
                        UIHelpers.show_success_message("Cliente cadastrado com sucesso!")
                    
                    # Clear form
                    if 'edit_client_id' in st.session_state:
                        del st.session_state.edit_client_id
                    
                    st.rerun()
                    
                except Exception as e:
                    UIHelpers.show_error_message(f"Erro ao salvar cliente: {str(e)}")

def show_import_clients():
    """Show client import interface"""
    st.subheader("📤 Importar Clientes")
    
    st.info("""
    **Formato do arquivo CSV:**
    - Nome, Tipo Documento, Número Documento, Email, Telefone, Endereço, Cidade, Estado, CEP, Categoria, Status
    - Campos obrigatórios: Nome, Tipo Documento, Número Documento
    - Tipos de documento aceitos: CPF, CNPJ, RG, Passaporte
    """)
    
    # File uploader
    uploaded_file = DataHelpers.import_csv_uploader("Selecionar arquivo CSV", key="import_clients")
    
    if uploaded_file is not None:
        # Show file info
        st.write(f"**Arquivo:** {uploaded_file.name}")
        st.write(f"**Tamanho:** {uploaded_file.size} bytes")
        
        # Import button
        if st.button("📥 Importar Clientes", use_container_width=True):
            with st.spinner("Importando clientes..."):
                result = ImportService.import_clients_from_csv(
                    uploaded_file.getvalue(),
                    AuthService.get_current_username()
                )
                
                if result['success']:
                    UIHelpers.show_success_message(result['message'])
                    
                    if result['errors']:
                        st.warning("⚠️ Alguns registros apresentaram erros:")
                        for error in result['errors']:
                            st.write(f"- {error}")
                else:
                    UIHelpers.show_error_message(result['message'])
    
    # Download template
    st.markdown("---")
    st.subheader("📋 Modelo de Importação")
    
    if st.button("⬇️ Baixar Modelo CSV", use_container_width=True):
        # Create sample CSV
        sample_data = """Nome,Tipo Documento,Número Documento,Email,Telefone,Endereço,Cidade,Estado,CEP,Categoria,Status
João Silva,CPF,12345678901,joao@email.com,(11) 99999-9999,Rua das Flores 123,São Paulo,SP,01234-567,Pessoa Física,active
Empresa ABC,CNPJ,12345678000195,contato@empresa.com,(11) 88888-8888,Av. Paulista 1000,São Paulo,SP,01310-100,Pessoa Jurídica,active"""
        
        st.download_button(
            "📥 Download Modelo",
            sample_data.encode('utf-8'),
            "modelo_clientes.csv",
            "text/csv"
        )

def show_clients_reports():
    """Show client reports and analytics"""
    st.subheader("📊 Relatórios de Clientes")
    
    clients = Client.get_all()
    
    if not clients:
        st.info("Nenhum cliente cadastrado para gerar relatórios.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_clients = len(clients)
        st.metric("Total de Clientes", total_clients)
    
    with col2:
        active_clients = len([c for c in clients if c.status == 'active'])
        st.metric("Clientes Ativos", active_clients)
    
    with col3:
        with_email = len([c for c in clients if c.email])
        st.metric("Com Email", with_email)
    
    with col4:
        with_phone = len([c for c in clients if c.phone])
        st.metric("Com Telefone", with_phone)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Status distribution
        status_counts = {}
        for client in clients:
            status_counts[client.status] = status_counts.get(client.status, 0) + 1
        
        from utils.helpers import ChartHelpers
        ChartHelpers.create_pie_chart(status_counts, "Distribuição por Status")
    
    with col2:
        # Document type distribution
        doc_type_counts = {}
        for client in clients:
            doc_type = client.document_type or 'Não informado'
            doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1
        
        ChartHelpers.create_pie_chart(doc_type_counts, "Distribuição por Tipo de Documento")
    
    # Category analysis
    if any(c.category for c in clients):
        st.subheader("📈 Análise por Categoria")
        
        category_counts = {}
        for client in clients:
            category = client.category or 'Sem categoria'
            category_counts[category] = category_counts.get(category, 0) + 1
        
        ChartHelpers.create_bar_chart(
            category_counts,
            "Clientes por Categoria",
            "Categoria",
            "Quantidade"
        )
    
    # Geographic distribution
    if any(c.state for c in clients):
        st.subheader("🗺️ Distribuição Geográfica")
        
        state_counts = {}
        for client in clients:
            state = client.state or 'Não informado'
            state_counts[state] = state_counts.get(state, 0) + 1
        
        ChartHelpers.create_bar_chart(
            state_counts,
            "Clientes por Estado",
            "Estado",
            "Quantidade"
        )
