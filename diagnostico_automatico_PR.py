import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import time
from fpdf import FPDF 
import tempfile
import re
import json
import plotly.express as px
import plotly.graph_objects as go 
import uuid

st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", initial_sidebar_state="expanded")

# !!!!! PASSO DE DEPURAÇÃO MAIS IMPORTANTE !!!!!
# !!!!! O BLOCO DE CSS ABAIXO ESTÁ COMENTADO. !!!!!
# !!!!! TESTE O APLICATIVO COM ELE COMENTADO. !!!!!
# !!!!! SE O CONTEÚDO APARECER, O PROBLEMA É O SEU CSS. !!!!!
"""
st.markdown(f\""" 
<style>
{'''
.login-container { max-width: 400px; margin: 60px auto 0 auto; padding: 40px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-family: 'Segoe UI', sans-serif; }
.login-container h2 { text-align: center; margin-bottom: 30px; font-weight: 600; font-size: 26px; color: #2563eb; }
.stButton>button { border-radius: 6px; background-color: #2563eb; color: white; font-weight: 500; padding: 0.5rem 1.2rem; margin-top: 0.5rem; }
.stDownloadButton>button { background-color: #10b981; color: white; font-weight: 600; border-radius: 6px; margin-top: 10px; padding: 0.5rem 1.2rem; }
.stTextInput>div>input, .stTextArea>div>textarea { border-radius: 6px; padding: 0.4rem; border: 1px solid #d1d5db; background-color: #f9fafb; }
.stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; padding: 10px 20px; }
.custom-card { border: 1px solid #e0e0e0; border-left: 5px solid #2563eb; padding: 15px; margin-bottom: 15px; border-radius: 5px; background-color: #f9f9f9; }
.custom-card h4 { margin-top: 0; color: #2563eb; }
.feedback-saved { font-size: 0.85em; color: green; font-style: italic; margin-top: -8px; margin-bottom: 8px; }
.analise-pergunta-cliente { font-size: 0.9em; color: #555; background-color: #f0f8ff; border-left: 3px solid #1e90ff; padding: 8px; margin-top: 5px; margin-bottom:10px; border-radius: 3px;}
.notification-dot { height: 8px; width: 8px; background-color: red; border-radius: 50%; display: inline-block; margin-left: 5px; }
.kpi-card { background-color: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; text-align: center; margin-bottom: 10px; }
.kpi-card h4 { font-size: 1.1em; color: #333; margin-bottom: 5px; }
.kpi-card .value { font-size: 1.8em; font-weight: bold; color: #2563eb; }
'''}
</style>
\""", unsafe_allow_html=True)
"""

st.title("🔒 Portal de Diagnóstico")

# --- Configurações de Arquivos ---
admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv"
historico_csv = "historico_clientes.csv"
analises_perguntas_csv = "analises_perguntas.csv"
notificacoes_csv = "notificacoes.csv"
instrucoes_txt_file = "instrucoes_clientes.txt"
LOGOS_DIR = "client_logos"
ST_KEY_VERSION = "v26_css_test" # Chave atualizada

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "admin_user_login_identifier": None, "last_cnpj_input": "" 
} # Removido outras chaves não essenciais para este teste
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias (Simples Placeholders para este teste) ---
def sanitize_column_name(name): return str(name).replace(" ","_") 
def pdf_safe_text_output(text): return str(text)
def inicializar_csv(filepath, columns, defaults=None):
    if not os.path.exists(filepath):
        pd.DataFrame(columns=columns).to_csv(filepath, index=False, encoding='utf-8')
        # st.sidebar.warning(f"Arquivo {filepath} criado.") # DEBUG
# --- Fim das Funções Utilitárias Simplificadas ---

try:
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    # ... (inicialize outros CSVs essenciais para login se necessário) ...
    if not (os.path.exists(admin_credenciais_csv) and os.path.getsize(admin_credenciais_csv) > 0):
        # Criar admin padrão se não existir, para facilitar o teste
        pd.DataFrame([{"Usuario": "admin", "Senha": "admin"}]).to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
        st.sidebar.info("Admin padrão (admin/admin) criado para teste.")

except Exception as e_init:
    st.error(f"Erro fatal na inicialização dos arquivos CSV: {e_init}")
    st.exception(e_init); st.stop()

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): 
    st.session_state.trigger_rerun_global = False; st.rerun()

st.sidebar.write(f"DEBUG (antes radio): admin_logado={st.session_state.get('admin_logado', False)}, cliente_logado={st.session_state.get('cliente_logado', False)}")

if not st.session_state.get("admin_logado", False) and not st.session_state.get("cliente_logado", False):
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key=f"tipo_usuario_radio_{ST_KEY_VERSION}") 
elif st.session_state.get("admin_logado", False): 
    aba = "Administrador"
else: 
    aba = "Cliente"
st.sidebar.write(f"DEBUG (após radio): aba='{aba}'")

# --- ÁREA DE LOGIN DO ADMINISTRADOR (Usando lógica CSV) ---
if aba == "Administrador" and not st.session_state.get("admin_logado", False):
    st.markdown('<div class="login-container">', unsafe_allow_html=True) # Ainda pode ser afetado por CSS se não comentado
    st.markdown(f'<h2 class="login-title">Login Administrador 🔑</h2>', unsafe_allow_html=True)
    with st.form(f"form_admin_login_{ST_KEY_VERSION}"): 
        u = st.text_input("Usuário", key=f"admin_u_{ST_KEY_VERSION}")
        p = st.text_input("Senha", type="password", key=f"admin_p_{ST_KEY_VERSION}") 
        if st.form_submit_button("Entrar"):
            try:
                if os.path.exists(admin_credenciais_csv) and os.path.getsize(admin_credenciais_csv) > 0:
                    df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                    admin_encontrado = df_creds[df_creds["Usuario"] == u]
                    if not admin_encontrado.empty and str(admin_encontrado.iloc[0]["Senha"]) == str(p):
                        st.session_state.admin_logado = True
                        st.session_state.admin_user_login_identifier = u 
                        st.success("Login de administrador bem-sucedido! ✅"); st.rerun()
                    else: st.error("Usuário ou senha inválidos.")
                else:
                     st.error(f"Arquivo de credenciais '{admin_credenciais_csv}' não encontrado ou vazio.")
            except Exception as e: st.error(f"Erro no login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DE LOGIN DO CLIENTE (Placeholder) ---
if aba == "Cliente" and not st.session_state.get("cliente_logado", False):
    st.markdown("Área de Login Cliente Placeholder") 
    st.stop()

# --- ÁREA DO CLIENTE LOGADO (Placeholder) ---
if aba == "Cliente" and st.session_state.get("cliente_logado", False):
    st.header(f"Painel Cliente Placeholder")
    st.markdown("Conteúdo da área do cliente placeholder...")
    if st.sidebar.button(f"Logout Cliente_{ST_KEY_VERSION}"):
        st.session_state.cliente_logado = False; st.rerun()


# --- ÁREA DO ADMINISTRADOR LOGADO (FOCO NA RENDERIZAÇÃO BÁSICA) ---
if aba == "Administrador" and st.session_state.get("admin_logado", False):
    st.sidebar.write(f"[DEBUG ADMIN] PONTO S1 - Entrou no bloco admin_logado.") 
    try:
        st.sidebar.success("🟢 Admin Logado")
        if st.sidebar.button(f"🚪 Sair do Painel Admin", key=f"logout_admin_{ST_KEY_VERSION}_adm"): 
            st.session_state.admin_logado = False
            if 'admin_user_login_identifier' in st.session_state:
                del st.session_state.admin_user_login_identifier
            st.rerun() 
        
        menu_admin_options = [
            "📊 Visão Geral e Diagnósticos", "🚦 Status dos Clientes", "📜 Histórico de Usuários",
            "📝 Gerenciar Perguntas", "💡 Gerenciar Análises de Perguntas",
            "✍️ Gerenciar Instruções Clientes", "👥 Gerenciar Clientes", 
            "👮 Gerenciar Administradores", "💾 Backup de Dados"
        ]
        menu_admin = st.sidebar.selectbox(
            "Funcionalidades Admin:", 
            menu_admin_options, 
            key=f"admin_menu_selectbox_{ST_KEY_VERSION}_adm" 
        )
        st.sidebar.info(f"[DEBUG Sidebar] Opção Selecionada: '{menu_admin}'")
        
        # --- Conteúdo Principal (Main Panel) ---
        st.write("[DEBUG Main Panel] PONTO MP0 - IMEDIATAMENTE ANTES DO HEADER") 

        admin_page_title = "Painel Admin (Default Header)" # Default
        if isinstance(menu_admin, str) and menu_admin:
            try:
                admin_page_title = f"Painel Admin: {menu_admin.split(' ')[0]}"
            except IndexError: 
                admin_page_title = f"Painel Admin: {menu_admin}"
        st.header(admin_page_title)
        st.write(f"[DEBUG Main Panel] PONTO MP1 - APÓS Header. Título: '{admin_page_title}'")

        st.write(f"[DEBUG Main Panel] PONTO MP2 - Antes do dispatch. menu_admin = '{menu_admin}'")

        if menu_admin == "📊 Visão Geral e Diagnósticos":
            st.subheader("📊 Visão Geral e Diagnósticos")
            st.markdown("Conteúdo placeholder para Visão Geral e Diagnósticos.")
            
        elif menu_admin == "🚦 Status dos Clientes":
            st.subheader("🚦 Status dos Clientes")
            st.markdown("Conteúdo placeholder para Status dos Clientes.")

        elif menu_admin == "📜 Histórico de Usuários":
            st.subheader("📜 Histórico de Usuários")
            st.markdown("Conteúdo placeholder para Histórico de Usuários.")
            st.markdown("Se esta mensagem aparecer, o dispatch para Histórico está funcionando.")
            if st.button(f"Botão Teste Histórico", key=f"btn_teste_hist_{ST_KEY_VERSION}"):
                st.info("Botão de teste do histórico clicado.")

        elif menu_admin == "📝 Gerenciar Perguntas":
            st.subheader("📝 Gerenciar Perguntas")
            st.markdown("Conteúdo placeholder para Gerenciar Perguntas.")

        elif menu_admin == "💡 Gerenciar Análises de Perguntas":
            st.subheader("💡 Gerenciar Análises de Perguntas")
            st.markdown("Conteúdo placeholder para Gerenciar Análises de Perguntas.")
            
        elif menu_admin == "✍️ Gerenciar Instruções Clientes":
            st.subheader("✍️ Gerenciar Instruções Clientes")
            st.markdown("Conteúdo placeholder para Gerenciar Instruções Clientes.")

        elif menu_admin == "👥 Gerenciar Clientes":
            st.subheader("👥 Gerenciar Clientes")
            st.markdown("Conteúdo placeholder para Gerenciar Clientes.")

        elif menu_admin == "👮 Gerenciar Administradores":
            st.subheader("👮 Gerenciar Administradores")
            st.markdown("Conteúdo placeholder para Gerenciar Administradores.")

        elif menu_admin == "💾 Backup de Dados":
            st.subheader("💾 Backup de Dados")
            st.markdown("Conteúdo placeholder para Backup de Dados.")
        
        else:
            st.warning(f"[DEBUG Main Panel] Opção de menu '{menu_admin}' não corresponde a nenhum bloco if/elif.")
        
        st.write(f"[DEBUG Main Panel] PONTO MP3 - Após dispatch do menu") # Renomeado para MP3

    except Exception as e_outer_admin_critical:
        st.error(f"Um erro crítico ocorreu na área administrativa: {e_outer_admin_critical}")
        st.exception(e_outer_admin_critical)
        st.write(f"[DEBUG Main Panel] PONTO MP_EXCEPT - Dentro do except e_outer_admin_critical ({e_outer_admin_critical})") 

if not st.session_state.get("admin_logado", False) and not st.session_state.get("cliente_logado", False) and ('aba' not in locals() or aba is None): # Verificação mais robusta para aba
    st.info("Fallback final: Selecione se você é Administrador ou Cliente para continuar.")