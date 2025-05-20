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
arquivo_csv = "diagnosticos_clientes.csv"
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
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone", "PodeFazerNovoDiagnostico", "JaVisualizouInstrucoes"]
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
    inicializar_csv(usuarios_csv, colunas_base_usuarios, defaults={"PodeFazerNovoDiagnostico": "True", "JaVisualizouInstrucoes": "False"}) # Salva como string True/False
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
            users_df.loc[idx, field] = str(value) # Salva como string
            users_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
            if 'user' in st.session_state and st.session_state.user and str(st.session_state.user.get('CNPJ')) == str(cnpj):
                st.session_state.user[field] = value # Atualiza na sessão com o tipo original
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
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v9_final") 
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v9_final"): 
        u = st.text_input("Usuário", key="admin_u_v9_final"); p = st.text_input("Senha", type="password", key="admin_p_v9_final")
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
    with st.form("form_cliente_login_v9_final"): 
        c = st.text_input("CNPJ", key="cli_c_v9_final", value=st.session_state.get("last_cnpj_input",""))
        s = st.text_input("Senha", type="password", key="cli_s_v9_final")
        if st.form_submit_button("Entrar"):
            st.session_state.last_cnpj_input = c
            try:
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                # Tratar colunas booleanas que podem não existir em arquivos antigos
                if "JaVisualizouInstrucoes" not in users_df.columns: users_df["JaVisualizouInstrucoes"] = "False"
                if "PodeFazerNovoDiagnostico" not in users_df.columns: users_df["PodeFazerNovoDiagnostico"] = "True"
                users_df["JaVisualizouInstrucoes"] = users_df["JaVisualizouInstrucoes"].astype(str) # Garantir que é string
                users_df["PodeFazerNovoDiagnostico"] = users_df["PodeFazerNovoDiagnostico"].astype(str) # Garantir que é string
                
                blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                if c in blocked_df["CNPJ"].values: st.error("CNPJ bloqueado."); st.stop()
                match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                if match.empty: st.error("CNPJ/senha inválidos."); st.stop()
                
                st.session_state.cliente_logado = True; st.session_state.cnpj = c
                st.session_state.user = match.iloc[0].to_dict()
                # Converter flags para booleano na sessão
                st.session_state.user["JaVisualizouInstrucoes"] = st.session_state.user.get("JaVisualizouInstrucoes", "False").lower() == "true"
                st.session_state.user["PodeFazerNovoDiagnostico"] = st.session_state.user.get("PodeFazerNovoDiagnostico", "True").lower() == "true"

                st.session_state.inicio_sessao_cliente = time.time()
                registrar_acao(c, "Login", "Usuário logou.")
                
                st.session_state.cliente_page = "Instruções" if not st.session_state.user["JaVisualizouInstrucoes"] \
                                               else ("Novo Diagnóstico" if st.session_state.user["PodeFazerNovoDiagnostico"] \
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

    menu_options_cli = ["Instruções", "Novo Diagnóstico", "Painel Principal"]
    try: current_idx_cli = menu_options_cli.index(st.session_state.cliente_page)
    except ValueError: current_idx_cli = 0; st.session_state.cliente_page = menu_options_cli[0]
    
    selected_page_cli = st.sidebar.radio("Menu Cliente", menu_options_cli, index=current_idx_cli, key="cli_menu_v9_final") 
    if selected_page_cli != st.session_state.cliente_page:
        st.session_state.cliente_page = selected_page_cli; st.rerun()

    if st.sidebar.button("⬅️ Sair do Portal Cliente", key="logout_cliente_v9_final"): 
        keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input']]
        for key in keys_to_clear: del st.session_state[key]
        for key_d, value_d in default_session_state.items():
             if key_d not in ['admin_logado', 'last_cnpj_input']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False; st.rerun()

    if st.session_state.cliente_page == "Instruções":
        st.subheader("📖 Instruções do Sistema de Diagnóstico")
        st.markdown("""(Seu texto completo das instruções aqui...)""") 
        if st.button("Entendi, prosseguir", key="btn_instrucoes_v9_final"): 
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", True)
            if st.session_state.user: st.session_state.user["JaVisualizouInstrucoes"] = True
            
            st.session_state.cliente_page = "Novo Diagnóstico" if st.session_state.user.get("PodeFazerNovoDiagnostico", True) else "Painel Principal"
            st.rerun()

    elif st.session_state.cliente_page == "Painel Principal":
        st.subheader("📌 Meu Painel de Diagnósticos")
        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf:
                    st.download_button(label="📄 Baixar PDF do Diagnóstico Recém-Enviado", data=f_pdf,
                                       file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                       key="dl_novo_diag_painel_v9_final") 
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
                    exp_key = f"exp_diag_v9_final_{idx_row_diag}_{row_diag_data['Data'].replace(' ','_').replace(':','-')}" 
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

                        if st.button("📄 Baixar PDF deste Diagnóstico", key=f"dl_pdf_antigo_v9_final_{idx_row_diag}"): 
                            medias_cat_pdf_antigo = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in row_diag_data.items() if "Media_Cat_" in k and pd.notna(v)}
                            pdf_path_antigo = gerar_pdf_diagnostico_completo(row_diag_data.to_dict(), st.session_state.user, perguntas_df_para_painel, row_diag_data.to_dict(), medias_cat_pdf_antigo, analises_df_para_painel)
                            if pdf_path_antigo:
                                with open(pdf_path_antigo, "rb") as f_antigo:
                                    st.download_button("Download PDF Confirmado", f_antigo, file_name=f"diag_{sanitize_column_name(row_diag_data['Empresa'])}_{str(row_diag_data['Data']).replace(':','-').replace(' ','_')}.pdf", mime="application/pdf", key=f"dl_confirm_antigo_v9_final_{idx_row_diag}") 
                                registrar_acao(st.session_state.cnpj, "Download PDF (Painel)", f"Baixou PDF de {row_diag_data['Data']}")
                            else: st.error("Erro ao gerar PDF para este diagnóstico.")
                        st.divider() 
        except Exception as e: st.error(f"Erro ao carregar painel do cliente: {e}"); st.exception(e)

    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader("📋 Formulário de Novo Diagnóstico")

        if not st.session_state.user.get("PodeFazerNovoDiagnostico", True): 
            st.warning("Você já enviou seu diagnóstico ou não tem permissão para um novo. Para realizar um novo, por favor, entre em contato com o administrador para liberação.")
            if st.button("Voltar ao Painel Principal", key="voltar_painel_novo_diag_bloq_v9_final"): st.session_state.cliente_page = "Painel Principal"; st.rerun() 
            st.stop()
        
        if st.session_state.diagnostico_enviado_sucesso: 
            st.success("🎯 Seu diagnóstico foi enviado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf_dl_sucesso:
                    st.download_button(label="📄 Baixar PDF do Diagnóstico Enviado", data=f_pdf_dl_sucesso,
                                       file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                       key="dl_pdf_sucesso_novo_diag_v9_final") 
            if st.button("Ir para o Painel Principal", key="ir_painel_apos_envio_sucesso_v9_final"): 
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

        if st.button("✔️ Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v9_final"): 
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

                update_user_data(st.session_state.cnpj, "PodeFazerNovoDiagnostico", False)
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

    if st.sidebar.button("🚪 Sair do Painel Admin", key="logout_admin_v9_final"): 
        st.session_state.admin_logado = False; st.rerun()

    menu_admin_options = ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Perguntas", 
                          "Gerenciar Análises de Perguntas", "Gerenciar Clientes", "Gerenciar Administradores"]
    menu_admin = st.sidebar.selectbox("Funcionalidades Admin:", menu_admin_options, key="admin_menu_selectbox_v9_final") 
    st.header(f"🔑 Painel Admin: {menu_admin}")

    if menu_admin == "Visão Geral e Diagnósticos":
        st.subheader("📊 Visão Geral dos Diagnósticos")
        diagnosticos_df_admin_orig = pd.DataFrame()
        admin_data_carregada_com_sucesso = False
        
        if not os.path.exists(arquivo_csv):
            st.error(f"ATENÇÃO: O arquivo de diagnósticos '{arquivo_csv}' não foi encontrado. Crie diagnósticos na área do cliente para popular.")
        elif os.path.getsize(arquivo_csv) == 0:
            st.warning(f"O arquivo de diagnósticos '{arquivo_csv}' está completamente vazio (0 bytes).")
        else:
            try:
                diagnosticos_df_admin_orig = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                if 'Data' in diagnosticos_df_admin_orig.columns:
                    diagnosticos_df_admin_orig['Data'] = pd.to_datetime(diagnosticos_df_admin_orig['Data'], errors='coerce')
                
                if diagnosticos_df_admin_orig.empty:
                    st.info("O arquivo de diagnósticos foi lido, mas não contém nenhuma linha de dados.")
                else:
                    admin_data_carregada_com_sucesso = True
            except pd.errors.EmptyDataError:
                 st.warning(f"O arquivo de diagnósticos '{arquivo_csv}' parece estar vazio ou contém apenas cabeçalhos.")
            except Exception as e_load_diag_admin:
                st.error(f"ERRO CRÍTICO AO CARREGAR DIAGNÓSTICOS: {e_load_diag_admin}")
                st.exception(e_load_diag_admin)

        if admin_data_carregada_com_sucesso:
            st.markdown("#### Indicadores Globais (Todos os Diagnósticos)")
            col_ig_adm1, col_ig_adm2, col_ig_adm3 = st.columns(3)
            col_ig_adm1.metric("📦 Total de Diagnósticos Registrados", len(diagnosticos_df_admin_orig))
            
            # Cálculo seguro de médias globais
            media_geral_global_adm = pd.to_numeric(diagnosticos_df_admin_orig.get("Média Geral"), errors='coerce').mean()
            col_ig_adm2.metric("📈 Média Geral Global", f"{media_geral_global_adm:.2f}" if pd.notna(media_geral_global_adm) else "N/A")
            
            gut_media_global_adm = pd.to_numeric(diagnosticos_df_admin_orig.get("GUT Média"), errors='coerce').mean()
            col_ig_adm3.metric("🔥 GUT Média Global", f"{gut_media_global_adm:.2f}" if pd.notna(gut_media_global_adm) else "N/A")
            st.divider()
        
        st.markdown("#### Filtros para Análise Detalhada:")
        col_f1, col_f2, col_f3 = st.columns(3)
        empresas_lista_admin_filtro = []
        if admin_data_carregada_com_sucesso and "Empresa" in diagnosticos_df_admin_orig.columns:
            empresas_lista_admin_filtro = sorted(diagnosticos_df_admin_orig["Empresa"].astype(str).unique().tolist())
        
        with col_f1:
            emp_sel_admin = st.selectbox("Filtrar por Empresa:", ["Todos os Clientes"] + empresas_lista_admin_filtro, key="admin_filtro_emp_v9_final")
        with col_f2:
            dt_ini_admin = st.date_input("Data Início:", value=None, key="admin_dt_ini_v9_final")
        with col_f3:
            dt_fim_admin = st.date_input("Data Fim:", value=None, key="admin_dt_fim_v9_final")

        if admin_data_carregada_com_sucesso:
            df_filtrado_admin_view = diagnosticos_df_admin_orig.copy()
            if emp_sel_admin != "Todos os Clientes":
                df_filtrado_admin_view = df_filtrado_admin_view[df_filtrado_admin_view["Empresa"] == emp_sel_admin]
            if dt_ini_admin:
                df_filtrado_admin_view = df_filtrado_admin_view[df_filtrado_admin_view['Data'] >= pd.to_datetime(dt_ini_admin)]
            if dt_fim_admin:
                df_filtrado_admin_view = df_filtrado_admin_view[df_filtrado_admin_view['Data'] < pd.to_datetime(dt_fim_admin) + pd.Timedelta(days=1)]

            if df_filtrado_admin_view.empty:
                st.info(f"Nenhum diagnóstico encontrado para os filtros aplicados: Empresa '{emp_sel_admin}', Período de {dt_ini_admin or 'Início'} até {dt_fim_admin or 'Fim'}.")
            else:
                st.markdown(f"#### Indicadores da Seleção Filtrada: {emp_sel_admin} (Período Selecionado)")
                col_if_adm1, col_if_adm2, col_if_adm3 = st.columns(3)
                col_if_adm1.metric("📦 Diagnósticos na Seleção", len(df_filtrado_admin_view))
                
                media_geral_filtrada_adm = pd.to_numeric(df_filtrado_admin_view.get("Média Geral"), errors='coerce').mean()
                col_if_adm2.metric("📈 Média Geral da Seleção", f"{media_geral_filtrada_adm:.2f}" if pd.notna(media_geral_filtrada_adm) else "N/A")
                
                gut_media_filtrada_adm = pd.to_numeric(df_filtrado_admin_view.get("GUT Média"), errors='coerce').mean()
                col_if_adm3.metric("🔥 GUT Média da Seleção", f"{gut_media_filtrada_adm:.2f}" if pd.notna(gut_media_filtrada_adm) else "N/A")
                st.divider()

                # Gráficos de Evolução (Exemplo)
                st.markdown("##### Evolução Temporal das Médias (para seleção filtrada)")
                if len(df_filtrado_admin_view) > 1:
                    try:
                        df_temp_chart = df_filtrado_admin_view.sort_values(by="Data")
                        fig_evolucao = px.line(df_temp_chart, x="Data", y=["Média Geral", "GUT Média"], 
                                               title="Evolução das Médias ao Longo do Tempo", markers=True)
                        st.plotly_chart(fig_evolucao, use_container_width=True)
                    except Exception as e_chart:
                        st.caption(f"Não foi possível gerar gráfico de evolução: {e_chart}")
                else:
                    st.caption("Gráfico de evolução requer mais de um diagnóstico na seleção.")
                st.divider()

                # Ranking de Empresas (se "Todos os Clientes" estiver selecionado)
                if emp_sel_admin == "Todos os Clientes":
                    st.markdown("##### Ranking de Empresas por Média Geral (para seleção filtrada)")
                    try:
                        ranking_empresas = df_filtrado_admin_view.groupby("Empresa")["Média Geral"].mean().sort_values(ascending=False).reset_index()
                        st.dataframe(ranking_empresas)
                    except Exception as e_rank:
                        st.caption(f"Não foi possível gerar ranking: {e_rank}")
                    st.divider()
                
                st.markdown(f"#### Detalhes dos Diagnósticos ({emp_sel_admin} - Filtro Aplicado)")
                st.dataframe(df_filtrado_admin_view.sort_values(by="Data", ascending=False).reset_index(drop=True))
                
                # Seção para detalhar um diagnóstico específico da lista filtrada
                st.markdown("#### Detalhar, Comentar e Baixar PDF de Diagnóstico Específico")
                if not df_filtrado_admin_view.empty:
                    diagnosticos_para_detalhe = df_filtrado_admin_view.apply(lambda row: f"{row['Data']} - {row['Empresa']} (ID: {row.name})", axis=1).tolist()
                    diag_selecionado_para_detalhe_str = st.selectbox("Selecione um Diagnóstico para Detalhar:", [""] + diagnosticos_para_detalhe, key="admin_select_diag_detalhe_v9")

                    if diag_selecionado_para_detalhe_str:
                        try:
                            # Extrair o índice original do DataFrame completo
                            diag_id_original = int(diag_selecionado_para_detalhe_str.split("(ID: ")[1].replace(")", ""))
                            diag_row_detalhe = diagnosticos_df_admin_orig.loc[diag_id_original] # Pegar do original para ter todos os dados
                            
                            st.markdown(f"##### Detalhes do Diagnóstico: {diag_row_detalhe['Data']} - {diag_row_detalhe['Empresa']}")
                            
                            # Mostrar informações básicas e perguntas/respostas
                            st.write(f"**Média Geral:** {diag_row_detalhe.get('Média Geral', 'N/A')}")
                            st.write(f"**GUT Média:** {diag_row_detalhe.get('GUT Média', 'N/A')}")
                            st.write(f"**Resumo Cliente:** {diag_row_detalhe.get('Diagnóstico', 'N/P')}")
                            st.write(f"**Análise Cliente:** {diag_row_detalhe.get('Análise do Cliente', 'N/P')}")

                            comentarios_admin_atuais = diag_row_detalhe.get('Comentarios_Admin', "")
                            novos_comentarios_admin = st.text_area("Comentários do Consultor:", value=comentarios_admin_atuais, key=f"com_admin_{diag_id_original}")

                            if st.button("Salvar Comentários do Consultor", key=f"save_com_admin_{diag_id_original}"):
                                diagnosticos_df_admin_orig.loc[diag_id_original, 'Comentarios_Admin'] = novos_comentarios_admin
                                diagnosticos_df_admin_orig.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                st.success("Comentários salvos!")
                                st.rerun() # Para recarregar os dados e mostrar o comentário atualizado

                            if st.button("📄 Baixar PDF deste Diagnóstico", key=f"dl_pdf_admin_detalhe_{diag_id_original}"):
                                # Coletar dados para o PDF
                                usuario_do_diag_pdf = pd.read_csv(usuarios_csv, dtype={'CNPJ':str}).set_index('CNPJ').loc[diag_row_detalhe['CNPJ']].to_dict()
                                perguntas_df_pdf_admin = pd.read_csv(perguntas_csv, encoding='utf-8')
                                analises_df_pdf_admin = carregar_analises_perguntas()
                                medias_cat_pdf_admin = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in diag_row_detalhe.items() if "Media_Cat_" in k and pd.notna(v)}

                                pdf_path_admin = gerar_pdf_diagnostico_completo(
                                    diag_row_detalhe.to_dict(), 
                                    usuario_do_diag_pdf, 
                                    perguntas_df_pdf_admin, 
                                    diag_row_detalhe.to_dict(), # Respostas estão no row
                                    medias_cat_pdf_admin, 
                                    analises_df_pdf_admin
                                )
                                if pdf_path_admin:
                                    with open(pdf_path_admin, "rb") as f_pdf_admin_dl:
                                        st.download_button("Download PDF Confirmado", f_pdf_admin_dl, 
                                                            file_name=f"diagnostico_admin_{sanitize_column_name(diag_row_detalhe['Empresa'])}_{str(diag_row_detalhe['Data']).replace(':','-').replace(' ','_')}.pdf", 
                                                            mime="application/pdf", 
                                                            key=f"dl_conf_admin_detalhe_{diag_id_original}")
                                else: st.error("Falha ao gerar PDF para este diagnóstico.")
                        except KeyError:
                            st.error("Não foi possível encontrar o diagnóstico selecionado. Tente recarregar a página.")
                        except Exception as e_detalhe_diag:
                            st.error(f"Erro ao detalhar diagnóstico: {e_detalhe_diag}")
                else:
                    st.caption("Nenhum diagnóstico na seleção atual para detalhar.")
        
        elif not os.path.exists(arquivo_csv) or (os.path.exists(arquivo_csv) and os.path.getsize(arquivo_csv) == 0) :
             pass # Mensagens de arquivo ausente ou vazio já foram dadas no início do bloco "Visão Geral"
        else: # Caso de erro não previsto no carregamento, mas que não setou admin_data_carregada_com_sucesso
            st.info("Não há dados de diagnóstico disponíveis para exibir informações.")


    # ... (Demais seções do Admin: Histórico, Gerenciar Perguntas, Gerenciar Análises, Gerenciar Clientes, Gerenciar Administradores - mantidas como na última versão funcional)
    elif menu_admin == "Gerenciar Análises de Perguntas":
        st.subheader("💡 Gerenciar Análises Vinculadas às Perguntas")
        df_analises_existentes_admin = carregar_analises_perguntas()
        try: df_perguntas_formulario_admin = pd.read_csv(perguntas_csv, encoding='utf-8')
        except: df_perguntas_formulario_admin = pd.DataFrame(columns=colunas_base_perguntas)

        st.markdown("#### Adicionar Nova Análise")
        if df_perguntas_formulario_admin.empty:
            st.warning("Nenhuma pergunta cadastrada no formulário. Adicione perguntas primeiro em 'Gerenciar Perguntas'.")
        else:
            lista_perguntas_txt_admin = [""] + df_perguntas_formulario_admin["Pergunta"].unique().tolist()
            pergunta_selecionada_analise_admin = st.selectbox("Selecione a Pergunta para adicionar análise:", lista_perguntas_txt_admin, key="sel_perg_analise_v9_final") 

            if pergunta_selecionada_analise_admin:
                st.caption(f"Pergunta selecionada: {pergunta_selecionada_analise_admin}")
                
                tipo_condicao_analise_display_admin = st.selectbox("Tipo de Condição para a Análise:", 
                                                     ["Faixa Numérica (p/ Pontuação 0-X)", 
                                                      "Valor Exato (p/ Escala)", 
                                                      "Faixa de Score (p/ Matriz GUT)", 
                                                      "Análise Padrão (default para a pergunta)"], 
                                                     key="tipo_cond_analise_v9_final") 
                
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
                    cond_val_min_ui_admin = cols_faixa_ui_admin[0].number_input("Valor Mínimo da Faixa", step=1.0, format="%.2f", key="cond_min_analise_v9_final") 
                    cond_val_max_ui_admin = cols_faixa_ui_admin[1].number_input("Valor Máximo da Faixa", step=1.0, format="%.2f", key="cond_max_analise_v9_final") 
                elif tipo_condicao_csv_val_admin == "ValorExatoEscala":
                    cond_val_exato_ui_admin = st.text_input("Valor Exato da Escala (ex: Baixo, Médio, Alto)", key="cond_exato_analise_v9_final") 
                elif tipo_condicao_csv_val_admin == "ScoreGUT":
                    cols_faixa_gut_ui_admin = st.columns(2)
                    cond_val_min_ui_admin = cols_faixa_gut_ui_admin[0].number_input("Score GUT Mínimo", step=1, key="cond_min_gut_analise_v9_final") 
                    cond_val_max_ui_admin = cols_faixa_gut_ui_admin[1].number_input("Score GUT Máximo (opcional, deixe 0 ou vazio se for 'acima de Mínimo')", value=0.0, step=1.0, format="%.0f", key="cond_max_gut_analise_v9_final") 

                texto_analise_nova_ui_admin = st.text_area("Texto da Análise:", height=150, key="txt_analise_nova_v9_final") 

                if st.button("💾 Salvar Nova Análise", key="salvar_analise_pergunta_v9_final"): 
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
            
            analise_del_id_admin = st.selectbox("Deletar Análise por ID:", [""] + df_analises_existentes_admin["ID_Analise"].astype(str).tolist(), key="del_analise_id_v9_final") 
            if st.button("🗑️ Deletar Análise", key="btn_del_analise_v9_final") and analise_del_id_admin: 
                df_analises_existentes_admin = df_analises_existentes_admin[df_analises_existentes_admin["ID_Analise"] != analise_del_id_admin]
                df_analises_existentes_admin.to_csv(analises_perguntas_csv, index=False, encoding='utf-8')
                st.warning("Análise deletada."); st.rerun()

    elif menu_admin == "Gerenciar Clientes":
        st.subheader("👥 Gerenciar Clientes")
        try:
            usuarios_df_gc = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
            if "PodeFazerNovoDiagnostico" not in usuarios_df_gc.columns: usuarios_df_gc["PodeFazerNovoDiagnostico"] = "True" # Default
            usuarios_df_gc["PodeFazerNovoDiagnostico"] = usuarios_df_gc["PodeFazerNovoDiagnostico"].astype(str).str.lower() == "true" # Converte para booleano para exibição
        except FileNotFoundError:
            st.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado.")
            usuarios_df_gc = pd.DataFrame(columns=colunas_base_usuarios) # DataFrame vazio para evitar mais erros
        except Exception as e_gc_load:
            st.error(f"Erro ao carregar usuários: {e_gc_load}")
            usuarios_df_gc = pd.DataFrame(columns=colunas_base_usuarios)

        st.markdown("#### Lista de Clientes Cadastrados")
        if not usuarios_df_gc.empty:
            st.dataframe(usuarios_df_gc[["CNPJ", "Empresa", "NomeContato", "Telefone", "PodeFazerNovoDiagnostico"]])

            st.markdown("#### Ações de Cliente")
            clientes_lista_gc = usuarios_df_gc["CNPJ"].tolist()
            cnpj_selecionado_gc = st.selectbox("Selecione o CNPJ do cliente para gerenciar:", [""] + clientes_lista_gc, key="sel_cnpj_gc_v9")

            if cnpj_selecionado_gc:
                cliente_data_gc = usuarios_df_gc[usuarios_df_gc["CNPJ"] == cnpj_selecionado_gc].iloc[0]
                st.write(f"**Empresa:** {cliente_data_gc['Empresa']}")
                
                pode_fazer_novo_atual_gc = cliente_data_gc["PodeFazerNovoDiagnostico"]
                
                if pode_fazer_novo_atual_gc:
                    if st.button(f"Bloquear Novo Diagnóstico para {cliente_data_gc['Empresa']}", key=f"bloq_diag_gc_{cnpj_selecionado_gc}"):
                        update_user_data(cnpj_selecionado_gc, "PodeFazerNovoDiagnostico", False)
                        st.success(f"Novo diagnóstico bloqueado para {cliente_data_gc['Empresa']}."); st.rerun()
                else:
                    if st.button(f"Liberar Novo Diagnóstico para {cliente_data_gc['Empresa']}", key=f"lib_diag_gc_{cnpj_selecionado_gc}"):
                        update_user_data(cnpj_selecionado_gc, "PodeFazerNovoDiagnostico", True)
                        st.success(f"Novo diagnóstico liberado para {cliente_data_gc['Empresa']}."); st.rerun()
                
                # Adicionar/Remover da lista de bloqueados geral
                try:
                    bloqueados_df_gc = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                except FileNotFoundError: bloqueados_df_gc = pd.DataFrame(columns=["CNPJ"])
                
                is_blocked_gc = cnpj_selecionado_gc in bloqueados_df_gc["CNPJ"].values
                if is_blocked_gc:
                    if st.button(f"Desbloquear Acesso Total para {cliente_data_gc['Empresa']}", key=f"desbloq_total_gc_{cnpj_selecionado_gc}"):
                        bloqueados_df_gc = bloqueados_df_gc[bloqueados_df_gc["CNPJ"] != cnpj_selecionado_gc]
                        bloqueados_df_gc.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        st.success(f"Acesso total desbloqueado para {cliente_data_gc['Empresa']}."); st.rerun()
                else:
                    if st.button(f"Bloquear Acesso Total para {cliente_data_gc['Empresa']}", type="primary", key=f"bloq_total_gc_{cnpj_selecionado_gc}"):
                        nova_entrada_bloqueio_gc = pd.DataFrame([{"CNPJ": cnpj_selecionado_gc}])
                        bloqueados_df_gc = pd.concat([bloqueados_df_gc, nova_entrada_bloqueio_gc], ignore_index=True)
                        bloqueados_df_gc.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        st.error(f"Acesso total bloqueado para {cliente_data_gc['Empresa']}."); st.rerun()

        st.markdown("---")
        st.markdown("#### Adicionar Novo Cliente")
        with st.form("form_novo_cliente_v9", clear_on_submit=True):
            novo_cnpj_gc = st.text_input("CNPJ do Novo Cliente:")
            nova_senha_gc = st.text_input("Senha para o Novo Cliente:", type="password")
            nova_empresa_gc = st.text_input("Nome da Empresa do Novo Cliente:")
            novo_contato_gc = st.text_input("Nome do Contato (opcional):")
            novo_telefone_gc = st.text_input("Telefone do Contato (opcional):")
            submit_novo_cliente_gc = st.form_submit_button("Cadastrar Novo Cliente")

            if submit_novo_cliente_gc:
                if novo_cnpj_gc and nova_senha_gc and nova_empresa_gc:
                    if novo_cnpj_gc not in usuarios_df_gc["CNPJ"].values:
                        nova_linha_cliente = pd.DataFrame([{
                            "CNPJ": novo_cnpj_gc, "Senha": nova_senha_gc, "Empresa": nova_empresa_gc,
                            "NomeContato": novo_contato_gc, "Telefone": novo_telefone_gc,
                            "PodeFazerNovoDiagnostico": "True", "JaVisualizouInstrucoes": "False" # Salva como string
                        }])
                        usuarios_df_gc = pd.concat([usuarios_df_gc, nova_linha_cliente], ignore_index=True)
                        usuarios_df_gc.to_csv(usuarios_csv, index=False, encoding='utf-8')
                        st.success(f"Cliente {nova_empresa_gc} cadastrado com sucesso!"); st.rerun()
                    else: st.error("CNPJ já cadastrado.")
                else: st.error("CNPJ, Senha e Nome da Empresa são obrigatórios.")
    # Adicione aqui as outras seções do Admin: Histórico de Usuários, Gerenciar Perguntas, Gerenciar Administradores


if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()