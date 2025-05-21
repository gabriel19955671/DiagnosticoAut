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
ST_KEY_VERSION = "v24" # Chave atualizada

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
            # Simplificado para brevidade, a lógica anterior de verificação de colunas pode ser mantida se desejar
            pass 
    except Exception as e:
        st.error(f"Erro Crítico ao inicializar ou ler o arquivo {filepath}: {e}")

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    # ... (chamadas inicializar_csv para outros arquivos) ...
except Exception as e_init_global:
    st.error(f"⚠️ ERRO CRÍTICO NA INICIALIZAÇÃO GLOBAL DE ARQUIVOS: {e_init_global}")
    st.exception(e_init_global); st.stop() 

# --- Funções Utilitárias (Notificação, Ação, Usuário, Análise) - Omitidas por brevidade ---
# Mantenha suas funções criar_notificacao, get_unread_notifications_count, etc. aqui
# Elas não são o foco do erro atual de renderização do admin.

def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    # ... (Código da função como na última correção - usando txt= e pdf.ln() após multi_cell onde necessário)
    # Omitido para brevidade, mas certifique-se que está correto no seu script final.
    return None # Placeholder

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
                # A linha abaixo é a crucial para o erro 'unexpected keyword argument 'ln'' se 'ln=0' estiver presente.
                pdf.multi_cell(w=cell_w, h=line_height_for_multicell, txt=pdf_safe_text_output(cell_content), border=0, align="L") 
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
    # Certifique-se que esta seção está completa e correta no seu script final.
    st.markdown("Área de Login Admin Placeholder") 
    pass

# --- ÁREA DE LOGIN DO CLIENTE ---
if aba == "Cliente" and not st.session_state.cliente_logado:
    # ... (Código de login do cliente com chaves ST_KEY_VERSION - OMITIDO PARA BREVIDADE)
    # Certifique-se que esta seção está completa e correta no seu script final.
    st.markdown("Área de Login Cliente Placeholder")
    pass

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    # ... (Código da área do cliente com chaves ST_KEY_VERSION - OMITIDO PARA BREVIDADE)
    # Certifique-se que esta seção está completa e correta no seu script final.
    st.subheader(f"Painel Cliente - Página: {st.session_state.get('cliente_page', 'N/A')}")
    st.markdown("Conteúdo da área do cliente aqui...")
    pass

# --- ÁREA DO ADMINISTRADOR LOGADO (SIMPLIFICADA PARA DEPURAÇÃO) ---
if aba == "Administrador" and st.session_state.admin_logado:
    try:
        try: 
            st.sidebar.image("https://via.placeholder.com/150x75.png?text=Sua+Logo+Admin", width=150) 
        except Exception as e_img_admin: 
            st.sidebar.caption(f"Logo admin não carregada: {e_img_admin}")
        
        st.sidebar.success("🟢 Admin Logado")
        if st.sidebar.button("🚪 Sair do Painel Admin", key=f"logout_admin_{ST_KEY_VERSION}_adm"): 
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
        
        st.sidebar.info(f"[DEBUG] Opção Selecionada: {menu_admin}") # LINHA DE DEPURAÇÃO
        
        st.header(f"{menu_admin.split(' ')[0]} {menu_admin.split(' ', 1)[1]}")

        # REMOVIDO CARREGAMENTO DE DADOS GERAIS DAQUI PARA ISOLAR O PROBLEMA DE RENDERIZAÇÃO DO MENU
        # df_usuarios_admin_geral = ...
        # diagnosticos_df_admin_orig_view = ...

        # Lógica de dispatch do menu admin (SUPER SIMPLIFICADA)
        if menu_admin == "📊 Visão Geral e Diagnósticos":
            st.subheader("📊 Visão Geral e Diagnósticos")
            st.markdown("Conteúdo para Visão Geral e Diagnósticos (em desenvolvimento).")
            # TODO: Reintroduzir a lógica e carregamento de dados para esta seção
            
        elif menu_admin == "🚦 Status dos Clientes":
            st.subheader("🚦 Status dos Clientes")
            st.markdown("Conteúdo para Status dos Clientes (em desenvolvimento).")
            # TODO: Reintroduzir a lógica e carregamento de dados para esta seção

        elif menu_admin == "📜 Histórico de Usuários":
            st.subheader("📜 Histórico de Usuários")
            st.markdown("Interface para visualizar e gerenciar histórico de usuários.")
            # TODO: Reintroduzir a lógica completa, incluindo filtros, tabela e o botão de download do PDF.
            # Exemplo de como reintroduzir o botão (após confirmar que esta seção é renderizada):
            # df_historico_filtrado_view_hu = pd.DataFrame() # Carregar ou filtrar dados aqui
            # if st.button("Baixar Histórico (PDF Teste)", key=f"btn_pdf_hist_teste_{ST_KEY_VERSION}"):
            #     if not df_historico_filtrado_view_hu.empty:
            #         gerar_pdf_historico(df_historico_filtrado_view_hu, "Título Teste Histórico")
            #     else:
            #         st.warning("Nenhum histórico para gerar PDF.")
            st.markdown("(Funcionalidade de PDF e exclusão de histórico a ser reativada aqui)")


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
            st.warning(f"Opção de menu '{menu_admin}' não implementada ou não reconhecida.")

    except Exception as e_outer_admin_critical:
        st.error(f"Um erro crítico ocorreu na área administrativa: {e_outer_admin_critical}")
        st.exception(e_outer_admin_critical) 

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")