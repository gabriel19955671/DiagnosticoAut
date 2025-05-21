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
ST_KEY_VERSION = "v23"

default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "confirmou_instrucoes_checkbox_cliente": False,
    "admin_user_login_identifier": None
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
            dtype_spec = {} 
            if filepath == usuarios_csv: dtype_spec = {'CNPJ': str}
            # ... (resto da lógica de inicializar_csv mantida)
            df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None) # Simplificado para brevidade
            # ...
    except Exception as e:
        st.error(f"Erro Crítico ao inicializar ou ler o arquivo {filepath}: {e}")
        st.info(f"A aplicação pode não funcionar corretamente. Verifique o arquivo e as permissões.")
        # raise # Considerar não levantar exceção aqui para permitir que o app tente carregar outras partes

try:
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
            f.write("""**Bem-vindo ao Portal de Diagnóstico Empresarial!** (Conteúdo padrão das instruções)""")
except Exception as e_init_global:
    st.error(f"⚠️ ERRO CRÍTICO NA INICIALIZAÇÃO GLOBAL DE ARQUIVOS: {e_init_global}")
    st.exception(e_init_global) 
    st.stop() 

def criar_notificacao(cnpj_cliente, mensagem, data_diag_ref=None):
    # ... (código mantido)
    pass
def get_unread_notifications_count(cnpj_cliente):
    # ... (código mantido)
    return 0
def marcar_notificacoes_como_lidas(cnpj_cliente, ids_notificacoes=None):
    # ... (código mantido)
    return True
def registrar_acao(cnpj, acao, desc):
    # ... (código mantido)
    pass
def update_user_data(cnpj, field, value):
    # ... (código mantido)
    return True
@st.cache_data
def carregar_analises_perguntas():
    # ... (código mantido)
    return pd.DataFrame(columns=colunas_base_analises)
def obter_analise_para_resposta(pergunta_texto, resposta_valor, df_analises):
    # ... (código mantido)
    return None

def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    try:
        pdf = FPDF()
        pdf.add_page()
        empresa_nome = user_data.get("Empresa", "N/D")
        # ... (restante da função, garantindo txt= e ln em cell() ou pdf.ln() após multi_cell())
        pdf.set_font("Arial", 'B', 16)
        pdf.multi_cell(w=0, h=10, txt=pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome}"), border=0, align='C'); pdf.ln(10)
        # ... (restante da função como na última correção, usando txt= e pdf.ln() após multi_cell)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf_path = tmpfile.name
            pdf.output(name=pdf_path, dest='F') 
        return pdf_path
    except Exception as e: 
        st.error(f"Erro crítico ao gerar PDF de diagnóstico: {e}"); st.exception(e)
        return None

def gerar_pdf_historico(df_historico_filtrado, titulo="Histórico de Ações"):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(w=0, h=10, txt=pdf_safe_text_output(titulo), border=0, ln=1, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "B", 8) 
        col_widths_config = {"Data": 35, "CNPJ": 35, "Ação": 40, "Descrição": 0} 
        
        page_width_effective = pdf.w - pdf.l_margin - pdf.r_margin
        headers_to_print_hist = [col for col in ["Data", "CNPJ", "Ação", "Descrição"] if col in df_historico_filtrado.columns]
        
        current_total_width_for_others = sum(col_widths_config.get(h,0) for h in headers_to_print_hist if h != "Descrição")
        desc_width = page_width_effective - current_total_width_for_others
        if desc_width <= 0 : desc_width = page_width_effective * 0.3 
        col_widths_config["Descrição"] = max(20, desc_width) 

        pdf.set_fill_color(200, 220, 255) 

        for header in headers_to_print_hist:
            pdf.cell(w=col_widths_config.get(header, 30), h=7, txt=pdf_safe_text_output(header), border=1, ln=0, align="C", fill=True)
        pdf.ln(7) 
        
        pdf.set_font("Arial", "", 8)
        line_height_for_multicell = 5 

        for _, row_data in df_historico_filtrado.iterrows():
            y_start_current_row = pdf.get_y()
            max_cell_height_in_row = line_height_for_multicell

            for header_key_calc in headers_to_print_hist:
                cell_text_calc = str(row_data.get(header_key_calc, ""))
                cell_w_calc = col_widths_config.get(header_key_calc, 30)
                num_lines = 1
                if cell_w_calc > 0 and pdf.get_string_width(cell_text_calc) > cell_w_calc:
                    try:
                        words = cell_text_calc.split(' ')
                        temp_line_for_calc = ""
                        num_l_calc = 1
                        for word in words:
                            if pdf.get_string_width(temp_line_for_calc + word + " ") > cell_w_calc - 2 : 
                                num_l_calc +=1
                                temp_line_for_calc = word + " "
                            else:
                                temp_line_for_calc += word + " "
                        num_lines = num_l_calc
                    except: 
                        num_lines = int(pdf.get_string_width(cell_text_calc) / cell_w_calc) + 1 if cell_w_calc > 0 else 1
                
                current_cell_content_height = num_lines * line_height_for_multicell
                max_cell_height_in_row = max(max_cell_height_in_row, current_cell_content_height)
            
            current_row_total_height = max(max_cell_height_in_row, line_height_for_multicell)

            if y_start_current_row + current_row_total_height > pdf.page_break_trigger and not pdf.in_footer:
                pdf.add_page()
                y_start_current_row = pdf.get_y() 
                pdf.set_font("Arial", "B", 8)
                pdf.set_fill_color(200, 220, 255)
                for header_np in headers_to_print_hist:
                     pdf.cell(w=col_widths_config.get(header_np, 30), h=7, txt=pdf_safe_text_output(header_np), border=1, ln=0, align="C", fill=True)
                pdf.ln(7)
                pdf.set_font("Arial", "", 8)
            
            current_x = pdf.l_margin
            for header_key_draw in headers_to_print_hist:
                pdf.set_xy(current_x, y_start_current_row) 
                cell_content = str(row_data.get(header_key_draw, ""))
                cell_w = col_widths_config.get(header_key_draw, 30)
                
                pdf.rect(current_x, y_start_current_row, cell_w, current_row_total_height)
                pdf.multi_cell(w=cell_w, h=line_height_for_multicell, txt=pdf_safe_text_output(cell_content), border=0, align="L") # Removido ln=0
                current_x += cell_w 
            
            pdf.set_y(y_start_current_row + current_row_total_height)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf_path = tmpfile.name
            pdf.output(name=pdf_path, dest='F') 
        return pdf_path
    except Exception as e_pdf_hist:
        st.error(f"Erro ao gerar PDF do histórico: {e_pdf_hist}")
        st.exception(e_pdf_hist) 
        return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): 
    st.session_state.trigger_rerun_global = False
    st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key=f"tipo_usuario_radio_{ST_KEY_VERSION}") 
elif st.session_state.admin_logado: 
    aba = "Administrador"
else: 
    aba = "Cliente"

# --- ÁREA DE LOGIN DO ADMINISTRADOR ---
if aba == "Administrador" and not st.session_state.admin_logado:
    # ... (Código de login do admin com chaves ST_KEY_VERSION - OMITIDO PARA BREVIDADE)
    pass

# --- ÁREA DE LOGIN DO CLIENTE ---
if aba == "Cliente" and not st.session_state.cliente_logado:
    # ... (Código de login do cliente com chaves ST_KEY_VERSION - OMITIDO PARA BREVIDADE)
    pass

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    # ... (Código da área do cliente com chaves ST_KEY_VERSION - OMITIDO PARA BREVIDADE)
    pass

# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    try:
        try: st.sidebar.image("https://via.placeholder.com/150x75.png?text=Sua+Logo+Admin", width=150) 
        except Exception as e_img_admin: st.sidebar.caption(f"Logo admin não carregada: {e_img_admin}")
        
        st.sidebar.success("🟢 Admin Logado")
        if st.sidebar.button("🚪 Sair do Painel Admin", key=f"logout_admin_{ST_KEY_VERSION}_adm"): 
            st.session_state.admin_logado = False
            if 'admin_user_login_identifier' in st.session_state:
                del st.session_state.admin_user_login_identifier
            st.rerun() 
        
        menu_admin_options = ["📊 Visão Geral e Diagnósticos", "🚦 Status dos Clientes", "📜 Histórico de Usuários",
                              "📝 Gerenciar Perguntas", "💡 Gerenciar Análises de Perguntas",
                              "✍️ Gerenciar Instruções Clientes",
                              "👥 Gerenciar Clientes", "👮 Gerenciar Administradores", "💾 Backup de Dados"]
        menu_admin = st.sidebar.selectbox("Funcionalidades Admin:", menu_admin_options, key=f"admin_menu_selectbox_{ST_KEY_VERSION}_adm") 
        
        # LINHA DE DEPURAÇÃO:
        st.sidebar.info(f"Opção de Menu Selecionada: {menu_admin}") # Para verificar o valor de menu_admin

        st.header(f"{menu_admin.split(' ')[0]} {menu_admin.split(' ', 1)[1]}")
        
        # Carregamento de dados gerais (com tratamento de erro menos disruptivo)
        df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios) 
        try:
            if os.path.exists(usuarios_csv) and os.path.getsize(usuarios_csv) > 0:
                df_usuarios_admin_temp_load = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                # ... (validação de colunas)
                df_usuarios_admin_geral = df_usuarios_admin_temp_load
        except Exception as e_load_users_adm_global: 
            st.sidebar.error(f"Erro ao carregar usuários: {e_load_users_adm_global}")

        diagnosticos_df_admin_orig_view = pd.DataFrame() 
        admin_data_carregada_view_sucesso = False
        try:
            if os.path.exists(arquivo_csv) and os.path.getsize(arquivo_csv) > 0:
                diagnosticos_df_admin_orig_view = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                if 'Data' in diagnosticos_df_admin_orig_view.columns: 
                    diagnosticos_df_admin_orig_view['Data'] = pd.to_datetime(diagnosticos_df_admin_orig_view['Data'], errors='coerce')
                if not diagnosticos_df_admin_orig_view.empty: 
                    admin_data_carregada_view_sucesso = True
            elif os.path.exists(arquivo_csv): # Existe mas está vazio
                 st.warning(f"Arquivo de diagnósticos ('{arquivo_csv}') está vazio.")
            # else: # Não existe
            #     st.warning(f"Arquivo de diagnósticos ('{arquivo_csv}') não encontrado.") # Já tratado no init, mas pode ser útil aqui também

        except Exception as e_adm_load_diag: 
            st.error(f"ERRO AO CARREGAR ARQUIVO DE DIAGNÓSTICOS ('{arquivo_csv}'): {e_adm_load_diag}")
            # st.exception(e_adm_load_diag) # Comentar esta linha se estiver parando a renderização de outras seções

        # Lógica de dispatch do menu admin
        try:
            if menu_admin == "📊 Visão Geral e Diagnósticos":
                st.subheader("📊 Visão Geral e Diagnósticos")
                st.markdown("Conteúdo da Visão Geral e Diagnósticos aqui...")
                # (Coloque a lógica completa desta seção aqui, usando ST_KEY_VERSION nas chaves)
            
            elif menu_admin == "🚦 Status dos Clientes":
                st.subheader("🚦 Status dos Clientes")
                st.markdown("Conteúdo do Status dos Clientes aqui...")
                # (Coloque a lógica completa desta seção aqui, usando ST_KEY_VERSION nas chaves)

            elif menu_admin == "📜 Histórico de Usuários":
                st.subheader("📜 Histórico de Ações")
                # ... (Código da seção Histórico de Usuários, como na resposta anterior, usando ST_KEY_VERSION nas chaves)
                # Exemplo de parte do código:
                df_historico_completo_hu = pd.DataFrame()
                try:
                    if os.path.exists(historico_csv) and os.path.getsize(historico_csv) > 0:
                        df_historico_completo_hu = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
                except Exception as e_hu_load:
                    st.error(f"Erro ao carregar histórico: {e_hu_load}")
                st.markdown("Filtros e tabela do histórico aqui...")
                # (Lógica completa da seção Histórico de Usuários)


            elif menu_admin == "📝 Gerenciar Perguntas":
                st.subheader("📝 Gerenciar Perguntas")
                st.markdown("Conteúdo de Gerenciar Perguntas aqui...")
                # (Coloque a lógica completa desta seção aqui, usando ST_KEY_VERSION nas chaves)
            elif menu_admin == "💡 Gerenciar Análises de Perguntas":
                st.subheader("💡 Gerenciar Análises de Perguntas")
                st.markdown("Conteúdo de Gerenciar Análises aqui...")
                # (Coloque a lógica completa desta seção aqui, usando ST_KEY_VERSION nas chaves)
            elif menu_admin == "✍️ Gerenciar Instruções Clientes":
                st.subheader("✍️ Gerenciar Instruções Clientes")
                st.markdown("Conteúdo de Gerenciar Instruções aqui...")
                # (Coloque a lógica completa desta seção aqui, usando ST_KEY_VERSION nas chaves)
            elif menu_admin == "👥 Gerenciar Clientes":
                st.subheader("👥 Gerenciar Clientes")
                st.markdown("Conteúdo de Gerenciar Clientes aqui...")
                # (Coloque a lógica completa desta seção aqui, usando ST_KEY_VERSION nas chaves)
            elif menu_admin == "👮 Gerenciar Administradores":
                st.subheader("👮 Gerenciar Administradores")
                st.markdown("Conteúdo de Gerenciar Administradores aqui...")
                # (Coloque a lógica completa desta seção aqui, usando ST_KEY_VERSION nas chaves)
            elif menu_admin == "💾 Backup de Dados":
                st.subheader("💾 Backup de Dados")
                st.markdown("Conteúdo de Backup de Dados aqui...")
                # (Coloque a lógica completa desta seção aqui, usando ST_KEY_VERSION nas chaves)
            else:
                st.warning(f"Opção de menu '{menu_admin}' não reconhecida ou em desenvolvimento.")

        except Exception as e_admin_menu_dispatch:
            st.error(f"Ocorreu um erro na funcionalidade '{menu_admin}': {e_admin_menu_dispatch}")
            st.exception(e_admin_menu_dispatch) 
            
    except Exception as e_outer_admin_critical:
        st.error(f"Um erro crítico e inesperado ocorreu na área administrativa: {e_outer_admin_critical}")
        st.exception(e_outer_admin_critical) 

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")