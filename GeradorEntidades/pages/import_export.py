"""
Streamlit page for importing and exporting data
"""

import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager
from utils.file_handler import FileHandler
from utils.validators import DataValidator
import config

def show_import_export():
    """Display the import/export interface"""
    st.header("📁 Importar/Exportar Dados")
    st.write("Importe dados de arquivos CSV/Excel ou exporte dados das suas entidades.")
    
    # Initialize database manager
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    
    # Get available entities
    entities = db_manager.get_all_entities()
    
    if not entities:
        st.warning("⚠️ Nenhuma entidade encontrada. Crie uma entidade primeiro na página 'Criar Entidade'.")
        return
    
    # Tabs for import and export
    tab1, tab2 = st.tabs(["📥 Importar Dados", "📤 Exportar Dados"])
    
    with tab1:
        show_import_section(db_manager, entities)
    
    with tab2:
        show_export_section(db_manager, entities)

def show_import_section(db_manager, entities):
    """Show data import section"""
    st.subheader("📥 Importar Dados")
    st.write("Importe dados de arquivos CSV ou Excel para suas entidades.")
    
    # Entity selection
    selected_entity = st.selectbox(
        "Selecione a entidade de destino:",
        options=entities,
        key="import_entity",
        help="Escolha a entidade onde os dados serão importados"
    )
    
    if not selected_entity:
        return
    
    # Get entity fields
    entity_fields = db_manager.get_entity_fields(selected_entity)
    
    if not entity_fields:
        st.error("❌ Erro ao carregar campos da entidade.")
        return
    
    # Show entity structure
    with st.expander("📋 Estrutura da Entidade"):
        st.write(f"**Entidade:** {selected_entity}")
        st.write("**Campos esperados:**")
        
        for field in entity_fields:
            st.write(f"- **{field['name']}** ({field['type']})")
    
    # Download template
    st.subheader("📄 Template de Importação")
    col1, col2 = st.columns(2)
    
    with col1:
        # Generate sample template
        template_df = FileHandler.get_sample_template(entity_fields)
        
        # CSV template download
        csv_template = FileHandler.export_to_csv(template_df)
        if csv_template:
            st.download_button(
                label="📄 Baixar Template CSV",
                data=csv_template,
                file_name=f"template_{selected_entity}.csv",
                mime="text/csv"
            )
    
    with col2:
        # Excel template download
        excel_template = FileHandler.export_to_excel(template_df)
        if excel_template:
            st.download_button(
                label="📄 Baixar Template Excel",
                data=excel_template,
                file_name=f"template_{selected_entity}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    st.divider()
    
    # File upload
    st.subheader("📁 Upload do Arquivo")
    uploaded_file = st.file_uploader(
        "Escolha um arquivo CSV ou Excel:",
        type=['csv', 'xlsx', 'xls'],
        help="Selecione o arquivo com os dados para importar"
    )
    
    if uploaded_file is not None:
        # Read uploaded file
        success, error_msg, df = FileHandler.read_uploaded_file(uploaded_file)
        
        if not success:
            st.error(f"❌ {error_msg}")
            return
        
        st.success(f"✅ Arquivo lido com sucesso! {len(df)} linhas encontradas.")
        
        # Show preview
        with st.expander("👀 Prévia dos Dados", expanded=True):
            st.dataframe(df.head(10), use_container_width=True)
            
            if len(df) > 10:
                st.info(f"Mostrando as primeiras 10 linhas de {len(df)} total.")
        
        # Validate data
        st.subheader("✅ Validação dos Dados")
        
        with st.spinner("Validando dados..."):
            is_valid, validation_errors, validated_df = FileHandler.validate_import_data(df, entity_fields)
        
        if is_valid:
            st.success(f"✅ Todos os {len(validated_df)} registros são válidos!")
            
            # Import options
            col1, col2 = st.columns(2)
            
            with col1:
                import_mode = st.radio(
                    "Modo de importação:",
                    options=["Adicionar aos dados existentes", "Substituir todos os dados"],
                    help="Escolha como os dados serão importados"
                )
            
            with col2:
                st.write("")  # Spacing
                
            # Import button
            if st.button("🚀 Importar Dados", type="primary", use_container_width=True):
                with st.spinner("Importando dados..."):
                    success_count = 0
                    error_count = 0
                    
                    # Clear existing data if replace mode
                    if import_mode == "Substituir todos os dados":
                        # Get all existing records and delete them
                        existing_df = db_manager.get_all_records(selected_entity)
                        for _, row in existing_df.iterrows():
                            db_manager.delete_record(selected_entity, row['id'])
                    
                    # Insert new records
                    for _, row in validated_df.iterrows():
                        record_data = row.to_dict()
                        
                        if db_manager.insert_record(selected_entity, record_data):
                            success_count += 1
                        else:
                            error_count += 1
                
                # Show results
                if error_count == 0:
                    st.success(f"🎉 Importação concluída! {success_count} registros importados com sucesso.")
                    st.balloons()
                else:
                    st.warning(f"⚠️ Importação parcial: {success_count} sucessos, {error_count} erros.")
        
        else:
            st.error(f"❌ {len(validation_errors)} erros de validação encontrados:")
            
            # Show validation errors
            with st.expander("📋 Detalhes dos Erros", expanded=True):
                for error in validation_errors[:20]:  # Show first 20 errors
                    st.error(f"• {error}")
                
                if len(validation_errors) > 20:
                    st.info(f"... e mais {len(validation_errors) - 20} erros.")
            
            st.info("💡 Corrija os erros no arquivo e tente novamente.")

def show_export_section(db_manager, entities):
    """Show data export section"""
    st.subheader("📤 Exportar Dados")
    st.write("Exporte os dados das suas entidades para arquivos CSV ou Excel.")
    
    # Entity selection
    selected_entity = st.selectbox(
        "Selecione a entidade para exportar:",
        options=entities,
        key="export_entity",
        help="Escolha a entidade cujos dados serão exportados"
    )
    
    if not selected_entity:
        return
    
    # Get entity data
    df = db_manager.get_all_records(selected_entity)
    entity_fields = db_manager.get_entity_fields(selected_entity)
    
    if df.empty:
        st.warning("⚠️ Nenhum dado encontrado para exportar nesta entidade.")
        return
    
    # Show data summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Registros", len(df))
    
    with col2:
        st.metric("Campos", len(entity_fields))
    
    with col3:
        st.metric("Tamanho Estimado", f"{len(df) * len(entity_fields) * 10} bytes")
    
    # Data preview
    with st.expander("👀 Prévia dos Dados", expanded=True):
        # Prepare display dataframe
        display_df = FileHandler.prepare_export_dataframe(df, entity_fields)
        st.dataframe(display_df.head(10), use_container_width=True)
        
        if len(display_df) > 10:
            st.info(f"Mostrando as primeiras 10 linhas de {len(display_df)} total.")
    
    st.divider()
    
    # Export options
    st.subheader("⚙️ Opções de Exportação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_id = st.checkbox(
            "Incluir ID dos registros",
            value=False,
            help="Incluir a coluna ID no arquivo exportado"
        )
    
    with col2:
        include_timestamp = st.checkbox(
            "Incluir data de criação",
            value=False,
            help="Incluir a coluna de timestamp no arquivo exportado"
        )
    
    # Prepare final export dataframe
    export_df = FileHandler.prepare_export_dataframe(df, entity_fields)
    
    if include_id and 'id' in df.columns:
        export_df.insert(0, 'ID', df['id'])
    
    if include_timestamp and 'created_at' in df.columns:
        export_df['Data de Criação'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m/%Y %H:%M')
    
    st.divider()
    
    # Export buttons
    st.subheader("📁 Download")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV Export
        csv_data = FileHandler.export_to_csv(export_df)
        if csv_data:
            st.download_button(
                label="📄 Baixar como CSV",
                data=csv_data,
                file_name=f"{selected_entity}_dados.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        # Excel Export
        excel_data = FileHandler.export_to_excel(export_df)
        if excel_data:
            st.download_button(
                label="📊 Baixar como Excel",
                data=excel_data,
                file_name=f"{selected_entity}_dados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    # Export summary
    with st.expander("📋 Resumo da Exportação"):
        st.write(f"**Entidade:** {selected_entity}")
        st.write(f"**Registros:** {len(export_df)}")
        st.write(f"**Colunas:** {len(export_df.columns)}")
        st.write("**Colunas incluídas:**")
        for col in export_df.columns:
            st.write(f"- {col}")

if __name__ == "__main__":
    show_import_export()
