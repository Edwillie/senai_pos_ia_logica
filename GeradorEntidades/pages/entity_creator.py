"""
Streamlit page for creating new entities (tables)
"""

import streamlit as st
from database.db_manager import DatabaseManager
import config

def show_entity_creator():
    """Display the entity creation interface"""
    st.header("🏗️ Criar Nova Entidade")
    st.write("Defina uma nova entidade (tabela) com campos personalizados.")
    
    # Initialize database manager
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    
    # Entity name input
    st.subheader("Nome da Entidade")
    entity_name = st.text_input(
        "Nome da entidade:",
        placeholder="Ex: Clientes, Produtos, Funcionários",
        help="Digite o nome da nova entidade (tabela) que será criada"
    )
    
    # Validate entity name
    if entity_name:
        # Clean entity name (remove spaces, special characters)
        clean_name = entity_name.replace(' ', '_').replace('-', '_').lower()
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c == '_')
        
        if clean_name != entity_name.replace(' ', '_').lower():
            st.info(f"O nome da entidade será salvo como: **{clean_name}**")
        
        # Check if entity already exists
        if db_manager.entity_exists(clean_name):
            st.error(f"❌ A entidade '{clean_name}' já existe!")
            return
    
    st.divider()
    
    # Fields definition
    st.subheader("Definição dos Campos")
    st.write("Adicione os campos que sua entidade terá:")
    
    # Initialize fields in session state
    if 'entity_fields' not in st.session_state:
        st.session_state.entity_fields = []
    
    # Add new field section
    with st.expander("➕ Adicionar Novo Campo", expanded=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            field_name = st.text_input("Nome do Campo:", key="new_field_name")
        
        with col2:
            field_type = st.selectbox(
                "Tipo de Dado:",
                options=list(config.SUPPORTED_DATA_TYPES.keys()),
                key="new_field_type"
            )
        
        with col3:
            st.write("")  # Spacing
            if st.button("Adicionar Campo", type="primary"):
                if field_name.strip():
                    # Check for duplicate field names
                    existing_names = [f['name'] for f in st.session_state.entity_fields]
                    if field_name not in existing_names:
                        st.session_state.entity_fields.append({
                            'name': field_name.strip(),
                            'type': field_type
                        })
                        st.success(f"Campo '{field_name}' adicionado!")
                        st.rerun()
                    else:
                        st.error("Campo com este nome já existe!")
                else:
                    st.error("Nome do campo é obrigatório!")
    
    # Display current fields
    if st.session_state.entity_fields:
        st.subheader("Campos Definidos")
        
        for i, field in enumerate(st.session_state.entity_fields):
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.text_input(
                    f"Campo {i+1}:",
                    value=field['name'],
                    disabled=True,
                    key=f"field_name_{i}"
                )
            
            with col2:
                st.text_input(
                    f"Tipo {i+1}:",
                    value=field['type'],
                    disabled=True,
                    key=f"field_type_{i}"
                )
            
            with col3:
                if st.button("✏️", key=f"edit_{i}", help="Editar campo"):
                    st.session_state[f"editing_field_{i}"] = True
                    st.rerun()
            
            with col4:
                if st.button("🗑️", key=f"delete_{i}", help="Remover campo"):
                    st.session_state.entity_fields.pop(i)
                    st.success("Campo removido!")
                    st.rerun()
        
        # Handle field editing
        for i, field in enumerate(st.session_state.entity_fields):
            if st.session_state.get(f"editing_field_{i}", False):
                with st.expander(f"✏️ Editando: {field['name']}", expanded=True):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        new_name = st.text_input(
                            "Novo nome:",
                            value=field['name'],
                            key=f"edit_name_{i}"
                        )
                    
                    with col2:
                        new_type = st.selectbox(
                            "Novo tipo:",
                            options=list(config.SUPPORTED_DATA_TYPES.keys()),
                            index=list(config.SUPPORTED_DATA_TYPES.keys()).index(field['type']),
                            key=f"edit_type_{i}"
                        )
                    
                    with col3:
                        st.write("")  # Spacing
                        if st.button("Salvar", key=f"save_edit_{i}"):
                            if new_name.strip():
                                st.session_state.entity_fields[i] = {
                                    'name': new_name.strip(),
                                    'type': new_type
                                }
                                st.session_state[f"editing_field_{i}"] = False
                                st.success("Campo atualizado!")
                                st.rerun()
                        
                        if st.button("Cancelar", key=f"cancel_edit_{i}"):
                            st.session_state[f"editing_field_{i}"] = False
                            st.rerun()
    
    st.divider()
    
    # Create entity button
    if entity_name and st.session_state.entity_fields:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 Criar Entidade", type="primary", use_container_width=True):
                clean_name = entity_name.replace(' ', '_').replace('-', '_').lower()
                clean_name = ''.join(c for c in clean_name if c.isalnum() or c == '_')
                
                with st.spinner("Criando entidade..."):
                    success = db_manager.create_entity(clean_name, st.session_state.entity_fields)
                
                if success:
                    st.success(f"✅ Entidade '{clean_name}' criada com sucesso!")
                    st.balloons()
                    
                    # Clear form
                    st.session_state.entity_fields = []
                    if 'new_field_name' in st.session_state:
                        del st.session_state['new_field_name']
                    
                    # Show summary
                    with st.expander("📋 Resumo da Entidade Criada"):
                        st.write(f"**Nome:** {clean_name}")
                        st.write("**Campos:**")
                        for field in st.session_state.entity_fields:
                            st.write(f"- {field['name']} ({field['type']})")
                    
                    st.info("💡 Agora você pode ir para 'Gerenciar Dados' para adicionar registros!")
                    
                else:
                    st.error("❌ Erro ao criar entidade. Verifique se o nome não está em uso.")
    
    elif entity_name and not st.session_state.entity_fields:
        st.warning("⚠️ Adicione pelo menos um campo para criar a entidade.")
    
    elif not entity_name and st.session_state.entity_fields:
        st.warning("⚠️ Digite o nome da entidade para continuar.")
    
    # Clear fields button
    if st.session_state.entity_fields:
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🗑️ Limpar Todos os Campos", use_container_width=True):
                st.session_state.entity_fields = []
                st.rerun()
    
    # Show existing entities
    st.divider()
    st.subheader("📚 Entidades Existentes")
    
    existing_entities = db_manager.get_all_entities()
    if existing_entities:
        for entity in existing_entities:
            with st.expander(f"📋 {entity}"):
                fields = db_manager.get_entity_fields(entity)
                if fields:
                    st.write("**Campos:**")
                    for field in fields:
                        st.write(f"- **{field['name']}** ({field['type']})")
                else:
                    st.write("Nenhum campo encontrado.")
                
                # Delete entity option
                if st.button(f"🗑️ Excluir Entidade '{entity}'", key=f"delete_entity_{entity}"):
                    if st.session_state.get(f"confirm_delete_{entity}", False):
                        success = db_manager.delete_entity(entity)
                        if success:
                            st.success(f"Entidade '{entity}' excluída com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao excluir entidade.")
                    else:
                        st.session_state[f"confirm_delete_{entity}"] = True
                        st.warning("⚠️ Clique novamente para confirmar a exclusão!")
    else:
        st.info("Nenhuma entidade criada ainda.")

if __name__ == "__main__":
    show_entity_creator()
