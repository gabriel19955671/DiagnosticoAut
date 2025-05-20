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
import uuid # Para IDs de análise

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide")

# CSS
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
</style>
""", unsafe_allow_html=True)

st.title("🔒 Portal de Diagnóstico")

# --- Configuração de Arquivos e Variáveis Globais ---
admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv" # CSV principal de diagnósticos
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv"
historico_csv = "historico_clientes.csv"
analises_perguntas_csv = "analises_perguntas.csv"
LOGOS_DIR = "client_logos"

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {}
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias ---
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_'); s = re.sub(r'(?u)[^-\w.]', '', s); return s
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
                         "JaVisualizouInstrucoes", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]

def inicializar_csv(filepath, columns, defaults=None):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if defaults:
                for col, default_val in defaults.items():
                    if col in columns: df_init[col] = default_val
            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else:
            df_init = pd.read_csv(filepath, encoding='utf-8', dtype={'CNPJ': str} if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv] else None)
            made_changes = False
            for col_idx, col_name in enumerate(columns): 
                if col_name not in df_init.columns:
                    default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                    df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=default_val)
                    made_changes = True
            if made_changes:
                df_init.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError:
        df_init = pd.DataFrame(columns=columns)
        if defaults:
            for col, default_val in defaults.items():
                if col in columns: df_init[col] = default_val
        df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e: st.error(f"Erro ao inicializar {filepath}: {e}"); raise

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios, 
                    defaults={"JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
except Exception: st.stop()

def registrar_acao(cnpj, acao, desc):
    try: hist_df = pd.read_csv(historico_csv, encoding='utf-8')
    except (FileNotFoundError, pd.errors.EmptyDataError): hist_df = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    new_entry = {"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": desc}
    hist_df = pd.concat([hist_df, pd.DataFrame([new_entry])], ignore_index=True)
    hist_df.to_csv(historico_csv, index=False, encoding='utf-8')

def update_user_data(cnpj, field, value):
    try:
        users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        idx = users_df[users_df['CNPJ'] == str(cnpj)].index
        if not idx.empty:
            users_df.loc[idx, field] = value 
            users_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
            if 'user' in st.session_state and st.session_state.user and str(st.session_state.user.get('CNPJ')) == str(cnpj):
                # Atualiza o tipo na sessão se for contador
                if field in ["DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]:
                    st.session_state.user[field] = int(value)
                else:
                    st.session_state.user[field] = value 
            return True
    except Exception as e: st.error(f"Erro ao atualizar usuário ({field}): {e}")
    return False

@st.cache_data
def carregar_analises_perguntas():
    try: return pd.read_csv(analises_perguntas_csv, encoding='utf-8')
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_analises)

def obter_analise_para_resposta(pergunta_texto, resposta_valor, df_analises):
    if df_analises.empty: return None
    analises_da_pergunta = df_analises[df_analises['TextoPerguntaOriginal'] == pergunta_texto]
    if analises_da_pergunta.empty: return None
    default_analise = None
    for _, row_analise in analises_da_pergunta.iterrows():
        tipo_cond = row_analise['TipoCondicao']; analise_txt = row_analise['TextoAnalise']
        if tipo_cond == 'Default': default_analise = analise_txt; continue
        if tipo_cond == 'FaixaNumerica':
            min_val=pd.to_numeric(row_analise['CondicaoValorMin'],errors='coerce');max_val=pd.to_numeric(row_analise['CondicaoValorMax'],errors='coerce');resp_num=pd.to_numeric(resposta_valor,errors='coerce')
            if pd.notna(resp_num) and pd.notna(min_val) and pd.notna(max_val) and min_val <= resp_num <= max_val: return analise_txt
        elif tipo_cond == 'ValorExatoEscala':
            if str(resposta_valor).strip().lower() == str(row_analise['CondicaoValorExato']).strip().lower(): return analise_txt
        elif tipo_cond == 'ScoreGUT':
            min_s=pd.to_numeric(row_analise['CondicaoValorMin'],errors='coerce');max_s=pd.to_numeric(row_analise['CondicaoValorMax'],errors='coerce');resp_s_gut=pd.to_numeric(resposta_valor,errors='coerce')
            is_min = pd.notna(resp_s_gut) and pd.notna(min_s) and resp_s_gut >= min_s
            is_max_ok = pd.isna(max_s) or (pd.notna(resp_s_gut) and resp_s_gut <= max_s)
            if is_min and is_max_ok: return analise_txt
    return default_analise

def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    try:
        pdf = FPDF()
        pdf.add_page()
        empresa_nome = user_data.get("Empresa", "N/D")
        cnpj_pdf = user_data.get("CNPJ", "N/D")
        logo_path = find_client_logo_path(cnpj_pdf)
        if logo_path:
            try:
                current_y = pdf.get_y(); max_h = 20
                pdf.image(logo_path, x=10, y=current_y, h=max_h)
                pdf.set_y(current_y + max_h + 5)
            except Exception: pass 

        pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome}"), 0, 1, 'C'); pdf.ln(5)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 7, pdf_safe_text_output(f"Data: {diag_data.get('Data','N/D')} | Empresa: {empresa_nome} (CNPJ: {cnpj_pdf})"))
        if user_data.get("NomeContato"): pdf.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {user_data.get('NomeContato')}"))
        if user_data.get("Telefone"): pdf.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {user_data.get('Telefone')}"))
        pdf.ln(3)
        pdf.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral: {diag_data.get('Média Geral','N/A')} | GUT Média: {diag_data.get('GUT Média','N/A')}")); pdf.ln(3)

        if medias_cat:
            pdf.set_font("Arial", 'B', 11); pdf.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria:")); pdf.set_font("Arial", size=10)
            for cat, media in medias_cat.items(): pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat}: {media:.2f}")); pdf.ln(1)
            pdf.ln(5)

        for titulo, campo in [("Resumo (Cliente):", "Diagnóstico"), ("Análise (Cliente):", "Análise do Cliente"), ("Comentários (Consultor):", "Comentarios_Admin")]:
            valor = diag_data.get(campo, "")
            if valor and not pd.isna(valor) and str(valor).strip():
                pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output(titulo))
                pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(str(valor))); pdf.ln(3)
        
        pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas e Análises:"))
        categorias = perguntas_df["Categoria"].unique() if not perguntas_df.empty and "Categoria" in perguntas_df.columns else []
        for categoria in categorias:
            pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria}")); pdf.set_font("Arial", size=9)
            perg_cat = perguntas_df[perguntas_df["Categoria"] == categoria]
            for _, p_row in perg_cat.iterrows():
                p_texto = p_row["Pergunta"]
                resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto, "N/R")) 
                analise_texto = None
                if "[Matriz GUT]" in p_texto:
                    g,u,t,score=0,0,0,0
                    if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                    elif isinstance(resp, str): 
                        try: data_gut=json.loads(resp.replace("'",'"'));g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                        except: pass 
                    score = g*u*t
                    pdf.multi_cell(0,6,pdf_safe_text_output(f"  - {p_texto.replace(' [Matriz GUT]','')}: G={g}, U={u}, T={t} (Score: {score})"))
                    analise_texto = obter_analise_para_resposta(p_texto, score, analises_df)
                else:
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {p_texto}: {resp}"))
                    analise_texto = obter_analise_para_resposta(p_texto, resp, analises_df)
                if analise_texto:
                    pdf.set_font("Arial", 'I', 8); pdf.set_text_color(100,100,100) 
                    pdf.multi_cell(0, 5, pdf_safe_text_output(f"    Análise: {analise_texto}"))
                    pdf.set_text_color(0,0,0); pdf.set_font("Arial", size=9) 
            pdf.ln(2)
        pdf.ln(3)
        pdf.add_page(); pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf.ln(5); pdf.set_font("Arial", size=10)
        gut_cards = []
        if not perguntas_df.empty: 
            for _, p_row in perguntas_df.iterrows():
                p_texto = p_row["Pergunta"]
                if "[Matriz GUT]" in p_texto:
                    resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto)) 
                    g,u,t,score=0,0,0,0
                    if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                    elif isinstance(resp, str):
                        try:data_gut=json.loads(resp.replace("'",'"'));g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                        except: pass
                    score = g*u*t
                    prazo = "N/A"
                    if score >= 75: prazo = "15 dias"
                    elif score >= 40: prazo = "30 dias"
                    elif score >= 20: prazo = "45 dias"
                    elif score > 0: prazo = "60 dias"
                    else: continue 
                    if prazo != "N/A": gut_cards.append({"Tarefa": p_texto.replace(" [Matriz GUT]", ""),"Prazo": prazo, "Score": score})
        if gut_cards:
            sorted_cards = sorted(gut_cards, key=lambda x: (int(x["Prazo"].split(" ")[0]), -x["Score"])) 
            for card in sorted_cards: pdf.multi_cell(0,6,pdf_safe_text_output(f"Prazo: {card['Prazo']} - Tarefa: {card['Tarefa']} (Score GUT: {card['Score']})"))
        else: pdf.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf_path = tmpfile.name; pdf.output(pdf_path)
        return pdf_path
    except Exception as e: st.error(f"Erro crítico ao gerar PDF: {e}"); return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v11") 
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v11"): 
        u = st.text_input("Usuário", key="admin_u_v11"); p = st.text_input("Senha", type="password", key="admin_p_v11")
        if st.form_submit_button("Entrar"):
            try:
                df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                if not df_creds[(df_creds["Usuario"] == u) & (df_creds["Senha"] == p)].empty:
                    st.session_state.admin_logado = True; st.success("Login admin OK!"); st.rerun()
                else: st.error("Usuário/senha admin inválidos.")
            except Exception as e: st.error(f"Erro login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_v11"): 
        c = st.text_input("CNPJ", key="cli_c_v11", value=st.session_state.get("last_cnpj_input",""))
        s = st.text_input("Senha", type="password", key="cli_s_v11")
        if st.form_submit_button("Entrar"):
            st.session_state.last_cnpj_input = c
            try:
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                if "JaVisualizouInstrucoes" not in users_df.columns: users_df["JaVisualizouInstrucoes"] = "False"
                if "DiagnosticosDisponiveis" not in users_df.columns: users_df["DiagnosticosDisponiveis"] = 1
                if "TotalDiagnosticosRealizados" not in users_df.columns: users_df["TotalDiagnosticosRealizados"] = 0
                
                users_df["JaVisualizouInstrucoes"] = users_df["JaVisualizouInstrucoes"].astype(str) 
                users_df["DiagnosticosDisponiveis"] = pd.to_numeric(users_df["DiagnosticosDisponiveis"], errors='coerce').fillna(1).astype(int)
                users_df["TotalDiagnosticosRealizados"] = pd.to_numeric(users_df["TotalDiagnosticosRealizados"], errors='coerce').fillna(0).astype(int)
                
                blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                if c in blocked_df["CNPJ"].values: st.error("CNPJ bloqueado."); st.stop()
                match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                if match.empty: st.error("CNPJ/senha inválidos."); st.stop()
                
                st.session_state.cliente_logado = True; st.session_state.cnpj = c
                st.session_state.user = match.iloc[0].to_dict()
                st.session_state.user["JaVisualizouInstrucoes"] = st.session_state.user.get("JaVisualizouInstrucoes", "False").lower() == "true"
                st.session_state.user["DiagnosticosDisponiveis"] = int(st.session_state.user.get("DiagnosticosDisponiveis", 1))
                st.session_state.user["TotalDiagnosticosRealizados"] = int(st.session_state.user.get("TotalDiagnosticosRealizados", 0))

                st.session_state.inicio_sessao_cliente = time.time()
                registrar_acao(c, "Login", "Usuário logou.")
                
                pode_fazer_novo_login = st.session_state.user["DiagnosticosDisponiveis"] > st.session_state.user["TotalDiagnosticosRealizados"]
                st.session_state.cliente_page = "Instruções" if not st.session_state.user["JaVisualizouInstrucoes"] \
                                               else ("Novo Diagnóstico" if pode_fazer_novo_login \
                                               else "Painel Principal")
                
                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}" 
                st.session_state.respostas_atuais_diagnostico = {} 
                st.session_state.progresso_diagnostico_percentual = 0
                st.session_state.progresso_diagnostico_contagem = (0,0)
                st.session_state.feedbacks_respostas = {}
                st.session_state.diagnostico_enviado_sucesso = False 

                st.success("Login cliente OK!"); st.rerun()
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    with st.sidebar.expander("Meu Perfil", expanded=False):
        logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
        if logo_cliente_path: st.image(logo_cliente_path, width=100)
        st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
        st.write(f"**CNPJ:** {st.session_state.cnpj}")
        st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
        st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")
        diagnosticos_restantes = st.session_state.user.get('DiagnosticosDisponiveis', 0) - st.session_state.user.get('TotalDiagnosticosRealizados', 0)
        st.write(f"**Diagnósticos Restantes:** {diagnosticos_restantes if diagnosticos_restantes > 0 else 0}")
        st.write(f"**Total Realizados:** {st.session_state.user.get('TotalDiagnosticosRealizados', 0)}")

    menu_options_cli = ["Instruções", "Novo Diagnóstico", "Painel Principal"]
    try: current_idx_cli = menu_options_cli.index(st.session_state.cliente_page)
    except ValueError: current_idx_cli = 0; st.session_state.cliente_page = menu_options_cli[0]
    
    selected_page_cli = st.sidebar.radio("Menu Cliente", menu_options_cli, index=current_idx_cli, key="cli_menu_v11") 
    if selected_page_cli != st.session_state.cliente_page:
        st.session_state.cliente_page = selected_page_cli; st.rerun()

    if st.sidebar.button("⬅️ Sair do Portal Cliente", key="logout_cliente_v11"): 
        keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input']]
        for key in keys_to_clear: del st.session_state[key]
        for key_d, value_d in default_session_state.items():
             if key_d not in ['admin_logado', 'last_cnpj_input']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False; st.rerun()

    if st.session_state.cliente_page == "Instruções":
        st.subheader("📖 Instruções do Sistema de Diagnóstico")
        st.markdown("""(Seu texto completo das instruções aqui...)""") 
        if st.button("Entendi, prosseguir", key="btn_instrucoes_v11"): 
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True") 
            if st.session_state.user: st.session_state.user["JaVisualizouInstrucoes"] = True
            
            pode_fazer_novo_inst = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_inst else "Painel Principal"
            st.rerun()

    elif st.session_state.cliente_page == "Painel Principal":
        st.subheader("📌 Meu Painel de Diagnósticos")
        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf:
                    st.download_button(label="📄 Baixar PDF do Diagnóstico Recém-Enviado", data=f_pdf,
                                       file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                       key="dl_novo_diag_painel_v11") 
                st.session_state.pdf_gerado_path = None 
                st.session_state.pdf_gerado_filename = None
            st.session_state.diagnostico_enviado_sucesso = False

        st.markdown("#### 📁 Diagnósticos Anteriores")
        try:
            df_antigos = pd.read_csv(arquivo_csv, dtype={'CNPJ': str}, encoding='utf-8')
            df_cliente_diags = df_antigos[df_antigos["CNPJ"] == st.session_state.cnpj]
            if df_cliente_diags.empty: st.info("Nenhum diagnóstico anterior.")
            else:
                df_cliente_diags = df_cliente_diags.sort_values(by="Data", ascending=False)
                perguntas_df_para_painel = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_para_painel.columns: perguntas_df_para_painel["Categoria"] = "Geral"
                analises_df_para_painel = carregar_analises_perguntas()

                for idx_row_diag, row_diag_data in df_cliente_diags.iterrows():
                    exp_key = f"exp_diag_v11_{idx_row_diag}_{row_diag_data['Data'].replace(' ','_').replace(':','-')}" 
                    with st.expander(f"📅 {row_diag_data['Data']} - {row_diag_data['Empresa']}", key=exp_key):
                        cols_metricas = st.columns(2)
                        cols_metricas[0].metric("Média Geral", f"{pd.to_numeric(row_diag_data.get('Média Geral'), errors='coerce'):.2f}" if pd.notna(row_diag_data.get('Média Geral')) else "N/A")
                        cols_metricas[1].metric("GUT Média (G*U*T)", f"{pd.to_numeric(row_diag_data.get('GUT Média'), errors='coerce'):.2f}" if pd.notna(row_diag_data.get('GUT Média')) else "N/A")
                        st.write(f"**Resumo (Cliente):** {row_diag_data.get('Diagnóstico', 'N/P')}")
                        
                        st.markdown("**Respostas e Análises Detalhadas:**")
                        if not perguntas_df_para_painel.empty:
                            for cat_loop in sorted(perguntas_df_para_painel["Categoria"].unique()): 
                                st.markdown(f"##### Categoria: {cat_loop}")
                                perg_cat_loop = perguntas_df_para_painel[perguntas_df_para_painel["Categoria"] == cat_loop]
                                for _, p_row_loop in perg_cat_loop.iterrows():
                                    p_texto_loop = p_row_loop["Pergunta"]
                                    resp_loop = row_diag_data.get(p_texto_loop, "N/R (Não Respondido ou Pergunta Nova)")
                                    st.markdown(f"**{p_texto_loop.split('[')[0].strip()}:**")
                                    st.markdown(f"> {resp_loop}") 
                                    valor_para_analise = resp_loop
                                    if "[Matriz GUT]" in p_texto_loop:
                                        g,u,t,score_gut_loop=0,0,0,0
                                        if isinstance(resp_loop, dict): 
                                            g,u,t=int(resp_loop.get("G",0)),int(resp_loop.get("U",0)),int(resp_loop.get("T",0))
                                        elif isinstance(resp_loop, str):
                                            try: 
                                                data_gut_loop=json.loads(resp_loop.replace("'",'"'))
                                                g,u,t=int(data_gut_loop.get("G",0)),int(data_gut_loop.get("U",0)),int(data_gut_loop.get("T",0))
                                            except (json.JSONDecodeError, TypeError): pass 
                                        score_gut_loop = g*u*t
                                        valor_para_analise = score_gut_loop
                                        st.caption(f"G={g}, U={u}, T={t} (Score GUT: {score_gut_loop})")
                                    analise_texto_painel = obter_analise_para_resposta(p_texto_loop, valor_para_analise, analises_df_para_painel)
                                    if analise_texto_painel:
                                        st.markdown(f"<div class='analise-pergunta-cliente'><b>Análise Consultor:</b> {analise_texto_painel}</div>", unsafe_allow_html=True)
                                st.markdown("---") 
                        else: st.caption("Estrutura de perguntas não carregada para detalhar respostas.")

                        if st.button("📄 Baixar PDF deste Diagnóstico", key=f"dl_pdf_antigo_v11_{idx_row_diag}"): 
                            medias_cat_pdf_antigo = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in row_diag_data.items() if "Media_Cat_" in k and pd.notna(v)}
                            pdf_path_antigo = gerar_pdf_diagnostico_completo(row_diag_data.to_dict(), st.session_state.user, perguntas_df_para_painel, row_diag_data.to_dict(), medias_cat_pdf_antigo, analises_df_para_painel)
                            if pdf_path_antigo:
                                with open(pdf_path_antigo, "rb") as f_antigo:
                                    st.download_button("Download PDF Confirmado", f_antigo, file_name=f"diag_{sanitize_column_name(row_diag_data['Empresa'])}_{str(row_diag_data['Data']).replace(':','-').replace(' ','_')}.pdf", mime="application/pdf", key=f"dl_confirm_antigo_v11_{idx_row_diag}") 
                                registrar_acao(st.session_state.cnpj, "Download PDF (Painel)", f"Baixou PDF de {row_diag_data['Data']}")
                            else: st.error("Erro ao gerar PDF para este diagnóstico.")
                        st.divider() 
        except Exception as e: st.error(f"Erro ao carregar painel do cliente: {e}"); st.exception(e)

    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader("📋 Formulário de Novo Diagnóstico")
        
        pode_fazer_novo_form = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
        if not pode_fazer_novo_form:
            st.warning("Você não tem diagnósticos disponíveis. Para realizar um novo, por favor, entre em contato com o administrador para liberação.")
            if st.button("Voltar ao Painel Principal", key="voltar_painel_novo_diag_bloq_v11"): st.session_state.cliente_page = "Painel Principal"; st.rerun() 
            st.stop()
        
        if st.session_state.diagnostico_enviado_sucesso: 
            st.success("🎯 Seu diagnóstico foi enviado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf_dl_sucesso:
                    st.download_button(label="📄 Baixar PDF do Diagnóstico Enviado", data=f_pdf_dl_sucesso,
                                       file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                       key="dl_pdf_sucesso_novo_diag_v11") 
            if st.button("Ir para o Painel Principal", key="ir_painel_apos_envio_sucesso_v11"): 
                st.session_state.cliente_page = "Painel Principal"
                st.session_state.diagnostico_enviado_sucesso = False; st.session_state.pdf_gerado_path = None; st.session_state.pdf_gerado_filename = None
                st.rerun()
            st.stop()

        try: perguntas_df_formulario = pd.read_csv(perguntas_csv, encoding='utf-8')
        except Exception as e: st.error(f"Erro ao carregar perguntas: {e}"); st.stop()
        if perguntas_df_formulario.empty: st.warning("Nenhuma pergunta cadastrada."); st.stop()
        if "Categoria" not in perguntas_df_formulario.columns: perguntas_df_formulario["Categoria"] = "Geral"

        total_perguntas_form = len(perguntas_df_formulario)
        if st.session_state.progresso_diagnostico_contagem[1] != total_perguntas_form:
            st.session_state.progresso_diagnostico_contagem = (st.session_state.progresso_diagnostico_contagem[0], total_perguntas_form)

        progresso_ph_novo = st.empty()

        def calcular_e_mostrar_progresso_novo(): 
            respondidas_novo = 0
            total_q_novo = st.session_state.progresso_diagnostico_contagem[1]
            if total_q_novo == 0: 
                st.session_state.progresso_diagnostico_percentual = 0
                progresso_ph_novo.info(f"📊 Progresso: 0 de 0 respondidas (0%)")
                return

            for _, p_row_prog_novo in perguntas_df_formulario.iterrows():
                p_texto_prog_novo = p_row_prog_novo["Pergunta"]
                resp_prog_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_prog_novo)
                if resp_prog_novo is not None:
                    if "[Matriz GUT]" in p_texto_prog_novo:
                        if isinstance(resp_prog_novo, dict) and (int(resp_prog_novo.get("G",0)) > 0 or int(resp_prog_novo.get("U",0)) > 0 or int(resp_prog_novo.get("T",0)) > 0): respondidas_novo +=1
                    elif "Escala" in p_texto_prog_novo: 
                        if resp_prog_novo != "Selecione": respondidas_novo +=1
                    elif isinstance(resp_prog_novo, str): 
                        if resp_prog_novo.strip() : respondidas_novo +=1
                    elif isinstance(resp_prog_novo, (int,float)):
                         if resp_prog_novo != 0 : respondidas_novo +=1 
            
            st.session_state.progresso_diagnostico_contagem = (respondidas_novo, total_q_novo)
            st.session_state.progresso_diagnostico_percentual = round((respondidas_novo / total_q_novo) * 100) if total_q_novo > 0 else 0
            progresso_ph_novo.info(f"📊 Progresso: {respondidas_novo} de {total_q_novo} respondidas ({st.session_state.progresso_diagnostico_percentual}%)")

        def on_change_resposta_novo(pergunta_txt_key_novo, widget_st_key_novo, tipo_pergunta_onchange_novo): 
            valor_widget_novo = st.session_state.get(widget_st_key_novo)
            if tipo_pergunta_onchange_novo == "GUT_G":
                current_gut_novo = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key_novo, {"G":0,"U":0,"T":0})
                current_gut_novo["G"] = valor_widget_novo
                st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
            elif tipo_pergunta_onchange_novo == "GUT_U":
                current_gut_novo = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key_novo, {"G":0,"U":0,"T":0})
                current_gut_novo["U"] = valor_widget_novo
                st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
            elif tipo_pergunta_onchange_novo == "GUT_T":
                current_gut_novo = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key_novo, {"G":0,"U":0,"T":0})
                current_gut_novo["T"] = valor_widget_novo
                st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
            else: st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = valor_widget_novo
            st.session_state.feedbacks_respostas[pergunta_txt_key_novo] = "Resposta registrada ✓"
            calcular_e_mostrar_progresso_novo()
        
        calcular_e_mostrar_progresso_novo()

        for categoria_novo in sorted(perguntas_df_formulario["Categoria"].unique()): 
            st.markdown(f"#### Categoria: {categoria_novo}")
            perg_cat_df_novo = perguntas_df_formulario[perguntas_df_formulario["Categoria"] == categoria_novo]
            for idx_novo, row_q_novo in perg_cat_df_novo.iterrows():
                p_texto_novo = str(row_q_novo["Pergunta"])
                w_key_novo = f"q_{st.session_state.id_formulario_atual}_{idx_novo}"
                cols_q_feedback = st.columns([0.9, 0.1])
                with cols_q_feedback[0]:
                    if "[Matriz GUT]" in p_texto_novo:
                        st.markdown(f"**{p_texto_novo.replace(' [Matriz GUT]', '')}**")
                        cols_gut_w_novo = st.columns(3)
                        gut_vals_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_novo, {"G":0,"U":0,"T":0})
                        key_g_n, key_u_n, key_t_n = f"{w_key_novo}_G", f"{w_key_novo}_U", f"{w_key_novo}_T"
                        cols_gut_w_novo[0].slider("Gravidade (0-5)",0,5,value=int(gut_vals_novo.get("G",0)), key=key_g_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_g_n, "GUT_G"))
                        cols_gut_w_novo[1].slider("Urgência (0-5)",0,5,value=int(gut_vals_novo.get("U",0)), key=key_u_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_u_n, "GUT_U"))
                        cols_gut_w_novo[2].slider("Tendência (0-5)",0,5,value=int(gut_vals_novo.get("T",0)), key=key_t_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_t_n, "GUT_T"))
                    elif "Pontuação (0-5)" in p_texto_novo:
                        st.slider(p_texto_novo,0,5,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Slider05"))
                    elif "Pontuação (0-10)" in p_texto_novo:
                        st.slider(p_texto_novo,0,10,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Slider010"))
                    elif "Texto Aberto" in p_texto_novo:
                        st.text_area(p_texto_novo,value=str(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,"")), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Texto"))
                    elif "Escala" in p_texto_novo:
                        opts_novo = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]
                        curr_val_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_novo, "Selecione")
                        st.selectbox(p_texto_novo, opts_novo, index=opts_novo.index(curr_val_novo) if curr_val_novo in opts_novo else 0, key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Escala"))
                    else:
                        st.slider(p_texto_novo,0,10,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "SliderDefault"))
                with cols_q_feedback[1]:
                    if st.session_state.feedbacks_respostas.get(p_texto_novo):
                        st.caption(f'<p class="feedback-saved" style="white-space: nowrap;">{st.session_state.feedbacks_respostas[p_texto_novo]}</p>', unsafe_allow_html=True)
                st.divider()
        
        key_obs_cli_n = f"obs_cli_diag_{st.session_state.id_formulario_atual}"
        st.text_area("Sua Análise/Observações (opcional):", value=st.session_state.respostas_atuais_diagnostico.get("__obs_cliente__", ""), 
                     key=key_obs_cli_n, on_change=on_change_resposta_novo, args=("__obs_cliente__", key_obs_cli_n, "ObsCliente"))
        key_res_cli_n = f"diag_resumo_diag_{st.session_state.id_formulario_atual}"
        st.text_area("✍️ Resumo/principais insights (para PDF):", value=st.session_state.respostas_atuais_diagnostico.get("__resumo_cliente__", ""), 
                     key=key_res_cli_n, on_change=on_change_resposta_novo, args=("__resumo_cliente__", key_res_cli_n, "ResumoCliente"))

        if st.button("✔️ Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v11"): 
            respostas_finais_envio_novo = st.session_state.respostas_atuais_diagnostico
            cont_resp_n, total_para_resp_n = st.session_state.progresso_diagnostico_contagem
            
            if cont_resp_n < total_para_resp_n:
                st.warning("Por favor, responda todas as perguntas para um diagnóstico completo.")
            elif not respostas_finais_envio_novo.get("__resumo_cliente__","").strip():
                st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
            else:
                soma_gut_n, count_gut_n = 0,0; respostas_csv_n = {}
                for p_n,r_n in respostas_finais_envio_novo.items():
                    if p_n.startswith("__"): continue
                    if "[Matriz GUT]" in p_n and isinstance(r_n, dict):
                        respostas_csv_n[p_n] = json.dumps(r_n)
                        g_n,u_n,t_n = int(r_n.get("G",0)), int(r_n.get("U",0)), int(r_n.get("T",0)); soma_gut_n += (g_n*u_n*t_n); count_gut_n +=1
                    else: respostas_csv_n[p_n] = r_n
                gut_media_n = round(soma_gut_n/count_gut_n,2) if count_gut_n > 0 else 0.0
                num_resp_n = [v_n for k_n,v_n in respostas_finais_envio_novo.items() if not k_n.startswith("__") and isinstance(v_n,(int,float)) and ("[Matriz GUT]" not in k_n) and ("Pontuação" in k_n)]
                media_geral_n = round(sum(num_resp_n)/len(num_resp_n),2) if num_resp_n else 0.0
                emp_nome_n = st.session_state.user.get("Empresa","N/D")
                
                nova_linha_diag_final_n = {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": st.session_state.cnpj,
                    "Nome": st.session_state.user.get("NomeContato", st.session_state.cnpj), "Email": "", "Empresa": emp_nome_n, 
                    "Média Geral": media_geral_n, "GUT Média": gut_media_n, "Observações": "", 
                    "Análise do Cliente": respostas_finais_envio_novo.get("__obs_cliente__",""),
                    "Diagnóstico": respostas_finais_envio_novo.get("__resumo_cliente__",""), "Comentarios_Admin": ""
                }
                nova_linha_diag_final_n.update(respostas_csv_n)
                medias_cat_final_n = {}
                for cat_iter_n in perguntas_df_formulario["Categoria"].unique():
                    soma_c_n, cont_c_n = 0,0
                    for _,pr_n in perguntas_df_formulario[perguntas_df_formulario["Categoria"]==cat_iter_n].iterrows():
                        pt_n = pr_n["Pergunta"]; rv_n = respostas_finais_envio_novo.get(pt_n)
                        if isinstance(rv_n,(int,float)) and ("[Matriz GUT]" not in pt_n) and ("Pontuação" in pt_n): soma_c_n+=rv_n; cont_c_n+=1
                    mc_n = round(soma_c_n/cont_c_n,2) if cont_c_n>0 else 0.0
                    nova_linha_diag_final_n[f"Media_Cat_{sanitize_column_name(cat_iter_n)}"] = mc_n
                    medias_cat_final_n[cat_iter_n] = mc_n
                
                try: df_todos_diags_n = pd.read_csv(arquivo_csv, encoding='utf-8')
                except (FileNotFoundError, pd.errors.EmptyDataError): df_todos_diags_n = pd.DataFrame()
                for col_n_n in nova_linha_diag_final_n.keys():
                    if col_n_n not in df_todos_diags_n.columns: df_todos_diags_n[col_n_n] = pd.NA
                df_todos_diags_n = pd.concat([df_todos_diags_n, pd.DataFrame([nova_linha_diag_final_n])], ignore_index=True)
                df_todos_diags_n.to_csv(arquivo_csv, index=False, encoding='utf-8')

                total_realizados_atual = st.session_state.user.get("TotalDiagnosticosRealizados", 0)
                update_user_data(st.session_state.cnpj, "TotalDiagnosticosRealizados", total_realizados_atual + 1)
                if st.session_state.user: st.session_state.user["TotalDiagnosticosRealizados"] = total_realizados_atual + 1
                
                registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", "Cliente enviou novo diagnóstico.")
                analises_df_para_pdf_n = carregar_analises_perguntas()
                pdf_path_gerado_n = gerar_pdf_diagnostico_completo(nova_linha_diag_final_n, st.session_state.user, perguntas_df_formulario, respostas_finais_envio_novo, medias_cat_final_n, analises_df_para_pdf_n)
                
                st.session_state.diagnostico_enviado_sucesso = True
                if pdf_path_gerado_n:
                    st.session_state.pdf_gerado_path = pdf_path_gerado_n
                    st.session_state.pdf_gerado_filename = f"diagnostico_{sanitize_column_name(emp_nome_n)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                st.session_state.respostas_atuais_diagnostico = {}
                st.session_state.progresso_diagnostico_percentual = 0
                st.session_state.progresso_diagnostico_contagem = (0,total_perguntas_form) 
                st.session_state.feedbacks_respostas = {}
                st.rerun() 

# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    try:
        st.sidebar.image("https://via.placeholder.com/150x75.png?text=Sua+Logo+Admin", width=150)
    except Exception as e_img_admin:
        st.sidebar.caption(f"Logo admin não carregada: {e_img_admin}")

    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("🚪 Sair do Painel Admin", key="logout_admin_v11"): 
        st.session_state.admin_logado = False; st.rerun()

    menu_admin_options = ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Perguntas", 
                          "Gerenciar Análises de Perguntas", "Gerenciar Clientes", "Gerenciar Administradores"]
    menu_admin = st.sidebar.selectbox("Funcionalidades Admin:", menu_admin_options, key="admin_menu_selectbox_v11") 
    st.header(f"🔑 Painel Admin: {menu_admin}")

    # CARREGAR DADOS NECESSÁRIOS PARA O PAINEL ADMIN (uma vez, se possível)
    try:
        df_usuarios_admin = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        if "DiagnosticosDisponiveis" not in df_usuarios_admin.columns: df_usuarios_admin["DiagnosticosDisponiveis"] = 1
        if "TotalDiagnosticosRealizados" not in df_usuarios_admin.columns: df_usuarios_admin["TotalDiagnosticosRealizados"] = 0
        df_usuarios_admin["DiagnosticosDisponiveis"] = pd.to_numeric(df_usuarios_admin["DiagnosticosDisponiveis"], errors='coerce').fillna(1).astype(int)
        df_usuarios_admin["TotalDiagnosticosRealizados"] = pd.to_numeric(df_usuarios_admin["TotalDiagnosticosRealizados"], errors='coerce').fillna(0).astype(int)

    except FileNotFoundError:
        st.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado. Algumas funcionalidades do painel podem ser limitadas.")
        df_usuarios_admin = pd.DataFrame(columns=colunas_base_usuarios) 
    except Exception as e_load_users_admin:
        st.error(f"Erro ao carregar dados de usuários para o painel admin: {e_load_users_admin}")
        df_usuarios_admin = pd.DataFrame(columns=colunas_base_usuarios)


    if menu_admin == "Visão Geral e Diagnósticos":
        st.subheader("📊 Visão Geral e Indicadores de Diagnósticos")
        diagnosticos_df_admin_orig = pd.DataFrame()
        admin_data_carregada_com_sucesso = False
        
        if not os.path.exists(arquivo_csv):
            st.error(f"ATENÇÃO: O arquivo de diagnósticos '{arquivo_csv}' não foi encontrado.")
        elif os.path.getsize(arquivo_csv) == 0:
            st.warning(f"O arquivo de diagnósticos '{arquivo_csv}' está completamente vazio.")
        else:
            try:
                diagnosticos_df_admin_orig = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                if 'Data' in diagnosticos_df_admin_orig.columns:
                    diagnosticos_df_admin_orig['Data'] = pd.to_datetime(diagnosticos_df_admin_orig['Data'], errors='coerce')
                if not diagnosticos_df_admin_orig.empty:
                    admin_data_carregada_com_sucesso = True
                else: st.info("Arquivo de diagnósticos lido, mas sem dados.")
            except pd.errors.EmptyDataError: st.warning(f"Arquivo '{arquivo_csv}' parece vazio ou só com cabeçalhos.")
            except Exception as e: st.error(f"ERRO AO CARREGAR DIAGNÓSTICOS: {e}"); st.exception(e)

        # --- MÉTRICAS GLOBAIS DO SISTEMA ---
        st.markdown("#### Métricas Gerais do Sistema")
        col_mg1, col_mg2 = st.columns(2)
        total_clientes_cadastrados_sistema = len(df_usuarios_admin)
        col_mg1.metric("👥 Total de Clientes Cadastrados", total_clientes_cadastrados_sistema)

        if admin_data_carregada_com_sucesso:
            total_diagnosticos_sistema = len(diagnosticos_df_admin_orig)
            col_mg2.metric("📋 Total de Diagnósticos Realizados (Sistema)", total_diagnosticos_sistema)
        else:
            col_mg2.metric("📋 Total de Diagnósticos Realizados (Sistema)", 0)
        st.divider()

        # --- FILTROS PARA ANÁLISE DETALHADA ---
        st.markdown("#### Filtros para Análise Detalhada de Diagnósticos")
        col_f1, col_f2, col_f3 = st.columns(3)
        empresas_lista_admin_filtro = []
        if admin_data_carregada_com_sucesso and "Empresa" in diagnosticos_df_admin_orig.columns:
            empresas_lista_admin_filtro = sorted(diagnosticos_df_admin_orig["Empresa"].astype(str).unique().tolist())
        
        with col_f1:
            emp_sel_admin = st.selectbox("Filtrar por Empresa:", ["Todos os Clientes"] + empresas_lista_admin_filtro, key="admin_filtro_emp_v11")
        with col_f2:
            dt_ini_admin = st.date_input("Data Início dos Diagnósticos:", value=None, key="admin_dt_ini_v11")
        with col_f3:
            dt_fim_admin = st.date_input("Data Fim dos Diagnósticos:", value=None, key="admin_dt_fim_v11")
        st.divider()

        # --- APLICAÇÃO DOS FILTROS E EXIBIÇÃO DOS DADOS FILTRADOS ---
        if admin_data_carregada_com_sucesso:
            df_diagnosticos_contexto = diagnosticos_df_admin_orig.copy()
            df_usuarios_contexto = df_usuarios_admin.copy()

            if emp_sel_admin != "Todos os Clientes":
                df_diagnosticos_contexto = df_diagnosticos_contexto[df_diagnosticos_contexto["Empresa"] == emp_sel_admin]
                df_usuarios_contexto = df_usuarios_contexto[df_usuarios_contexto["Empresa"] == emp_sel_admin]
            
            # Aplicar filtro de data apenas aos diagnósticos
            df_diagnosticos_filtrados_para_metricas = df_diagnosticos_contexto.copy() # Para métricas de diagnóstico
            if dt_ini_admin:
                df_diagnosticos_filtrados_para_metricas = df_diagnosticos_filtrados_para_metricas[df_diagnosticos_filtrados_para_metricas['Data'] >= pd.to_datetime(dt_ini_admin)]
            if dt_fim_admin:
                df_diagnosticos_filtrados_para_metricas = df_diagnosticos_filtrados_para_metricas[df_diagnosticos_filtrados_para_metricas['Data'] < pd.to_datetime(dt_fim_admin) + pd.Timedelta(days=1)]

            st.markdown(f"#### Análise para: **{emp_sel_admin}** (Período de Diagnósticos: {dt_ini_admin or 'Início'} a {dt_fim_admin or 'Fim'})")
            
            # Métricas de Clientes (baseadas nos filtros de Empresa e Data aplicados aos diagnósticos)
            cnpjs_usuarios_no_contexto_empresa = set(df_usuarios_contexto['CNPJ'].unique())
            cnpjs_com_diagnostico_no_periodo_e_empresa = set(df_diagnosticos_filtrados_para_metricas['CNPJ'].unique())
            
            clientes_sem_diagnostico_no_filtro = len(cnpjs_usuarios_no_contexto_empresa - cnpjs_com_diagnostico_no_periodo_e_empresa)
            clientes_com_pelo_menos_um_diag_no_filtro = len(cnpjs_com_diagnostico_no_periodo_e_empresa)
            
            clientes_com_mais_de_um_diag_no_filtro = 0
            if not df_diagnosticos_filtrados_para_metricas.empty:
                contagem_diag_por_cliente_no_filtro = df_diagnosticos_filtrados_para_metricas.groupby('CNPJ').size()
                clientes_com_mais_de_um_diag_no_filtro = len(contagem_diag_por_cliente_no_filtro[contagem_diag_por_cliente_no_filtro > 1])

            col_pm1, col_pm2, col_pm3 = st.columns(3)
            col_pm1.metric("Clientes SEM Diagnóstico (no filtro)", clientes_sem_diagnostico_no_filtro)
            col_pm2.metric("Clientes COM Diagnóstico (no filtro)", clientes_com_pelo_menos_um_diag_no_filtro)
            col_pm3.metric("Clientes COM MAIS DE 1 Diagnóstico (no filtro)", clientes_com_mais_de_um_diag_no_filtro)
            st.divider()

            if df_diagnosticos_filtrados_para_metricas.empty:
                st.info(f"Nenhum diagnóstico encontrado para os filtros aplicados.")
            else:
                st.markdown(f"##### Indicadores da Seleção Filtrada de Diagnósticos")
                col_if_adm1, col_if_adm2, col_if_adm3 = st.columns(3)
                col_if_adm1.metric("📦 Diagnósticos na Seleção", len(df_diagnosticos_filtrados_para_metricas))
                media_geral_filtrada_adm = pd.to_numeric(df_diagnosticos_filtrados_para_metricas.get("Média Geral"), errors='coerce').mean()
                col_if_adm2.metric("📈 Média Geral da Seleção", f"{media_geral_filtrada_adm:.2f}" if pd.notna(media_geral_filtrada_adm) else "N/A")
                gut_media_filtrada_adm = pd.to_numeric(df_diagnosticos_filtrados_para_metricas.get("GUT Média"), errors='coerce').mean()
                col_if_adm3.metric("🔥 GUT Média da Seleção", f"{gut_media_filtrada_adm:.2f}" if pd.notna(gut_media_filtrada_adm) else "N/A")
                st.divider()
                
                st.markdown(f"##### Diagnósticos Detalhados (Seleção Filtrada)")
                st.dataframe(df_diagnosticos_filtrados_para_metricas.sort_values(by="Data", ascending=False).reset_index(drop=True))
                # ... (Lógica para Detalhar, Comentar e Baixar PDF específico mantida como antes)
        
        elif not os.path.exists(arquivo_csv) or (os.path.exists(arquivo_csv) and os.path.getsize(arquivo_csv) == 0) :
             pass 
        else: 
            st.info("Não há dados de diagnóstico carregados para aplicar filtros ou exibir informações.")


    elif menu_admin == "Histórico de Usuários":
        st.subheader("📜 Histórico de Ações")
        try:
            df_historico_completo = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
            df_usuarios_para_filtro_hist = pd.read_csv(usuarios_csv, encoding='utf-8', usecols=['CNPJ', 'Empresa', 'NomeContato'], dtype={'CNPJ': str})
        except FileNotFoundError:
            st.error("Arquivo de histórico ou usuários não encontrado.")
            df_historico_completo = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"]) # Evita erro adiante
            df_usuarios_para_filtro_hist = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato'])
        except Exception as e:
            st.error(f"Erro ao carregar dados para o histórico: {e}")
            df_historico_completo = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
            df_usuarios_para_filtro_hist = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato'])

        st.markdown("#### Filtros do Histórico")
        col_h_f1, col_h_f2 = st.columns(2)
        empresas_hist_list = ["Todas"]
        if not df_usuarios_para_filtro_hist.empty:
            empresas_hist_list.extend(sorted(df_usuarios_para_filtro_hist['Empresa'].astype(str).unique().tolist()))
        
        emp_sel_hist = col_h_f1.selectbox("Filtrar por Empresa:", empresas_hist_list, key="hist_emp_sel_v11")
        nome_cnpj_busca_hist = col_h_f2.text_input("Buscar por Nome do Contato ou CNPJ:", key="hist_nome_cnpj_busca_v11")

        df_historico_filtrado = df_historico_completo.copy()

        if emp_sel_hist != "Todas":
            cnpjs_da_empresa = df_usuarios_para_filtro_hist[df_usuarios_para_filtro_hist['Empresa'] == emp_sel_hist]['CNPJ'].tolist()
            df_historico_filtrado = df_historico_filtrado[df_historico_filtrado['CNPJ'].isin(cnpjs_da_empresa)]
        
        if nome_cnpj_busca_hist.strip():
            busca_lower = nome_cnpj_busca_hist.strip().lower()
            cnpjs_match_nome = []
            if not df_usuarios_para_filtro_hist.empty:
                cnpjs_match_nome = df_usuarios_para_filtro_hist[
                    df_usuarios_para_filtro_hist['NomeContato'].astype(str).str.lower().str.contains(busca_lower, na=False)
                ]['CNPJ'].tolist()
            
            df_historico_filtrado = df_historico_filtrado[
                df_historico_filtrado['CNPJ'].isin(cnpjs_match_nome) | 
                df_historico_filtrado['CNPJ'].astype(str).str.lower().str.contains(busca_lower) |
                df_historico_filtrado['Ação'].astype(str).str.lower().str.contains(busca_lower) | # Adiciona busca na Ação
                df_historico_filtrado['Descrição'].astype(str).str.lower().str.contains(busca_lower) # Adiciona busca na Descrição
            ]

        st.markdown("#### Registros do Histórico")
        if not df_historico_filtrado.empty:
            st.dataframe(df_historico_filtrado.sort_values(by="Data", ascending=False))
        else:
            st.info("Nenhum registro de histórico encontrado para os filtros aplicados.")


    elif menu_admin == "Gerenciar Perguntas":
        # ... (Código da seção Gerenciar Perguntas mantido)
        st.subheader("📝 Gerenciar Perguntas do Diagnóstico")
        tabs_perg_admin = st.tabs(["📋 Perguntas Atuais", "➕ Adicionar Nova Pergunta"])
        try:
            perguntas_df_admin_gp = pd.read_csv(perguntas_csv, encoding='utf-8')
            if "Categoria" not in perguntas_df_admin_gp.columns: perguntas_df_admin_gp["Categoria"] = "Geral"
        except (FileNotFoundError, pd.errors.EmptyDataError):
            perguntas_df_admin_gp = pd.DataFrame(columns=colunas_base_perguntas)
        
        with tabs_perg_admin[0]:
            if perguntas_df_admin_gp.empty: st.info("Nenhuma pergunta cadastrada.")
            else:
                for i_p_admin, row_p_admin in perguntas_df_admin_gp.iterrows():
                    cols_p_admin = st.columns([4, 2, 0.5, 0.5])
                    with cols_p_admin[0]:
                        nova_p_text_admin = st.text_input("Pergunta", value=str(row_p_admin["Pergunta"]), key=f"edit_p_txt_v11_{i_p_admin}")
                    with cols_p_admin[1]:
                        nova_cat_text_admin = st.text_input("Categoria", value=str(row_p_admin.get("Categoria", "Geral")), key=f"edit_p_cat_v11_{i_p_admin}")
                    with cols_p_admin[2]:
                        st.write(""); 
                        if st.button("💾", key=f"salvar_p_adm_v11_{i_p_admin}", help="Salvar"):
                            perguntas_df_admin_gp.loc[i_p_admin, "Pergunta"] = nova_p_text_admin
                            perguntas_df_admin_gp.loc[i_p_admin, "Categoria"] = nova_cat_text_admin
                            perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                            st.success(f"Pergunta {i_p_admin+1} atualizada."); st.rerun()
                    with cols_p_admin[3]:
                        st.write(""); 
                        if st.button("🗑️", key=f"deletar_p_adm_v11_{i_p_admin}", help="Deletar"):
                            perguntas_df_admin_gp = perguntas_df_admin_gp.drop(i_p_admin).reset_index(drop=True)
                            perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                            st.warning(f"Pergunta {i_p_admin+1} removida."); st.rerun()
                    st.divider()
        with tabs_perg_admin[1]:
            with st.form("form_nova_pergunta_admin_v11"):
                st.subheader("➕ Adicionar Nova Pergunta")
                nova_p_form_txt_admin = st.text_input("Texto da Pergunta", key="nova_p_input_admin_txt_v11")
                cat_existentes_gp = sorted(list(perguntas_df_admin_gp['Categoria'].astype(str).unique())) if not perguntas_df_admin_gp.empty else []
                cat_options_gp = ["Nova Categoria"] + cat_existentes_gp
                cat_selecionada_gp = st.selectbox("Categoria:", cat_options_gp, key="cat_select_admin_new_q_v11")
                nova_cat_form_admin_gp = st.text_input("Nome da Nova Categoria:", key="nova_cat_input_admin_new_q_v11") if cat_selecionada_gp == "Nova Categoria" else cat_selecionada_gp
                
                tipo_p_form_admin = st.selectbox("Tipo de Pergunta (será adicionado ao final do texto da pergunta):",
                                                 ["Pontuação (0-10)", "Pontuação (0-5)", "Texto Aberto", "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)", "[Matriz GUT]"],
                                                 key="tipo_p_select_admin_new_q_v11")
                add_p_btn_admin = st.form_submit_button("Adicionar Pergunta")
                if add_p_btn_admin:
                    if nova_p_form_txt_admin.strip() and nova_cat_form_admin_gp.strip():
                        p_completa_add_admin = f"{nova_p_form_txt_admin.strip()} [{tipo_p_form_admin.replace('[','').replace(']','')}]"
                        nova_entrada_p_add_admin = pd.DataFrame([[p_completa_add_admin, nova_cat_form_admin_gp.strip()]], columns=["Pergunta", "Categoria"])
                        perguntas_df_admin_gp = pd.concat([perguntas_df_admin_gp, nova_entrada_p_add_admin], ignore_index=True)
                        perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                        st.success(f"Pergunta adicionada!"); st.rerun()
                    else: st.warning("Texto da pergunta e categoria são obrigatórios.")

    elif menu_admin == "Gerenciar Análises de Perguntas":
        # ... (Código da seção Gerenciar Análises de Perguntas, como na versão anterior)
        st.subheader("💡 Gerenciar Análises Vinculadas às Perguntas")
        df_analises_existentes_admin = carregar_analises_perguntas()
        try: df_perguntas_formulario_admin = pd.read_csv(perguntas_csv, encoding='utf-8')
        except: df_perguntas_formulario_admin = pd.DataFrame(columns=colunas_base_perguntas)

        st.markdown("#### Adicionar Nova Análise")
        if df_perguntas_formulario_admin.empty:
            st.warning("Nenhuma pergunta cadastrada no formulário. Adicione perguntas primeiro em 'Gerenciar Perguntas'.")
        else:
            lista_perguntas_txt_admin = [""] + df_perguntas_formulario_admin["Pergunta"].unique().tolist()
            pergunta_selecionada_analise_admin = st.selectbox("Selecione a Pergunta para adicionar análise:", lista_perguntas_txt_admin, key="sel_perg_analise_v11") 

            if pergunta_selecionada_analise_admin:
                st.caption(f"Pergunta selecionada: {pergunta_selecionada_analise_admin}")
                
                tipo_condicao_analise_display_admin = st.selectbox("Tipo de Condição para a Análise:", 
                                                     ["Faixa Numérica (p/ Pontuação 0-X)", 
                                                      "Valor Exato (p/ Escala)", 
                                                      "Faixa de Score (p/ Matriz GUT)", 
                                                      "Análise Padrão (default para a pergunta)"], 
                                                     key="tipo_cond_analise_v11") 
                
                map_tipo_cond_to_csv_admin = {
                    "Faixa Numérica (p/ Pontuação 0-X)": "FaixaNumerica", 
                    "Valor Exato (p/ Escala)": "ValorExatoEscala", 
                    "Faixa de Score (p/ Matriz GUT)": "ScoreGUT", 
                    "Análise Padrão (default para a pergunta)": "Default"
                }
                tipo_condicao_csv_val_admin = map_tipo_cond_to_csv_admin[tipo_condicao_analise_display_admin]

                cond_val_min_ui_admin, cond_val_max_ui_admin, cond_val_exato_ui_admin = None, None, None
                if tipo_condicao_csv_val_admin == "FaixaNumerica":
                    cols_faixa_ui_admin = st.columns(2)
                    cond_val_min_ui_admin = cols_faixa_ui_admin[0].number_input("Valor Mínimo da Faixa", step=1.0, format="%.2f", key="cond_min_analise_v11") 
                    cond_val_max_ui_admin = cols_faixa_ui_admin[1].number_input("Valor Máximo da Faixa", step=1.0, format="%.2f", key="cond_max_analise_v11") 
                elif tipo_condicao_csv_val_admin == "ValorExatoEscala":
                    cond_val_exato_ui_admin = st.text_input("Valor Exato da Escala (ex: Baixo, Médio, Alto)", key="cond_exato_analise_v11") 
                elif tipo_condicao_csv_val_admin == "ScoreGUT":
                    cols_faixa_gut_ui_admin = st.columns(2)
                    cond_val_min_ui_admin = cols_faixa_gut_ui_admin[0].number_input("Score GUT Mínimo", step=1, key="cond_min_gut_analise_v11") 
                    cond_val_max_ui_admin = cols_faixa_gut_ui_admin[1].number_input("Score GUT Máximo (opcional, deixe 0 ou vazio se for 'acima de Mínimo')", value=0.0, step=1.0, format="%.0f", key="cond_max_gut_analise_v11") 

                texto_analise_nova_ui_admin = st.text_area("Texto da Análise:", height=150, key="txt_analise_nova_v11") 

                if st.button("💾 Salvar Nova Análise", key="salvar_analise_pergunta_v11"): 
                    if texto_analise_nova_ui_admin.strip():
                        nova_id_analise_admin = str(uuid.uuid4())
                        nova_entrada_analise_admin = {
                            "ID_Analise": nova_id_analise_admin, 
                            "TextoPerguntaOriginal": pergunta_selecionada_analise_admin,
                            "TipoCondicao": tipo_condicao_csv_val_admin,
                            "CondicaoValorMin": cond_val_min_ui_admin if cond_val_min_ui_admin is not None else pd.NA,
                            "CondicaoValorMax": cond_val_max_ui_admin if cond_val_max_ui_admin is not None and cond_val_max_ui_admin !=0 else pd.NA, 
                            "CondicaoValorExato": cond_val_exato_ui_admin if cond_val_exato_ui_admin else pd.NA,
                            "TextoAnalise": texto_analise_nova_ui_admin
                        }
                        df_analises_existentes_admin = pd.concat([df_analises_existentes_admin, pd.DataFrame([nova_entrada_analise_admin])], ignore_index=True)
                        df_analises_existentes_admin.to_csv(analises_perguntas_csv, index=False, encoding='utf-8')
                        st.success("Nova análise salva!"); st.rerun()
                    else: st.error("O texto da análise não pode estar vazio.")
        
        st.markdown("---"); st.subheader("📜 Análises Cadastradas")
        if df_analises_existentes_admin.empty: st.info("Nenhuma análise cadastrada.")
        else:
            df_display_analises = df_analises_existentes_admin.copy()
            for col_num_format in ['CondicaoValorMin', 'CondicaoValorMax']:
                if col_num_format in df_display_analises.columns:
                    df_display_analises[col_num_format] = pd.to_numeric(df_display_analises[col_num_format], errors='coerce').fillna("") 
            st.dataframe(df_display_analises)
            
            analise_del_id_admin = st.selectbox("Deletar Análise por ID:", [""] + df_analises_existentes_admin["ID_Analise"].astype(str).tolist(), key="del_analise_id_v11") 
            if st.button("🗑️ Deletar Análise", key="btn_del_analise_v11") and analise_del_id_admin: 
                df_analises_existentes_admin = df_analises_existentes_admin[df_analises_existentes_admin["ID_Analise"] != analise_del_id_admin]
                df_analises_existentes_admin.to_csv(analises_perguntas_csv, index=False, encoding='utf-8')
                st.warning("Análise deletada."); st.rerun()


    elif menu_admin == "Gerenciar Clientes":
        st.subheader("👥 Gerenciar Clientes")
        try:
            df_usuarios_gc = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
            if "DiagnosticosDisponiveis" not in df_usuarios_gc.columns: df_usuarios_gc["DiagnosticosDisponiveis"] = 1
            if "TotalDiagnosticosRealizados" not in df_usuarios_gc.columns: df_usuarios_gc["TotalDiagnosticosRealizados"] = 0
            df_usuarios_gc["DiagnosticosDisponiveis"] = pd.to_numeric(df_usuarios_gc["DiagnosticosDisponiveis"], errors='coerce').fillna(1).astype(int)
            df_usuarios_gc["TotalDiagnosticosRealizados"] = pd.to_numeric(df_usuarios_gc["TotalDiagnosticosRealizados"], errors='coerce').fillna(0).astype(int)
        except FileNotFoundError:
            st.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado.")
            df_usuarios_gc = pd.DataFrame(columns=colunas_base_usuarios)
        except Exception as e_gc_load_full:
            st.error(f"Erro ao carregar usuários: {e_gc_load_full}")
            df_usuarios_gc = pd.DataFrame(columns=colunas_base_usuarios)

        st.markdown("#### Lista de Clientes Cadastrados")
        if not df_usuarios_gc.empty:
            cols_display_gc = ["CNPJ", "Empresa", "NomeContato", "Telefone", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]
            st.dataframe(df_usuarios_gc[cols_display_gc])

            st.markdown("#### Ações de Cliente")
            clientes_lista_gc_ops = df_usuarios_gc.apply(lambda row: f"{row['Empresa']} ({row['CNPJ']})", axis=1).tolist()
            cliente_selecionado_str_gc = st.selectbox("Selecione o cliente para gerenciar:", [""] + clientes_lista_gc_ops, key="sel_cliente_gc_v11")

            if cliente_selecionado_str_gc:
                cnpj_selecionado_gc_val = cliente_selecionado_str_gc.split('(')[-1].replace(')','').strip()
                cliente_data_gc_val = df_usuarios_gc[df_usuarios_gc["CNPJ"] == cnpj_selecionado_gc_val].iloc[0]
                
                st.write(f"**Empresa:** {cliente_data_gc_val['Empresa']}")
                st.write(f"**Diagnósticos Disponíveis (Slots):** {cliente_data_gc_val['DiagnosticosDisponiveis']}")
                st.write(f"**Diagnósticos Já Realizados:** {cliente_data_gc_val['TotalDiagnosticosRealizados']}")
                
                if st.button(f"Conceder +1 Diagnóstico para {cliente_data_gc_val['Empresa']}", key=f"conceder_diag_gc_v11_{cnpj_selecionado_gc_val}"):
                    novos_disponiveis = cliente_data_gc_val['DiagnosticosDisponiveis'] + 1
                    if update_user_data(cnpj_selecionado_gc_val, "DiagnosticosDisponiveis", novos_disponiveis):
                        registrar_acao("ADMIN", "Concessão Diagnóstico", f"Admin concedeu +1 slot de diagnóstico para {cliente_data_gc_val['Empresa']} (CNPJ: {cnpj_selecionado_gc_val}). Total agora: {novos_disponiveis}")
                        st.success(f"+1 Slot de diagnóstico concedido para {cliente_data_gc_val['Empresa']}. Total agora: {novos_disponiveis}."); st.rerun()
                    else:
                        st.error("Falha ao conceder diagnóstico.")
                
                try: bloqueados_df_gc_check = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                except FileNotFoundError: bloqueados_df_gc_check = pd.DataFrame(columns=["CNPJ"])
                
                is_blocked_gc_check = cnpj_selecionado_gc_val in bloqueados_df_gc_check["CNPJ"].values
                if is_blocked_gc_check:
                    if st.button(f"Desbloquear Acesso Total para {cliente_data_gc_val['Empresa']}", key=f"desbloq_total_gc_v11_{cnpj_selecionado_gc_val}"):
                        bloqueados_df_gc_check = bloqueados_df_gc_check[bloqueados_df_gc_check["CNPJ"] != cnpj_selecionado_gc_val]
                        bloqueados_df_gc_check.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        st.success(f"Acesso total desbloqueado para {cliente_data_gc_val['Empresa']}."); st.rerun()
                else:
                    if st.button(f"Bloquear Acesso Total para {cliente_data_gc_val['Empresa']}", type="primary", key=f"bloq_total_gc_v11_{cnpj_selecionado_gc_val}"):
                        nova_entrada_bloqueio_gc_val = pd.DataFrame([{"CNPJ": cnpj_selecionado_gc_val}])
                        bloqueados_df_gc_check = pd.concat([bloqueados_df_gc_check, nova_entrada_bloqueio_gc_val], ignore_index=True)
                        bloqueados_df_gc_check.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        st.error(f"Acesso total bloqueado para {cliente_data_gc_val['Empresa']}."); st.rerun()
        else:
            st.info("Nenhum cliente cadastrado para gerenciar.")

        st.markdown("---")
        st.markdown("#### Adicionar Novo Cliente")
        with st.form("form_novo_cliente_v11", clear_on_submit=True):
            novo_cnpj_gc_form = st.text_input("CNPJ do Novo Cliente:")
            nova_senha_gc_form = st.text_input("Senha para o Novo Cliente:", type="password")
            nova_empresa_gc_form = st.text_input("Nome da Empresa do Novo Cliente:")
            novo_contato_gc_form = st.text_input("Nome do Contato (opcional):")
            novo_telefone_gc_form = st.text_input("Telefone do Contato (opcional):")
            submit_novo_cliente_gc_form = st.form_submit_button("Cadastrar Novo Cliente")

            if submit_novo_cliente_gc_form:
                if novo_cnpj_gc_form and nova_senha_gc_form and nova_empresa_gc_form:
                    if df_usuarios_gc.empty or (novo_cnpj_gc_form not in df_usuarios_gc["CNPJ"].values):
                        nova_linha_cliente_form = pd.DataFrame([{
                            "CNPJ": novo_cnpj_gc_form, "Senha": nova_senha_gc_form, "Empresa": nova_empresa_gc_form,
                            "NomeContato": novo_contato_gc_form, "Telefone": novo_telefone_gc_form,
                            "JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0
                        }])
                        df_usuarios_gc_updated = pd.concat([df_usuarios_gc, nova_linha_cliente_form], ignore_index=True)
                        df_usuarios_gc_updated.to_csv(usuarios_csv, index=False, encoding='utf-8')
                        st.success(f"Cliente {nova_empresa_gc_form} cadastrado com sucesso!"); st.rerun()
                    else: st.error("CNPJ já cadastrado.")
                else: st.error("CNPJ, Senha e Nome da Empresa são obrigatórios.")
    
    elif menu_admin == "Gerenciar Administradores":
        st.subheader("👮 Gerenciar Administradores")
        try:
            admins_df_mng = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
        except (FileNotFoundError, pd.errors.EmptyDataError):
            admins_df_mng = pd.DataFrame(columns=["Usuario", "Senha"])
        
        st.dataframe(admins_df_mng[["Usuario"]])
        st.markdown("---"); st.subheader("➕ Adicionar Novo Admin")
        with st.form("form_novo_admin_mng_v11"):
            novo_admin_user_mng = st.text_input("Usuário do Admin")
            novo_admin_pass_mng = st.text_input("Senha do Admin", type="password")
            adicionar_admin_btn_mng = st.form_submit_button("Adicionar Admin")
        if adicionar_admin_btn_mng:
            if novo_admin_user_mng and novo_admin_pass_mng:
                if novo_admin_user_mng in admins_df_mng["Usuario"].values:
                    st.error(f"Usuário '{novo_admin_user_mng}' já existe.")
                else:
                    novo_admin_data_mng = pd.DataFrame([[novo_admin_user_mng, novo_admin_pass_mng]], columns=["Usuario", "Senha"])
                    admins_df_mng = pd.concat([admins_df_mng, novo_admin_data_mng], ignore_index=True)
                    admins_df_mng.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                    st.success(f"Admin '{novo_admin_user_mng}' adicionado!"); st.rerun()
            else: st.warning("Preencha todos os campos.")
        
        st.markdown("---"); st.subheader("🗑️ Remover Admin")
        if not admins_df_mng.empty:
            admin_para_remover_mng = st.selectbox("Remover Admin:", options=[""] + admins_df_mng["Usuario"].tolist(), key="remove_admin_select_mng_v11")
            if st.button("Remover Admin Selecionado", type="primary", key="btn_remove_admin_v11") and admin_para_remover_mng:
                if len(admins_df_mng) == 1 and admin_para_remover_mng == admins_df_mng["Usuario"].iloc[0]:
                    st.error("Não é possível remover o único administrador.")
                else:
                    admins_df_mng = admins_df_mng[admins_df_mng["Usuario"] != admin_para_remover_mng]
                    admins_df_mng.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                    st.warning(f"Admin '{admin_para_remover_mng}' removido."); st.rerun()
        else: st.info("Nenhum administrador para remover.")


if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()