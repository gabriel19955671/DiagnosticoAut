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

# CSS (Mantido como antes)
st.markdown("""
<style>
.login-container { max-width: 400px; margin: 60px auto 0 auto; padding: 40px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-family: 'Segoe UI', sans-serif; }
.login-container h2 { text-align: center; margin-bottom: 30px; font-weight: 600; font-size: 26px; color: #2563eb; }
/* ... (resto do CSS omitido para brevidade, mantenha o seu CSS original) ... */
.kpi-card .value { font-size: 1.8em; font-weight: bold; color: #2563eb; }
</style>
""", unsafe_allow_html=True)

st.title("🔒 Portal de Diagnóstico")

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
ST_KEY_VERSION = "v24_debug" # Chave atualizada para depuração

default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "confirmou_instrucoes_checkbox_cliente": False,
    "admin_user_login_identifier": None,
    "last_cnpj_input": "" # Adicionado para persistir o último CNPJ
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_'); s = re.sub(r'(?u)[^-\w.]', '', s); return s
def pdf_safe_text_output(text): 
    return str(text).encode('latin-1', 'replace').decode('latin-1')
def find_client_logo_path(cnpj_arg):
    if not cnpj_arg: return None
    base = str(cnpj_arg).replace('/', '').replace('.', '').replace('-', '')
    for ext in ["png", "jpg", "jpeg"]:
        path = os.path.join(LOGOS_DIR, f"{base}_logo.{ext}")
        if os.path.exists(path): return path
    return None

if not os.path.exists(LOGOS_DIR):
    try: os.makedirs(LOGOS_DIR)
    except OSError as e: st.error(f"Erro ao criar diretório de logos '{LOGOS_DIR}': {e}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone",
                         "ConfirmouInstrucoesParaSlotAtual", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "LiberacoesExtrasConcedidas"]
# ... (outras colunas base)

def inicializar_csv(filepath, columns, defaults=None):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if defaults:
                for col, default_val in defaults.items():
                    if col in columns: df_init[col] = default_val
            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else:
            # Simplificado para brevidade, a lógica anterior de verificação de colunas pode ser mantida
            pass
    except Exception as e:
        st.error(f"Erro Crítico ao inicializar ou ler o arquivo {filepath}: {e}")
        # Não levantar exceção aqui para permitir que o app tente carregar

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    # ... (outras chamadas inicializar_csv)
    if not os.path.exists(instrucoes_txt_file):
        with open(instrucoes_txt_file, "w", encoding="utf-8") as f:
            f.write("""**Bem-vindo!** (Instruções simplificadas)""")
except Exception as e_init_global:
    st.error(f"⚠️ ERRO CRÍTICO NA INICIALIZAÇÃO GLOBAL DE ARQUIVOS: {e_init_global}")
    st.exception(e_init_global); st.stop() 

# --- Funções PDF (mantidas, mas não serão chamadas nesta versão de depuração do admin) ---
def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    # ... (código da função como corrigido anteriormente)
    st.info("gerar_pdf_diagnostico_completo chamada (placeholder)")
    return None 
def gerar_pdf_historico(df_historico_filtrado, titulo="Histórico de Ações"):
    # ... (código da função como corrigido anteriormente)
    st.info("gerar_pdf_historico chamada (placeholder)")
    return None

# --- Outras Funções Utilitárias (Notificação, Ação, Usuário, Análise) - OMITIDAS POR BREVIDADE ---
# Mantenha suas funções aqui. Elas não são o foco do erro "nada aparece".

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): 
    st.session_state.trigger_rerun_global = False
    st.rerun()

st.sidebar.write(f"DEBUG (antes do radio): admin_logado={st.session_state.get('admin_logado', False)}, cliente_logado={st.session_state.get('cliente_logado', False)}")

if not st.session_state.get("admin_logado", False) and not st.session_state.get("cliente_logado", False):
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key=f"tipo_usuario_radio_{ST_KEY_VERSION}") 
elif st.session_state.get("admin_logado", False): 
    aba = "Administrador"
else: 
    aba = "Cliente"

st.sidebar.write(f"DEBUG (após radio): aba='{aba}'")

# --- ÁREA DE LOGIN DO ADMINISTRADOR ---
if aba == "Administrador" and not st.session_state.get("admin_logado", False):
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador 🔑</h2>', unsafe_allow_html=True)
    with st.form(f"form_admin_login_{ST_KEY_VERSION}"): 
        u = st.text_input("Usuário", key=f"admin_u_{ST_KEY_VERSION}")
        p = st.text_input("Senha", type="password", key=f"admin_p_{ST_KEY_VERSION}") 
        if st.form_submit_button("Entrar"):
            try:
                if os.path.exists(admin_credenciais_csv) and os.path.getsize(admin_credenciais_csv) > 0:
                    df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                    admin_encontrado = df_creds[df_creds["Usuario"] == u]
                    if not admin_encontrado.empty and admin_encontrado.iloc[0]["Senha"] == p:
                        st.session_state.admin_logado = True
                        st.session_state.admin_user_login_identifier = u 
                        st.success("Login de administrador bem-sucedido! ✅"); st.rerun()
                    else: st.error("Usuário ou senha inválidos.")
                else:
                     st.error(f"Arquivo de credenciais '{admin_credenciais_csv}' não encontrado ou vazio.")
            except Exception as e: st.error(f"Erro no login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DE LOGIN DO CLIENTE ---
if aba == "Cliente" and not st.session_state.get("cliente_logado", False):
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente 🏢</h2>', unsafe_allow_html=True)
    # ... (Seu código de login do cliente aqui, com chaves ST_KEY_VERSION)
    st.markdown("Formulário de login do cliente aqui...") # Placeholder
    if st.button("Login Cliente (Placeholder)", key=f"login_cliente_placeholder_{ST_KEY_VERSION}"):
        st.info("Botão de login cliente placeholder clicado.")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.get("cliente_logado", False):
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}! 👋")
    # ... (Resto da sidebar do cliente)
    if st.sidebar.button(f"⬅️ Sair do Portal Cliente", key=f"logout_cliente_{ST_KEY_VERSION}"):
        # ... (lógica de logout do cliente)
        st.session_state.cliente_logado = False
        st.rerun()
    
    st.header(f"Área do Cliente - {st.session_state.get('cliente_page', 'N/A')}")
    st.markdown(f"Conteúdo da página do cliente: **{st.session_state.get('cliente_page', 'N/A')}**")
    st.markdown("--- Conteúdo da área do cliente ---")


# --- ÁREA DO ADMINISTRADOR LOGADO (RADICALMENTE SIMPLIFICADA PARA DEPURAÇÃO) ---
if aba == "Administrador" and st.session_state.get("admin_logado", False):
    st.sidebar.write("[DEBUG ADMIN] Entrou no bloco admin_logado.") 
    try:
        st.sidebar.success("🟢 Admin Logado")
        if st.sidebar.button(f"🚪 Sair do Painel Admin", key=f"logout_admin_{ST_KEY_VERSION}_adm"): 
            st.session_state.admin_logado = False
            if 'admin_user_login_identifier' in st.session_state:
                del st.session_state.admin_user_login_identifier
            st.rerun() 
        
        menu_admin_options = [
            "📊 Visão Geral e Diagnósticos", 
            "🚦 Status dos Clientes", 
            "📜 Histórico de Usuários",
            "📝 Gerenciar Perguntas", 
            "💡 Gerenciar Análises de Perguntas",
            "✍️ Gerenciar Instruções Clientes", 
            "👥 Gerenciar Clientes", 
            "👮 Gerenciar Administradores", 
            "💾 Backup de Dados"
        ]
        menu_admin = st.sidebar.selectbox( # Adicionado key aqui
            "Funcionalidades Admin:", 
            menu_admin_options, 
            key=f"admin_menu_selectbox_{ST_KEY_VERSION}_adm" 
        )
        
        st.sidebar.info(f"[DEBUG ADMIN Sidebar] Opção Selecionada: {menu_admin}")
        
        # Cabeçalho principal da página do admin
        # A linha abaixo pode causar erro se menu_admin for None ou não for string
        if isinstance(menu_admin, str) and menu_admin:
            st.header(f"Painel Admin: {menu_admin.split(' ')[0]}") # Simplificado para evitar erro se split falhar
        else:
            st.header("Painel Admin")
            st.warning("[DEBUG ADMIN] menu_admin não é uma string válida ou está vazio.")

        st.write(f"[DEBUG ADMIN Main Panel] Renderizando seção para: {menu_admin}")

        # Lógica de dispatch do menu admin (SUPER SIMPLIFICADA)
        if menu_admin == "📊 Visão Geral e Diagnósticos":
            st.subheader("📊 Visão Geral e Diagnósticos")
            st.markdown("Conteúdo para Visão Geral e Diagnósticos (em desenvolvimento).")
            
        elif menu_admin == "🚦 Status dos Clientes":
            st.subheader("🚦 Status dos Clientes")
            st.markdown("Conteúdo para Status dos Clientes (em desenvolvimento).")

        elif menu_admin == "📜 Histórico de Usuários":
            st.subheader("📜 Histórico de Usuários")
            st.markdown("Conteúdo para Histórico de Usuários (em desenvolvimento).")
            # O botão de PDF e a lógica de exclusão seriam reintroduzidos aqui gradualmente.
            if st.button("Teste PDF Histórico (Simples)", key=f"pdf_hist_placeholder_btn_{ST_KEY_VERSION}"):
                st.info("Geraria PDF do histórico aqui.")


        elif menu_admin == "📝 Gerenciar Perguntas":
            st.subheader("📝 Gerenciar Perguntas")
            st.markdown("Conteúdo para Gerenciar Perguntas (em desenvolvimento).")

        elif menu_admin == "💡 Gerenciar Análises de Perguntas":
            st.subheader("💡 Gerenciar Análises de Perguntas")
            st.markdown("Conteúdo para Gerenciar Análises de Perguntas (em desenvolvimento).")
            
        elif menu_admin == "✍️ Gerenciar Instruções Clientes":
            st.subheader("✍️ Gerenciar Instruções Clientes")
            st.markdown("Conteúdo para Gerenciar Instruções Clientes (em desenvolvimento).")

        elif menu_admin == "👥 Gerenciar Clientes":
            st.subheader("👥 Gerenciar Clientes")
            st.markdown("Conteúdo para Gerenciar Clientes (em desenvolvimento).")

        elif menu_admin == "👮 Gerenciar Administradores":
            st.subheader("👮 Gerenciar Administradores")
            st.markdown("Conteúdo para Gerenciar Administradores (em desenvolvimento).")

        elif menu_admin == "💾 Backup de Dados":
            st.subheader("💾 Backup de Dados")
            st.markdown("Conteúdo para Backup de Dados (em desenvolvimento).")
        
        else:
            st.warning(f"Opção de menu '{menu_admin}' não implementada ou não reconhecida no dispatch.")

    except Exception as e_outer_admin_critical:
        st.error(f"Um erro crítico ocorreu na área administrativa: {e_outer_admin_critical}")
        st.exception(e_outer_admin_critical) 

if not st.session_state.get("admin_logado", False) and not st.session_state.get("cliente_logado", False) and 'aba' not in locals() :
    # Este bloco só executa se nenhuma das condições de login ou aba foi satisfeita antes,
    # o que pode indicar um problema no fluxo inicial.
    st.info("Selecione se você é Administrador ou Cliente para continuar (Fallback).")