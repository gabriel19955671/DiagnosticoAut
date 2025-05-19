import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
from fpdf import FPDF
import tempfile
import re 
import json
import plotly.express as px 

st.set_page_config(page_title="Portal de Diagnóstico", layout="wide") 

# CSS (mantido)
st.markdown("""
<style>
/* ... Seu CSS anterior aqui ... */
.login-container {
    max-width: 400px;
    margin: 60px auto 0 auto;
    padding: 40px;
    border-radius: 8px;
    background-color: #ffffff;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    font-family: 'Segoe UI', sans-serif;
}
.login-container h2 {
    text-align: center;
    margin-bottom: 30px;
    font-weight: 600;
    font-size: 26px;
    color: #2563eb;
}
.stButton>button {
    border-radius: 6px;
    background-color: #2563eb;
    color: white;
    font-weight: 500;
    padding: 0.5rem 1.2rem;
    margin-top: 0.5rem;
}
.stDownloadButton>button {
    background-color: #10b981;
    color: white;
    font-weight: 600;
    border-radius: 6px;
    margin-top: 10px;
    padding: 0.5rem 1.2rem;
}
.stTextInput>div>input, .stTextArea>div>textarea {
    border-radius: 6px;
    padding: 0.4rem;
    border: 1px solid #d1d5db;
    background-color: #f9fafb;
}
.stTabs [data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 600;
    padding: 10px 20px;
}
.custom-card {
    border: 1px solid #e0e0e0;
    border-left: 5px solid #2563eb; 
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 5px;
    background-color: #f9f9f9;
}
.custom-card h4 {
    margin-top: 0;
    color: #2563eb;
}
</style>
""", unsafe_allow_html=True)

st.title("🔒 Portal de Diagnóstico")
st.write("DEBUG: Título do Portal renderizado.") # DEBUG INICIAL

# --- Configuração de Arquivos e Variáveis Globais ---
admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv" 
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv" 
historico_csv = "historico_clientes.csv"

# --- Inicialização do Session State ---
if "admin_logado" not in st.session_state: st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state: st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state: st.session_state.diagnostico_enviado = False
if "inicio_sessao_cliente" not in st.session_state: st.session_state.inicio_sessao_cliente = None
if "cliente_page" not in st.session_state: st.session_state.cliente_page = "Painel Principal"
if "cnpj" not in st.session_state: st.session_state.cnpj = None
if "user" not in st.session_state: st.session_state.user = None
# A chave DIAGNOSTICO_FORM_ID_KEY será definida dinamicamente com base no CNPJ

# --- Funções Utilitárias ---
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s) 
    return s

def pdf_safe_text_output(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# --- Criação e Verificação de Arquivos ---
colunas_base_diagnosticos = [
    "Data", "CNPJ", "Nome", "Email", "Empresa",
    "Média Geral", "GUT Média", "Observações", "Diagnóstico", 
    "Análise do Cliente", "Comentarios_Admin"
]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone"]
colunas_base_perguntas = ["Pergunta", "Categoria"]

def inicializar_csv(filepath, columns, is_perguntas_file=False):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df = pd.DataFrame(columns=columns)
            df.to_csv(filepath, index=False, encoding='utf-8')
        else:
            df = pd.read_csv(filepath, encoding='utf-8')
            missing_cols = [col for col in columns if col not in df.columns]
            made_changes = False
            if missing_cols:
                for col in missing_cols:
                    if is_perguntas_file and col == "Categoria": df[col] = "Geral"
                    else: df[col] = pd.NA 
                made_changes = True
            if is_perguntas_file and "Categoria" not in df.columns:
                df["Categoria"] = "Geral"; made_changes = True
            if made_changes:
                df.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError: 
        pd.DataFrame(columns=columns).to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erro ao inicializar/verificar {filepath}: {e}. O app pode não funcionar corretamente.")
        # Removido st.stop() para tentar continuar e identificar outros erros.

st.write("DEBUG: Inicializando arquivos CSV...")
try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios)
    inicializar_csv(perguntas_csv, colunas_base_perguntas, is_perguntas_file=True)
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
    st.write("DEBUG: Arquivos CSV inicializados (ou verificados).")
except Exception as e_init_main:
    st.error(f"Falha crítica na inicialização de arquivos CSV base: {e_init_main}")
    st.exception(e_init_main)
    st.markdown("---")
    st.markdown("### Solução de Problemas:")
    st.markdown("""
    1. Verifique se você tem permissão de escrita na pasta onde o script está rodando.
    2. Tente deletar os arquivos CSV mencionados acima da pasta do script. Eles serão recriados na próxima execução.
    3. Se o problema persistir, pode haver um problema mais sério com o ambiente ou permissões.
    """)
    st.stop()


def registrar_acao(cnpj, acao, descricao):
    # ... (código mantido)
    try:
        historico_df_ra_d = pd.read_csv(historico_csv, encoding='utf-8') 
    except (FileNotFoundError, pd.errors.EmptyDataError): 
        historico_df_ra_d = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data_ra_d = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }
    historico_df_ra_d = pd.concat([historico_df_ra_d, pd.DataFrame([nova_data_ra_d])], ignore_index=True)
    historico_df_ra_d.to_csv(historico_csv, index=False, encoding='utf-8')


def gerar_pdf_diagnostico_completo(diagnostico_data, usuario_data, perguntas_df_geracao, respostas_coletadas_geracao, medias_categorias_geracao):
    # ... (Código da função gerar_pdf_diagnostico_completo mantido da versão anterior) ...
    try:
        pdf = FPDF()
        pdf.add_page()
        # ... (Resto da lógica de geração de PDF)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_g_pdf:
            pdf_path_g_pdf = tmpfile_g_pdf.name
            pdf.output(pdf_path_g_pdf)
        return pdf_path_g_pdf
    except Exception as e_pdf_ger:
        st.error(f"Erro ao gerar PDF: {e_pdf_ger}")
        return None


# --- Lógica de Login e Navegação Principal (Admin/Cliente) ---
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    st.write("DEBUG: Exibindo seleção de tipo de usuário (Admin/Cliente).")
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_main_debug_v2")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"
st.write(f"DEBUG: Aba selecionada/definida: {aba}")


if aba == "Administrador" and not st.session_state.admin_logado:
    st.write("DEBUG: Exibindo formulário de login do Administrador.")
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_page_debug_v2"): 
        usuario_admin_login_pg_d2 = st.text_input("Usuário", key="admin_user_login_page_d2") 
        senha_admin_login_pg_d2 = st.text_input("Senha", type="password", key="admin_pass_login_page_d2")
        entrar_admin_login_pg_d2 = st.form_submit_button("Entrar")
    if entrar_admin_login_pg_d2:
        st.write("DEBUG: Botão Entrar (Admin) pressionado.")
        try:
            df_admin_login_creds_pg_d2 = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            st.write(f"DEBUG: CSV Admin lido. Conteúdo: {df_admin_login_creds_pg_d2.head().to_dict()}")
            admin_encontrado = df_admin_login_creds_pg_d2[
                (df_admin_login_creds_pg_d2["Usuario"] == usuario_admin_login_pg_d2) & 
                (df_admin_login_creds_pg_d2["Senha"] == senha_admin_login_pg_d2)
            ]
            if not admin_encontrado.empty:
                st.write("DEBUG: Admin encontrado. Configurando sessão.")
                st.session_state.admin_logado = True
                st.success("Login de administrador bem-sucedido!")
                st.session_state.trigger_admin_rerun = True
                st.rerun() 
            else: 
                st.error("Usuário ou senha inválidos.")
                st.write("DEBUG: Admin não encontrado ou senha inválida.")
        except FileNotFoundError: st.error(f"Arquivo {admin_credenciais_csv} não encontrado.")
        except Exception as e_login_admin_d2: st.error(f"Erro no login do admin: {e_login_admin_d2}"); st.exception(e_login_admin_d2)
    st.markdown('</div>', unsafe_allow_html=True)
    st.write("DEBUG: Fim da seção de login do admin (se não logado). Parando execução aqui.")
    st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    # ... (código login cliente mantido, adicione DEBUG writes se necessário)
    st.write("DEBUG: Exibindo formulário de login do Cliente.")
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    # ... (restante do login do cliente como antes, com try-except) ...
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    st.write("DEBUG: Entrou na área do Cliente Logado.")
    try: 
        st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
        st.write("DEBUG: Sidebar do cliente - Bem-vindo renderizado.")
        
        DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME_D = f"form_id_diagnostico_cliente_{st.session_state.cnpj}"

        st.session_state.cliente_page = st.sidebar.radio(
            "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
            index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page),
            key="cliente_menu_radio_main_debug_v2"
        )
        st.write(f"DEBUG: Sidebar do cliente - Menu radio renderizado. Página selecionada: {st.session_state.cliente_page}")

        if st.sidebar.button("⬅️ Sair do Portal Cliente"):
            # ... (lógica de logout do cliente) ...
            st.rerun()

        if st.session_state.cliente_page == "Painel Principal":
            st.write("DEBUG: Renderizando Painel Principal do Cliente.")
            # ... (código do Painel Principal)
            # Adicione st.write("DEBUG: Subseção X do Painel Principal") antes de cada subseção
            st.subheader("📌 Instruções Gerais") # Exemplo
            st.write("DEBUG: Instruções Gerais (Cliente) renderizadas.")
            # ...

        elif st.session_state.cliente_page == "Novo Diagnóstico":
            st.write("DEBUG: Renderizando Novo Diagnóstico (Cliente).")
            # ... (código do Novo Diagnóstico)
            # Adicione st.write("DEBUG: Carregando perguntas para Novo Diagnóstico") antes de ler o CSV
            # E st.write("DEBUG: Loop de categorias do formulário iniciado") etc.
            st.subheader("📋 Formulário de Novo Diagnóstico") # Exemplo
            st.write("DEBUG: Formulário de Novo Diagnóstico (Cliente) - Cabeçalho renderizado.")
            # ...

    except Exception as e_cliente_area_d:
        st.error(f"Ocorreu um erro na área do cliente: {e_cliente_area_d}")
        st.exception(e_cliente_area_d) 


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    st.write("DEBUG: Entrou na área do Administrador Logado.")
    try: 
        st.sidebar.image("https://raw.githubusercontent.com/AndersonCRMG/AppDiagnostico/main/Logo%20Transparente%20(1).png", width=100)
        st.sidebar.success("🟢 Admin Logado")
        st.write("DEBUG: Sidebar do Admin - Imagem e status Logado renderizados.")

        if st.sidebar.button("🚪 Sair do Painel Admin"):
            st.write("DEBUG: Botão Sair (Admin) pressionado.")
            st.session_state.admin_logado = False
            st.experimental_rerun() # Ou st.rerun() se preferir consistência

        menu_admin_main_view_d = st.sidebar.selectbox( 
            "Funcionalidades Admin:",
            ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Perguntas", 
             "Gerenciar Clientes", "Gerenciar Administradores"],
            key="admin_menu_selectbox_main_page_view_debug_v2" 
        )
        st.write(f"DEBUG: Sidebar do Admin - Selectbox renderizado. Opção: {menu_admin_main_view_d}")
        st.header(f"🔑 Painel Admin: {menu_admin_main_view_d}")
        st.write("DEBUG: Cabeçalho do Painel Admin renderizado.")

        if menu_admin_main_view_d == "Visão Geral e Diagnósticos":
            st.write("DEBUG: Renderizando Visão Geral e Diagnósticos (Admin).")
            # ... (código da Visão Geral e Diagnósticos, adicione mais DEBUG prints internos)
            st.subheader("📊 Visão Geral dos Diagnósticos") # Exemplo
            st.write("DEBUG: Visão Geral (Admin) - Subheader renderizado.")
            # ...
        
        # Adicione st.write("DEBUG: Renderizando Seção X (Admin)") para as outras seções
        elif menu_admin_main_view_d == "Histórico de Usuários":
            st.write("DEBUG: Renderizando Histórico de Usuários (Admin).")
            # ...
        elif menu_admin_main_view_d == "Gerenciar Perguntas":
            st.write("DEBUG: Renderizando Gerenciar Perguntas (Admin).")
            # ...
        elif menu_admin_main_view_d == "Gerenciar Clientes":
            st.write("DEBUG: Renderizando Gerenciar Clientes (Admin).")
            # ...
        elif menu_admin_main_view_d == "Gerenciar Administradores":
            st.write("DEBUG: Renderizando Gerenciar Administradores (Admin).")
            # ...

    except Exception as e_admin_area_d:
        st.error(f"Ocorreu um erro na área administrativa: {e_admin_area_d}")
        st.exception(e_admin_area_d)


if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.write("DEBUG: Fim do script, estado de login não definido para exibir conteúdo principal.")
    st.stop()

st.write(f"DEBUG: Fim do script. Estado admin_logado: {st.session_state.admin_logado}, cliente_logado: {st.session_state.cliente_logado}, aba: {aba if 'aba' in locals() else 'Não definida'}")