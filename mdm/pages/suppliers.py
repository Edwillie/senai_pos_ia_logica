import streamlit as st
from typing import Optional
from models.supplier import Supplier
from services.auth_service import AuthService
from services.export_service import ExportService, ImportService
from utils.validators import Validators
from utils.helpers import UIHelpers, FormHelpers, DataHelpers

def show_suppliers_page():
    """Show suppliers management page"""
    st.header("🏭 Gerenciamento de Fornecedores")
    
    # Check authentication
    AuthService.require_auth()
    
    # Action tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Listar", "➕ Cadastrar", "📥 Importar", "📊 Relatórios"])
    
    with tab1:
        show_suppliers_list()
    
    with tab2:
        show_supplier_form()
    
    with tab3:
        show_import_suppliers()
    
    with tab4:
        show_suppliers_reports()

def show_suppliers_list():
    """Show list of suppliers with search and filters"""
    st.subheader("📋 Lista de Fornecedores")
    
    # Search and filters
    filters = UIHelpers.create_search_filters('suppliers')
    
    # Get suppliers based on filters
    if filters.get('query') or any(v for k, v in filters.items() if k != 'query'):
        suppliers = Supplier.search(
            query=filters.get('query', ''),
            filters={k: v for k, v in filters.items() if k != 'query' and v}
        )
    else:
        suppliers = Supplier.get_all(status='active')
    
    if suppliers:
        # Convert to display format
        supplier_data = []
        for supplier in suppliers:
            supplier_data.append({
                'ID': supplier.id,
                'Nome': supplier.name,
                'Documento': f"{supplier.document_type}: {Validators.format_document_number(supplier.document_type, supplier.document_number)}",
                'Email': supplier.email or '-',
                'Telefone': Validators.format_phone_number(supplier.phone) or '-',
                'Cidade': supplier.city or '-',
                'Contato': supplier.contact_person or '-',
                'Categoria': supplier.category or '-',
                'Produtos': supplier.get_products_count(),
                'Status': UIHelpers.create_status_badge(supplier.status)
            })
        
        # Pagination
        paginated = DataHelpers.paginate_data(supplier_data, page_size=10)
        
        # Display info
        st.info(f"Mostrando {paginated['showing_from']}-{paginated['showing_to']} de {paginated['total_items']} fornecedores")
        
        # Display table
        for i, supplier in enumerate(paginated['data']):
            with st.expander(f"🏭 {supplier['Nome']} - {supplier['Documento']}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Email:** {supplier['Email']}")
                    st.write(f"**Telefone:** {supplier['Telefone']}")
                    st.write(f"**Cidade:** {supplier['Cidade']}")
                    st.write(f"**Contato:** {supplier['Contato']}")
                    st.write(f"**Categoria:** {supplier['Categoria']}")
                    st.write(f"**Produtos:** {supplier['Produtos']}")
                
                with col2:
                    if st.button("✏️ Editar", key=f"edit_supplier_{supplier['ID']}"):
                        st.session_state.edit_supplier_id = supplier['ID']
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Excluir", key=f"delete_supplier_{supplier['ID']}"):
                        if UIHelpers.create_confirmation_dialog(
                            f"Tem certeza que deseja excluir o fornecedor '{supplier['Nome']}'?",
                            f"delete_supplier_{supplier['ID']}"
                        ):
                            if Supplier.delete(supplier['ID'], AuthService.get_current_username()):
                                UIHelpers.show_success_message("Fornecedor excluído com sucesso!")
                                st.rerun()
                            else:
                                UIHelpers.show_error_message("Erro ao excluir fornecedor.")
        
        # Export button
        st.markdown("---")
        if st.button("📥 Exportar Fornecedores (CSV)", use_container_width=True):
            csv_data = ExportService.export_suppliers_to_csv()
            st.download_button(
                "⬇️ Download CSV",
                csv_data,
                f"fornecedores_{st.session_state.get('export_timestamp', 'export')}.csv",
                "text/csv"
            )
    
    else:
        st.info("Nenhum fornecedor encontrado.")
        if st.button("➕ Cadastrar Primeiro Fornecedor"):
            st.session_state.current_tab = 1
            st.rerun()

def show_supplier_form(supplier_id: Optional[int] = None):
    """Show supplier creation/editing form"""
    # Check if editing existing supplier
    edit_supplier_id = st.session_state.get('edit_supplier_id')
    if edit_supplier_id:
        supplier_id = edit_supplier_id
        st.session_state.edit_supplier_id = None  # Clear after use
    
    if supplier_id:
        st.subheader("✏️ Editar Fornecedor")
        supplier = Supplier.get_by_id(supplier_id)
        if not supplier:
            UIHelpers.show_error_message("Fornecedor não encontrado.")
            return
    else:
        st.subheader("➕ Cadastrar Novo Fornecedor")
        supplier = Supplier()
    
    # Form
    with st.form("supplier_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nome *", value=supplier.name)
            
            document_type = st.selectbox(
                "Tipo de Documento *",
                options=["CNPJ", "CPF", "RG", "Passaporte"],
                index=["CNPJ", "CPF", "RG", "Passaporte"].index(supplier.document_type) if supplier.document_type else 0
            )
            
            document_number = FormHelpers.create_document_input(
                "Número do Documento *",
                document_type,
                supplier.document_number
            )
            
            email = FormHelpers.create_email_input("Email", supplier.email)
            
            phone = FormHelpers.create_phone_input("Telefone", supplier.phone)
            
            contact_person = st.text_input("Pessoa de Contato", value=supplier.contact_person)
            
            category = st.text_input("Categoria", value=supplier.category)
            
            # Category suggestions
            existing_categories = Supplier.get_categories()
            if existing_categories:
                st.selectbox(
                    "Ou selecione uma categoria existente:",
                    options=[''] + existing_categories,
                    key='supplier_category_select'
                )
                
                if st.session_state.get('supplier_category_select'):
                    category = st.session_state.supplier_category_select
        
        with col2:
            address = st.text_area("Endereço", value=supplier.address)
            
            city = st.text_input("Cidade", value=supplier.city)
            
            state = st.selectbox(
                "Estado",
                options=["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
                        "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", 
                        "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"],
                index=0 if not supplier.state else ["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
                        "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", 
                        "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"].index(supplier.state)
            )
            
            zip_code = FormHelpers.create_zip_code_input("CEP", supplier.zip_code)
            
            status = st.selectbox(
                "Status",
                options=["active", "inactive"],
                index=0 if supplier.status == "active" else 1,
                format_func=lambda x: "Ativo" if x == "active" else "Inativo"
            )
        
        # Form buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit = st.form_submit_button("💾 Salvar", use_container_width=True)
        
        with col2:
            cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if cancel:
            if 'edit_supplier_id' in st.session_state:
                del st.session_state.edit_supplier_id
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
                'contact_person': contact_person,
                'status': status
            }
            
            errors = Validators.validate_supplier_data(form_data)
            
            if errors:
                for error in errors:
                    UIHelpers.show_error_message(error)
            else:
                # Update supplier object
                supplier.name = name
                supplier.document_type = document_type
                supplier.document_number = document_number
                supplier.email = email
                supplier.phone = phone
                supplier.address = address
                supplier.city = city
                supplier.state = state
                supplier.zip_code = zip_code
                supplier.category = category
                supplier.contact_person = contact_person
                supplier.status = status
                
                try:
                    # Save supplier
                    supplier.save(AuthService.get_current_username())
                    
                    if supplier_id:
                        UIHelpers.show_success_message("Fornecedor atualizado com sucesso!")
                    else:
                        UIHelpers.show_success_message("Fornecedor cadastrado com sucesso!")
                    
                    # Clear form
                    if 'edit_supplier_id' in st.session_state:
                        del st.session_state.edit_supplier_id
                    
                    st.rerun()
                    
                except Exception as e:
                    UIHelpers.show_error_message(f"Erro ao salvar fornecedor: {str(e)}")

def show_import_suppliers():
    """Show supplier import interface"""
    st.subheader("📤 Importar Fornecedores")
    
    st.info("""
    **Formato do arquivo CSV:**
    - Nome, Tipo Documento, Número Documento, Email, Telefone, Endereço, Cidade, Estado, CEP, Categoria, Pessoa de Contato, Status
    - Campos obrigatórios: Nome, Tipo Documento, Número Documento
    - Tipos de documento aceitos: CNPJ, CPF, RG, Passaporte
    """)
    
    # File uploader
    uploaded_file = DataHelpers.import_csv_uploader("Selecionar arquivo CSV", key="import_suppliers")
    
    if uploaded_file is not None:
        # Show file info
        st.write(f"**Arquivo:** {uploaded_file.name}")
        st.write(f"**Tamanho:** {uploaded_file.size} bytes")
        
        # Import button
        if st.button("📥 Importar Fornecedores", use_container_width=True):
            with st.spinner("Importando fornecedores..."):
                result = ImportService.import_suppliers_from_csv(
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
        sample_data = """Nome,Tipo Documento,Número Documento,Email,Telefone,Endereço,Cidade,Estado,CEP,Categoria,Pessoa de Contato,Status
Fornecedor ABC Ltda,CNPJ,12345678000195,contato@abc.com,(11) 99999-9999,Rua Industrial 100,São Paulo,SP,01234-567,Tecnologia,João Silva,active
Fornecedor XYZ S.A.,CNPJ,98765432000123,vendas@xyz.com,(11) 88888-8888,Av. Comercial 200,Rio de Janeiro,RJ,20000-000,Materiais,Maria Santos,active"""
        
        st.download_button(
            "📥 Download Modelo",
            sample_data.encode('utf-8'),
            "modelo_fornecedores.csv",
            "text/csv"
        )

def show_suppliers_reports():
    """Show supplier reports and analytics"""
    st.subheader("📊 Relatórios de Fornecedores")
    
    suppliers = Supplier.get_all()
    
    if not suppliers:
        st.info("Nenhum fornecedor cadastrado para gerar relatórios.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_suppliers = len(suppliers)
        st.metric("Total de Fornecedores", total_suppliers)
    
    with col2:
        active_suppliers = len([s for s in suppliers if s.status == 'active'])
        st.metric("Fornecedores Ativos", active_suppliers)
    
    with col3:
        with_email = len([s for s in suppliers if s.email])
        st.metric("Com Email", with_email)
    
    with col4:
        with_contact = len([s for s in suppliers if s.contact_person])
        st.metric("Com Contato", with_contact)
    
    # Product count analysis
    suppliers_with_products = []
    total_products = 0
    
    for supplier in suppliers:
        product_count = supplier.get_products_count()
        if product_count > 0:
            suppliers_with_products.append(supplier)
            total_products += product_count
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Fornecedores com Produtos", len(suppliers_with_products))
    
    with col2:
        st.metric("Total de Produtos Fornecidos", total_products)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Status distribution
        status_counts = {}
        for supplier in suppliers:
            status_counts[supplier.status] = status_counts.get(supplier.status, 0) + 1
        
        from utils.helpers import ChartHelpers
        ChartHelpers.create_pie_chart(status_counts, "Distribuição por Status")
    
    with col2:
        # Document type distribution
        doc_type_counts = {}
        for supplier in suppliers:
            doc_type = supplier.document_type or 'Não informado'
            doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1
        
        ChartHelpers.create_pie_chart(doc_type_counts, "Distribuição por Tipo de Documento")
    
    # Category analysis
    if any(s.category for s in suppliers):
        st.subheader("📈 Análise por Categoria")
        
        category_counts = {}
        for supplier in suppliers:
            category = supplier.category or 'Sem categoria'
            category_counts[category] = category_counts.get(category, 0) + 1
        
        ChartHelpers.create_bar_chart(
            category_counts,
            "Fornecedores por Categoria",
            "Categoria",
            "Quantidade"
        )
    
    # Geographic distribution
    if any(s.state for s in suppliers):
        st.subheader("🗺️ Distribuição Geográfica")
        
        state_counts = {}
        for supplier in suppliers:
            state = supplier.state or 'Não informado'
            state_counts[state] = state_counts.get(state, 0) + 1
        
        ChartHelpers.create_bar_chart(
            state_counts,
            "Fornecedores por Estado",
            "Estado",
            "Quantidade"
        )
    
    # Product supply analysis
    if suppliers_with_products:
        st.subheader("📦 Análise de Fornecimento")
        
        # Top suppliers by product count
        supplier_product_counts = {}
        for supplier in suppliers_with_products:
            product_count = supplier.get_products_count()
            supplier_product_counts[supplier.name] = product_count
        
        # Sort by product count and take top 10
        top_suppliers = dict(sorted(supplier_product_counts.items(), 
                                  key=lambda x: x[1], reverse=True)[:10])
        
        ChartHelpers.create_bar_chart(
            top_suppliers,
            "Top 10 Fornecedores por Quantidade de Produtos",
            "Fornecedor",
            "Produtos"
        )
        
        # Product distribution analysis
        product_ranges = {
            "1-5 produtos": 0,
            "6-10 produtos": 0,
            "11-20 produtos": 0,
            "21-50 produtos": 0,
            "Mais de 50 produtos": 0
        }
        
        for supplier in suppliers_with_products:
            count = supplier.get_products_count()
            if count <= 5:
                product_ranges["1-5 produtos"] += 1
            elif count <= 10:
                product_ranges["6-10 produtos"] += 1
            elif count <= 20:
                product_ranges["11-20 produtos"] += 1
            elif count <= 50:
                product_ranges["21-50 produtos"] += 1
            else:
                product_ranges["Mais de 50 produtos"] += 1
        
        ChartHelpers.create_pie_chart(
            product_ranges,
            "Distribuição por Quantidade de Produtos Fornecidos"
        )
