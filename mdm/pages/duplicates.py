import streamlit as st
from models.audit import PotentialDuplicate
from services.auth_service import AuthService
from services.duplicate_service import DuplicateDetectionService
from utils.helpers import UIHelpers

def show_duplicates_page():
    """Show duplicates management page"""
    st.header("🔍 Gerenciamento de Duplicatas")
    
    # Check authentication
    AuthService.require_auth()
    
    # Action tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Detectar", "📋 Revisar", "📊 Relatórios"])
    
    with tab1:
        show_duplicate_detection()
    
    with tab2:
        show_duplicate_review()
    
    with tab3:
        show_duplicate_reports()

def show_duplicate_detection():
    """Show duplicate detection interface"""
    st.subheader("🔍 Detecção de Duplicatas")
    
    st.info("""
    A detecção de duplicatas analisa registros similares baseado em:
    - **Clientes**: Nome, CPF/CNPJ, email, telefone
    - **Produtos**: Código, nome, descrição
    - **Fornecedores**: Nome, CPF/CNPJ, email, pessoa de contato
    """)
    
    # Detection settings
    col1, col2 = st.columns(2)
    
    with col1:
        threshold = st.slider(
            "Limite de Similaridade (%)",
            min_value=50,
            max_value=95,
            value=80,
            step=5,
            help="Quanto maior o valor, mais restritiva será a detecção"
        )
    
    with col2:
        entity_types = st.multiselect(
            "Tipos de Entidade",
            options=["Clientes", "Produtos", "Fornecedores"],
            default=["Clientes", "Produtos", "Fornecedores"]
        )
    
    # Detection buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Detectar Todas", use_container_width=True):
            run_full_detection(threshold / 100)
    
    with col2:
        if "Clientes" in entity_types and st.button("👥 Detectar Clientes", use_container_width=True):
            run_client_detection(threshold / 100)
    
    with col3:
        if "Produtos" in entity_types and st.button("📦 Detectar Produtos", use_container_width=True):
            run_product_detection(threshold / 100)
    
    with col4:
        if "Fornecedores" in entity_types and st.button("🏭 Detectar Fornecedores", use_container_width=True):
            run_supplier_detection(threshold / 100)
    
    # Show current pending duplicates summary
    st.markdown("---")
    show_pending_summary()

def run_full_detection(threshold: float):
    """Run full duplicate detection"""
    with st.spinner("Executando detecção completa de duplicatas..."):
        results = DuplicateDetectionService.run_all_duplicate_detection(threshold)
        
        total_found = sum(results.values())
        
        if total_found > 0:
            UIHelpers.show_warning_message(
                f"🔍 Detecção concluída! Encontradas {total_found} possíveis duplicatas:"
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👥 Clientes", results['clients'])
            with col2:
                st.metric("📦 Produtos", results['products'])
            with col3:
                st.metric("🏭 Fornecedores", results['suppliers'])
        else:
            UIHelpers.show_success_message("✅ Nenhuma duplicata encontrada!")
        
        st.rerun()

def run_client_detection(threshold: float):
    """Run client duplicate detection"""
    with st.spinner("Detectando duplicatas de clientes..."):
        duplicates = DuplicateDetectionService.detect_client_duplicates(threshold)
        
        if duplicates:
            UIHelpers.show_warning_message(f"Encontradas {len(duplicates)} possíveis duplicatas de clientes")
        else:
            UIHelpers.show_success_message("Nenhuma duplicata de cliente encontrada!")
        
        st.rerun()

def run_product_detection(threshold: float):
    """Run product duplicate detection"""
    with st.spinner("Detectando duplicatas de produtos..."):
        duplicates = DuplicateDetectionService.detect_product_duplicates(threshold)
        
        if duplicates:
            UIHelpers.show_warning_message(f"Encontradas {len(duplicates)} possíveis duplicatas de produtos")
        else:
            UIHelpers.show_success_message("Nenhuma duplicata de produto encontrada!")
        
        st.rerun()

def run_supplier_detection(threshold: float):
    """Run supplier duplicate detection"""
    with st.spinner("Detectando duplicatas de fornecedores..."):
        duplicates = DuplicateDetectionService.detect_supplier_duplicates(threshold)
        
        if duplicates:
            UIHelpers.show_warning_message(f"Encontradas {len(duplicates)} possíveis duplicatas de fornecedores")
        else:
            UIHelpers.show_success_message("Nenhuma duplicata de fornecedor encontrada!")
        
        st.rerun()

def show_pending_summary():
    """Show summary of pending duplicates"""
    st.subheader("📊 Resumo de Duplicatas Pendentes")
    
    # Get counts
    client_duplicates = len(PotentialDuplicate.get_pending('clients'))
    product_duplicates = len(PotentialDuplicate.get_pending('products'))
    supplier_duplicates = len(PotentialDuplicate.get_pending('suppliers'))
    total_pending = client_duplicates + product_duplicates + supplier_duplicates
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Pendentes", total_pending)
    
    with col2:
        st.metric("👥 Clientes", client_duplicates)
    
    with col3:
        st.metric("📦 Produtos", product_duplicates)
    
    with col4:
        st.metric("🏭 Fornecedores", supplier_duplicates)
    
    if total_pending > 0:
        st.info(f"💡 Você tem {total_pending} duplicatas pendentes para revisar na aba 'Revisar'")

def show_duplicate_review():
    """Show duplicate review interface"""
    st.subheader("📋 Revisar Duplicatas")
    
    # Filter by entity type
    entity_filter = st.selectbox(
        "Filtrar por tipo:",
        options=["Todos", "Clientes", "Produtos", "Fornecedores"],
        index=0
    )
    
    # Get pending duplicates
    if entity_filter == "Todos":
        pending_duplicates = PotentialDuplicate.get_pending()
    else:
        table_name = {
            "Clientes": "clients",
            "Produtos": "products", 
            "Fornecedores": "suppliers"
        }.get(entity_filter)
        pending_duplicates = PotentialDuplicate.get_pending(table_name)
    
    if not pending_duplicates:
        st.success("🎉 Não há duplicatas pendentes para revisar!")
        return
    
    st.info(f"📝 {len(pending_duplicates)} duplicatas pendentes para revisar")
    
    # Review each duplicate
    for i, duplicate in enumerate(pending_duplicates):
        with st.expander(f"🔍 Duplicata {i+1} - {duplicate.table_name.title()} (Similaridade: {duplicate.similarity_score:.1%})"):
            show_duplicate_comparison(duplicate)

def show_duplicate_comparison(duplicate: PotentialDuplicate):
    """Show comparison between two potential duplicate records"""
    # Get the actual records
    record1, record2 = DuplicateDetectionService.get_duplicate_details(duplicate)
    
    if not record1 or not record2:
        st.error("Erro ao carregar registros para comparação")
        return
    
    # Display comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📄 Registro 1")
        display_record_details(record1, duplicate.table_name)
    
    with col2:
        st.markdown("### 📄 Registro 2")
        display_record_details(record2, duplicate.table_name)
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(f"✅ Manter Registro 1", key=f"keep1_{duplicate.id}"):
            if DuplicateDetectionService.merge_records(duplicate, record1.id, AuthService.get_current_username()):
                UIHelpers.show_success_message("Registros mesclados! Registro 1 mantido, Registro 2 excluído.")
                st.rerun()
            else:
                UIHelpers.show_error_message("Erro ao mesclar registros.")
    
    with col2:
        if st.button(f"✅ Manter Registro 2", key=f"keep2_{duplicate.id}"):
            if DuplicateDetectionService.merge_records(duplicate, record2.id, AuthService.get_current_username()):
                UIHelpers.show_success_message("Registros mesclados! Registro 2 mantido, Registro 1 excluído.")
                st.rerun()
            else:
                UIHelpers.show_error_message("Erro ao mesclar registros.")
    
    with col3:
        if st.button(f"❌ Não são duplicatas", key=f"not_dup_{duplicate.id}"):
            if DuplicateDetectionService.mark_as_not_duplicate(duplicate, AuthService.get_current_username()):
                UIHelpers.show_success_message("Marcado como não duplicata.")
                st.rerun()
            else:
                UIHelpers.show_error_message("Erro ao marcar como não duplicata.")

def display_record_details(record, table_name: str):
    """Display record details based on table type"""
    if table_name == 'clients':
        st.write(f"**ID:** {record.id}")
        st.write(f"**Nome:** {record.name}")
        st.write(f"**Documento:** {record.document_type} - {record.document_number}")
        st.write(f"**Email:** {record.email or 'Não informado'}")
        st.write(f"**Telefone:** {record.phone or 'Não informado'}")
        st.write(f"**Cidade:** {record.city or 'Não informado'}")
        st.write(f"**Categoria:** {record.category or 'Não informado'}")
        st.write(f"**Status:** {record.status}")
    
    elif table_name == 'products':
        st.write(f"**ID:** {record.id}")
        st.write(f"**Código:** {record.code}")
        st.write(f"**Nome:** {record.name}")
        st.write(f"**Descrição:** {record.description or 'Não informado'}")
        st.write(f"**Categoria:** {record.category or 'Não informado'}")
        st.write(f"**Preço:** {UIHelpers.format_currency(record.unit_price) if record.unit_price else 'Não informado'}")
        st.write(f"**Unidade:** {record.unit_of_measure or 'Não informado'}")
        st.write(f"**Fornecedor:** {record.get_supplier_name() or 'Não informado'}")
        st.write(f"**Status:** {record.status}")
    
    elif table_name == 'suppliers':
        st.write(f"**ID:** {record.id}")
        st.write(f"**Nome:** {record.name}")
        st.write(f"**Documento:** {record.document_type} - {record.document_number}")
        st.write(f"**Email:** {record.email or 'Não informado'}")
        st.write(f"**Telefone:** {record.phone or 'Não informado'}")
        st.write(f"**Cidade:** {record.city or 'Não informado'}")
        st.write(f"**Contato:** {record.contact_person or 'Não informado'}")
        st.write(f"**Categoria:** {record.category or 'Não informado'}")
        st.write(f"**Status:** {record.status}")

def show_duplicate_reports():
    """Show duplicate detection reports and statistics"""
    st.subheader("📊 Relatórios de Duplicatas")
    
    # Get all duplicates (pending and resolved)
    all_duplicates = []
    for table_name in ['clients', 'products', 'suppliers']:
        with st.spinner(f"Carregando duplicatas de {table_name}..."):
            from config.database import db_manager
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM potential_duplicates 
                    WHERE table_name = ? 
                    ORDER BY created_at DESC
                ''', (table_name,))
                
                rows = cursor.fetchall()
                for row in rows:
                    all_duplicates.append(PotentialDuplicate.from_dict(dict(row)))
    
    if not all_duplicates:
        st.info("Nenhuma duplicata foi detectada ainda.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_duplicates = len(all_duplicates)
    pending_count = len([d for d in all_duplicates if d.status == 'pending'])
    merged_count = len([d for d in all_duplicates if d.status == 'merged'])
    not_duplicate_count = len([d for d in all_duplicates if d.status == 'not_duplicate'])
    
    with col1:
        st.metric("Total Detectadas", total_duplicates)
    
    with col2:
        st.metric("Pendentes", pending_count)
    
    with col3:
        st.metric("Mescladas", merged_count)
    
    with col4:
        st.metric("Não Duplicatas", not_duplicate_count)
    
    # Status distribution chart
    if all_duplicates:
        status_counts = {}
        for duplicate in all_duplicates:
            status_counts[duplicate.status] = status_counts.get(duplicate.status, 0) + 1
        
        from utils.helpers import ChartHelpers
        ChartHelpers.create_pie_chart(status_counts, "Distribuição por Status")
    
    # Table distribution
    col1, col2 = st.columns(2)
    
    with col1:
        table_counts = {}
        for duplicate in all_duplicates:
            table_name = duplicate.table_name.title()
            table_counts[table_name] = table_counts.get(table_name, 0) + 1
        
        ChartHelpers.create_pie_chart(table_counts, "Distribuição por Tipo de Entidade")
    
    with col2:
        # Similarity score distribution
        similarity_ranges = {
            "50-60%": 0,
            "60-70%": 0,
            "70-80%": 0,
            "80-90%": 0,
            "90-100%": 0
        }
        
        for duplicate in all_duplicates:
            score = duplicate.similarity_score * 100
            if score < 60:
                similarity_ranges["50-60%"] += 1
            elif score < 70:
                similarity_ranges["60-70%"] += 1
            elif score < 80:
                similarity_ranges["70-80%"] += 1
            elif score < 90:
                similarity_ranges["80-90%"] += 1
            else:
                similarity_ranges["90-100%"] += 1
        
        ChartHelpers.create_bar_chart(
            similarity_ranges,
            "Distribuição por Similaridade",
            "Faixa de Similaridade",
            "Quantidade"
        )
    
    # Recent activity
    st.subheader("🕒 Atividade Recente")
    
    recent_duplicates = sorted(all_duplicates, key=lambda x: x.created_at or '', reverse=True)[:10]
    
    if recent_duplicates:
        for duplicate in recent_duplicates:
            status_icon = {
                'pending': '⏳',
                'merged': '✅',
                'not_duplicate': '❌'
            }.get(duplicate.status, '❓')
            
            st.write(f"{status_icon} **{duplicate.table_name.title()}** - "
                    f"Similaridade: {duplicate.similarity_score:.1%} - "
                    f"Status: {duplicate.status.title()} - "
                    f"Criado: {UIHelpers.format_datetime(duplicate.created_at)}")
    
    # Cleanup old resolved duplicates
    st.markdown("---")
    st.subheader("🧹 Limpeza de Dados")
    
    resolved_count = len([d for d in all_duplicates if d.status in ['merged', 'not_duplicate']])
    
    if resolved_count > 0:
        st.info(f"Existem {resolved_count} duplicatas já resolvidas no sistema.")
        
        if st.button("🗑️ Limpar Duplicatas Resolvidas", use_container_width=True):
            if UIHelpers.create_confirmation_dialog(
                f"Tem certeza que deseja remover {resolved_count} registros de duplicatas já resolvidas?",
                "cleanup_duplicates"
            ):
                # Remove resolved duplicates
                from config.database import db_manager
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        DELETE FROM potential_duplicates 
                        WHERE status IN ('merged', 'not_duplicate')
                    ''')
                    deleted_count = cursor.rowcount
                    conn.commit()
                
                UIHelpers.show_success_message(f"Removidos {deleted_count} registros de duplicatas resolvidas.")
                st.rerun()
