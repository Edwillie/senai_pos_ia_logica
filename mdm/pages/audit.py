import streamlit as st
from models.audit import AuditTrail
from services.auth_service import AuthService
from services.export_service import ExportService
from utils.helpers import UIHelpers, DataHelpers
import json
from datetime import datetime, timedelta

def show_audit_page():
    """Show audit trail page"""
    st.header("📋 Trilha de Auditoria")
    
    # Check authentication and admin privileges
    AuthService.require_admin()
    
    # Action tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Registros", "👤 Por Usuário", "📊 Estatísticas", "🧹 Manutenção"])
    
    with tab1:
        show_audit_records()
    
    with tab2:
        show_user_activity()
    
    with tab3:
        show_audit_statistics()
    
    with tab4:
        show_audit_maintenance()

def show_audit_records():
    """Show audit trail records with filters"""
    st.subheader("📋 Registros de Auditoria")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        table_filter = st.selectbox(
            "Tabela:",
            options=["", "clients", "products", "suppliers", "users"],
            format_func=lambda x: {
                "": "Todas",
                "clients": "Clientes",
                "products": "Produtos", 
                "suppliers": "Fornecedores",
                "users": "Usuários"
            }.get(x, x)
        )
    
    with col2:
        action_filter = st.selectbox(
            "Ação:",
            options=["", "INSERT", "UPDATE", "DELETE"],
            format_func=lambda x: {
                "": "Todas",
                "INSERT": "Inserção",
                "UPDATE": "Atualização",
                "DELETE": "Exclusão"
            }.get(x, x)
        )
    
    with col3:
        user_filter = st.text_input("Usuário:")
    
    with col4:
        days_filter = st.selectbox(
            "Período:",
            options=[7, 30, 90, 365, 0],
            format_func=lambda x: {
                7: "Últimos 7 dias",
                30: "Últimos 30 dias",
                90: "Últimos 90 dias",
                365: "Último ano",
                0: "Todos"
            }.get(x)
        )
    
    # Get filtered records
    records = get_filtered_audit_records(table_filter, action_filter, user_filter, days_filter)
    
    if records:
        # Pagination
        paginated = DataHelpers.paginate_data(records, page_size=20)
        
        st.info(f"Mostrando {paginated['showing_from']}-{paginated['showing_to']} de {paginated['total_items']} registros")
        
        # Display records
        for record in paginated['data']:
            with st.expander(f"📝 {record.table_name.title()} - {record.action} - {UIHelpers.format_datetime(record.changed_at)}"):
                show_audit_record_details(record)
        
        # Export button
        st.markdown("---")
        if st.button("📥 Exportar Auditoria (CSV)", use_container_width=True):
            csv_data = ExportService.export_audit_trail_to_csv(limit=len(records))
            st.download_button(
                "⬇️ Download CSV",
                csv_data,
                f"auditoria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    else:
        st.info("Nenhum registro de auditoria encontrado com os filtros aplicados.")

def show_audit_record_details(record: AuditTrail):
    """Show detailed information about an audit record"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**ID do Registro:** {record.record_id}")
        st.write(f"**Tabela:** {record.table_name.title()}")
        st.write(f"**Ação:** {record.action}")
        st.write(f"**Usuário:** {record.changed_by}")
        st.write(f"**Data/Hora:** {UIHelpers.format_datetime(record.changed_at)}")
    
    with col2:
        # Show changes if available
        if record.action == 'UPDATE':
            changes = record.get_changes()
            if changes:
                st.write("**Alterações:**")
                for field, change in changes.items():
                    if change['type'] == 'modified':
                        st.write(f"- **{field}:** `{change['old']}` → `{change['new']}`")
                    elif change['type'] == 'added':
                        st.write(f"- **{field}:** Adicionado `{change['new']}`")
                    elif change['type'] == 'removed':
                        st.write(f"- **{field}:** Removido `{change['old']}`")
        
        elif record.action == 'INSERT':
            new_values = record.get_new_values_dict()
            if new_values:
                st.write("**Valores Inseridos:**")
                for field, value in new_values.items():
                    if field not in ['id', 'created_at', 'updated_at']:
                        st.write(f"- **{field}:** `{value}`")
        
        elif record.action == 'DELETE':
            old_values = record.get_old_values_dict()
            if old_values:
                st.write("**Valores Removidos:**")
                for field, value in old_values.items():
                    if field not in ['id', 'created_at', 'updated_at']:
                        st.write(f"- **{field}:** `{value}`")

def show_user_activity():
    """Show activity by user"""
    st.subheader("👤 Atividade por Usuário")
    
    # Get all users who have audit records
    stats = AuditTrail.get_statistics()
    user_activity = stats.get('by_user', {})
    
    if not user_activity:
        st.info("Nenhuma atividade de usuário encontrada.")
        return
    
    # User selection
    selected_user = st.selectbox(
        "Selecionar usuário:",
        options=list(user_activity.keys()),
        format_func=lambda x: f"{x} ({user_activity[x]} ações)"
    )
    
    if selected_user:
        # Get user's activity
        user_records = AuditTrail.get_user_activity(selected_user, limit=100)
        
        if user_records:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Ações", len(user_records))
            
            with col2:
                recent_count = len([r for r in user_records if is_recent(r.changed_at, days=7)])
                st.metric("Últimos 7 dias", recent_count)
            
            with col3:
                tables = set(r.table_name for r in user_records)
                st.metric("Tabelas Afetadas", len(tables))
            
            # Activity breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                # Actions by type
                action_counts = {}
                for record in user_records:
                    action_counts[record.action] = action_counts.get(record.action, 0) + 1
                
                from utils.helpers import ChartHelpers
                ChartHelpers.create_pie_chart(action_counts, f"Ações de {selected_user}")
            
            with col2:
                # Actions by table
                table_counts = {}
                for record in user_records:
                    table_name = record.table_name.title()
                    table_counts[table_name] = table_counts.get(table_name, 0) + 1
                
                ChartHelpers.create_pie_chart(table_counts, f"Tabelas Modificadas por {selected_user}")
            
            # Recent activity timeline
            st.subheader("🕒 Atividade Recente")
            
            recent_records = user_records[:20]  # Last 20 records
            
            for record in recent_records:
                action_icon = {
                    'INSERT': '➕',
                    'UPDATE': '✏️',
                    'DELETE': '🗑️'
                }.get(record.action, '📝')
                
                st.write(f"{action_icon} **{record.table_name.title()}** (ID: {record.record_id}) - "
                        f"{record.action} - {UIHelpers.format_datetime(record.changed_at)}")

def show_audit_statistics():
    """Show audit trail statistics and analytics"""
    st.subheader("📊 Estatísticas de Auditoria")
    
    # Get statistics
    stats = AuditTrail.get_statistics()
    
    if stats.get('total_records', 0) == 0:
        st.info("Nenhum registro de auditoria disponível.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Registros", stats['total_records'])
    
    with col2:
        st.metric("Atividade Recente", stats['recent_activity'])
    
    with col3:
        tables_count = len(stats.get('by_table', {}))
        st.metric("Tabelas Monitoradas", tables_count)
    
    with col4:
        users_count = len(stats.get('by_user', {}))
        st.metric("Usuários Ativos", users_count)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Records by table
        if stats.get('by_table'):
            table_data = {
                table.title(): count 
                for table, count in stats['by_table'].items()
            }
            
            from utils.helpers import ChartHelpers
            ChartHelpers.create_pie_chart(table_data, "Registros por Tabela")
    
    with col2:
        # Records by action
        if stats.get('by_action'):
            action_data = {
                action.title(): count 
                for action, count in stats['by_action'].items()
            }
            
            ChartHelpers.create_pie_chart(action_data, "Registros por Ação")
    
    # Top users
    if stats.get('by_user'):
        st.subheader("👥 Usuários Mais Ativos")
        
        ChartHelpers.create_bar_chart(
            stats['by_user'],
            "Atividade por Usuário",
            "Usuário",
            "Ações"
        )
    
    # Activity timeline (last 30 days)
    st.subheader("📈 Timeline de Atividade (Últimos 30 dias)")
    
    # Get daily activity for last 30 days
    daily_activity = get_daily_activity(30)
    
    if daily_activity:
        ChartHelpers.create_line_chart(
            daily_activity,
            'date',
            'count',
            "Atividade Diária"
        )
    else:
        st.info("Dados insuficientes para gerar timeline.")

def show_audit_maintenance():
    """Show audit trail maintenance options"""
    st.subheader("🧹 Manutenção da Auditoria")
    
    # Get current statistics
    stats = AuditTrail.get_statistics()
    total_records = stats.get('total_records', 0)
    
    if total_records == 0:
        st.info("Nenhum registro de auditoria para manutenção.")
        return
    
    st.info(f"📊 Total atual: {total_records} registros de auditoria")
    
    # Cleanup options
    st.subheader("🗑️ Limpeza de Registros Antigos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        days_to_keep = st.selectbox(
            "Manter registros dos últimos:",
            options=[30, 90, 180, 365, 730],
            index=3,  # Default to 365 days
            format_func=lambda x: f"{x} dias"
        )
    
    with col2:
        # Calculate how many records would be deleted
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        from config.database import db_manager
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM audit_trail 
                WHERE changed_at < ?
            ''', (cutoff_date.isoformat(),))
            
            old_records_count = cursor.fetchone()[0]
    
    st.write(f"📋 Registros que seriam removidos: {old_records_count}")
    st.write(f"📋 Registros que seriam mantidos: {total_records - old_records_count}")
    
    if old_records_count > 0:
        if st.button(f"🗑️ Remover Registros Antigos ({old_records_count})", use_container_width=True):
            if UIHelpers.create_confirmation_dialog(
                f"Tem certeza que deseja remover {old_records_count} registros de auditoria "
                f"anteriores a {days_to_keep} dias?",
                "cleanup_audit"
            ):
                deleted_count = AuditTrail.cleanup_old_records(days_to_keep)
                UIHelpers.show_success_message(f"Removidos {deleted_count} registros antigos de auditoria.")
                st.rerun()
    else:
        st.success("✅ Não há registros antigos para remover com o período selecionado.")
    
    # Database optimization
    st.markdown("---")
    st.subheader("⚡ Otimização do Banco")
    
    if st.button("🔧 Otimizar Tabela de Auditoria", use_container_width=True):
        with st.spinner("Otimizando banco de dados..."):
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("VACUUM")
                    conn.commit()
                
                UIHelpers.show_success_message("Banco de dados otimizado com sucesso!")
            except Exception as e:
                UIHelpers.show_error_message(f"Erro ao otimizar banco: {str(e)}")
    
    # Export all audit data
    st.markdown("---")
    st.subheader("📥 Backup Completo")
    
    if st.button("📥 Exportar Toda Auditoria", use_container_width=True):
        with st.spinner("Gerando backup completo..."):
            csv_data = ExportService.export_audit_trail_to_csv(limit=total_records)
            
            st.download_button(
                "⬇️ Download Backup Completo",
                csv_data,
                f"backup_auditoria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )

def get_filtered_audit_records(table_filter: str, action_filter: str, user_filter: str, days_filter: int):
    """Get audit records with applied filters"""
    from config.database import db_manager
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        sql = "SELECT * FROM audit_trail WHERE 1=1"
        params = []
        
        if table_filter:
            sql += " AND table_name = ?"
            params.append(table_filter)
        
        if action_filter:
            sql += " AND action = ?"
            params.append(action_filter)
        
        if user_filter:
            sql += " AND changed_by LIKE ?"
            params.append(f"%{user_filter}%")
        
        if days_filter > 0:
            cutoff_date = datetime.now() - timedelta(days=days_filter)
            sql += " AND changed_at >= ?"
            params.append(cutoff_date.isoformat())
        
        sql += " ORDER BY changed_at DESC LIMIT 1000"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        return [AuditTrail.from_dict(dict(row)) for row in rows]

def get_daily_activity(days: int):
    """Get daily activity count for the last N days"""
    from config.database import db_manager
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT DATE(changed_at) as date, COUNT(*) as count
            FROM audit_trail 
            WHERE changed_at >= ?
            GROUP BY DATE(changed_at)
            ORDER BY date
        ''', (cutoff_date.isoformat(),))
        
        rows = cursor.fetchall()
        
        return [{'date': row[0], 'count': row[1]} for row in rows]

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
