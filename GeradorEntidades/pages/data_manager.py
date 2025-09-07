"""
Streamlit page for managing data (CRUD operations)
"""

import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager
from utils.validators import DataValidator
from datetime import datetime, date
import config

def show_data_manager():
    """Display the data management interface"""
    st.header("📊 Gerenciar Dados")
    st.write("Visualize, adicione, edite e exclua registros das suas entidades.")
    
    # Initialize database manager
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    
    # Get available entities
    entities = db_manager.get_all_entities()
    
    if not entities:
        st.warning("⚠️ Nenhuma entidade encontrada. Crie uma entidade primeiro na página 'Criar Entidade'.")
        return
    
    # Entity selection
    selected_entity = st.selectbox(
        "Selecione uma entidade:",
        options=entities,
        help="Escolha a entidade que deseja gerenciar"
    )
    
    if not selected_entity:
        return
    
    # Get entity fields
    entity_fields = db_manager.get_entity_fields(selected_entity)
    
    if not entity_fields:
        st.error("❌ Erro ao carregar campos da entidade.")
        return
    
    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📋 Visualizar Dados", "➕ Adicionar Registro", "✏️ Editar/Excluir"])
    
    with tab1:
        show_data_view(db_manager, selected_entity, entity_fields)
    
    with tab2:
        show_add_record(db_manager, selected_entity, entity_fields)
    
    with tab3:
        show_edit_delete(db_manager, selected_entity, entity_fields)

def show_data_view(db_manager, entity_name, entity_fields):
    """Show data visualization tab"""
    st.subheader(f"📋 Dados da Entidade: {entity_name}")
    
    # Get all records
    df = db_manager.get_all_records(entity_name)
    
    if df.empty:
        st.info("📝 Nenhum registro encontrado. Adicione alguns dados!")
        return
    
    # Display record count
    st.metric("Total de Registros", len(df))
    
    # Search and filter options
    with st.expander("🔍 Filtros e Busca"):
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("Buscar em todos os campos:", key="search_data")
        
        with col2:
            # Field-specific filter
            filter_field = st.selectbox(
                "Filtrar por campo:",
                options=["Todos"] + [field['name'] for field in entity_fields],
                key="filter_field"
            )
    
    # Apply filters
    filtered_df = df.copy()
    
    if search_term:
        # Search in all text columns
        mask = False
        for col in df.columns:
            if df[col].dtype == 'object':  # Text columns
                mask |= df[col].astype(str).str.contains(search_term, case=False, na=False)
        filtered_df = df[mask]
    
    # Display filtered data
    if not filtered_df.empty:
        # Format display columns
        display_df = format_dataframe_for_display(filtered_df, entity_fields)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Show filtered count if different from total
        if len(filtered_df) != len(df):
            st.info(f"Mostrando {len(filtered_df)} de {len(df)} registros")
    else:
        st.warning("Nenhum registro encontrado com os filtros aplicados.")

def show_add_record(db_manager, entity_name, entity_fields):
    """Show add record tab"""
    st.subheader(f"➕ Adicionar Novo Registro em: {entity_name}")
    
    with st.form("add_record_form"):
        st.write("Preencha os campos abaixo:")
        
        form_data = {}
        
        # Create input fields based on entity definition
        for field in entity_fields:
            field_name = field['name']
            field_type = field['type']
            
            form_data[field_name] = create_input_widget(field_name, field_type, key=f"add_{field_name}")
        
        # Submit button
        submitted = st.form_submit_button("💾 Salvar Registro", type="primary")
        
        if submitted:
            # Validate data
            is_valid, errors, validated_data = DataValidator.validate_record(entity_fields, form_data)
            
            if is_valid:
                # Insert record
                success = db_manager.insert_record(entity_name, validated_data)
                
                if success:
                    st.success("✅ Registro adicionado com sucesso!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar registro.")
            else:
                st.error("❌ Erros de validação encontrados:")
                for error in errors:
                    st.error(f"• {error}")

def show_edit_delete(db_manager, entity_name, entity_fields):
    """Show edit/delete tab"""
    st.subheader(f"✏️ Editar/Excluir Registros de: {entity_name}")
    
    # Get all records
    df = db_manager.get_all_records(entity_name)
    
    if df.empty:
        st.info("📝 Nenhum registro encontrado para editar.")
        return
    
    # Record selection
    st.write("Selecione um registro para editar ou excluir:")
    
    # Create a display version for selection
    display_df = format_dataframe_for_display(df, entity_fields)
    
    # Add selection column
    selection_df = display_df.copy()
    selection_df.insert(0, "Selecionar", False)
    
    # Use data editor for selection
    edited_df = st.data_editor(
        selection_df,
        disabled=list(selection_df.columns[1:]),  # Disable all except selection
        hide_index=True,
        use_container_width=True
    )
    
    # Find selected rows
    selected_rows = edited_df[edited_df["Selecionar"] == True]
    
    if not selected_rows.empty:
        selected_index = selected_rows.index[0]
        selected_record = df.iloc[selected_index]
        record_id = selected_record['id']
        
        st.divider()
        
        # Edit form
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✏️ Editar Registro")
            
            with st.form("edit_record_form"):
                form_data = {}
                
                # Create input fields with current values
                for field in entity_fields:
                    field_name = field['name']
                    field_type = field['type']
                    
                    # Get current value
                    current_value = selected_record.get(field_name.replace(' ', '_').lower())
                    
                    form_data[field_name] = create_input_widget(
                        field_name, 
                        field_type, 
                        value=current_value,
                        key=f"edit_{field_name}_{record_id}"
                    )
                
                # Submit button
                if st.form_submit_button("💾 Atualizar Registro", type="primary"):
                    # Validate data
                    is_valid, errors, validated_data = DataValidator.validate_record(entity_fields, form_data)
                    
                    if is_valid:
                        # Update record
                        success = db_manager.update_record(entity_name, record_id, validated_data)
                        
                        if success:
                            st.success("✅ Registro atualizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao atualizar registro.")
                    else:
                        st.error("❌ Erros de validação encontrados:")
                        for error in errors:
                            st.error(f"• {error}")
        
        with col2:
            st.subheader("🗑️ Excluir Registro")
            
            # Show current record details
            st.write("**Registro selecionado:**")
            for field in entity_fields:
                field_name = field['name']
                current_value = selected_record.get(field_name.replace(' ', '_').lower())
                st.write(f"**{field_name}:** {current_value}")
            
            st.divider()
            
            # Delete confirmation
            if st.button("🗑️ Excluir Registro", type="secondary", use_container_width=True):
                if st.session_state.get(f"confirm_delete_{record_id}", False):
                    success = db_manager.delete_record(entity_name, record_id)
                    
                    if success:
                        st.success("✅ Registro excluído com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao excluir registro.")
                else:
                    st.session_state[f"confirm_delete_{record_id}"] = True
                    st.warning("⚠️ Clique novamente para confirmar a exclusão!")

def create_input_widget(field_name, field_type, value=None, key=None):
    """Create appropriate input widget based on field type"""
    
    if field_type == "Texto":
        return st.text_input(
            f"{field_name}:",
            value=value if value is not None else "",
            key=key
        )
    
    elif field_type == "Número Inteiro":
        return st.number_input(
            f"{field_name}:",
            value=int(value) if value is not None and value != "" else 0,
            step=1,
            format="%d",
            key=key
        )
    
    elif field_type == "Número Decimal":
        return st.number_input(
            f"{field_name}:",
            value=float(value) if value is not None and value != "" else 0.0,
            step=0.01,
            format="%.2f",
            key=key
        )
    
    elif field_type == "Data":
        if value is not None and value != "":
            try:
                if isinstance(value, str):
                    date_value = datetime.strptime(value, '%Y-%m-%d').date()
                else:
                    date_value = value
            except:
                date_value = date.today()
        else:
            date_value = date.today()
        
        return st.date_input(
            f"{field_name}:",
            value=date_value,
            key=key
        )
    
    elif field_type == "Booleano":
        bool_value = False
        if value is not None:
            if isinstance(value, bool):
                bool_value = value
            elif isinstance(value, str):
                bool_value = value.lower() in ['true', '1', 'sim', 'yes']
            else:
                bool_value = bool(value)
        
        return st.checkbox(
            f"{field_name}:",
            value=bool_value,
            key=key
        )
    
    else:
        return st.text_input(f"{field_name}:", value=value if value is not None else "", key=key)

def format_dataframe_for_display(df, entity_fields):
    """Format DataFrame for better display"""
    display_df = df.copy()
    
    # Remove system columns for display
    system_columns = ['created_at']
    for col in system_columns:
        if col in display_df.columns:
            display_df = display_df.drop(columns=[col])
    
    # Format columns based on field types
    field_type_map = {field['name'].replace(' ', '_').lower(): field['type'] for field in entity_fields}
    
    for col in display_df.columns:
        if col in field_type_map:
            field_type = field_type_map[col]
            
            if field_type == "Data":
                # Format dates
                display_df[col] = pd.to_datetime(display_df[col], errors='coerce').dt.strftime('%d/%m/%Y')
            elif field_type == "Booleano":
                # Format booleans
                display_df[col] = display_df[col].map({True: 'Sim', False: 'Não', None: ''})
            elif field_type == "Número Decimal":
                # Format decimals
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "")
    
    # Rename columns to original field names
    column_mapping = {}
    for field in entity_fields:
        db_column = field['name'].replace(' ', '_').lower()
        if db_column in display_df.columns:
            column_mapping[db_column] = field['name']
    
    display_df = display_df.rename(columns=column_mapping)
    
    return display_df

if __name__ == "__main__":
    show_data_manager()
