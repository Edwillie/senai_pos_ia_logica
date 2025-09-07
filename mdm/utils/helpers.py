import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

class UIHelpers:
    
    @staticmethod
    def show_success_message(message: str):
        """Show success message with icon"""
        st.success(f"✅ {message}")
    
    @staticmethod
    def show_error_message(message: str):
        """Show error message with icon"""
        st.error(f"❌ {message}")
    
    @staticmethod
    def show_warning_message(message: str):
        """Show warning message with icon"""
        st.warning(f"⚠️ {message}")
    
    @staticmethod
    def show_info_message(message: str):
        """Show info message with icon"""
        st.info(f"ℹ️ {message}")
    
    @staticmethod
    def create_metric_card(title: str, value: Any, delta: Optional[str] = None, 
                          delta_color: str = "normal"):
        """Create a metric card"""
        st.metric(
            label=title,
            value=value,
            delta=delta,
            delta_color=delta_color
        )
    
    @staticmethod
    def create_status_badge(status: str) -> str:
        """Create colored status badge"""
        status_colors = {
            'active': '🟢',
            'inactive': '🔴',
            'pending': '🟡',
            'deleted': '⚫',
            'merged': '🔵',
            'not_duplicate': '⚪'
        }
        
        return f"{status_colors.get(status, '⚪')} {status.title()}"
    
    @staticmethod
    def format_datetime(dt_string: str) -> str:
        """Format datetime string for display"""
        if not dt_string:
            return ""
        
        try:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return dt_string
    
    @staticmethod
    def format_currency(value: Optional[float]) -> str:
        """Format currency value"""
        if value is None:
            return ""
        
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @staticmethod
    def create_search_filters(entity_type: str) -> Dict[str, Any]:
        """Create search and filter interface"""
        filters = {}
        
        # Search query
        search_query = st.text_input("🔍 Buscar", placeholder="Digite para buscar...")
        filters['query'] = search_query
        
        # Entity-specific filters
        if entity_type in ['clients', 'suppliers']:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                document_type = st.selectbox(
                    "Tipo de Documento",
                    options=["", "CPF", "CNPJ"],
                    index=0
                )
                if document_type:
                    filters['document_type'] = document_type
            
            with col2:
                category = st.text_input("Categoria")
                if category:
                    filters['category'] = category
            
            with col3:
                status = st.selectbox(
                    "Status",
                    options=["", "active", "inactive", "deleted"],
                    index=0
                )
                if status:
                    filters['status'] = status
        
        elif entity_type == 'products':
            col1, col2, col3 = st.columns(3)
            
            with col1:
                category = st.text_input("Categoria")
                if category:
                    filters['category'] = category
            
            with col2:
                unit_of_measure = st.text_input("Unidade de Medida")
                if unit_of_measure:
                    filters['unit_of_measure'] = unit_of_measure
            
            with col3:
                status = st.selectbox(
                    "Status",
                    options=["", "active", "inactive", "deleted"],
                    index=0
                )
                if status:
                    filters['status'] = status
        
        return filters
    
    @staticmethod
    def create_data_table(data: List[Dict[str, Any]], columns: List[str], 
                         actions: List[str] = None) -> Optional[Dict[str, Any]]:
        """Create interactive data table with actions"""
        if not data:
            st.info("Nenhum registro encontrado.")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Display table
        st.dataframe(df[columns], use_container_width=True)
        
        # Action buttons
        if actions:
            selected_index = st.selectbox(
                "Selecionar registro para ação:",
                options=range(len(data)),
                format_func=lambda x: f"{data[x].get('name', data[x].get('code', f'Registro {x+1}'))}"
            )
            
            if selected_index is not None:
                col_actions = st.columns(len(actions))
                
                for i, action in enumerate(actions):
                    with col_actions[i]:
                        if st.button(action, key=f"{action}_{selected_index}"):
                            return {
                                'action': action,
                                'record': data[selected_index],
                                'index': selected_index
                            }
        
        return None
    
    @staticmethod
    def create_confirmation_dialog(message: str, key: str) -> bool:
        """Create confirmation dialog"""
        if f"confirm_{key}" not in st.session_state:
            st.session_state[f"confirm_{key}"] = False
        
        if not st.session_state[f"confirm_{key}"]:
            st.warning(message)
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Confirmar", key=f"confirm_yes_{key}"):
                    st.session_state[f"confirm_{key}"] = True
                    st.rerun()
            
            with col2:
                if st.button("Cancelar", key=f"confirm_no_{key}"):
                    return False
            
            return False
        else:
            # Reset confirmation state
            st.session_state[f"confirm_{key}"] = False
            return True

class ChartHelpers:
    
    @staticmethod
    def create_pie_chart(data: Dict[str, int], title: str):
        """Create pie chart"""
        if not data:
            st.info("Sem dados para exibir")
            return
        
        fig = px.pie(
            values=list(data.values()),
            names=list(data.keys()),
            title=title
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def create_bar_chart(data: Dict[str, int], title: str, x_label: str = "", y_label: str = ""):
        """Create bar chart"""
        if not data:
            st.info("Sem dados para exibir")
            return
        
        fig = px.bar(
            x=list(data.keys()),
            y=list(data.values()),
            title=title,
            labels={'x': x_label, 'y': y_label}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def create_line_chart(data: List[Dict[str, Any]], x_col: str, y_col: str, title: str):
        """Create line chart"""
        if not data:
            st.info("Sem dados para exibir")
            return
        
        df = pd.DataFrame(data)
        
        fig = px.line(
            df,
            x=x_col,
            y=y_col,
            title=title
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def create_gauge_chart(value: float, max_value: float, title: str):
        """Create gauge chart"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            delta={'reference': max_value * 0.8},
            gauge={
                'axis': {'range': [None, max_value]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, max_value * 0.5], 'color': "lightgray"},
                    {'range': [max_value * 0.5, max_value * 0.8], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value * 0.9
                }
            }
        ))
        
        st.plotly_chart(fig, use_container_width=True)

class DataHelpers:
    
    @staticmethod
    def paginate_data(data: List[Any], page_size: int = 10) -> Dict[str, Any]:
        """Paginate data for display"""
        total_items = len(data)
        total_pages = (total_items + page_size - 1) // page_size
        
        if total_pages == 0:
            return {
                'data': [],
                'current_page': 1,
                'total_pages': 0,
                'total_items': 0
            }
        
        # Page selector
        current_page = st.selectbox(
            "Página:",
            options=range(1, total_pages + 1),
            index=0,
            format_func=lambda x: f"Página {x} de {total_pages}"
        )
        
        # Calculate slice indices
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)
        
        return {
            'data': data[start_idx:end_idx],
            'current_page': current_page,
            'total_pages': total_pages,
            'total_items': total_items,
            'showing_from': start_idx + 1,
            'showing_to': end_idx
        }
    
    @staticmethod
    def export_to_csv_button(data: bytes, filename: str, label: str = "Exportar CSV"):
        """Create CSV export button"""
        st.download_button(
            label=f"📥 {label}",
            data=data,
            file_name=filename,
            mime="text/csv"
        )
    
    @staticmethod
    def import_csv_uploader(label: str = "Importar CSV", key: str = None):
        """Create CSV import file uploader"""
        return st.file_uploader(
            f"📤 {label}",
            type=['csv'],
            key=key,
            help="Selecione um arquivo CSV para importar dados"
        )
    
    @staticmethod
    def calculate_statistics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic statistics for data"""
        if not data:
            return {}
        
        total_count = len(data)
        
        # Count by status
        status_counts = {}
        for item in data:
            status = item.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Recent items (last 7 days)
        recent_count = 0
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for item in data:
            created_at = item.get('created_at')
            if created_at:
                try:
                    item_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if item_date >= cutoff_date:
                        recent_count += 1
                except:
                    pass
        
        return {
            'total_count': total_count,
            'status_counts': status_counts,
            'recent_count': recent_count
        }

class FormHelpers:
    
    @staticmethod
    def create_document_input(label: str, document_type: str, value: str = "") -> str:
        """Create document number input with validation"""
        placeholder = "000.000.000-00" if document_type == "CPF" else "00.000.000/0000-00"
        
        return st.text_input(
            label,
            value=value,
            placeholder=placeholder,
            help=f"Digite o {document_type} (apenas números ou formatado)"
        )
    
    @staticmethod
    def create_phone_input(label: str, value: str = "") -> str:
        """Create phone number input"""
        return st.text_input(
            label,
            value=value,
            placeholder="(11) 99999-9999",
            help="Digite o telefone (apenas números ou formatado)"
        )
    
    @staticmethod
    def create_email_input(label: str, value: str = "") -> str:
        """Create email input"""
        return st.text_input(
            label,
            value=value,
            placeholder="exemplo@email.com",
            help="Digite um endereço de email válido"
        )
    
    @staticmethod
    def create_zip_code_input(label: str, value: str = "") -> str:
        """Create ZIP code input"""
        return st.text_input(
            label,
            value=value,
            placeholder="00000-000",
            help="Digite o CEP (apenas números ou formatado)"
        )
    
    @staticmethod
    def create_currency_input(label: str, value: Optional[float] = None) -> Optional[float]:
        """Create currency input"""
        return st.number_input(
            label,
            value=value if value is not None else 0.0,
            min_value=0.0,
            format="%.2f",
            help="Digite o valor em reais"
        )
