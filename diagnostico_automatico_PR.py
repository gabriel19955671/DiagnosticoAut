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
# !!!!! A LINHA ABAIXO DEVE PERMANECER COMENTADA PARA ESTE TESTE !!!!!
# st.markdown("""
# <style>
# /* SEU CSS PERSONALIZADO COMPLETO IRIA AQUI */
# .login-container { max-width: 400px; } 
# /* ... etc ... */
# </style>
# """, unsafe_allow_html=True)
# !!!!! SE O CONTEÚDO APARECER COM ESTA LINHA COMENTADA, O PROBLEMA É SEU CSS. !!!!!

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
ST_KEY_VERSION = "v26" 

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "confirmou_instrucoes_checkbox_cliente": False,
    "admin_user_login_identifier": None,
    "last_cnpj_input": "" 
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
                col_missing = False
                temp_df_to_save = pd.read_csv(filepath, encoding='utf-8') 

                for col_idx, col_name in enumerate(columns):
                    if col_name not in df_check.columns:
                        default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
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
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios, defaults={"ConfirmouInstrucoesParaSlotAtual": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0, "LiberacoesExtrasConcedidas": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"]) 
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos) 
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False}) 
    if not os.path.exists(instrucoes_txt_file):
        with open(instrucoes_txt_file, "w", encoding="utf-8") as f:
            f.write("""**Bem-vindo ao Portal de Diagnóstico Empresarial!** (Conteúdo padrão)""")
except Exception as e_init_global:
    st.error(f"⚠️ ERRO CRÍTICO NA INICIALIZAÇÃO GLOBAL DE ARQUIVOS: {e_init_global}")
    st.exception(e_init_global); st.stop() 

# --- Funções Utilitárias Restauradas (coloque o corpo completo das suas funções aqui) ---
def criar_notificacao(cnpj_cliente, mensagem, data_diag_ref=None): pass
def get_unread_notifications_count(cnpj_cliente): return 0
def marcar_notificacoes_como_lidas(cnpj_cliente, ids_notificacoes=None): return True
def registrar_acao(cnpj, acao, desc):
    try:
        if os.path.exists(historico_csv) and os.path.getsize(historico_csv) > 0:
            hist_df = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
        else:
            hist_df = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
        new_entry = {"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": str(cnpj), "Ação": str(acao), "Descrição": str(desc)}
        hist_df = pd.concat([hist_df, pd.DataFrame([new_entry])], ignore_index=True)
        hist_df.to_csv(historico_csv, index=False, encoding='utf-8')
    except Exception as e: st.warning(f"Falha ao registrar ação: {e}")

def update_user_data(cnpj, field, value): pass
@st.cache_data
def carregar_analises_perguntas(): return pd.DataFrame(columns=colunas_base_analises)
def obter_analise_para_resposta(pergunta_texto, resposta_valor, df_analises): return None
# --- Funções PDF ---
def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    # (Use a última versão funcional desta função, com txt= e ln em cell())
    st.info("gerar_pdf_diagnostico_completo (placeholder)")
    return None 
def gerar_pdf_historico(df_historico_filtrado, titulo="Histórico de Ações"):
    # (Use a última versão funcional desta função, com txt= e ln em cell(), sem ln em multi_cell)
    st.info("gerar_pdf_historico (placeholder)")
    return None
# --- FIM DAS FUNÇÕES UTILITÁRIAS ---

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): 
    st.session_state.trigger_rerun_global = False
    st.rerun()

st.sidebar.write(f"DEBUG (antes radio): admin_logado={st.session_state.get('admin_logado', False)}, cliente_logado={st.session_state.get('cliente_logado', False)}")

if not st.session_state.get("admin_logado", False) and not st.session_state.get("cliente_logado", False):
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key=f"tipo_usuario_radio_{ST_KEY_VERSION}") 
elif st.session_state.get("admin_logado", False): 
    aba = "Administrador"
else: 
    aba = "Cliente"
st.sidebar.write(f"DEBUG (após radio): aba='{aba}'")

# --- ÁREA DE LOGIN DO ADMINISTRADOR (RESTAURADA) ---
if aba == "Administrador" and not st.session_state.get("admin_logado", False):
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown(f'<h2 class="login-title">Login Administrador 🔑</h2>', unsafe_allow_html=True)
    with st.form(f"form_admin_login_{ST_KEY_VERSION}"): 
        u = st.text_input("Usuário", key=f"admin_u_{ST_KEY_VERSION}")
        p = st.text_input("Senha", type="password", key=f"admin_p_{ST_KEY_VERSION}") 
        if st.form_submit_button("Entrar"):
            try:
                if os.path.exists(admin_credenciais_csv) and os.path.getsize(admin_credenciais_csv) > 0:
                    df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                    admin_encontrado = df_creds[df_creds["Usuario"] == u]
                    if not admin_encontrado.empty and str(admin_encontrado.iloc[0]["Senha"]) == str(p): # Comparar como string
                        st.session_state.admin_logado = True
                        st.session_state.admin_user_login_identifier = u 
                        st.success("Login de administrador bem-sucedido! ✅"); st.rerun()
                    else: st.error("Usuário ou senha inválidos.")
                else:
                     st.error(f"Arquivo de credenciais '{admin_credenciais_csv}' não encontrado ou vazio.")
            except Exception as e: st.error(f"Erro no login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DE LOGIN DO CLIENTE (RESTAURADA) ---
if aba == "Cliente" and not st.session_state.get("cliente_logado", False):
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown(f'<h2 class="login-title">Login Cliente 🏢</h2>', unsafe_allow_html=True)
    with st.form(f"form_cliente_login_{ST_KEY_VERSION}"): 
        c = st.text_input("CNPJ", key=f"cli_c_{ST_KEY_VERSION}", value=st.session_state.get("last_cnpj_input","")) 
        s = st.text_input("Senha", type="password", key=f"cli_s_{ST_KEY_VERSION}") 
        if st.form_submit_button("Entrar"):
            st.session_state.last_cnpj_input = c
            try:
                if not (os.path.exists(usuarios_csv) and os.path.getsize(usuarios_csv) > 0):
                    st.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado ou vazio. Contate o administrador.")
                    st.stop()
                
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                
                cols_to_check_cliente = {
                    "ConfirmouInstrucoesParaSlotAtual": ("False", str), 
                    "DiagnosticosDisponiveis": (1, int),
                    "TotalDiagnosticosRealizados": (0, int),
                    "LiberacoesExtrasConcedidas": (0, int)
                }
                for col_cliente, (default_val_cliente, col_type_cliente) in cols_to_check_cliente.items():
                    if col_cliente not in users_df.columns: users_df[col_cliente] = default_val_cliente
                    if col_type_cliente == int: users_df[col_cliente] = pd.to_numeric(users_df[col_cliente], errors='coerce').fillna(default_val_cliente).astype(int)
                    else: users_df[col_cliente] = users_df[col_cliente].astype(str)

                if not (os.path.exists(usuarios_bloqueados_csv)):
                     st.error(f"Arquivo de usuários bloqueados '{usuarios_bloqueados_csv}' não encontrado."); st.stop()
                blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                
                if c in blocked_df["CNPJ"].values: st.error("CNPJ bloqueado."); st.stop()

                match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == str(s))] # Comparar senha como string
                if match.empty: st.error("CNPJ ou senha inválidos."); st.stop()

                st.session_state.cliente_logado = True; st.session_state.cnpj = c
                st.session_state.user = match.iloc[0].to_dict()
                st.session_state.user["ConfirmouInstrucoesParaSlotAtual"] = str(st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", "False")).lower() == "true"
                st.session_state.user["DiagnosticosDisponiveis"] = int(st.session_state.user.get("DiagnosticosDisponiveis", 1))
                st.session_state.user["TotalDiagnosticosRealizados"] = int(st.session_state.user.get("TotalDiagnosticosRealizados", 0))
                st.session_state.user["LiberacoesExtrasConcedidas"] = int(st.session_state.user.get("LiberacoesExtrasConcedidas", 0))
                st.session_state.inicio_sessao_cliente = time.time()
                registrar_acao(c, "Login", "Usuário logou.")
                pode_fazer_novo_login = st.session_state.user["DiagnosticosDisponiveis"] > st.session_state.user["TotalDiagnosticosRealizados"]
                if pode_fazer_novo_login and not st.session_state.user["ConfirmouInstrucoesParaSlotAtual"]: st.session_state.cliente_page = "Instruções"
                elif pode_fazer_novo_login and st.session_state.user["ConfirmouInstrucoesParaSlotAtual"]: st.session_state.cliente_page = "Novo Diagnóstico"
                else: st.session_state.cliente_page = "Painel Principal"
                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                st.session_state.respostas_atuais_diagnostico = {}; st.session_state.progresso_diagnostico_percentual = 0; st.session_state.progresso_diagnostico_contagem = (0,0); st.session_state.feedbacks_respostas = {}; st.session_state.diagnostico_enviado_sucesso = False; st.session_state.confirmou_instrucoes_checkbox_cliente = False
                st.success("Login cliente OK! ✅"); st.rerun()
            except FileNotFoundError as fnf_e: st.error(f"Erro de configuração: Arquivo {fnf_e.filename} não encontrado.")
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DO CLIENTE LOGADO (ESTRUTURA RESTAURADA) ---
if aba == "Cliente" and st.session_state.get("cliente_logado", False):
    # (COLE SEU CÓDIGO COMPLETO DA ÁREA DO CLIENTE AQUI, COM CHAVES ATUALIZADAS PARA ST_KEY_VERSION)
    # Exemplo mínimo:
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}! 👋")
    if st.sidebar.button(f"Sair Cliente", key=f"logout_cliente_{ST_KEY_VERSION}"):
        st.session_state.cliente_logado = False
        # Limpar dados da sessão do cliente se necessário
        st.rerun()
    st.header(f"Painel Cliente: {st.session_state.get('cliente_page', 'Página Desconhecida')}")
    st.markdown(f"Conteúdo da página do cliente **'{st.session_state.get('cliente_page')}'** aqui.")
    # Certifique-se de ter a lógica do menu do cliente e o conteúdo de cada página aqui.


# --- ÁREA DO ADMINISTRADOR LOGADO (FOCO NA SEÇÃO HISTÓRICO E PLACEHOLDERS) ---
if aba == "Administrador" and st.session_state.get("admin_logado", False):
    st.sidebar.write(f"[DEBUG ADMIN] PONTO S1 - Entrou no bloco admin_logado. Chave Sessão: {ST_KEY_VERSION}") 
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

        # Carregamento de dados gerais DENTRO do try para pegar erros
        df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios) 
        diagnosticos_df_admin_orig_view = pd.DataFrame() 
        admin_data_carregada_view_sucesso = False
        try:
            if os.path.exists(usuarios_csv) and os.path.getsize(usuarios_csv) > 0:
                df_usuarios_admin_geral = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                # Validação de colunas em df_usuarios_admin_geral (opcional, mas bom)
            if os.path.exists(arquivo_csv) and os.path.getsize(arquivo_csv) > 0:
                diagnosticos_df_admin_orig_view = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                if 'Data' in diagnosticos_df_admin_orig_view.columns: 
                    diagnosticos_df_admin_orig_view['Data'] = pd.to_datetime(diagnosticos_df_admin_orig_view['Data'], errors='coerce')
                if not diagnosticos_df_admin_orig_view.empty: 
                    admin_data_carregada_view_sucesso = True
        except Exception as e_data_load_admin:
            st.error(f"Erro ao carregar dados gerais para o painel admin: {e_data_load_admin}")
            # Não usar st.exception() aqui para não parar o script


        if menu_admin == "📊 Visão Geral e Diagnósticos":
            st.subheader("📊 Visão Geral e Diagnósticos")
            st.markdown("Conteúdo para Visão Geral e Diagnósticos (em desenvolvimento).")
            # TODO: Adicionar a lógica real e carregamento de dados específico para esta seção
            
        elif menu_admin == "🚦 Status dos Clientes":
            st.subheader("🚦 Status dos Clientes")
            st.markdown("Conteúdo para Status dos Clientes (em desenvolvimento).")
            # TODO: Adicionar a lógica real e carregamento de dados específico para esta seção

        elif menu_admin == "📜 Histórico de Usuários":
            st.subheader("📜 Histórico de Usuários")
            
            df_historico_completo_hu = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
            df_usuarios_para_filtro_hu = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato'])
            try:
                if os.path.exists(historico_csv) and os.path.getsize(historico_csv) > 0:
                    df_historico_completo_hu = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
                
                if os.path.exists(usuarios_csv) and os.path.getsize(usuarios_csv) > 0:
                    df_usuarios_para_filtro_hu = pd.read_csv(usuarios_csv, encoding='utf-8', usecols=['CNPJ', 'Empresa', 'NomeContato'], dtype={'CNPJ': str})

            except Exception as e_hu_load: 
                st.error(f"Erro ao carregar dados para Histórico: {e_hu_load}")
            
            if df_historico_completo_hu.empty and df_usuarios_para_filtro_hu.empty:
                 st.info("Nenhum dado de histórico ou usuário encontrado para exibir ou filtrar.")
            else:
                st.markdown("#### Filtros do Histórico")
                col_hu_f1, col_hu_f2 = st.columns(2)
                empresas_hist_list_hu = ["Todas"]
                if not df_usuarios_para_filtro_hu.empty and 'Empresa' in df_usuarios_para_filtro_hu.columns: 
                    empresas_hist_list_hu.extend(sorted(df_usuarios_para_filtro_hu['Empresa'].astype(str).unique().tolist()))
                
                emp_sel_hu = col_hu_f1.selectbox("Filtrar por Empresa:", empresas_hist_list_hu, key=f"hist_emp_sel_{ST_KEY_VERSION}_hu_adm")
                termo_busca_hu = col_hu_f2.text_input("Buscar por Nome do Contato, CNPJ, Ação ou Descrição:", key=f"hist_termo_busca_{ST_KEY_VERSION}_hu_adm")
                
                df_historico_filtrado_view_hu = df_historico_completo_hu.copy() 
                cnpjs_da_empresa_selecionada_hu = []

                if emp_sel_hu != "Todas" and not df_usuarios_para_filtro_hu.empty: 
                    cnpjs_da_empresa_selecionada_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['Empresa'] == emp_sel_hu]['CNPJ'].tolist()
                    if not df_historico_filtrado_view_hu.empty:
                        df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_da_empresa_selecionada_hu)]
                
                if termo_busca_hu.strip() and not df_historico_filtrado_view_hu.empty :
                    busca_lower_hu = termo_busca_hu.strip().lower()
                    # ... (lógica de busca como antes) ...
                
                st.markdown("#### Registros do Histórico")
                if not df_historico_filtrado_view_hu.empty:
                    st.dataframe(df_historico_filtrado_view_hu.sort_values(by="Data", ascending=False))
                    if st.button("📄 Baixar Histórico Filtrado (PDF)", key=f"download_hist_filtrado_pdf_{ST_KEY_VERSION}_hu_adm"):
                        # ... (lógica de download do PDF como antes) ...
                        pass # Omitido para brevidade
                    
                    if emp_sel_hu != "Todas" and not df_historico_filtrado_view_hu.empty and cnpjs_da_empresa_selecionada_hu:
                        # ... (lógica de exclusão de histórico como antes) ...
                        pass # Omitido para brevidade
                else:
                    st.info("Nenhum registro de histórico encontrado para os filtros aplicados.")

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
            st.warning(f"[DEBUG ADMIN Main Panel] Opção de menu '{menu_admin}' não corresponde a nenhum bloco if/elif.")
        
        st.write(f"[DEBUG ADMIN Main Panel] PONTO MP4 - Após dispatch do menu")

    except Exception as e_outer_admin_critical:
        st.error(f"Um erro crítico ocorreu na área administrativa: {e_outer_admin_critical}")
        st.exception(e_outer_admin_critical)
        st.write(f"[DEBUG ADMIN Main Panel] PONTO MP_EXCEPT - Dentro do except e_outer_admin_critical ({e_outer_admin_critical})") 

if not st.session_state.get("admin_logado", False) and not st.session_state.get("cliente_logado", False) and ('aba' not in locals() or aba is None):
    st.info("Fallback final: Selecione se você é Administrador ou Cliente para continuar.")