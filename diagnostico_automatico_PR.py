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

# !!!!! PASSO DE DEPURAÇÃO CRUCIAL !!!!!
# !!!!! O BLOCO DE CSS ABAIXO ESTÁ INTENCIONALMENTE COMENTADO PARA ESTE TESTE. !!!!!
# !!!!! POR FAVOR, EXECUTE O CÓDIGO DESTA FORMA PRIMEIRO. !!!!!
# !!!!! SE O CONTEÚDO DO ADMIN APARECER, O PROBLEMA É O SEU CSS. !!!!!
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
ST_KEY_VERSION = "v28_final_css_test" 

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "confirmou_instrucoes_checkbox_cliente": False,
    "admin_user_login_identifier": None, "last_cnpj_input": "" 
} 
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias ---
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
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Mensagem", "DataHora", "Lida"]

def inicializar_csv(filepath, columns, defaults=None):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if defaults:
                for col, default_val in defaults.items():
                    if col in columns: df_init[col] = default_val
            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else:
            try:
                df_check = pd.read_csv(filepath, encoding='utf-8', nrows=0) 
                dtype_map_read = {}
                if filepath == usuarios_csv or filepath == usuarios_bloqueados_csv or filepath == arquivo_csv or filepath == historico_csv:
                    if 'CNPJ' in columns: dtype_map_read['CNPJ'] = str
                if filepath == notificacoes_csv:
                    if 'CNPJ_Cliente' in columns: dtype_map_read['CNPJ_Cliente'] = str
                
                temp_df_to_save = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_map_read if dtype_map_read else None)
                col_missing = False

                for col_idx, col_name in enumerate(columns):
                    if col_name not in df_check.columns:
                        default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                        if pd.api.types.is_numeric_dtype(default_val) and defaults and not pd.isna(default_val):
                             temp_df_to_save.insert(loc=min(col_idx, len(temp_df_to_save.columns)), column=col_name, value=pd.Series([default_val] * len(temp_df_to_save), dtype=type(default_val)))
                        else:
                             temp_df_to_save.insert(loc=min(col_idx, len(temp_df_to_save.columns)), column=col_name, value=default_val)
                        col_missing = True
                if col_missing:
                    temp_df_to_save.to_csv(filepath, index=False, encoding='utf-8')
            except pd.errors.EmptyDataError: 
                df_init = pd.DataFrame(columns=columns)
                if defaults:
                    for col, default_val in defaults.items():
                        if col in columns: df_init[col] = default_val
                df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erro Crítico ao inicializar ou ler o arquivo {filepath}: {e}")

try:
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    if not (os.path.exists(admin_credenciais_csv) and os.path.getsize(admin_credenciais_csv) > 0):
        pd.DataFrame([{"Usuario": "admin", "Senha": "admin"}]).to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
        st.sidebar.info("Admin padrão (admin/admin) criado para primeiro uso.")

    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios, defaults={"ConfirmouInstrucoesParaSlotAtual": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0, "LiberacoesExtrasConcedidas": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"]) 
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos) 
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False}) 
    if not os.path.exists(instrucoes_txt_file):
        with open(instrucoes_txt_file, "w", encoding="utf-8") as f:
            f.write("""**Bem-vindo ao Portal de Diagnóstico Empresarial!** (Conteúdo padrão das instruções)""")
except Exception as e_init_global:
    st.error(f"⚠️ ERRO CRÍTICO NA INICIALIZAÇÃO GLOBAL DE ARQUIVOS: {e_init_global}")
    st.exception(e_init_global); st.stop() 

# --- Funções Utilitárias Completas ---
def criar_notificacao(cnpj_cliente, mensagem, data_diag_ref=None):
    try:
        df_notificacoes = pd.DataFrame(columns=colunas_base_notificacoes)
        if os.path.exists(notificacoes_csv) and os.path.getsize(notificacoes_csv) > 0:
            df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
        
        msg_final = mensagem
        if data_diag_ref:
            msg_final = f"O consultor adicionou comentários ao seu diagnóstico de {data_diag_ref}."
        nova_notificacao = {"ID_Notificacao": str(uuid.uuid4()), "CNPJ_Cliente": str(cnpj_cliente), "Mensagem": msg_final, "DataHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Lida": False}
        df_notificacoes = pd.concat([df_notificacoes, pd.DataFrame([nova_notificacao])], ignore_index=True)
        df_notificacoes.to_csv(notificacoes_csv, index=False, encoding='utf-8')
    except Exception as e: st.warning(f"Falha ao criar notificação: {e}")

def get_unread_notifications_count(cnpj_cliente):
    try:
        if os.path.exists(notificacoes_csv) and os.path.getsize(notificacoes_csv) > 0:
            df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
            unread_count = len(df_notificacoes[(df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente)) & (df_notificacoes['Lida'] == False)])
            return unread_count
    except Exception as e: st.warning(f"Falha ao ler notificações: {e}")
    return 0

def marcar_notificacoes_como_lidas(cnpj_cliente, ids_notificacoes=None):
    try:
        if os.path.exists(notificacoes_csv) and os.path.getsize(notificacoes_csv) > 0:
            df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
            if ids_notificacoes:
                df_notificacoes.loc[(df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente)) & (df_notificacoes['ID_Notificacao'].isin(ids_notificacoes)), 'Lida'] = True
            else:
                df_notificacoes.loc[df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente), 'Lida'] = True
            df_notificacoes.to_csv(notificacoes_csv, index=False, encoding='utf-8')
            return True
    except Exception as e: st.error(f"Erro ao marcar notificações como lidas: {e}"); 
    return False

def registrar_acao(cnpj, acao, desc):
    try:
        df_hist = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
        if os.path.exists(historico_csv) and os.path.getsize(historico_csv) > 0:
            df_hist = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
        
        new_entry = pd.DataFrame([{"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                   "CNPJ": str(cnpj), "Ação": str(acao), "Descrição": str(desc)}])
        df_hist = pd.concat([df_hist, new_entry], ignore_index=True)
        df_hist.to_csv(historico_csv, index=False, encoding='utf-8')
    except Exception as e: st.warning(f"Falha ao registrar ação no histórico: {e}")


def update_user_data(cnpj, field, value):
    try:
        if not (os.path.exists(usuarios_csv) and os.path.getsize(usuarios_csv) > 0) :
            st.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado para atualização."); return False
        users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        idx = users_df[users_df['CNPJ'] == str(cnpj)].index
        if not idx.empty:
            users_df.loc[idx, field] = value
            users_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
            # Atualizar st.session_state.user se o usuário logado for o afetado
            if 'user' in st.session_state and st.session_state.user and str(st.session_state.user.get('CNPJ')) == str(cnpj):
                if field in ["DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "LiberacoesExtrasConcedidas"] and value is not None:
                    try: st.session_state.user[field] = int(value)
                    except ValueError: st.warning(f"Valor inválido '{value}' para campo numérico '{field}' ao atualizar session_state.")
                elif field == "ConfirmouInstrucoesParaSlotAtual":
                    st.session_state.user[field] = str(value).lower() == "true"
                else:
                    st.session_state.user[field] = value
            return True
        else:
            st.warning(f"Usuário com CNPJ {cnpj} não encontrado para atualização.")
    except Exception as e: st.error(f"Erro ao atualizar usuário ({field}): {e}")
    return False

@st.cache_data
def carregar_analises_perguntas():
    try: 
        if os.path.exists(analises_perguntas_csv) and os.path.getsize(analises_perguntas_csv) > 0:
            return pd.read_csv(analises_perguntas_csv, encoding='utf-8')
    except Exception as e: st.warning(f"Erro ao carregar análises: {e}")
    return pd.DataFrame(columns=colunas_base_analises)

def obter_analise_para_resposta(pergunta_texto, resposta_valor, df_analises):
    if df_analises is None or df_analises.empty: return None
    # ... (sua lógica completa aqui)
    return None

# --- Funções PDF (Use as versões que você confirmou que funcionam) ---
def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    # (Use sua versão funcional desta função)
    st.info("gerar_pdf_diagnostico_completo (placeholder - Restaure sua lógica)")
    return None 
def gerar_pdf_historico(df_historico_filtrado, titulo="Histórico de Ações"):
    # (Use a versão desta função que você confirmou que o PDF estava OK)
    st.info(f"Gerando PDF do Histórico (placeholder): {titulo}")
    return "dummy_historico.pdf" # Placeholder
# --- FIM DAS FUNÇÕES PDF ---


# --- Lógica de Login e Navegação Principal ---
# ... (código de seleção de aba mantido como antes)
if not st.session_state.get("admin_logado", False) and not st.session_state.get("cliente_logado", False):
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key=f"tipo_usuario_radio_{ST_KEY_VERSION}") 
elif st.session_state.get("admin_logado", False): 
    aba = "Administrador"
else: 
    aba = "Cliente"
st.sidebar.write(f"DEBUG (após radio): aba='{aba}'")


# --- ÁREA DE LOGIN DO ADMINISTRADOR (RESTAURADA) ---
if aba == "Administrador" and not st.session_state.get("admin_logado", False):
    # (Mantenha o CSS do login-container COMENTADO no st.markdown principal para este teste)
    st.markdown('<div>', unsafe_allow_html=True) 
    st.markdown(f'<h2>Login Administrador 🔑</h2>', unsafe_allow_html=True)
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
                else: st.error(f"Arquivo de credenciais '{admin_credenciais_csv}' não encontrado ou vazio.")
            except Exception as e: st.error(f"Erro no login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DE LOGIN DO CLIENTE (RESTAURADA) ---
if aba == "Cliente" and not st.session_state.get("cliente_logado", False):
    st.markdown('<div>', unsafe_allow_html=True) 
    st.markdown(f'<h2>Login Cliente 🏢</h2>', unsafe_allow_html=True)
    with st.form(f"form_cliente_login_{ST_KEY_VERSION}"): 
        c = st.text_input("CNPJ", key=f"cli_c_{ST_KEY_VERSION}", value=st.session_state.get("last_cnpj_input","")) 
        s = st.text_input("Senha", type="password", key=f"cli_s_{ST_KEY_VERSION}") 
        if st.form_submit_button("Entrar Cliente"):
            st.session_state.last_cnpj_input = c
            try:
                if not (os.path.exists(usuarios_csv) and os.path.getsize(usuarios_csv) > 0):
                    st.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado ou vazio. Contate o administrador.")
                    st.stop()
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                # ... (resto da sua lógica de login cliente validada) ...
                match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == str(s))]
                if match.empty: st.error("CNPJ ou senha inválidos."); st.stop()
                st.session_state.cliente_logado = True; st.session_state.cnpj = c
                st.session_state.user = match.iloc[0].to_dict()
                # ... (resto da configuração do st.session_state.user) ...
                st.success("Login cliente OK! ✅"); st.rerun()
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()


# --- ÁREA DO CLIENTE LOGADO (RESTAURADA - SUBSTITUA PELO SEU CÓDIGO COMPLETO) ---
if aba == "Cliente" and st.session_state.get("cliente_logado", False):
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.get('user',{}).get('Empresa','Cliente')}! 👋") 
    if st.sidebar.button(f"Sair Cliente", key=f"logout_cliente_{ST_KEY_VERSION}"):
        st.session_state.cliente_logado = False
        # Limpe st.session_state.user, st.session_state.cnpj, etc.
        st.rerun()
    
    st.header(f"Painel Cliente: {st.session_state.get('cliente_page', 'Página Desconhecida')}")
    st.markdown("Substitua este placeholder pelo conteúdo real da área do cliente, incluindo o menu de páginas do cliente e a lógica de cada página.")
    # Exemplo:
    # if st.session_state.cliente_page == "Instruções":
    #     st.write("Conteúdo das Instruções aqui...")
    # elif st.session_state.cliente_page == "Novo Diagnóstico":
    #     st.write("Conteúdo do Novo Diagnóstico aqui...")


# --- ÁREA DO ADMINISTRADOR LOGADO (COM HISTÓRICO RESTAURADO E OUTROS PLACEHOLDERS) ---
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
        st.sidebar.info(f"[DEBUG Sidebar] Opção: '{menu_admin}'")
        
        admin_page_title_prefix = menu_admin.split(' ')[0] if isinstance(menu_admin, str) and menu_admin else "Admin"
        st.header(f"Painel Admin: {admin_page_title_prefix}")
        st.write(f"[DEBUG Main Panel] Renderizando: {menu_admin}")

        if menu_admin == "📊 Visão Geral e Diagnósticos":
            st.subheader("📊 Visão Geral e Diagnósticos")
            st.markdown("CONTEÚDO DE TESTE VISÍVEL: Visão Geral e Diagnósticos.")
            
        elif menu_admin == "🚦 Status dos Clientes":
            st.subheader("🚦 Status dos Clientes")
            st.markdown("CONTEÚDO DE TESTE VISÍVEL: Status dos Clientes.")

        elif menu_admin == "📜 Histórico de Usuários":
            st.subheader("📜 Histórico de Usuários")
            st.markdown("CONTEÚDO DE TESTE VISÍVEL: Histórico de Usuários.") # Placeholder inicial
            
            # Carregamento de dados DENTRO da seção específica
            df_historico_completo_hu = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
            df_usuarios_para_filtro_hu = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato'])
            try:
                if os.path.exists(historico_csv) and os.path.getsize(historico_csv) > 0:
                    df_historico_completo_hu = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
                
                if os.path.exists(usuarios_csv) and os.path.getsize(usuarios_csv) > 0: 
                    df_usuarios_para_filtro_hu = pd.read_csv(usuarios_csv, encoding='utf-8', usecols=['CNPJ', 'Empresa', 'NomeContato'], dtype={'CNPJ': str})

            except Exception as e_hu_load: 
                st.error(f"Erro ao carregar dados para Histórico: {e_hu_load}")
            
            if not (df_historico_completo_hu.empty and df_usuarios_para_filtro_hu.empty):
                st.markdown("#### Filtros do Histórico")
                col_hu_f1, col_hu_f2 = st.columns(2)
                empresas_hist_list_hu = ["Todas"]
                if not df_usuarios_para_filtro_hu.empty and 'Empresa' in df_usuarios_para_filtro_hu.columns: 
                    empresas_hist_list_hu.extend(sorted(df_usuarios_para_filtro_hu['Empresa'].astype(str).unique().tolist()))
                
                emp_sel_hu = col_hu_f1.selectbox("Filtrar por Empresa:", empresas_hist_list_hu, key=f"hist_emp_sel_{ST_KEY_VERSION}_hu_adm")
                termo_busca_hu = col_hu_f2.text_input("Buscar em Descrição, Ação ou CNPJ:", key=f"hist_termo_busca_{ST_KEY_VERSION}_hu_adm")
                
                df_historico_filtrado_view_hu = df_historico_completo_hu.copy() 
                cnpjs_da_empresa_selecionada_hu = []

                if emp_sel_hu != "Todas" and not df_usuarios_para_filtro_hu.empty: 
                    cnpjs_da_empresa_selecionada_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['Empresa'] == emp_sel_hu]['CNPJ'].tolist()
                    if not df_historico_filtrado_view_hu.empty:
                        df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_da_empresa_selecionada_hu)]
                
                if termo_busca_hu.strip() and not df_historico_filtrado_view_hu.empty :
                    busca_lower_hu = termo_busca_hu.strip().lower()
                    df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[
                        df_historico_filtrado_view_hu['CNPJ'].astype(str).str.lower().str.contains(busca_lower_hu, na=False) | 
                        df_historico_filtrado_view_hu['Ação'].astype(str).str.lower().str.contains(busca_lower_hu, na=False) | 
                        df_historico_filtrado_view_hu['Descrição'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)
                    ]
                
                st.markdown("#### Registros do Histórico")
                if not df_historico_filtrado_view_hu.empty:
                    st.dataframe(df_historico_filtrado_view_hu.sort_values(by="Data", ascending=False))
                    if st.button("📄 Baixar Histórico Filtrado (PDF)", key=f"download_hist_filtrado_pdf_{ST_KEY_VERSION}_hu_adm"):
                        # (A função gerar_pdf_historico deve estar completa e funcional)
                        pdf_path_hist = gerar_pdf_historico(df_historico_filtrado_view_hu, f"Histórico - {emp_sel_hu}")
                        if pdf_path_hist and os.path.exists(pdf_path_hist): # Checar se o path é válido
                            with open(pdf_path_hist, "rb") as f_pdf_hist: 
                                st.download_button(label="Download PDF Confirmado", data=f_pdf_hist, file_name=f"historico_{sanitize_column_name(emp_sel_hu)}.pdf", mime="application/pdf", key=f"confirm_download_hist_pdf_{ST_KEY_VERSION}_hu_adm")
                            try: os.remove(pdf_path_hist) 
                            except: pass
                        else:
                             st.error("Falha ao gerar ou encontrar o PDF do histórico.")
                
                    if emp_sel_hu != "Todas" and not df_historico_filtrado_view_hu.empty and cnpjs_da_empresa_selecionada_hu:
                        st.markdown("---")
                        st.markdown(f"#### 🗑️ Resetar Histórico da Empresa: {emp_sel_hu}")
                        with st.expander(f"⚠️ ATENÇÃO: Excluir TODO o histórico da Empresa '{emp_sel_hu}'"):
                            st.warning(f"Esta ação é irreversível...") # Texto completo da warning aqui
                            confirm_text_delete_hist = st.text_input(f"Para confirmar, digite '{emp_sel_hu}':", key=f"confirm_text_delete_hist_emp_{emp_sel_hu}_{ST_KEY_VERSION}").strip()
                            if st.button(f"🗑️ Excluir Histórico de '{emp_sel_hu}' AGORA", type="primary", key=f"btn_delete_hist_emp_{emp_sel_hu}_{ST_KEY_VERSION}", disabled=(confirm_text_delete_hist != emp_sel_hu)):
                                # (Lógica de exclusão como antes)
                                st.info("Lógica de exclusão de histórico aqui.")
                else:
                    st.info("Nenhum registro de histórico encontrado para os filtros aplicados.")
            else:
                st.info("Arquivos de histórico ou usuários não encontrados ou vazios. Verifique a inicialização.")


        elif menu_admin == "📝 Gerenciar Perguntas":
            st.subheader("📝 Gerenciar Perguntas")
            st.markdown("CONTEÚDO DE TESTE VISÍVEL: Gerenciar Perguntas.")
        # ... (adicione placeholders para TODAS as outras opções de menu_admin_options)
        else:
            st.warning(f"[DEBUG ADMIN Main Panel] Opção de menu '{menu_admin}' não correspondeu a nenhum bloco if/elif.")
        
        st.write(f"[DEBUG ADMIN Main Panel] PONTO MP4 - Após dispatch do menu")

    except Exception as e_outer_admin_critical:
        st.error(f"Um erro crítico ocorreu na área administrativa: {e_outer_admin_critical}")
        st.exception(e_outer_admin_critical)

if not st.session_state.get("admin_logado", False) and not st.session_state.get("cliente_logado", False) and ('aba' not in locals() or aba is None):
    st.info("Fallback final: Selecione se você é Administrador ou Cliente para continuar.")