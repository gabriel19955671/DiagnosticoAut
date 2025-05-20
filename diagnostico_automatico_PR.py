import streamlit as st
# Adicionar um print para o console do terminal imediatamente
print("DEBUG CONSOLE: Script Python iniciado.")
st.write("DEBUG UI: Script Streamlit iniciado (antes de set_page_config).") # Para ver se o script chega aqui

import pandas as pd
from datetime import datetime, date # Mantido para funções básicas
import os # Mantido para funções básicas
import time # Mantido para funções básicas
from fpdf import FPDF # Mantido se gerar_pdf for chamado em algum lugar
import tempfile # Mantido
import re # Mantido
import json # Mantido
# plotly e plotly.graph_objects não são usados na versão simplificada, mas podem ser mantidos
# import plotly.express as px
# import plotly.graph_objects as go 
import uuid # Mantido

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
try:
    st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", initial_sidebar_state="expanded")
    print("DEBUG CONSOLE: st.set_page_config executado.")
    st.write("DEBUG UI: st.set_page_config executado.")
except Exception as e_set_page_config:
    print(f"ERRO CRÍTICO em st.set_page_config: {e_set_page_config}")
    # Não podemos usar st.error aqui se set_page_config falhou
    # Este erro apareceria no terminal.
    # Para tentar mostrar algo na UI se set_page_config falhar (improvável que funcione bem):
    # import sys
    # sys.stderr.write(f"ERRO CRÍTICO em st.set_page_config: {e_set_page_config}\n")
    # st.markdown(f"## ERRO CRÍTICO em st.set_page_config:\n```\n{e_set_page_config}\n```")
    st.stop()


st.title("🔒 Portal de Diagnóstico")
st.write("DEBUG UI: Linha APÓS st.title()")
st.markdown("---")

# --- Configuração de Arquivos e Variáveis Globais ---
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

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "📖 Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "confirmou_instrucoes_checkbox_cliente": False
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias (Mínimas necessárias para login e estrutura básica) ---
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_'); s = re.sub(r'(?u)[^-\w.]', '', s); return s
# pdf_safe_text_output e find_client_logo_path são usados em gerar_pdf, que pode não ser chamado na versão simplificada
# mas são mantidos para integridade se o usuário descomentar partes.
def pdf_safe_text_output(text): return str(text).encode('latin-1', 'replace').decode('latin-1')
def find_client_logo_path(cnpj_arg):
    if not cnpj_arg: return None
    base = str(cnpj_arg).replace('/', '').replace('.', '').replace('-', '')
    for ext in ["png", "jpg", "jpeg"]:
        path = os.path.join(LOGOS_DIR, f"{base}_logo.{ext}")
        if os.path.exists(path): return path
    return None


# --- Criação e Verificação de Arquivos e Pastas ---
if not os.path.exists(LOGOS_DIR):
    try: os.makedirs(LOGOS_DIR)
    except OSError as e: st.error(f"Erro ao criar diretório de logos '{LOGOS_DIR}': {e}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone",
                         "ConfirmouInstrucoesParaSlotAtual", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "LiberacoesExtrasConcedidas"]
# colunas_base_perguntas e outras não são estritamente necessárias para o teste de "aparecer algo"
# mas são mantidas para consistência com a estrutura original.
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
            print(f"DEBUG CONSOLE: Arquivo {filepath} criado/inicializado (vazio ou com defaults).")
        else:
            dtype_spec = {}
            if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, historico_csv]:
                if 'CNPJ' in columns: dtype_spec['CNPJ'] = str
                if 'CNPJ_Cliente' in columns: dtype_spec['CNPJ_Cliente'] = str
            
            df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)
            print(f"DEBUG CONSOLE: Arquivo {filepath} lido.")
            made_changes = False
            expected_cols_df = pd.DataFrame(columns=columns)
            for col_idx, col_name in enumerate(expected_cols_df.columns):
                if col_name not in df_init.columns:
                    default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                    df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=default_val)
                    made_changes = True
                    print(f"DEBUG CONSOLE: Coluna {col_name} adicionada a {filepath}.")
            if made_changes:
                df_init.to_csv(filepath, index=False, encoding='utf-8')
                print(f"DEBUG CONSOLE: Arquivo {filepath} salvo com novas colunas.")
    except pd.errors.EmptyDataError:
        print(f"DEBUG CONSOLE: pd.errors.EmptyDataError para {filepath}. Criando com colunas.")
        df_init = pd.DataFrame(columns=columns)
        if defaults:
            for col, default_val in defaults.items():
                if col in columns: df_init[col] = default_val
        df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erro GERAL em inicializar_csv para o arquivo {filepath}: {e}")
        st.info(f"Verifique se o arquivo '{filepath}' não está corrompido ou se o programa tem permissão para acessá-lo.")
        raise

try:
    print("DEBUG CONSOLE: Iniciando inicialização de CSVs...")
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios,
                    defaults={"ConfirmouInstrucoesParaSlotAtual": "False", "DiagnosticosDisponiveis": 1,
                              "TotalDiagnosticosRealizados": 0, "LiberacoesExtrasConcedidas": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False})

    if not os.path.exists(instrucoes_txt_file):
        with open(instrucoes_txt_file, "w", encoding="utf-8") as f:
            f.write("""**Bem-vindo ao Portal de Diagnóstico Empresarial!** (Conteúdo Padrão das Instruções)""")
    print("DEBUG CONSOLE: Finalizada inicialização de CSVs e arquivo de instruções.")
    st.write("DEBUG UI: Inicialização de arquivos CSV e instruções concluída.")
except Exception as e_init_global:
    st.error(f"⚠️ ERRO CRÍTICO NA INICIALIZAÇÃO DOS ARQUIVOS DE DADOS:")
    st.error(f"Ocorreu um problema ao carregar ou criar os arquivos de dados necessários.")
    st.error(f"Verifique o console/terminal do Streamlit para o traceback completo do Python, se disponível.")
    st.error(f"Detalhes do erro: {e_init_global}")
    st.exception(e_init_global)
    st.warning("A aplicação não pode continuar até que este problema seja resolvido.")
    st.info("""
    Possíveis causas:
    - Um dos arquivos CSV (ex: 'usuarios.csv', 'diagnosticos_clientes.csv') está corrompido.
    - A aplicação não tem permissão para ler/escrever arquivos na pasta onde está rodando.
    - O disco pode estar cheio.
    """)
    st.stop()

# --- Funções de Notificação (Simplificadas se necessário, mas mantidas por enquanto) ---
def criar_notificacao(cnpj_cliente, mensagem, data_diag_ref=None):
    # ... (implementação como antes)
    pass
def get_unread_notifications_count(cnpj_cliente):
    # ... (implementação como antes)
    return 0
def marcar_notificacoes_como_lidas(cnpj_cliente, ids_notificacoes=None):
    # ... (implementação como antes)
    return True

# --- Demais Funções Utilitárias (Simplificadas se necessário, mas mantidas por enquanto) ---
def registrar_acao(cnpj, acao, desc):
    # ... (implementação como antes)
    pass
def update_user_data(cnpj, field, value):
    # ... (implementação como antes)
    return True
# @st.cache_data # Removido cache para simplificar depuração
def carregar_analises_perguntas(): # Removido cache
    try: return pd.read_csv(analises_perguntas_csv, encoding='utf-8')
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_analises)
# ... (outras funções utilitárias como obter_analise_para_resposta, gerar_pdf_diagnostico_completo, gerar_pdf_historico podem ser mantidas
#      pois só são chamadas em contextos específicos que estamos tentando evitar por enquanto)

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v15_simples")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

st.write(f"DEBUG UI: Aba selecionada/ativa: {aba}")

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador 🔑</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v15_simples"):
        u = st.text_input("Usuário", key="admin_u_v15_s"); p = st.text_input("Senha", type="password", key="admin_p_v15_s")
        if st.form_submit_button("Entrar"):
            try:
                df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                admin_encontrado = df_creds[df_creds["Usuario"] == u]
                if not admin_encontrado.empty and admin_encontrado.iloc[0]["Senha"] == p:
                    st.session_state.admin_logado = True; st.success("Login de administrador bem-sucedido! ✅"); st.rerun()
                else: st.error("Usuário ou senha inválidos.")
            except FileNotFoundError: st.error(f"Arquivo de credenciais de admin não encontrado: {admin_credenciais_csv}")
            except Exception as e: st.error(f"Erro no login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente 🏢</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_v15_simples"):
        c = st.text_input("CNPJ", key="cli_c_v15_s", value=st.session_state.get("last_cnpj_input",""))
        s = st.text_input("Senha", type="password", key="cli_s_v15_s")
        if st.form_submit_button("Entrar"):
            st.session_state.last_cnpj_input = c
            try:
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                for col, default_val_user, col_type in [
                    ("ConfirmouInstrucoesParaSlotAtual", "False", str),
                    ("DiagnosticosDisponiveis", 1, int),
                    ("TotalDiagnosticosRealizados", 0, int),
                    ("LiberacoesExtrasConcedidas", 0, int)
                ]:
                    if col not in users_df.columns: users_df[col] = default_val_user
                    if col_type == int:
                        users_df[col] = pd.to_numeric(users_df[col], errors='coerce').fillna(default_val_user).astype(int)
                    else:
                        users_df[col] = users_df[col].astype(str)

                blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                if c in blocked_df["CNPJ"].values: st.error("CNPJ bloqueado."); st.stop()

                match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                if match.empty: st.error("CNPJ ou senha inválidos."); st.stop()

                st.session_state.cliente_logado = True; st.session_state.cnpj = c
                st.session_state.user = match.iloc[0].to_dict()
                st.session_state.user["ConfirmouInstrucoesParaSlotAtual"] = str(st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", "False")).lower() == "true"
                st.session_state.user["DiagnosticosDisponiveis"] = int(st.session_state.user.get("DiagnosticosDisponiveis", 1))
                st.session_state.user["TotalDiagnosticosRealizados"] = int(st.session_state.user.get("TotalDiagnosticosRealizados", 0))
                st.session_state.user["LiberacoesExtrasConcedidas"] = int(st.session_state.user.get("LiberacoesExtrasConcedidas", 0))

                st.session_state.inicio_sessao_cliente = time.time()
                # registrar_acao(c, "Login", "Usuário logou.") # Simplificado

                pode_fazer_novo_login = st.session_state.user["DiagnosticosDisponiveis"] > st.session_state.user["TotalDiagnosticosRealizados"]
                if pode_fazer_novo_login and not st.session_state.user["ConfirmouInstrucoesParaSlotAtual"]:
                    st.session_state.cliente_page = "📖 Instruções"
                elif pode_fazer_novo_login and st.session_state.user["ConfirmouInstrucoesParaSlotAtual"]:
                    st.session_state.cliente_page = "📝 Novo Diagnóstico"
                else:
                    st.session_state.cliente_page = "📊 Painel Principal"

                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                st.session_state.respostas_atuais_diagnostico = {}; st.session_state.progresso_diagnostico_percentual = 0; st.session_state.progresso_diagnostico_contagem = (0,0); st.session_state.feedbacks_respostas = {}; st.session_state.diagnostico_enviado_sucesso = False; st.session_state.confirmou_instrucoes_checkbox_cliente = False
                st.success("Login cliente OK! ✅"); st.rerun()
            except FileNotFoundError as fnf_e:
                st.error(f"Erro de configuração: Arquivo {fnf_e.filename} não encontrado. Contate o administrador.")
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    if "user" not in st.session_state or st.session_state.user is None or \
       "cnpj" not in st.session_state or st.session_state.cnpj is None:
        st.error("Erro de sessão. Por favor, faça o login novamente.")
        # ... (código de reset de sessão como antes) ...
        st.session_state.cliente_logado = False; st.rerun()

    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}! 👋")
    # ... (expander do perfil simplificado ou como antes)

    unread_notif_count_val = get_unread_notifications_count(st.session_state.cnpj) # Pode ser simplificado para 0
    notif_menu_label_val = "🔔 Notificações"
    if unread_notif_count_val > 0: notif_menu_label_val = f"🔔 Notificações ({unread_notif_count_val})"
    menu_options_cli_val = ["📖 Instruções", "📝 Novo Diagnóstico", "📊 Painel Principal", notif_menu_label_val]
    
    pode_fazer_novo_sidebar_val = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
    confirmou_instrucoes_sidebar_val = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)
    instrucoes_pendentes_obrigatorias_val = pode_fazer_novo_sidebar_val and not confirmou_instrucoes_sidebar_val

    st.sidebar.markdown("---")
    st.sidebar.caption(f"DEBUG INFO (Barra Lateral):")
    st.sidebar.write(f"`ss.cliente_page` (atual): `{st.session_state.cliente_page}`")
    st.sidebar.write(f"`pode_fazer_novo`: `{pode_fazer_novo_sidebar_val}`")
    st.sidebar.write(f"`confirmou_instr`: `{confirmou_instrucoes_sidebar_val}`")
    st.sidebar.write(f"`instr_pend_obrig`: `{instrucoes_pendentes_obrigatorias_val}`")
    
    effective_cliente_page_for_radio_default = st.session_state.cliente_page
    
    if instrucoes_pendentes_obrigatorias_val and st.session_state.cliente_page != "📖 Instruções":
        st.sidebar.error("❗REDIRECIONAMENTO AUTOMÁTICO: Para 'Instruções' (pendência obrigatória).")
        effective_cliente_page_for_radio_default = "📖 Instruções"
        if st.session_state.cliente_page != "📖 Instruções":
            st.session_state.cliente_page = "📖 Instruções" 

    st.sidebar.write(f"`effective_page_for_radio`: `{effective_cliente_page_for_radio_default}`")
    st.sidebar.markdown("---")
    st.sidebar.error("PERGUNTA PARA VOCÊ: Ao tentar acessar 'Painel Principal' ou 'Novo Diagnóstico', você vê o 'ALERTA DE DEPURAÇÃO MÁXIMA' em vermelho na área de conteúdo principal da página?")


    current_page_for_radio_display = effective_cliente_page_for_radio_default
    if current_page_for_radio_display == "Notificações": current_page_for_radio_display = notif_menu_label_val
    
    try: current_idx_cli_val = menu_options_cli_val.index(current_page_for_radio_display)
    except ValueError:
        st.sidebar.warning(f"DEBUG: `current_page_for_radio_display` ('{current_page_for_radio_display}') não encontrada no menu. Default para Instruções.")
        current_idx_cli_val = 0
        if st.session_state.cliente_page != "📖 Instruções":
            st.session_state.cliente_page = "📖 Instruções"
    
    selected_page_cli_raw_val = st.sidebar.radio("Menu Cliente", menu_options_cli_val, index=current_idx_cli_val, key="cli_menu_v15_debug_radio_final")
    selected_page_cli_actual = "Notificações" if "Notificações" in selected_page_cli_raw_val else selected_page_cli_raw_val
    
    if selected_page_cli_actual != st.session_state.cliente_page: 
        if instrucoes_pendentes_obrigatorias_val and selected_page_cli_actual != "📖 Instruções":
            st.sidebar.error("⚠️ ACESSO NEGADO! Você deve primeiro ler e confirmar as instruções na página '📖 Instruções' para acessar outras seções ou iniciar um novo diagnóstico.")
        else:
            st.session_state.cliente_page = selected_page_cli_actual
            st.rerun()

    if st.sidebar.button("⬅️ Sair do Portal Cliente", key="logout_cliente_v15_final"):
        # ... (lógica de logout como antes) ...
        st.session_state.cliente_logado = False; st.rerun()

    st.markdown("---")
    st.subheader(f"DEBUG GLOBAL (Área Cliente): Tentando renderizar conteúdo para: st.session_state.cliente_page = `{st.session_state.cliente_page}`")
    st.markdown("---")

    # --- Conteúdo da Página do Cliente (SUPER SIMPLIFICADO) ---
    st.write(f"DEBUG UI: Verificando qual bloco de página renderizar para '{st.session_state.cliente_page}'...")

    if st.session_state.cliente_page == "📖 Instruções":
        st.write("DEBUG UI: Entrando no bloco 'Instruções'")
        st.subheader("📖 Instruções do Sistema de Diagnóstico")
        st.write("Conteúdo da página de instruções aqui... (Verifique se você precisa confirmar algo abaixo se um novo diagnóstico estiver disponível).")
        # (Lógica de confirmação de instruções da versão anterior deve ser inserida aqui gradualmente)
        if st.session_state.user:
            pode_fazer_novo_inst_page_val = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            confirmou_inst_atual = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)
            if pode_fazer_novo_inst_page_val and not confirmou_inst_atual:
                 st.error("🛑 **AÇÃO NECESSÁRIA:** Para prosseguir para um NOVO DIAGNÓSTICO, você DEVE marcar a caixa de confirmação abaixo e clicar em 'Prosseguir para o Diagnóstico'.")
            if pode_fazer_novo_inst_page_val:
                st.checkbox("Declaro que li e compreendi...", key="temp_confirm_instr_debug")
                if st.button("Prosseguir para Diagnóstico (TESTE)", key="temp_prosseguir_debug"):
                    update_user_data(st.session_state.cnpj, "ConfirmouInstrucoesParaSlotAtual", "True") # Simula confirmação
                    st.session_state.cliente_page = "📝 Novo Diagnóstico"; st.rerun()
        st.write("DEBUG UI: Saindo do bloco 'Instruções'")

    elif st.session_state.cliente_page == "📊 Painel Principal":
        st.write("DEBUG UI: Entrando no bloco 'Painel Principal'")
        st.error(f"ALERTA DE DEPURAÇÃO MÁXIMA: BLOCO 'Painel Principal' ALCANÇADO!")
        st.subheader("📊 Painel Principal do Cliente (Versão de Teste SUPER SIMPLIFICADA)")
        st.write("Se você está vendo isto, o bloco do Painel Principal foi alcançado. O conteúdo original está comentado no código.")
        st.balloons()
        st.write("DEBUG UI: Saindo do bloco 'Painel Principal'")
        
    elif st.session_state.cliente_page == "📝 Novo Diagnóstico":
        st.write("DEBUG UI: Entrando no bloco 'Novo Diagnóstico'")
        st.error(f"ALERTA DE DEPURAÇÃO MÁXIMA: BLOCO 'Novo Diagnóstico' ALCANÇADO!")
        st.subheader("📝 Formulário de Novo Diagnóstico (Versão de Teste SUPER SIMPLIFICADA)")
        # Verificações de permissão
        if not st.session_state.user: st.error("Erro de sessão."); st.stop()
        pode_fazer = st.session_state.user.get("DiagnosticosDisponiveis",0) > st.session_state.user.get("TotalDiagnosticosRealizados",0)
        confirmou = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)
        if not pode_fazer: st.warning("Sem diagnósticos disponíveis."); st.stop()
        if not confirmou: st.warning("Instruções não confirmadas."); st.stop()
        
        st.write("Se você vê isto, as checagens de permissão passaram. O formulário original está comentado no código.")
        st.balloons()
        st.write("DEBUG UI: Saindo do bloco 'Novo Diagnóstico'")

    elif st.session_state.cliente_page == "Notificações":
        st.write("DEBUG UI: Entrando no bloco 'Notificações'")
        st.subheader("🔔 Minhas Notificações")
        st.write("Conteúdo da página de notificações aqui...")
        st.write("DEBUG UI: Saindo do bloco 'Notificações'")
    else: 
        st.error(f"ERRO DE ROTEAMENTO DE PÁGINA: Página do cliente desconhecida ou não definida: '{st.session_state.cliente_page}'")
        st.warning("Por favor, tente fazer login novamente ou contate o suporte se o problema persistir.")

# --- ÁREA DO ADMINISTRADOR LOGADO (SUPER SIMPLIFICADA PARA TESTE) ---
elif aba == "Administrador" and st.session_state.admin_logado:
    st.error("ALERTA DE DEPURAÇÃO MÁXIMA: BLOCO 'Admin' ALCANÇADO!")
    st.header("Área Administrativa (Versão de Teste SUPER SIMPLIFICADA)")
    st.write("Se você vê isto, o bloco do admin foi alcançado. O conteúdo original está comentado no código.")
    st.balloons()
    if st.sidebar.button("🚪 Sair do Painel Admin (TESTE)", key="logout_admin_v15_simples"):
        st.session_state.admin_logado = False
        st.rerun()
    st.write("DEBUG UI: FIM Admin (SIMPLIFICADO)")


if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")

print("DEBUG CONSOLE: Script Python finalizado.")
st.write("DEBUG UI: Fim do script Streamlit.")