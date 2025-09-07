import streamlit as st
from datetime import datetime, timedelta
from models.client import Client
from models.product import Product
from models.supplier import Supplier
from models.audit import AuditTrail, PotentialDuplicate
from services.duplicate_service import DuplicateDetectionService
from utils.helpers import UIHelpers, ChartHelpers
import plotly.express as px
import pandas as pd

def show_dashboard():
    """Show main dashboard with metrics and charts"""
    st.header("📊 Dashboard - Visão Geral")
    
    # Key metrics row
    show_key_metrics()
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        show_entity_distribution()
        show_recent_activity()
    
    with col2:
        show_duplicate_status()
        show_audit_summary()
    
    st.markdown("---")
    
    # Actions row
    show_quick_actions()

def show_key_metrics():
    """Show key metrics cards"""
    st.subheader("📈 Métricas Principais")
    
    # Get counts
    total_clients = Client.get_count(status='active')
    total_products = Product.get_count(status='active')
    total_suppliers = Supplier.get_count(status='active')
    pending_duplicates = PotentialDuplicate.get_count(status='pending')
    
    # Calculate recent additions (last 7 days)
    recent_clients = len([c for c in Client.get_all() if is_recent(c.created_at)])
    recent_products = len([p for p in Product.get_all() if is_recent(p.created_at)])
    recent_suppliers = len([s for s in Supplier.get_all() if is_recent(s.created_at)])
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        UIHelpers.create_metric_card(
            "👥 Clientes Ativos",
            total_clients,
            f"+{recent_clients} esta semana" if recent_clients > 0 else None,
            "normal"
        )
    
    with col2:
        UIHelpers.create_metric_card(
            "📦 Produtos Ativos",
            total_products,
            f"+{recent_products} esta semana" if recent_products > 0 else None,
            "normal"
        )
    
    with col3:
        UIHelpers.create_metric_card(
            "🏭 Fornecedores Ativos",
            total_suppliers,
            f"+{recent_suppliers} esta semana" if recent_suppliers > 0 else None,
            "normal"
        )
    
    with col4:
        UIHelpers.create_metric_card(
            "🔍 Duplicatas Pendentes",
            pending_duplicates,
            "Requer atenção" if pending_duplicates > 0 else "Tudo limpo",
            "inverse" if pending_duplicates > 0 else "normal"
        )

def show_entity_distribution():
    """Show distribution of entities by category"""
    st.subheader("📊 Distribuição por Categoria")
    
    # Get category data
    client_categories = {}
    for client in Client.get_all(status='active'):
        category = client.category or 'Sem categoria'
        client_categories[category] = client_categories.get(category, 0) + 1
    
    product_categories = {}
    for product in Product.get_all(status='active'):
        category = product.category or 'Sem categoria'
        product_categories[category] = product_categories.get(category, 0) + 1
    
    supplier_categories = {}
    for supplier in Supplier.get_all(status='active'):
        category = supplier.category or 'Sem categoria'
        supplier_categories[category] = supplier_categories.get(category, 0) + 1
    
    # Create tabs for different entity types
    tab1, tab2, tab3 = st.tabs(["Clientes", "Produtos", "Fornecedores"])
    
    with tab1:
        if client_categories:
            ChartHelpers.create_pie_chart(client_categories, "Clientes por Categoria")
        else:
            st.info("Nenhum cliente cadastrado")
    
    with tab2:
        if product_categories:
            ChartHelpers.create_pie_chart(product_categories, "Produtos por Categoria")
        else:
            st.info("Nenhum produto cadastrado")
    
    with tab3:
        if supplier_categories:
            ChartHelpers.create_pie_chart(supplier_categories, "Fornecedores por Categoria")
        else:
            st.info("Nenhum fornecedor cadastrado")

def show_recent_activity():
    """Show recent activity timeline"""
    st.subheader("🕒 Atividade Recente")
    
    # Get recent audit records
    recent_audits = AuditTrail.get_recent_changes(limit=10)
    
    if recent_audits:
        activity_data = []
        
        for audit in recent_audits:
            activity_data.append({
                'Data/Hora': UIHelpers.format_datetime(audit.changed_at),
                'Tabela': audit.table_name.title(),
                'Ação': audit.action.title(),
                'Usuário': audit.changed_by,
                'ID': audit.record_id
            })
        
        df = pd.DataFrame(activity_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma atividade recente")

def show_duplicate_status():
    """Show duplicate detection status"""
    st.subheader("🔍 Status de Duplicatas")
    
    # Get duplicate counts by table
    duplicate_counts = {}
    
    for table_name in ['clients', 'products', 'suppliers']:
        pending_count = len(PotentialDuplicate.get_pending(table_name))
        duplicate_counts[table_name.title()] = pending_count
    
    if any(duplicate_counts.values()):
        ChartHelpers.create_bar_chart(
            duplicate_counts,
            "Duplicatas Pendentes por Tipo",
            "Tipo de Entidade",
            "Quantidade"
        )
    else:
        st.success("✅ Nenhuma duplicata pendente encontrada!")
    
    # Quick duplicate detection button
    if st.button("🔍 Executar Detecção de Duplicatas", use_container_width=True):
        with st.spinner("Detectando duplicatas..."):
            results = DuplicateDetectionService.run_all_duplicate_detection()
            
            total_found = sum(results.values())
            if total_found > 0:
                UIHelpers.show_warning_message(
                    f"Encontradas {total_found} possíveis duplicatas: "
                    f"{results['clients']} clientes, "
                    f"{results['products']} produtos, "
                    f"{results['suppliers']} fornecedores"
                )
            else:
                UIHelpers.show_success_message("Nenhuma duplicata encontrada!")
            
            st.rerun()

def show_audit_summary():
    """Show audit trail summary"""
    st.subheader("📋 Resumo de Auditoria")
    
    # Get audit statistics
    stats = AuditTrail.get_statistics()
    
    if stats.get('total_records', 0) > 0:
        # Show total records
        st.metric("Total de Registros de Auditoria", stats['total_records'])
        
        # Show activity by action
        if stats.get('by_action'):
            action_data = {
                action.title(): count 
                for action, count in stats['by_action'].items()
            }
            ChartHelpers.create_bar_chart(
                action_data,
                "Ações de Auditoria",
                "Tipo de Ação",
                "Quantidade"
            )
        
        # Show recent activity count
        recent_activity = stats.get('recent_activity', 0)
        st.metric(
            "Atividade (Últimos 7 dias)",
            recent_activity,
            delta=f"{recent_activity} alterações"
        )
    else:
        st.info("Nenhum registro de auditoria disponível")

def show_quick_actions():
    """Show quick action buttons"""
    st.subheader("⚡ Ações Rápidas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Novo Cliente", use_container_width=True):
            st.session_state.current_page = 'clients'
            st.session_state.client_action = 'create'
            st.rerun()
    
    with col2:
        if st.button("➕ Novo Produto", use_container_width=True):
            st.session_state.current_page = 'products'
            st.session_state.product_action = 'create'
            st.rerun()
    
    with col3:
        if st.button("➕ Novo Fornecedor", use_container_width=True):
            st.session_state.current_page = 'suppliers'
            st.session_state.supplier_action = 'create'
            st.rerun()
    
    with col4:
        if st.button("🔍 Ver Duplicatas", use_container_width=True):
            st.session_state.current_page = 'duplicates'
            st.rerun()
    
    # Export actions
    st.markdown("### 📥 Exportar Dados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Exportar Clientes", use_container_width=True):
            from services.export_service import ExportService
            csv_data = ExportService.export_clients_to_csv()
            st.download_button(
                "⬇️ Download CSV Clientes",
                csv_data,
                f"clientes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col2:
        if st.button("📥 Exportar Produtos", use_container_width=True):
            from services.export_service import ExportService
            csv_data = ExportService.export_products_to_csv()
            st.download_button(
                "⬇️ Download CSV Produtos",
                csv_data,
                f"produtos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col3:
        if st.button("📥 Exportar Fornecedores", use_container_width=True):
            from services.export_service import ExportService
            csv_data = ExportService.export_suppliers_to_csv()
            st.download_button(
                "⬇️ Download CSV Fornecedores",
                csv_data,
                f"fornecedores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )

def is_recent(date_string: str, days: int = 7) -> bool:
    """Check if a date is within the last N days"""
    if not date_string:
        return False
    
    try:
        date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        cutoff = datetime.now() - timedelta(days=days)
        return date >= cutoff
    except:
        return False

def show_system_health():
    """Show system health indicators"""
    st.subheader("🏥 Saúde do Sistema")
    
    # Database connectivity
    try:
        from config.database import db_manager
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            db_status = "✅ Conectado"
    except:
        db_status = "❌ Erro de conexão"
    
    # Data integrity checks
    total_records = (
        Client.get_count() + 
        Product.get_count() + 
        Supplier.get_count()
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status do Banco", db_status)
    
    with col2:
        st.metric("Total de Registros", total_records)
    
    with col3:
        audit_count = AuditTrail.get_statistics().get('total_records', 0)
        st.metric("Registros de Auditoria", audit_count)
