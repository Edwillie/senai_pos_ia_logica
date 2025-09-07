# 🗃️ Gerador de Entidades - Sistema CRUD Dinâmico

Um sistema completo para criação e gerenciamento dinâmico de entidades (tabelas) desenvolvido em Python com Streamlit e SQLite.

## 📋 Funcionalidades

### 🏗️ Criação Dinâmica de Entidades
- Crie tabelas personalizadas sem programação
- Defina campos com diferentes tipos de dados
- Suporte para: Texto, Números (Inteiro/Decimal), Datas e Booleanos

### 📊 Gerenciamento Completo de Dados
- **Visualizar**: Interface intuitiva para visualização de dados
- **Adicionar**: Formulários dinâmicos baseados na estrutura da entidade
- **Editar**: Modificação de registros existentes
- **Excluir**: Remoção segura com confirmação

### 📁 Importação e Exportação
- **Importar**: Dados de arquivos CSV e Excel (.xlsx)
- **Exportar**: Dados para CSV e Excel
- **Templates**: Geração automática de templates para importação
- **Validação**: Verificação automática de tipos de dados

### ✅ Validação de Dados
- Validação em tempo real conforme tipos definidos
- Tratamento de erros com mensagens claras
- Suporte a diferentes formatos de data
- Conversão automática de tipos

## 🛠️ Tecnologias Utilizadas

- **Python 3.x**: Linguagem principal
- **Streamlit**: Interface web interativa
- **SQLite**: Banco de dados local
- **Pandas**: Manipulação e análise de dados
- **OpenPyXL**: Suporte para arquivos Excel

## 📦 Instalação

### Pré-requisitos
- Python 3.7 ou superior
- Windows 11 (testado e otimizado)

### Passos de Instalação

1. **Clone ou baixe o projeto**
   ```bash
   git clone <url-do-repositorio>
   cd GeradorEntidades
   ```

2. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute a aplicação**
   ```bash
   streamlit run app.py
   ```

4. **Acesse no navegador**
   - A aplicação abrirá automaticamente em `http://localhost:8501`

## 🚀 Como Usar

### 1. Criando uma Nova Entidade

1. Acesse a página **"Criar Entidade"**
2. Digite o nome da entidade (ex: "Clientes", "Produtos")
3. Adicione campos definindo:
   - Nome do campo
   - Tipo de dado
4. Clique em **"Criar Entidade"**

### 2. Gerenciando Dados

1. Vá para **"Gerenciar Dados"**
2. Selecione a entidade desejada
3. Use as abas para:
   - **Visualizar**: Ver todos os registros
   - **Adicionar**: Criar novos registros
   - **Editar/Excluir**: Modificar dados existentes

### 3. Importando Dados

1. Acesse **"Importar/Exportar"**
2. Selecione a entidade de destino
3. Baixe o template CSV/Excel
4. Preencha o template com seus dados
5. Faça upload do arquivo preenchido
6. Confirme a importação após validação

### 4. Exportando Dados

1. Na página **"Importar/Exportar"**
2. Selecione a entidade para exportar
3. Configure as opções de exportação
4. Baixe o arquivo CSV ou Excel

## 📊 Tipos de Dados Suportados

| Tipo | Descrição | Exemplos |
|------|-----------|----------|
| **Texto** | Strings e caracteres | "João Silva", "Descrição do produto" |
| **Número Inteiro** | Números inteiros | 123, -45, 0 |
| **Número Decimal** | Números com casas decimais | 123.45, -67.89, 0.5 |
| **Data** | Datas em vários formatos | 25/12/2023, 2023-12-25 |
| **Booleano** | Verdadeiro/Falso | Sim/Não, True/False, 1/0 |

## 📁 Estrutura do Projeto

```
GeradorEntidades/
├── app.py                 # Aplicação principal
├── config.py             # Configurações do sistema
├── requirements.txt      # Dependências Python
├── README.md            # Documentação
├── database/
│   └── db_manager.py    # Gerenciador do banco SQLite
├── utils/
│   ├── validators.py    # Validadores de dados
│   └── file_handler.py  # Manipulação de arquivos
└── pages/
    ├── entity_creator.py    # Página de criação de entidades
    ├── data_manager.py      # Página de gerenciamento de dados
    └── import_export.py     # Página de importação/exportação
```

## 🔧 Configuração

### Arquivo `config.py`
- **DATABASE_PATH**: Caminho do banco SQLite
- **SUPPORTED_DATA_TYPES**: Tipos de dados suportados
- **MAX_FILE_SIZE_MB**: Tamanho máximo para upload
- **ALLOWED_EXTENSIONS**: Extensões de arquivo permitidas

### Banco de Dados
- O banco SQLite é criado automaticamente como `entities.db`
- Tabela de metadados armazena definições das entidades
- Cada entidade vira uma tabela no banco

## 🛡️ Validação e Segurança

### Validação de Dados
- Verificação de tipos em tempo real
- Tratamento de formatos de data brasileiros
- Conversão automática de valores booleanos
- Mensagens de erro detalhadas

### Segurança
- Sanitização de nomes de entidades e campos
- Prevenção de SQL injection com prepared statements
- Validação de uploads de arquivo

## 🐛 Solução de Problemas

### Problemas Comuns

1. **Erro ao instalar dependências**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Erro de encoding em arquivos CSV**
   - O sistema tenta múltiplas codificações automaticamente
   - Salve o CSV com encoding UTF-8 se possível

3. **Streamlit não abre no navegador**
   ```bash
   streamlit run app.py --server.port 8501
   ```

4. **Banco de dados corrompido**
   - Delete o arquivo `entities.db`
   - Reinicie a aplicação (criará novo banco)

## 📈 Melhorias Futuras

- [ ] Suporte para relacionamentos entre entidades
- [ ] Backup e restore automático
- [ ] Mais tipos de dados (JSON, Imagens)
- [ ] Interface para consultas SQL customizadas
- [ ] Autenticação e controle de acesso
- [ ] API REST para integração externa

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Desenvolvedor

Desenvolvido para o curso SENAI - Sistema de Gerenciamento Dinâmico de Entidades.

---

**🎯 Objetivo**: Facilitar a criação e gerenciamento de dados estruturados sem necessidade de conhecimento técnico em bancos de dados.
