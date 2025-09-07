import streamlit as st
from typing import Optional
from models.product import Product
from models.supplier import Supplier
from services.auth_service import AuthService
from services.export_service import ExportService, ImportService
from utils.validators import Validators
from utils.helpers import UIHelpers, FormHelpers, DataHelpers

def show_products_page():
    """Show products management page"""
    st.header("📦 Gerenciamento de Produtos")
    
    # Check authentication
    AuthService.require_auth()
    
    # Action tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Listar", "➕ Cadastrar", "📥 Importar", "📊 Relatórios"])
    
    with tab1:
        show_products_list()
    
    with tab2:
        show_product_form()
    
    with tab3:
        show_import_products()
    
    with tab4:
        show_products_reports()

def show_products_list():
    """Show list of products with search and filters"""
    st.subheader("📋 Lista de Produtos")
    
    # Search and filters
    filters = UIHelpers.create_search_filters('products')
    
    # Get products based on filters
    if filters.get('query') or any(v for k, v in filters.items() if k != 'query'):
        products = Product.search(
            query=filters.get('query', ''),
            filters={k: v for k, v in filters.items() if k != 'query' and v}
        )
    else:
        products = Product.get_all(status='active')
    
    if products:
        # Convert to display format
        product_data = []
        for product in products:
            supplier_name = product.get_supplier_name() or '-'
            
            product_data.append({
                'ID': product.id,
                'Código': product.code,
                'Nome': product.name,
                'Categoria': product.category or '-',
                'Preço': UIHelpers.format_currency(product.unit_price) if product.unit_price else '-',
                'Unidade': product.unit_of_measure or '-',
                'Fornecedor': supplier_name,
                'Status': UIHelpers.create_status_badge(product.status)
            })
        
        # Pagination
        paginated = DataHelpers.paginate_data(product_data, page_size=10)
        
        # Display info
        st.info(f"Mostrando {paginated['showing_from']}-{paginated['showing_to']} de {paginated['total_items']} produtos")
        
        # Display table
        for i, product in enumerate(paginated['data']):
            with st.expander(f"📦 {product['Código']} - {product['Nome']}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Categoria:** {product['Categoria']}")
                    st.write(f"**Preço:** {product['Preço']}")
                    st.write(f"**Unidade:** {product['Unidade']}")
                    st.write(f"**Fornecedor:** {product['Fornecedor']}")
                
                with col2:
                    if st.button("✏️ Editar", key=f"edit_product_{product['ID']}"):
                        st.session_state.edit_product_id = product['ID']
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Excluir", key=f"delete_product_{product['ID']}"):
                        if UIHelpers.create_confirmation_dialog(
                            f"Tem certeza que deseja excluir o produto '{product['Nome']}'?",
                            f"delete_product_{product['ID']}"
                        ):
                            if Product.delete(product['ID'], AuthService.get_current_username()):
                                UIHelpers.show_success_message("Produto excluído com sucesso!")
                                st.rerun()
                            else:
                                UIHelpers.show_error_message("Erro ao excluir produto.")
        
        # Export button
        st.markdown("---")
        if st.button("📥 Exportar Produtos (CSV)", use_container_width=True):
            csv_data = ExportService.export_products_to_csv()
            st.download_button(
                "⬇️ Download CSV",
                csv_data,
                f"produtos_{st.session_state.get('export_timestamp', 'export')}.csv",
                "text/csv"
            )
    
    else:
        st.info("Nenhum produto encontrado.")
        if st.button("➕ Cadastrar Primeiro Produto"):
            st.session_state.current_tab = 1
            st.rerun()

def show_product_form(product_id: Optional[int] = None):
    """Show product creation/editing form"""
    # Check if editing existing product
    edit_product_id = st.session_state.get('edit_product_id')
    if edit_product_id:
        product_id = edit_product_id
        st.session_state.edit_product_id = None  # Clear after use
    
    if product_id:
        st.subheader("✏️ Editar Produto")
        product = Product.get_by_id(product_id)
        if not product:
            UIHelpers.show_error_message("Produto não encontrado.")
            return
    else:
        st.subheader("➕ Cadastrar Novo Produto")
        product = Product()
    
    # Get suppliers for dropdown
    suppliers = Supplier.get_for_dropdown()
    supplier_options = [{'id': None, 'name': 'Nenhum'}] + suppliers
    
    # Form
    with st.form("product_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            code = st.text_input("Código *", value=product.code)
            
            name = st.text_input("Nome *", value=product.name)
            
            description = st.text_area("Descrição", value=product.description)
            
            category = st.text_input("Categoria", value=product.category)
            
            # Category suggestions
            existing_categories = Product.get_categories()
            if existing_categories:
                st.selectbox(
                    "Ou selecione uma categoria existente:",
                    options=[''] + existing_categories,
                    key='category_select'
                )
                
                if st.session_state.get('category_select'):
                    category = st.session_state.category_select
        
        with col2:
            unit_price = FormHelpers.create_currency_input(
                "Preço Unitário",
                product.unit_price
            )
            
            unit_of_measure = st.text_input(
                "Unidade de Medida",
                value=product.unit_of_measure,
                placeholder="ex: kg, un, m, l"
            )
            
            # Unit of measure suggestions
            existing_units = Product.get_units_of_measure()
            if existing_units:
                st.selectbox(
                    "Ou selecione uma unidade existente:",
                    options=[''] + existing_units,
                    key='unit_select'
                )
                
                if st.session_state.get('unit_select'):
                    unit_of_measure = st.session_state.unit_select
            
            # Supplier selection
            supplier_names = [s['name'] for s in supplier_options]
            current_supplier_index = 0
            
            if product.supplier_id:
                for i, supplier in enumerate(supplier_options):
                    if supplier['id'] == product.supplier_id:
                        current_supplier_index = i
                        break
            
            selected_supplier_name = st.selectbox(
                "Fornecedor",
                options=supplier_names,
                index=current_supplier_index
            )
            
            # Get supplier ID
            supplier_id = None
            for supplier in supplier_options:
                if supplier['name'] == selected_supplier_name:
                    supplier_id = supplier['id']
                    break
            
            status = st.selectbox(
                "Status",
                options=["active", "inactive"],
                index=0 if product.status == "active" else 1,
                format_func=lambda x: "Ativo" if x == "active" else "Inativo"
            )
        
        # Form buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit = st.form_submit_button("💾 Salvar", use_container_width=True)
        
        with col2:
            cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if cancel:
            if 'edit_product_id' in st.session_state:
                del st.session_state.edit_product_id
            st.rerun()
        
        if submit:
            # Validate form data
            form_data = {
                'code': code,
                'name': name,
                'unit_price': unit_price
            }
            
            errors = Validators.validate_product_data(form_data)
            
            # Check for duplicate code
            existing_product = Product.get_by_code(code)
            if existing_product and existing_product.id != product.id:
                errors.append("Já existe um produto com este código")
            
            if errors:
                for error in errors:
                    UIHelpers.show_error_message(error)
            else:
                # Update product object
                product.code = code
                product.name = name
                product.description = description
                product.category = category
                product.unit_price = unit_price if unit_price > 0 else None
                product.unit_of_measure = unit_of_measure
                product.supplier_id = supplier_id
                product.status = status
                
                try:
                    # Save product
                    product.save(AuthService.get_current_username())
                    
                    if product_id:
                        UIHelpers.show_success_message("Produto atualizado com sucesso!")
                    else:
                        UIHelpers.show_success_message("Produto cadastrado com sucesso!")
                    
                    # Clear form
                    if 'edit_product_id' in st.session_state:
                        del st.session_state.edit_product_id
                    
                    st.rerun()
                    
                except Exception as e:
                    UIHelpers.show_error_message(f"Erro ao salvar produto: {str(e)}")

def show_import_products():
    """Show product import interface"""
    st.subheader("📤 Importar Produtos")
    
    st.info("""
    **Formato do arquivo CSV:**
    - Código, Nome, Descrição, Categoria, Preço Unitário, Unidade de Medida, Fornecedor, Status
    - Campos obrigatórios: Código, Nome
    - O fornecedor deve existir no sistema (usar nome exato)
    """)
    
    # File uploader
    uploaded_file = DataHelpers.import_csv_uploader("Selecionar arquivo CSV", key="import_products")
    
    if uploaded_file is not None:
        # Show file info
        st.write(f"**Arquivo:** {uploaded_file.name}")
        st.write(f"**Tamanho:** {uploaded_file.size} bytes")
        
        # Import button
        if st.button("📥 Importar Produtos", use_container_width=True):
            with st.spinner("Importando produtos..."):
                result = ImportService.import_products_from_csv(
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
        sample_data = """Código,Nome,Descrição,Categoria,Preço Unitário,Unidade de Medida,Fornecedor,Status
PROD001,Produto Exemplo 1,Descrição do produto 1,Eletrônicos,99.90,un,Fornecedor ABC,active
PROD002,Produto Exemplo 2,Descrição do produto 2,Informática,199.50,un,Fornecedor XYZ,active"""
        
        st.download_button(
            "📥 Download Modelo",
            sample_data.encode('utf-8'),
            "modelo_produtos.csv",
            "text/csv"
        )

def show_products_reports():
    """Show product reports and analytics"""
    st.subheader("📊 Relatórios de Produtos")
    
    products = Product.get_all()
    
    if not products:
        st.info("Nenhum produto cadastrado para gerar relatórios.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_products = len(products)
        st.metric("Total de Produtos", total_products)
    
    with col2:
        active_products = len([p for p in products if p.status == 'active'])
        st.metric("Produtos Ativos", active_products)
    
    with col3:
        with_price = len([p for p in products if p.unit_price])
        st.metric("Com Preço", with_price)
    
    with col4:
        with_supplier = len([p for p in products if p.supplier_id])
        st.metric("Com Fornecedor", with_supplier)
    
    # Price analysis
    products_with_price = [p for p in products if p.unit_price]
    if products_with_price:
        col1, col2 = st.columns(2)
        
        with col1:
            avg_price = sum(p.unit_price for p in products_with_price) / len(products_with_price)
            st.metric("Preço Médio", UIHelpers.format_currency(avg_price))
        
        with col2:
            max_price = max(p.unit_price for p in products_with_price)
            st.metric("Maior Preço", UIHelpers.format_currency(max_price))
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Status distribution
        status_counts = {}
        for product in products:
            status_counts[product.status] = status_counts.get(product.status, 0) + 1
        
        from utils.helpers import ChartHelpers
        ChartHelpers.create_pie_chart(status_counts, "Distribuição por Status")
    
    with col2:
        # Category distribution
        category_counts = {}
        for product in products:
            category = product.category or 'Sem categoria'
            category_counts[category] = category_counts.get(category, 0) + 1
        
        ChartHelpers.create_pie_chart(category_counts, "Distribuição por Categoria")
    
    # Unit of measure analysis
    if any(p.unit_of_measure for p in products):
        st.subheader("📏 Análise por Unidade de Medida")
        
        unit_counts = {}
        for product in products:
            unit = product.unit_of_measure or 'Não informado'
            unit_counts[unit] = unit_counts.get(unit, 0) + 1
        
        ChartHelpers.create_bar_chart(
            unit_counts,
            "Produtos por Unidade de Medida",
            "Unidade",
            "Quantidade"
        )
    
    # Supplier analysis
    if any(p.supplier_id for p in products):
        st.subheader("🏭 Análise por Fornecedor")
        
        supplier_counts = {}
        for product in products:
            supplier_name = product.get_supplier_name() or 'Sem fornecedor'
            supplier_counts[supplier_name] = supplier_counts.get(supplier_name, 0) + 1
        
        ChartHelpers.create_bar_chart(
            supplier_counts,
            "Produtos por Fornecedor",
            "Fornecedor",
            "Quantidade"
        )
    
    # Price range analysis
    if products_with_price:
        st.subheader("💰 Análise de Preços")
        
        # Price ranges
        price_ranges = {
            "Até R$ 50": 0,
            "R$ 50 - R$ 100": 0,
            "R$ 100 - R$ 500": 0,
            "R$ 500 - R$ 1000": 0,
            "Acima de R$ 1000": 0
        }
        
        for product in products_with_price:
            price = product.unit_price
            if price <= 50:
                price_ranges["Até R$ 50"] += 1
            elif price <= 100:
                price_ranges["R$ 50 - R$ 100"] += 1
            elif price <= 500:
                price_ranges["R$ 100 - R$ 500"] += 1
            elif price <= 1000:
                price_ranges["R$ 500 - R$ 1000"] += 1
            else:
                price_ranges["Acima de R$ 1000"] += 1
        
        ChartHelpers.create_bar_chart(
            price_ranges,
            "Distribuição por Faixa de Preço",
            "Faixa de Preço",
            "Quantidade"
        )
