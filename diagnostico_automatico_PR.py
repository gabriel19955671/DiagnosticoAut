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
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", page_icon="📊")

# --- CSS Melhorado ---
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', sans-serif;
}
.login-container {
    max-width: 450px;
    margin: 40px auto 0 auto;
    padding: 40px;
    border-radius: 10px;
    background-color: #ffffff;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    font-family: 'Segoe UI', sans-serif;
}
.login-container img {
    display: block;
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 20px;
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
    padding: 0.6rem 1.3rem;
    margin-top: 0.5rem;
    border: none;
    transition: background-color 0.3s ease;
}
.stButton>button:hover {
    background-color: #1d4ed8;
}
.stButton>button.secondary {
    background-color: #e5e7eb;
    color: #374151;
}
.stButton>button.secondary:hover {
    background-color: #d1d5db;
}
.stDownloadButton>button {
    background-color: #10b981;
    color: white;
    font-weight: 600;
    border-radius: 6px;
    margin-top: 10px;
    padding: 0.6rem 1.3rem;
    border: none;
    transition: background-color 0.3s ease;
}
.stDownloadButton>button:hover {
    background-color: #059669;
}
.stTextInput>div>input, .stTextArea>div>textarea, .stDateInput>div>input, .stSelectbox>div>div {
    border-radius: 6px;
    padding: 0.6rem;
    border: 1px solid #d1d5db;
    background-color: #f9fafb;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.stTextInput>div>input:focus, .stTextArea>div>textarea:focus, .stDateInput>div>input:focus, .stSelectbox>div>div:focus-within {
    border-color: #2563eb;
    box-shadow: 0 0 0 0.1rem rgba(37, 99, 235, 0.25);
}
.stTabs [data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 600;
    padding: 12px 22px;
    border-radius: 6px 6px 0 0;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #2563eb;
    color: white;
}
.custom-card {
    border: 1px solid #e0e0e0;
    border-left: 5px solid #2563eb;
    padding: 20px;
    margin-bottom: 15px;
    border-radius: 8px;
    background-color: #ffffff;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07);
}
.custom-card h4 {
    margin-top: 0;
    color: #2563eb;
    font-size: 1.1em;
}
.feedback-saved {
    font-size: 0.85em;
    color: #10b981;
    font-style: italic;
    margin-top: -8px;
    margin-bottom: 8px;
}
.analise-pergunta-cliente {
    font-size: 0.9em;
    color: #333;
    background-color: #eef2ff;
    border-left: 3px solid #6366f1;
    padding: 10px;
    margin-top: 8px;
    margin-bottom:12px;
    border-radius: 4px;
}
[data-testid="stMetric"] {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 15px 20px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07);
    border: 1px solid #e0e0e0;
}
[data-testid="stMetricLabel"] {
    font-weight: 500;
    color: #4b5563;
}
[data-testid="stMetricValue"] {
    font-size: 1.8em;
}
[data-testid="stMetricDelta"] {
    font-size: 0.9em;
}
.stExpander {
    border: 1px solid #e0e0e0 !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07) !important;
    margin-bottom: 15px !important;
}
.stExpander header {
    font-weight: 600 !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 15px !important;
}
.dashboard-item {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07);
    margin-bottom: 20px;
    border: 1px solid #e0e0e0;
    height: 100%;
}
.dashboard-item h5 {
    margin-top: 0;
    margin-bottom: 15px;
    color: #2563eb;
    font-size: 1.1em;
    border-bottom: 1px solid #eee;
    padding-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- Funções de Gráficos ---
def create_radar_chart(data_dict, title="Radar Chart"):
    if not data_dict: return None
    categories = list(data_dict.keys())
    values = list(data_dict.values())
    if not categories or not values or len(categories) < 3 : return None

    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    df_radar = pd.DataFrame(dict(r=values_closed, theta=categories_closed))
    fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True, template="seaborn")
    fig.update_traces(fill='toself', line=dict(color='#2563eb'))
    fig.update_layout(title={'text': title, 'x':0.5, 'xanchor': 'center'},
                      polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                      font=dict(family="Segoe UI, sans-serif"),
                      margin=dict(l=50, r=50, t=70, b=50))
    return fig

def create_gut_barchart(gut_data_list, title="Top Prioridades (GUT)"):
    if not gut_data_list: return None
    df_gut = pd.DataFrame(gut_data_list)
    df_gut = df_gut.sort_values(by="Score", ascending=False).head(10)
    if df_gut.empty: return None
    fig = px.bar(df_gut, x="Score", y="Tarefa", title=title, orientation='h',
                 color="Score", color_continuous_scale=px.colors.sequential.Blues_r,
                 labels={'Tarefa':'Tarefa/Pergunta', 'Score':'Score GUT'})
    fig.update_layout(yaxis={'categoryorder':'total ascending'},
                      xaxis_title="Score GUT", yaxis_title="",
                      font=dict(family="Segoe UI, sans-serif"),
                      height=400 + len(df_gut)*20,
                      margin=dict(l=250, r=20, t=70, b=20))
    return fig

def create_diagnostics_timeline_chart(df_diagnostics, title="Diagnósticos Realizados ao Longo do Tempo"):
    if df_diagnostics.empty or 'Data' not in df_diagnostics.columns: return None
    df_diag_copy = df_diagnostics.copy()
    df_diag_copy['Data'] = pd.to_datetime(df_diag_copy['Data'])
    diag_counts_monthly = df_diag_copy.groupby(pd.Grouper(key='Data', freq='M')).size().reset_index(name='Contagem')
    diag_counts_monthly['Mês'] = diag_counts_monthly['Data'].dt.strftime('%Y-%m')
    if diag_counts_monthly.empty: return None
    fig = px.line(diag_counts_monthly, x='Mês', y='Contagem', title=title, markers=True,
                  labels={'Mês':'Mês', 'Contagem':'Nº de Diagnósticos'}, line_shape="spline")
    fig.update_traces(line=dict(color='#2563eb'))
    fig.update_layout(font=dict(family="Segoe UI, sans-serif"))
    return fig

def create_avg_category_scores_chart(df_diagnostics, title="Média de Scores por Categoria (Todos Clientes)"):
    if df_diagnostics.empty: return None
    media_cols = [col for col in df_diagnostics.columns if col.startswith("Media_Cat_")]
    if not media_cols: return None

    avg_scores_data = []
    for col in media_cols:
        numeric_scores = pd.to_numeric(df_diagnostics[col], errors='coerce')
        if not numeric_scores.isnull().all():
            avg_scores_data.append({
                'Categoria': col.replace("Media_Cat_", "").replace("_", " "),
                'Média_Score': numeric_scores.mean()
            })
    
    if not avg_scores_data: return None
    avg_scores = pd.DataFrame(avg_scores_data)
    avg_scores = avg_scores.sort_values(by="Média_Score", ascending=False)

    fig = px.bar(avg_scores, x='Categoria', y='Média_Score', title=title,
                 color='Média_Score', color_continuous_scale=px.colors.sequential.Blues_r,
                 labels={'Categoria':'Categoria', 'Média_Score':'Média do Score'})
    fig.update_layout(xaxis_tickangle=-45, font=dict(family="Segoe UI, sans-serif"),
                      yaxis=dict(range=[0,5.5]))
    return fig

def create_client_engagement_pie(df_usuarios, title="Engajamento de Clientes (Nº de Diagnósticos)"):
    if df_usuarios.empty or 'TotalDiagnosticosRealizados' not in df_usuarios.columns: return None
    
    def categorize_diagnostics(count):
        if count == 0: return "0 Diagnósticos"
        if count == 1: return "1 Diagnóstico"
        if count == 2: return "2 Diagnósticos"
        return "3+ Diagnósticos"

    df_usuarios_copy = df_usuarios.copy()
    df_usuarios_copy['Engajamento'] = df_usuarios_copy['TotalDiagnosticosRealizados'].apply(categorize_diagnostics)
    engagement_counts = df_usuarios_copy['Engajamento'].value_counts().reset_index()
    engagement_counts.columns = ['Categoria_Engajamento', 'Numero_Clientes']

    if engagement_counts.empty: return None

    fig = px.pie(engagement_counts, values='Numero_Clientes', names='Categoria_Engajamento', title=title,
                 color_discrete_sequence=px.colors.sequential.Blues_r)
    fig.update_traces(textposition='inside', textinfo='percent+label', insidetextorientation='radial')
    fig.update_layout(font=dict(family="Segoe UI, sans-serif"), legend_title_text='Nível de Engajamento')
    return fig

# --- Configuração de Arquivos e Variáveis Globais ---
admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv"
historico_csv = "historico_clientes.csv"
analises_perguntas_csv = "analises_perguntas.csv"
notificacoes_csv = "notificacoes.csv" # NOVO ARQUIVO
instrucoes_custom_path = "instrucoes_portal.md" # NOVO ARQUIVO
instrucoes_default_path = "instrucoes_portal_default.md" # NOVO ARQUIVO
LOGOS_DIR = "client_logos"

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "force_sidebar_rerun_after_notif_read_v19": False # Chave nova e específica
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias (exceto gráficos) ---
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

if not os.path.exists(LOGOS_DIR):
    try: os.makedirs(LOGOS_DIR)
    except OSError as e: st.error(f"Erro ao criar diretório de logos '{LOGOS_DIR}': {e}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone",
                         "JaVisualizouInstrucoes", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Timestamp", "Mensagem", "Lida"] # NOVAS COLUNAS

def inicializar_csv(filepath, columns, defaults=None):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if defaults:
                for col, default_val in defaults.items():
                    if col in columns: df_init[col] = default_val
            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else:
            df_init = pd.read_csv(filepath, encoding='utf-8', dtype={'CNPJ': str, 'CNPJ_Cliente': str} if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv] else None)
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
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False}) # INICIALIZA NOTIFICACOES
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
                if field in ["DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]:
                    st.session_state.user[field] = int(value)
                elif field == "JaVisualizouInstrucoes":
                    st.session_state.user[field] = str(value).lower() == "true"
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
        with st.spinner("Gerando PDF do diagnóstico... Aguarde."):
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
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v19")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v19"):
        u = st.text_input("Usuário", key="admin_u_v19"); p = st.text_input("Senha", type="password", key="admin_p_v19")
        if st.form_submit_button("Entrar", use_container_width=True, icon="🔑"):
            try:
                df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                if not df_creds[(df_creds["Usuario"] == u) & (df_creds["Senha"] == p)].empty:
                    st.session_state.admin_logado = True
                    st.toast("Login de admin bem-sucedido!", icon="🎉")
                    st.rerun()
                else: st.error("Usuário/senha admin inválidos.")
            except Exception as e: st.error(f"Erro login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_v19"):
        c = st.text_input("CNPJ", key="cli_c_v19", value=st.session_state.get("last_cnpj_input",""))
        s = st.text_input("Senha", type="password", key="cli_s_v19")
        if st.form_submit_button("Entrar", use_container_width=True, icon="👤"):
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

                st.toast("Login de cliente bem-sucedido!", icon="👋")
                st.rerun()
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    with st.sidebar.expander("👤 Meu Perfil", expanded=False):
        logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
        if logo_cliente_path: st.image(logo_cliente_path, width=100)
        st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
        st.write(f"**CNPJ:** {st.session_state.cnpj}")
        st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
        st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")
        diagnosticos_restantes = st.session_state.user.get('DiagnosticosDisponiveis', 0) - st.session_state.user.get('TotalDiagnosticosRealizados', 0)
        st.write(f"**Diagnósticos Restantes:** {max(0, diagnosticos_restantes)}")
        st.write(f"**Total Realizados:** {st.session_state.user.get('TotalDiagnosticosRealizados', 0)}")

    # Contagem de notificações não lidas
    notificacoes_nao_lidas_count = 0
    if os.path.exists(notificacoes_csv):
        try:
            df_notif_check = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str})
            if not df_notif_check.empty and 'Lida' in df_notif_check.columns:
                df_notif_check['Lida'] = df_notif_check['Lida'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': False, '': False}).fillna(False)
                notificacoes_nao_lidas_count = len(df_notif_check[
                    (df_notif_check["CNPJ_Cliente"] == st.session_state.cnpj) &
                    (df_notif_check["Lida"] == False)
                ])
        except pd.errors.EmptyDataError: notificacoes_nao_lidas_count = 0
        except Exception as e_notif_check: print(f"Erro ao verificar notificações: {e_notif_check}")

    notificacoes_label = "🔔 Notificações"
    if notificacoes_nao_lidas_count > 0:
        notificacoes_label = f"🔔 Notificações ({notificacoes_nao_lidas_count} Nova(s))"

    menu_options_cli_map = {
        "Instruções": "📖 Instruções",
        "Novo Diagnóstico": "📋 Novo Diagnóstico",
        "Painel Principal": "🏠 Painel Principal",
        "Notificações": notificacoes_label
    }
    menu_options_cli_display = list(menu_options_cli_map.values())

    default_display_option = menu_options_cli_map.get(st.session_state.cliente_page, menu_options_cli_display[0])
    try:
        current_idx_cli = menu_options_cli_display.index(default_display_option)
    except ValueError:
        current_idx_cli = 0

    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v19")
    selected_page_cli_clean = ""
    for key_page, val_page_display in menu_options_cli_map.items():
        if val_page_display == selected_page_cli_raw: # Compara com o valor que pode ter o contador
            if key_page == "Notificações": # Caso especial para notificações
                selected_page_cli_clean = "Notificações"
            else:
                selected_page_cli_clean = key_page
            break
    
    if selected_page_cli_clean and selected_page_cli_clean != st.session_state.cliente_page :
        st.session_state.cliente_page = selected_page_cli_clean
        st.session_state.force_sidebar_rerun_after_notif_read_v19 = False # Resetar a flag ao mudar de página
        st.rerun()


    if st.sidebar.button("Sair do Portal Cliente", icon="⬅️", key="logout_cliente_v19", use_container_width=True):
        keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input']]
        for key in keys_to_clear: del st.session_state[key]
        for key_d, value_d in default_session_state.items():
            if key_d not in ['admin_logado', 'last_cnpj_input']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.toast("Logout realizado.", icon="👋")
        st.rerun()

    if st.session_state.cliente_page == "Instruções":
        st.subheader(menu_options_cli_map["Instruções"])
        instrucoes_content_md = ""
        if os.path.exists(instrucoes_custom_path):
            with open(instrucoes_custom_path, "r", encoding="utf-8") as f:
                instrucoes_content_md = f.read()
        elif os.path.exists(instrucoes_default_path):
            with open(instrucoes_default_path, "r", encoding="utf-8") as f:
                instrucoes_content_md = f.read()
            st.caption("Exibindo instruções padrão. O administrador pode personalizar este texto.")
        else:
            instrucoes_content_md = "As instruções não estão disponíveis no momento. Por favor, contate o administrador."
        st.markdown(instrucoes_content_md, unsafe_allow_html=True)

        if st.button("Entendi, prosseguir", key="btn_instrucoes_v19", icon="👍"):
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True")
            if st.session_state.user: st.session_state.user["JaVisualizouInstrucoes"] = True
            pode_fazer_novo_inst = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_inst else "Painel Principal"
            st.rerun()

    elif st.session_state.cliente_page == "Notificações":
        st.subheader(menu_options_cli_map["Notificações"].split(" (")[0]) # Remove count for header
        ids_para_marcar_como_lidas_on_display = []
        try:
            df_notificacoes_todas = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str})
            if not df_notificacoes_todas.empty and 'Lida' in df_notificacoes_todas.columns:
                df_notificacoes_todas['Lida'] = df_notificacoes_todas['Lida'].astype(str).str.lower().map({'true': True, 'false': False, '': False, 'nan': False}).fillna(False)
            else:
                df_notificacoes_todas = pd.DataFrame(columns=colunas_base_notificacoes)

            minhas_notificacoes = df_notificacoes_todas[
                df_notificacoes_todas["CNPJ_Cliente"] == st.session_state.cnpj
            ].sort_values(by="Timestamp", ascending=False)

            if minhas_notificacoes.empty:
                st.info("Você não tem nenhuma notificação no momento.")
            else:
                st.caption("As notificações são marcadas como lidas ao serem exibidas nesta página.")
                for _, row_notif in minhas_notificacoes.iterrows():
                    cor_borda = "#2563eb" if not row_notif["Lida"] else "#adb5bd"
                    icon_lida = "✉️" if not row_notif["Lida"] else "📨"
                    
                    st.markdown(f"""
                    <div class="custom-card" style="border-left: 5px solid {cor_borda}; margin-bottom: 10px;">
                        <p style="font-size: 0.8em; color: #6b7280;">{icon_lida} {row_notif["Timestamp"]}</p>
                        <p>{row_notif["Mensagem"]}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if not row_notif["Lida"]:
                        ids_para_marcar_como_lidas_on_display.append(row_notif["ID_Notificacao"])
                
                if ids_para_marcar_como_lidas_on_display:
                    indices_para_atualizar = df_notificacoes_todas[df_notificacoes_todas["ID_Notificacao"].isin(ids_para_marcar_como_lidas_on_display)].index
                    df_notificacoes_todas.loc[indices_para_atualizar, "Lida"] = True
                    df_notificacoes_todas.to_csv(notificacoes_csv, index=False, encoding='utf-8')
                    st.session_state['force_sidebar_rerun_after_notif_read_v19'] = True # Flag para o rerun

        except (FileNotFoundError, pd.errors.EmptyDataError):
            st.info("Você não tem nenhuma notificação no momento.")
        except Exception as e_notif_display:
            st.error(f"Erro ao carregar suas notificações: {e_notif_display}")

        if st.session_state.get('force_sidebar_rerun_after_notif_read_v19'):
            del st.session_state['force_sidebar_rerun_after_notif_read_v19']
            st.rerun()


    elif st.session_state.cliente_page == "Painel Principal":
        st.subheader(menu_options_cli_map["Painel Principal"])
        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf:
                    st.download_button(label="Baixar PDF do Diagnóstico Recém-Enviado", data=f_pdf,
                                       file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                       key="dl_novo_diag_painel_v19", icon="📄")
                st.session_state.pdf_gerado_path = None
                st.session_state.pdf_gerado_filename = None
            st.session_state.diagnostico_enviado_sucesso = False

        with st.expander("ℹ️ Informações Importantes", expanded=False):
            st.markdown("- Visualize seus diagnósticos anteriores e sua evolução.")
            st.markdown("- Acompanhe seu plano de ação no Kanban.")
            st.markdown("- Para um novo diagnóstico (se liberado), selecione 'Novo Diagnóstico' no menu ao lado.")

        df_antigos = pd.read_csv(arquivo_csv, dtype={'CNPJ': str}, encoding='utf-8')
        df_cliente_diags_raw = df_antigos[df_antigos["CNPJ"] == st.session_state.cnpj]

        if not df_cliente_diags_raw.empty:
            df_cliente_diags = df_cliente_diags_raw.sort_values(by="Data", ascending=False)
            latest_diag_data = df_cliente_diags.iloc[0].to_dict()

            st.markdown("#### 📊 Visão Geral do Último Diagnóstico")
            col_graph1, col_graph2 = st.columns(2)

            with col_graph1:
                st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
                st.markdown("##### Scores por Categoria")
                medias_cat_latest = {
                    k.replace("Media_Cat_", "").replace("_", " "): pd.to_numeric(v, errors='coerce')
                    for k, v in latest_diag_data.items()
                    if k.startswith("Media_Cat_") and pd.notna(pd.to_numeric(v, errors='coerce'))
                }
                if medias_cat_latest:
                    fig_radar = create_radar_chart(medias_cat_latest, title="")
                    if fig_radar:
                        st.plotly_chart(fig_radar, use_container_width=True)
                    else:
                        st.caption("Não foi possível gerar o gráfico de radar.")
                else:
                    st.caption("Sem dados de média por categoria para o último diagnóstico.")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_graph2:
                st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
                st.markdown("##### Top Prioridades (Matriz GUT)")
                gut_data_list_client = []
                for pergunta_key, resp_val_str in latest_diag_data.items():
                    if isinstance(pergunta_key, str) and "[Matriz GUT]" in pergunta_key:
                        try:
                            if pd.notna(resp_val_str) and isinstance(resp_val_str, str):
                                gut_data = json.loads(resp_val_str.replace("'", "\""))
                                g, u, t = int(gut_data.get("G", 0)), int(gut_data.get("U", 0)), int(gut_data.get("T", 0))
                                score = g * u * t
                                if score > 0:
                                    gut_data_list_client.append({
                                        "Tarefa": pergunta_key.replace(" [Matriz GUT]", ""),
                                        "Score": score
                                    })
                        except (json.JSONDecodeError, ValueError, TypeError):
                            pass
                
                if gut_data_list_client:
                    fig_gut_bar = create_gut_barchart(gut_data_list_client, title="")
                    if fig_gut_bar:
                        st.plotly_chart(fig_gut_bar, use_container_width=True)
                    else:
                        st.caption("Não foi possível gerar gráfico de prioridades GUT.")
                else:
                    st.caption("Nenhuma prioridade GUT identificada no último diagnóstico.")
                st.markdown('</div>', unsafe_allow_html=True)
            st.divider()

        st.markdown("#### 📁 Diagnósticos Anteriores")
        try:
            if df_cliente_diags_raw.empty: st.info("Nenhum diagnóstico anterior.")
            else:
                # df_cliente_diags já está ordenado
                try:
                    perguntas_df_para_painel = pd.read_csv(perguntas_csv, encoding='utf-8')
                    if "Categoria" not in perguntas_df_para_painel.columns: perguntas_df_para_painel["Categoria"] = "Geral"
                except FileNotFoundError:
                    st.error(f"Arquivo de perguntas '{perguntas_csv}' não encontrado para detalhar diagnósticos.")
                    perguntas_df_para_painel = pd.DataFrame()

                analises_df_para_painel = carregar_analises_perguntas()

                for idx_row_diag, row_diag_data in df_cliente_diags.iterrows(): # df_cliente_diags já está ordenado
                    with st.expander(f"📅 {row_diag_data['Data']} - {row_diag_data['Empresa']}"):
                        st.markdown('<div class="custom-card" style="padding-top: 10px; padding-bottom: 10px;">', unsafe_allow_html=True) # CARD INÍCIO
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

                        analise_cli_val_cv_painel = row_diag_data.get("Análise do Cliente", "")
                        analise_cli_cv_input = st.text_area("🧠 Minha Análise sobre este Diagnóstico:", value=analise_cli_val_cv_painel, key=f"analise_cv_painel_v19_{idx_row_diag}")
                        if st.button("Salvar Minha Análise", key=f"salvar_analise_cv_painel_v19_{idx_row_diag}", icon="💾"):
                            try:
                                df_antigos_upd = pd.read_csv(arquivo_csv, encoding='utf-8')
                                df_antigos_upd.loc[idx_row_diag, "Análise do Cliente"] = analise_cli_cv_input
                                df_antigos_upd.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                registrar_acao(st.session_state.cnpj, "Análise Cliente (Edição Painel)", f"Editou análise do diagnóstico de {row_diag_data['Data']}")
                                st.toast("Sua análise foi salva!", icon="🎉"); st.rerun()
                            except Exception as e_save_analise_painel: st.error(f"Erro ao salvar sua análise: {e_save_analise_painel}")

                        com_admin_val_cv_painel = row_diag_data.get("Comentarios_Admin", "")
                        if com_admin_val_cv_painel and not pd.isna(com_admin_val_cv_painel):
                            st.markdown("**Comentários do Consultor:**"); st.info(f"{com_admin_val_cv_painel}")
                        else: st.caption("Nenhum comentário do consultor para este diagnóstico.")

                        if st.button("Baixar PDF deste Diagnóstico", key=f"dl_pdf_antigo_v19_{idx_row_diag}", icon="📄"):
                            medias_cat_pdf_antigo = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in row_diag_data.items() if "Media_Cat_" in k and pd.notna(v)}
                            pdf_path_antigo = gerar_pdf_diagnostico_completo(row_diag_data.to_dict(), st.session_state.user, perguntas_df_para_painel, row_diag_data.to_dict(), medias_cat_pdf_antigo, analises_df_para_painel)
                            if pdf_path_antigo:
                                with open(pdf_path_antigo, "rb") as f_antigo:
                                    st.download_button("Clique para Baixar", f_antigo,
                                                        file_name=f"diag_{sanitize_column_name(row_diag_data['Empresa'])}_{str(row_diag_data['Data']).replace(':','-').replace(' ','_')}.pdf",
                                                        mime="application/pdf",
                                                        key=f"dl_confirm_antigo_v19_{idx_row_diag}_{time.time()}",
                                                        icon="📄")
                                registrar_acao(st.session_state.cnpj, "Download PDF (Painel)", f"Baixou PDF de {row_diag_data['Data']}")
                            else: st.error("Erro ao gerar PDF para este diagnóstico.")
                        st.markdown('</div>', unsafe_allow_html=True)

                st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
                if not df_cliente_diags.empty:
                    latest_diag_kanban = df_cliente_diags.iloc[0]
                    gut_cards_kanban = []
                    for pergunta_k, resposta_k_str in latest_diag_kanban.items():
                        if isinstance(pergunta_k, str) and "[Matriz GUT]" in pergunta_k:
                            try:
                                if pd.notna(resposta_k_str) and isinstance(resposta_k_str, str):
                                    gut_data_k = json.loads(resposta_k_str.replace("'", "\""))
                                    g_k, u_k, t_k = int(gut_data_k.get("G", 0)), int(gut_data_k.get("U", 0)), int(gut_data_k.get("T", 0))
                                    score_gut_k = g_k * u_k * t_k
                                    prazo_k = "N/A"
                                    if score_gut_k >= 75: prazo_k = "15 dias"
                                    elif score_gut_k >= 40: prazo_k = "30 dias"
                                    elif score_gut_k >= 20: prazo_k = "45 dias"
                                    elif score_gut_k > 0: prazo_k = "60 dias"
                                    else: continue
                                    if prazo_k != "N/A":
                                        gut_cards_kanban.append({"Tarefa": pergunta_k.replace(" [Matriz GUT]", ""), "Prazo": prazo_k, "Score": score_gut_k, "Responsável": st.session_state.user.get("Empresa", "N/D")})
                            except (json.JSONDecodeError, ValueError, TypeError) as e_kanban_painel: st.warning(f"Erro ao processar GUT para Kanban '{pergunta_k}': {e_kanban_painel}")

                    if gut_cards_kanban:
                        gut_cards_sorted_kanban = sorted(gut_cards_kanban, key=lambda x: x["Score"], reverse=True)
                        prazos_unicos_kanban = sorted(list(set(card["Prazo"] for card in gut_cards_sorted_kanban)), key=lambda x_prazo: int(x_prazo.split(" ")[0]))
                        if prazos_unicos_kanban:
                            cols_kanban = st.columns(len(prazos_unicos_kanban))
                            for idx_col_k, prazo_k_col in enumerate(prazos_unicos_kanban):
                                with cols_kanban[idx_col_k]:
                                    st.markdown(f"#### ⏱️ {prazo_k_col}")
                                    for card_k_item in gut_cards_sorted_kanban:
                                        if card_k_item["Prazo"] == prazo_k_col:
                                            st.markdown(f"""<div class="custom-card"><b>{card_k_item['Tarefa']}</b> (Score GUT: {card_k_item['Score']})<br><small><i>👤 {card_k_item['Responsável']}</i></small></div>""", unsafe_allow_html=True)
                    else:
                        st.info("Nenhuma ação prioritária (GUT > 0) identificada no último diagnóstico para o Kanban.")
                else:
                    st.info("Nenhum diagnóstico para gerar o Kanban.")
                st.divider()

                st.subheader("📈 Comparativo de Evolução das Médias")
                if not df_cliente_diags.empty and len(df_cliente_diags) > 1:
                    df_evolucao = df_cliente_diags.sort_values(by="Data").copy()
                    df_evolucao["Data"] = pd.to_datetime(df_evolucao["Data"])
                    cols_plot_evol = ['Média Geral', 'GUT Média']
                    for col_ev in df_evolucao.columns:
                        if str(col_ev).startswith("Media_Cat_"):
                            df_evolucao[col_ev] = pd.to_numeric(df_evolucao[col_ev], errors='coerce')
                            if not df_evolucao[col_ev].isnull().all():
                                cols_plot_evol.append(col_ev)

                    df_evolucao_plot = df_evolucao.set_index("Data")[cols_plot_evol].dropna(axis=1, how='all')
                    if not df_evolucao_plot.empty:
                        rename_map = {col: col.replace("Media_Cat_", "Média ").replace("_", " ") for col in df_evolucao_plot.columns}
                        df_evolucao_plot_renamed = df_evolucao_plot.rename(columns=rename_map)
                        st.line_chart(df_evolucao_plot_renamed)
                    else:
                        st.info("Não há dados suficientes ou válidos nas colunas de médias para plotar o gráfico de evolução.")
                else:
                    st.info("São necessários pelo menos dois diagnósticos para exibir o comparativo de evolução.")
                st.divider()

                st.subheader("📊 Comparação Detalhada Entre Dois Diagnósticos")
                if not df_cliente_diags.empty and len(df_cliente_diags) > 1:
                    datas_opts_comp = df_cliente_diags["Data"].astype(str).tolist()
                    idx_atual_comp = 0
                    idx_anterior_comp = 1 if len(datas_opts_comp) > 1 else 0

                    col_comp1, col_comp2 = st.columns(2)
                    diag1_data_str = col_comp1.selectbox("Selecione o Diagnóstico 1 (Mais Recente):", datas_opts_comp, index=idx_atual_comp, key="comp_diag1_sel_v19")
                    diag2_data_str = col_comp2.selectbox("Selecione o Diagnóstico 2 (Anterior):", datas_opts_comp, index=idx_anterior_comp, key="comp_diag2_sel_v19")

                    if diag1_data_str and diag2_data_str and diag1_data_str != diag2_data_str:
                        diag1_comp = df_cliente_diags[df_cliente_diags["Data"] == diag1_data_str].iloc[0]
                        diag2_comp = df_cliente_diags[df_cliente_diags["Data"] == diag2_data_str].iloc[0]

                        st.markdown(f"#### Comparando: `{diag1_data_str}` vs `{diag2_data_str}`")
                        metricas_comparacao = []
                        cols_interesse_comp = ["Média Geral", "GUT Média"] + [col for col in df_cliente_diags.columns if str(col).startswith("Media_Cat_")]

                        for metrica in cols_interesse_comp:
                            if metrica in diag1_comp and metrica in diag2_comp:
                                val1 = pd.to_numeric(diag1_comp.get(metrica), errors='coerce')
                                val2 = pd.to_numeric(diag2_comp.get(metrica), errors='coerce')
                                evolucao_txt = "➖"
                                delta_val = None
                                if pd.notna(val1) and pd.notna(val2):
                                    delta = val1 - val2
                                    delta_val = f"{delta:+.2f}"
                                    if val1 > val2: evolucao_txt = f"🔼 Melhorou"
                                    elif val1 < val2: evolucao_txt = f"🔽 Piorou"
                                metricas_comparacao.append({
                                    "Métrica": metrica.replace("Media_Cat_", "Média ").replace("_", " "),
                                    diag1_data_str.split(" ")[0]: f"{val1:.2f}" if pd.notna(val1) else "N/A",
                                    diag2_data_str.split(" ")[0]: f"{val2:.2f}" if pd.notna(val2) else "N/A",
                                    "Diferença": delta_val if delta_val else "N/A",
                                    "Evolução": evolucao_txt
                                })
                        if metricas_comparacao:
                            st.dataframe(pd.DataFrame(metricas_comparacao), use_container_width=True)
                        else:
                            st.info("Não foi possível gerar a tabela de comparação para as métricas selecionadas.")
                    elif diag1_data_str == diag2_data_str and len(df_cliente_diags)>1 :
                        st.warning("Selecione dois diagnósticos diferentes para comparação.")
                else:
                    st.info("São necessários pelo menos dois diagnósticos para fazer uma comparação detalhada.")

        except Exception as e: st.error(f"Erro ao carregar painel do cliente: {e}"); st.exception(e)

    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader(menu_options_cli_map["Novo Diagnóstico"])
        pode_fazer_novo_form = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
        if not pode_fazer_novo_form:
            st.warning("Você não tem diagnósticos disponíveis. Para realizar um novo, por favor, entre em contato com o administrador para liberação.")
            if st.button("Voltar ao Painel Principal", key="voltar_painel_novo_diag_bloq_v19", icon="↩️"): st.session_state.cliente_page = "Painel Principal"; st.rerun()
            st.stop()

        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu diagnóstico foi enviado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf_dl_sucesso:
                    st.download_button(label="Baixar PDF do Diagnóstico Enviado", data=f_pdf_dl_sucesso,
                                       file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                       key="dl_pdf_sucesso_novo_diag_v19", icon="📄")
            if st.button("Ir para o Painel Principal", key="ir_painel_apos_envio_sucesso_v19", icon="🏠"):
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
            progresso_ph_novo.progress(st.session_state.progresso_diagnostico_percentual / 100,
                                       text=f"📊 Progresso: {respondidas_novo} de {total_q_novo} respondidas ({st.session_state.progresso_diagnostico_percentual}%)")


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
            st.session_state.feedbacks_respostas[pergunta_txt_key_novo] = "✓" 
            calcular_e_mostrar_progresso_novo()

        calcular_e_mostrar_progresso_novo()

        for categoria_novo in sorted(perguntas_df_formulario["Categoria"].unique()):
            st.markdown(f"#### Categoria: {categoria_novo}")
            perg_cat_df_novo = perguntas_df_formulario[perguntas_df_formulario["Categoria"] == categoria_novo]
            for idx_novo, row_q_novo in perg_cat_df_novo.iterrows():
                p_texto_novo = str(row_q_novo["Pergunta"])
                w_key_novo = f"q_v19_{st.session_state.id_formulario_atual}_{idx_novo}"

                with st.container():
                    cols_q_feedback = st.columns([0.95, 0.05])
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
                            st.markdown(f'<div class="feedback-saved" style="text-align: center; padding-top: 25px;">{st.session_state.feedbacks_respostas[p_texto_novo]}</div>', unsafe_allow_html=True)
                st.divider()

        key_obs_cli_n = f"obs_cli_diag_v19_{st.session_state.id_formulario_atual}"
        st.text_area("Sua Análise/Observações (opcional):", value=st.session_state.respostas_atuais_diagnostico.get("__obs_cliente__", ""),
                     key=key_obs_cli_n, on_change=on_change_resposta_novo, args=("__obs_cliente__", key_obs_cli_n, "ObsCliente"))
        key_res_cli_n = f"diag_resumo_diag_v19_{st.session_state.id_formulario_atual}"
        st.text_area("✍️ Resumo/principais insights (para PDF):", value=st.session_state.respostas_atuais_diagnostico.get("__resumo_cliente__", ""),
                     key=key_res_cli_n, on_change=on_change_resposta_novo, args=("__resumo_cliente__", key_res_cli_n, "ResumoCliente"))

        if st.button("Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v19", icon="✔️", use_container_width=True):
            with st.spinner("Processando e salvando seu diagnóstico..."):
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
        st.sidebar.image("https://via.placeholder.com/200x80.png?text=Logo+Admin", use_container_width=True)
    except Exception as e_img_admin:
        st.sidebar.caption(f"Logo admin não carregada: {e_img_admin}")

    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v19", use_container_width=True):
        st.session_state.admin_logado = False
        st.toast("Logout de admin realizado.", icon="👋")
        st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": "📊",
        "Histórico de Usuários": "📜",
        "Gerenciar Perguntas": "📝",
        "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar Clientes": "👥",
        "Gerenciar Administradores": "👮",
        "Gerenciar Instruções": "⚙️" # NOVA OPÇÃO
    }
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key]} {key}" for key in admin_page_text_keys]

    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v19"
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v19"

    def admin_menu_on_change():
        selected_display_value = st.session_state[WIDGET_KEY_SB_ADMIN_MENU]
        new_text_key = None
        for text_key, emoji in menu_admin_options_map.items():
            if f"{emoji} {text_key}" == selected_display_value:
                new_text_key = text_key
                break
        if new_text_key and new_text_key != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
            st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key

    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or \
       st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] not in admin_page_text_keys:
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]

    current_admin_page_text_key_for_index = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    try:
        expected_display_value_for_current_page = f"{menu_admin_options_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
        current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
    except (ValueError, KeyError):
        current_admin_menu_index = 0
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]

    st.sidebar.selectbox(
        "Funcionalidades Admin:",
        options=admin_options_for_display,
        index=current_admin_menu_index,
        key=WIDGET_KEY_SB_ADMIN_MENU,
        on_change=admin_menu_on_change
    )

    menu_admin = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    header_display_name = f"{menu_admin_options_map[menu_admin]} {menu_admin}"
    st.header(header_display_name)


    df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios)
    try:
        df_usuarios_admin_temp_load = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        if "DiagnosticosDisponiveis" not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load["DiagnosticosDisponiveis"] = 1
        if "TotalDiagnosticosRealizados" not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load["TotalDiagnosticosRealizados"] = 0
        df_usuarios_admin_temp_load["DiagnosticosDisponiveis"] = pd.to_numeric(df_usuarios_admin_temp_load["DiagnosticosDisponiveis"], errors='coerce').fillna(1).astype(int)
        df_usuarios_admin_temp_load["TotalDiagnosticosRealizados"] = pd.to_numeric(df_usuarios_admin_temp_load["TotalDiagnosticosRealizados"], errors='coerce').fillna(0).astype(int)
        df_usuarios_admin_geral = df_usuarios_admin_temp_load
    except FileNotFoundError:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes"]:
            st.sidebar.error(f"Arquivo '{usuarios_csv}' não encontrado. Funcionalidades limitadas.")
    except Exception as e_load_users_adm_global:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes"]:
            st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm_global}")


    if menu_admin == "Visão Geral e Diagnósticos":
        diagnosticos_df_admin_orig_view = pd.DataFrame()
        admin_data_carregada_view_sucesso = False

        if not os.path.exists(arquivo_csv):
            st.error(f"ATENÇÃO: O arquivo de diagnósticos '{arquivo_csv}' não foi encontrado.")
        elif os.path.getsize(arquivo_csv) == 0:
            st.warning(f"O arquivo de diagnósticos '{arquivo_csv}' está completamente vazio.")
        else:
            try:
                diagnosticos_df_admin_orig_view = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                if 'Data' in diagnosticos_df_admin_orig_view.columns:
                    diagnosticos_df_admin_orig_view['Data'] = pd.to_datetime(diagnosticos_df_admin_orig_view['Data'], errors='coerce')
                if not diagnosticos_df_admin_orig_view.empty:
                    admin_data_carregada_view_sucesso = True
                else: st.info("Arquivo de diagnósticos lido, mas sem dados.")
            except pd.errors.EmptyDataError: st.warning(f"Arquivo '{arquivo_csv}' parece vazio ou só com cabeçalhos.")
            except Exception as e: st.error(f"ERRO AO CARREGAR DIAGNÓSTICOS: {e}"); st.exception(e)

        st.markdown("#### KPIs Gerais do Sistema")
        kpi_cols_v19 = st.columns(3)
        total_clientes_cadastrados_vg = len(df_usuarios_admin_geral) if not df_usuarios_admin_geral.empty else 0
        kpi_cols_v19[0].metric("👥 Clientes Cadastrados", total_clientes_cadastrados_vg)

        if admin_data_carregada_view_sucesso:
            total_diagnosticos_sistema_vg = len(diagnosticos_df_admin_orig_view)
            kpi_cols_v19[1].metric("📋 Diagnósticos Realizados", total_diagnosticos_sistema_vg)
            avg_geral_sistema = pd.to_numeric(diagnosticos_df_admin_orig_view.get("Média Geral"), errors='coerce').mean()
            kpi_cols_v19[2].metric("📈 Média Geral (Sistema)", f"{avg_geral_sistema:.2f}" if pd.notna(avg_geral_sistema) else "N/A")
        else:
            kpi_cols_v19[1].metric("📋 Diagnósticos Realizados", 0)
            kpi_cols_v19[2].metric("📈 Média Geral (Sistema)", "N/A")
        st.divider()

        st.markdown("#### Análises Gráficas do Sistema")
        dash_cols1_v19 = st.columns(2)
        with dash_cols1_v19[0]:
            st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
            st.markdown("##### Diagnósticos ao Longo do Tempo")
            if admin_data_carregada_view_sucesso:
                fig_timeline = create_diagnostics_timeline_chart(diagnosticos_df_admin_orig_view)
                if fig_timeline: st.plotly_chart(fig_timeline, use_container_width=True)
                else: st.caption("Não há dados suficientes para o gráfico de linha do tempo.")
            else: st.caption("Dados de diagnóstico não carregados.")
            st.markdown('</div>', unsafe_allow_html=True)

        with dash_cols1_v19[1]:
            st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
            st.markdown("##### Engajamento de Clientes")
            if not df_usuarios_admin_geral.empty:
                fig_engagement = create_client_engagement_pie(df_usuarios_admin_geral)
                if fig_engagement: st.plotly_chart(fig_engagement, use_container_width=True)
                else: st.caption("Não há dados suficientes para o gráfico de engajamento.")
            else: st.caption("Dados de usuários não carregados.")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
        st.markdown("##### Média de Scores por Categoria (Global)")
        if admin_data_carregada_view_sucesso:
            fig_avg_cat = create_avg_category_scores_chart(diagnosticos_df_admin_orig_view)
            if fig_avg_cat: st.plotly_chart(fig_avg_cat, use_container_width=True)
            else: st.caption("Não há dados de categorias para exibir.")
        else: st.caption("Dados de diagnóstico não carregados.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()

        st.markdown("#### Filtros para Análise Detalhada de Diagnósticos")
        filter_cols_v19 = st.columns(3)

        empresas_lista_admin_filtro_vg = []
        if not df_usuarios_admin_geral.empty and "Empresa" in df_usuarios_admin_geral.columns:
            empresas_lista_admin_filtro_vg = sorted(df_usuarios_admin_geral["Empresa"].astype(str).unique().tolist())
        options_empresa_filtro = ["Todos os Clientes"] + empresas_lista_admin_filtro_vg

        KEY_EMPRESA_FILTRO_VALUE_GV = "admin_filtro_emp_gv_v19_value"
        KEY_WIDGET_EMPRESA_FILTRO_GV = "admin_filtro_emp_gv_v19_widget"
        KEY_DT_INI_FILTRO_VALUE_GV = "admin_dt_ini_gv_v19_value"
        KEY_DT_FIM_FILTRO_VALUE_GV = "admin_dt_fim_gv_v19_value"


        def gv_empresa_filter_on_change():
            st.session_state[KEY_EMPRESA_FILTRO_VALUE_GV] = st.session_state[KEY_WIDGET_EMPRESA_FILTRO_GV]

        if KEY_EMPRESA_FILTRO_VALUE_GV not in st.session_state or \
           st.session_state[KEY_EMPRESA_FILTRO_VALUE_GV] not in options_empresa_filtro:
            st.session_state[KEY_EMPRESA_FILTRO_VALUE_GV] = options_empresa_filtro[0]

        current_empresa_gv_value = st.session_state[KEY_EMPRESA_FILTRO_VALUE_GV]
        try:
            current_empresa_gv_index = options_empresa_filtro.index(current_empresa_gv_value)
        except ValueError:
            current_empresa_gv_index = 0
            st.session_state[KEY_EMPRESA_FILTRO_VALUE_GV] = options_empresa_filtro[0]

        with filter_cols_v19[0]:
            st.selectbox(
                "Filtrar por Empresa:",
                options=options_empresa_filtro,
                index=current_empresa_gv_index,
                key=KEY_WIDGET_EMPRESA_FILTRO_GV,
                on_change=gv_empresa_filter_on_change
            )
            emp_sel_admin_vg = st.session_state[KEY_EMPRESA_FILTRO_VALUE_GV]

        with filter_cols_v19[1]:
            dt_ini_admin_vg = st.date_input("Data Início:",
                                            value=st.session_state.get(KEY_DT_INI_FILTRO_VALUE_GV, None),
                                            key=KEY_DT_INI_FILTRO_VALUE_GV)
        with filter_cols_v19[2]:
            dt_fim_admin_vg = st.date_input("Data Fim:",
                                            value=st.session_state.get(KEY_DT_FIM_FILTRO_VALUE_GV, None),
                                            key=KEY_DT_FIM_FILTRO_VALUE_GV)
        st.divider()

        df_diagnosticos_contexto_filtro_vg = diagnosticos_df_admin_orig_view.copy() if admin_data_carregada_view_sucesso else pd.DataFrame(columns=colunas_base_diagnosticos)
        df_usuarios_contexto_filtro_vg = df_usuarios_admin_geral.copy()

        if emp_sel_admin_vg != "Todos os Clientes":
            df_diagnosticos_contexto_filtro_vg = df_diagnosticos_contexto_filtro_vg[df_diagnosticos_contexto_filtro_vg["Empresa"] == emp_sel_admin_vg]
            df_usuarios_contexto_filtro_vg = df_usuarios_contexto_filtro_vg[df_usuarios_contexto_filtro_vg["Empresa"] == emp_sel_admin_vg]

        df_diagnosticos_filtrados_view_final_vg = df_diagnosticos_contexto_filtro_vg.copy()
        if dt_ini_admin_vg:
            df_diagnosticos_filtrados_view_final_vg = df_diagnosticos_filtrados_view_final_vg[df_diagnosticos_filtrados_view_final_vg['Data'] >= pd.to_datetime(dt_ini_admin_vg)]
        if dt_fim_admin_vg:
            df_diagnosticos_filtrados_view_final_vg = df_diagnosticos_filtrados_view_final_vg[df_diagnosticos_filtrados_view_final_vg['Data'] < pd.to_datetime(dt_fim_admin_vg) + pd.Timedelta(days=1)]


        st.markdown(f"#### Análise para: **{emp_sel_admin_vg}** (Período de Diagnósticos: {dt_ini_admin_vg or 'Início'} a {dt_fim_admin_vg or 'Fim'})")

        kpi_cols_filt_v19 = st.columns(3)
        cnpjs_usuarios_contexto_final_vg = set(df_usuarios_contexto_filtro_vg['CNPJ'].unique()) if not df_usuarios_contexto_filtro_vg.empty else set()
        cnpjs_com_diagnostico_contexto_final_vg = set(df_diagnosticos_filtrados_view_final_vg['CNPJ'].unique()) if not df_diagnosticos_filtrados_view_final_vg.empty else set()

        clientes_sem_diagnostico_final_vg = len(cnpjs_usuarios_contexto_final_vg - cnpjs_com_diagnostico_contexto_final_vg)
        clientes_com_pelo_menos_um_diag_final_vg = len(cnpjs_com_diagnostico_contexto_final_vg)

        clientes_com_mais_de_um_diag_final_vg = 0
        if not df_diagnosticos_filtrados_view_final_vg.empty:
            contagem_diag_por_cliente_final_vg = df_diagnosticos_filtrados_view_final_vg.groupby('CNPJ').size()
            clientes_com_mais_de_um_diag_final_vg = len(contagem_diag_por_cliente_final_vg[contagem_diag_por_cliente_final_vg > 1])

        kpi_cols_filt_v19[0].metric("Clientes SEM Diag. (Filtro)", clientes_sem_diagnostico_final_vg)
        kpi_cols_filt_v19[1].metric("Clientes COM Diag. (Filtro)", clientes_com_pelo_menos_um_diag_final_vg)
        kpi_cols_filt_v19[2].metric("Clientes COM +1 Diag. (Filtro)", clientes_com_mais_de_um_diag_final_vg)
        st.divider()

        if not admin_data_carregada_view_sucesso and os.path.exists(arquivo_csv) and os.path.getsize(arquivo_csv) > 0 :
            st.warning("Não foi possível processar os dados de diagnósticos para os indicadores filtrados.")
        elif df_diagnosticos_filtrados_view_final_vg.empty and admin_data_carregada_view_sucesso:
            st.info(f"Nenhum diagnóstico encontrado para os filtros aplicados.")
        elif not df_diagnosticos_filtrados_view_final_vg.empty:
            st.markdown(f"##### Indicadores da Seleção Filtrada de Diagnósticos")
            kpi_cols_sel_filt_v19 = st.columns(3)
            kpi_cols_sel_filt_v19[0].metric("📦 Diagnósticos na Seleção", len(df_diagnosticos_filtrados_view_final_vg))
            media_geral_filtrada_adm_vg = pd.to_numeric(df_diagnosticos_filtrados_view_final_vg.get("Média Geral"), errors='coerce').mean()
            kpi_cols_sel_filt_v19[1].metric("📈 Média Geral da Seleção", f"{media_geral_filtrada_adm_vg:.2f}" if pd.notna(media_geral_filtrada_adm_vg) else "N/A")
            gut_media_filtrada_adm_vg = pd.to_numeric(df_diagnosticos_filtrados_view_final_vg.get("GUT Média"), errors='coerce').mean()
            kpi_cols_sel_filt_v19[2].metric("🔥 GUT Média da Seleção", f"{gut_media_filtrada_adm_vg:.2f}" if pd.notna(gut_media_filtrada_adm_vg) else "N/A")
            st.divider()

            st.markdown(f"##### Diagnósticos Detalhados (Seleção Filtrada)")
            df_display_admin = df_diagnosticos_filtrados_view_final_vg.sort_values(by="Data", ascending=False).reset_index(drop=True)

            try:
                perguntas_df_admin_view = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_admin_view.columns: perguntas_df_admin_view["Categoria"] = "Geral"
            except FileNotFoundError: perguntas_df_admin_view = pd.DataFrame()
            analises_df_admin_view = carregar_analises_perguntas()

            for idx_diag_adm, row_diag_adm in df_display_admin.iterrows():
                with st.expander(f"🔎 {row_diag_adm['Data']} - {row_diag_adm['Empresa']} (CNPJ: {row_diag_adm['CNPJ']})"):
                    st.markdown('<div class="custom-card" style="padding-top:10px; padding-bottom:10px;">', unsafe_allow_html=True)

                    m1, m2 = st.columns(2)
                    m1.metric("Média Geral", f"{pd.to_numeric(row_diag_adm.get('Média Geral'), errors='coerce'):.2f}" if pd.notna(row_diag_adm.get('Média Geral')) else "N/A")
                    m2.metric("GUT Média", f"{pd.to_numeric(row_diag_adm.get('GUT Média'), errors='coerce'):.2f}" if pd.notna(row_diag_adm.get('GUT Média')) else "N/A")

                    st.write(f"**Resumo (Cliente):** {row_diag_adm.get('Diagnóstico', 'N/P')}")
                    st.write(f"**Análise (Cliente):** {row_diag_adm.get('Análise do Cliente', 'N/P')}")

                    com_admin_atual = row_diag_adm.get("Comentarios_Admin", "")
                    com_admin_input = st.text_area("Comentários do Consultor (visível para o cliente):",
                                                   value=com_admin_atual,
                                                   key=f"com_admin_input_v19_{idx_diag_adm}")
                    if st.button("Salvar Comentário do Consultor", icon="💬", key=f"save_com_admin_v19_{idx_diag_adm}"):
                        if com_admin_input != com_admin_atual:
                            original_index = diagnosticos_df_admin_orig_view[
                                (diagnosticos_df_admin_orig_view["CNPJ"] == row_diag_adm["CNPJ"]) &
                                (diagnosticos_df_admin_orig_view["Data"] == row_diag_adm["Data"])
                            ].index

                            if not original_index.empty:
                                diagnosticos_df_admin_orig_view.loc[original_index[0], "Comentarios_Admin"] = com_admin_input
                                diagnosticos_df_admin_orig_view.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                
                                # Adicionar notificação
                                try:
                                    df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str})
                                    if 'Lida' in df_notificacoes.columns:
                                        df_notificacoes['Lida'] = df_notificacoes['Lida'].astype(str).str.lower().map({'true': True, 'false': False, '':False, 'nan':False}).fillna(False)
                                    else: df_notificacoes['Lida'] = False
                                except (FileNotFoundError, pd.errors.EmptyDataError):
                                    df_notificacoes = pd.DataFrame(columns=colunas_base_notificacoes)

                                nova_notificacao = pd.DataFrame([{
                                    "ID_Notificacao": str(uuid.uuid4()),
                                    "CNPJ_Cliente": row_diag_adm["CNPJ"],
                                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "Mensagem": f"O consultor adicionou um novo comentário ao seu diagnóstico de {row_diag_adm['Data']}.",
                                    "Lida": False
                                }])
                                df_notificacoes = pd.concat([df_notificacoes, nova_notificacao], ignore_index=True)
                                df_notificacoes.to_csv(notificacoes_csv, index=False, encoding='utf-8')
                                st.toast("Comentário salvo e cliente notificado!", icon="🔔")
                                df_diagnosticos_filtrados_view_final_vg.loc[df_diagnosticos_filtrados_view_final_vg.index == idx_diag_adm, "Comentarios_Admin"] = com_admin_input
                                st.rerun()
                            else:
                                st.error("Erro ao encontrar diagnóstico original para salvar comentário.")
                        else:
                            st.info("Nenhuma alteração no comentário.")


                    if st.button("Baixar PDF Detalhado", icon="📄", key=f"dl_pdf_adm_diag_v19_{idx_diag_adm}"):
                        user_data_pdf_adm = {}
                        if not df_usuarios_admin_geral.empty:
                            match_user = df_usuarios_admin_geral[df_usuarios_admin_geral['CNPJ'] == row_diag_adm['CNPJ']]
                            if not match_user.empty:
                                user_data_pdf_adm = match_user.iloc[0].to_dict()

                        medias_cat_pdf_adm = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in row_diag_adm.items() if "Media_Cat_" in k and pd.notna(v)}
                        pdf_path_adm_d = gerar_pdf_diagnostico_completo(row_diag_adm.to_dict(), user_data_pdf_adm, perguntas_df_admin_view, row_diag_adm.to_dict(), medias_cat_pdf_adm, analises_df_admin_view)
                        if pdf_path_adm_d:
                            with open(pdf_path_adm_d, "rb") as f_adm_d:
                                st.download_button("Download PDF Confirmado", f_adm_d,
                                                   file_name=f"diag_{sanitize_column_name(row_diag_adm['Empresa'])}_{str(row_diag_adm['Data']).replace(':','-').replace(' ','_')}.pdf",
                                                   mime="application/pdf",
                                                   key=f"dl_confirm_adm_diag_v19_{idx_diag_adm}_{time.time()}",
                                                   icon="📄")
                        else:
                            st.error("Erro ao gerar PDF para este diagnóstico.")
                    st.markdown('</div>', unsafe_allow_html=True)

        elif not admin_data_carregada_view_sucesso:
            st.warning("Dados de diagnósticos não puderam ser carregados. Funcionalidades limitadas.")

    elif menu_admin == "Gerenciar Instruções":
        st.markdown("#### ✍️ Editar Texto das Instruções para Clientes")
        
        current_instructions_text = ""
        if os.path.exists(instrucoes_custom_path):
            with open(instrucoes_custom_path, "r", encoding="utf-8") as f:
                current_instructions_text = f.read()
        elif os.path.exists(instrucoes_default_path):
            with open(instrucoes_default_path, "r", encoding="utf-8") as f:
                current_instructions_text = f.read()
            with open(instrucoes_custom_path, "w", encoding="utf-8") as f_custom:
                f_custom.write(current_instructions_text)
            st.info(f"Arquivo de instruções '{instrucoes_custom_path}' não encontrado. Carregado e salvo a partir do padrão.")
        else:
            st.error(f"Arquivo de instruções padrão '{instrucoes_default_path}' não encontrado! Crie este arquivo com o texto base.")
            current_instructions_text = "Erro ao carregar instruções. Verifique os arquivos no servidor."

        edited_text = st.text_area(
            "Edite o texto abaixo (suporta Markdown):",
            value=current_instructions_text,
            height=600,
            key="instrucoes_editor_v19"
        )

        if st.button("Salvar Instruções", key="save_instrucoes_v19", icon="💾", use_container_width=True):
            try:
                with open(instrucoes_custom_path, "w", encoding="utf-8") as f:
                    f.write(edited_text)
                st.toast("Instruções salvas com sucesso!", icon="🎉")
                current_instructions_text = edited_text 
            except Exception as e_save_instr:
                st.error(f"Erro ao salvar as instruções: {e_save_instr}")

    elif menu_admin == "Histórico de Usuários":
        try:
            df_historico_completo_hu = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
            df_usuarios_para_filtro_hu = pd.read_csv(usuarios_csv, encoding='utf-8', usecols=['CNPJ', 'Empresa', 'NomeContato'], dtype={'CNPJ': str})
        except FileNotFoundError:
            st.error("Arquivo de histórico ou usuários não encontrado.")
            df_historico_completo_hu = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"]) 
            df_usuarios_para_filtro_hu = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato'])
        except Exception as e_hu:
            st.error(f"Erro ao carregar dados para o histórico: {e_hu}")
            df_historico_completo_hu = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
            df_usuarios_para_filtro_hu = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato'])

        st.markdown("#### Filtros do Histórico")
        col_hu_f1, col_hu_f2 = st.columns(2)
        empresas_hist_list_hu = ["Todas"]
        if not df_usuarios_para_filtro_hu.empty and 'Empresa' in df_usuarios_para_filtro_hu.columns:
            empresas_hist_list_hu.extend(sorted(df_usuarios_para_filtro_hu['Empresa'].astype(str).unique().tolist()))
        
        emp_sel_hu = col_hu_f1.selectbox("Filtrar por Empresa:", empresas_hist_list_hu, key="hist_emp_sel_v19")
        termo_busca_hu = col_hu_f2.text_input("Buscar por Nome do Contato, CNPJ, Ação ou Descrição:", key="hist_termo_busca_v19")

        df_historico_filtrado_view_hu = df_historico_completo_hu.copy()

        if emp_sel_hu != "Todas" and not df_usuarios_para_filtro_hu.empty:
            cnpjs_da_empresa_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['Empresa'] == emp_sel_hu]['CNPJ'].tolist()
            df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_da_empresa_hu)]
        
        if termo_busca_hu.strip():
            busca_lower_hu = termo_busca_hu.strip().lower()
            cnpjs_match_nome_hu = []
            if not df_usuarios_para_filtro_hu.empty and 'NomeContato' in df_usuarios_para_filtro_hu.columns:
                cnpjs_match_nome_hu = df_usuarios_para_filtro_hu[
                    df_usuarios_para_filtro_hu['NomeContato'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)
                ]['CNPJ'].tolist()
            
            df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[
                df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_match_nome_hu) | 
                df_historico_filtrado_view_hu['CNPJ'].astype(str).str.lower().str.contains(busca_lower_hu) |
                df_historico_filtrado_view_hu['Ação'].astype(str).str.lower().str.contains(busca_lower_hu, na=False) |
                df_historico_filtrado_view_hu['Descrição'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)
            ]

        st.markdown("#### Registros do Histórico")
        if not df_historico_filtrado_view_hu.empty:
            st.dataframe(df_historico_filtrado_view_hu.sort_values(by="Data", ascending=False), use_container_width=True)
        else:
            st.info("Nenhum registro de histórico encontrado para os filtros aplicados.")

    elif menu_admin == "Gerenciar Perguntas":
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
                    with st.container():
                        st.markdown(f"""
                        <div class="custom-card" style="margin-bottom: 15px;">
                            <p style="font-size: 0.8em; color: #6b7280; margin-bottom: 5px;">ID: {i_p_admin} | Categoria: <b>{row_p_admin.get("Categoria", "Geral")}</b></p>
                            <p style="font-weight: 500;">{row_p_admin["Pergunta"]}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        with st.expander("✏️ Editar Pergunta"):
                            cols_edit_perg = st.columns([3, 2])
                            novo_p_text_admin = cols_edit_perg[0].text_area("Texto da Pergunta:", value=str(row_p_admin["Pergunta"]), key=f"edit_p_txt_v19_gp_{i_p_admin}", height=100)
                            nova_cat_text_admin = cols_edit_perg[1].text_input("Categoria:", value=str(row_p_admin.get("Categoria", "Geral")), key=f"edit_p_cat_v19_gp_{i_p_admin}")

                            col_btn1, col_btn2 = st.columns([0.15, 0.85])
                            if col_btn1.button("Salvar", key=f"salvar_p_adm_v19_gp_{i_p_admin}", help="Salvar Alterações", icon="💾"):
                                perguntas_df_admin_gp.loc[i_p_admin, "Pergunta"] = novo_p_text_admin
                                perguntas_df_admin_gp.loc[i_p_admin, "Categoria"] = nova_cat_text_admin
                                perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.toast(f"Pergunta {i_p_admin} atualizada.", icon="✅"); st.rerun()

                            if col_btn2.button("Deletar", type="primary", key=f"deletar_p_adm_v19_gp_{i_p_admin}", help="Deletar Pergunta", icon="🗑️"):
                                perguntas_df_admin_gp = perguntas_df_admin_gp.drop(i_p_admin).reset_index(drop=True)
                                perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.toast(f"Pergunta {i_p_admin} removida.", icon="🗑️"); st.rerun()
                    st.divider()
        with tabs_perg_admin[1]:
            with st.form("form_nova_pergunta_admin_v19_gp"):
                st.subheader("➕ Adicionar Nova Pergunta")
                nova_p_form_txt_admin = st.text_input("Texto da Pergunta", key="nova_p_input_admin_txt_v19_gp")
                cat_existentes_gp = sorted(list(perguntas_df_admin_gp['Categoria'].astype(str).unique())) if not perguntas_df_admin_gp.empty else []
                cat_options_gp = ["Nova Categoria"] + cat_existentes_gp
                cat_selecionada_gp = st.selectbox("Categoria:", cat_options_gp, key="cat_select_admin_new_q_v19_gp")
                nova_cat_form_admin_gp = st.text_input("Nome da Nova Categoria:", key="nova_cat_input_admin_new_q_v19_gp") if cat_selecionada_gp == "Nova Categoria" else cat_selecionada_gp

                tipo_p_form_admin = st.selectbox("Tipo de Pergunta (será adicionado ao final do texto da pergunta):",
                                                 ["Pontuação (0-10)", "Pontuação (0-5)", "Texto Aberto", "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)", "[Matriz GUT]"],
                                                 key="tipo_p_select_admin_new_q_v19_gp")
                add_p_btn_admin = st.form_submit_button("Adicionar Pergunta", icon="➕", use_container_width=True)
                if add_p_btn_admin:
                    if nova_p_form_txt_admin.strip() and nova_cat_form_admin_gp.strip():
                        p_completa_add_admin = f"{nova_p_form_txt_admin.strip()} [{tipo_p_form_admin.replace('[','').replace(']','')}]"
                        nova_entrada_p_add_admin = pd.DataFrame([[p_completa_add_admin, nova_cat_form_admin_gp.strip()]], columns=["Pergunta", "Categoria"])
                        perguntas_df_admin_gp = pd.concat([perguntas_df_admin_gp, nova_entrada_p_add_admin], ignore_index=True)
                        perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                        st.toast(f"Pergunta adicionada!", icon="🎉"); st.rerun()
                    else: st.warning("Texto da pergunta e categoria são obrigatórios.")

    elif menu_admin == "Gerenciar Análises de Perguntas":
        df_analises_existentes_admin = carregar_analises_perguntas()
        try: df_perguntas_formulario_admin = pd.read_csv(perguntas_csv, encoding='utf-8')
        except: df_perguntas_formulario_admin = pd.DataFrame(columns=colunas_base_perguntas)

        st.markdown("#### Adicionar Nova Análise")
        if df_perguntas_formulario_admin.empty:
            st.warning("Nenhuma pergunta cadastrada no formulário. Adicione perguntas primeiro em 'Gerenciar Perguntas'.")
        else:
            lista_perguntas_txt_admin = [""] + df_perguntas_formulario_admin["Pergunta"].unique().tolist()
            pergunta_selecionada_analise_admin = st.selectbox("Selecione a Pergunta para adicionar análise:", lista_perguntas_txt_admin, key="sel_perg_analise_v19_ga")

            if pergunta_selecionada_analise_admin:
                st.caption(f"Pergunta selecionada: {pergunta_selecionada_analise_admin}")

                tipo_condicao_analise_display_admin = st.selectbox("Tipo de Condição para a Análise:",
                                                                   ["Faixa Numérica (p/ Pontuação 0-X)",
                                                                    "Valor Exato (p/ Escala)",
                                                                    "Faixa de Score (p/ Matriz GUT)",
                                                                    "Análise Padrão (default para a pergunta)"],
                                                                   key="tipo_cond_analise_v19_ga")

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
                    cond_val_min_ui_admin = cols_faixa_ui_admin[0].number_input("Valor Mínimo da Faixa", step=1.0, format="%.2f", key="cond_min_analise_v19_ga")
                    cond_val_max_ui_admin = cols_faixa_ui_admin[1].number_input("Valor Máximo da Faixa", step=1.0, format="%.2f", key="cond_max_analise_v19_ga")
                elif tipo_condicao_csv_val_admin == "ValorExatoEscala":
                    cond_val_exato_ui_admin = st.text_input("Valor Exato da Escala (ex: Baixo, Médio, Alto)", key="cond_exato_analise_v19_ga")
                elif tipo_condicao_csv_val_admin == "ScoreGUT":
                    cols_faixa_gut_ui_admin = st.columns(2)
                    cond_val_min_ui_admin = cols_faixa_gut_ui_admin[0].number_input("Score GUT Mínimo", step=1, key="cond_min_gut_analise_v19_ga")
                    cond_val_max_ui_admin = cols_faixa_gut_ui_admin[1].number_input("Score GUT Máximo (opcional, deixe 0 ou vazio se for 'acima de Mínimo')", value=0.0, step=1.0, format="%.0f", key="cond_max_gut_analise_v19_ga")

                texto_analise_nova_ui_admin = st.text_area("Texto da Análise:", height=150, key="txt_analise_nova_v19_ga")

                if st.button("Salvar Nova Análise", key="salvar_analise_pergunta_v19_ga", icon="💾", use_container_width=True):
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
                        st.toast("Nova análise salva!", icon="🎉"); st.rerun()
                    else: st.error("O texto da análise não pode estar vazio.")

        st.markdown("---"); st.subheader("📜 Análises Cadastradas")
        if df_analises_existentes_admin.empty: st.info("Nenhuma análise cadastrada.")
        else:
            df_display_analises = df_analises_existentes_admin.copy()
            for col_num_format in ['CondicaoValorMin', 'CondicaoValorMax']:
                if col_num_format in df_display_analises.columns:
                    df_display_analises[col_num_format] = pd.to_numeric(df_display_analises[col_num_format], errors='coerce').fillna("")
            st.dataframe(df_display_analises, use_container_width=True)

            analise_del_id_admin = st.selectbox("Deletar Análise por ID:", [""] + df_analises_existentes_admin["ID_Analise"].astype(str).tolist(), key="del_analise_id_v19_ga")
            if st.button("Deletar Análise Selecionada", key="btn_del_analise_v19_ga", icon="🗑️", type="primary"):
                if analise_del_id_admin:
                    df_analises_existentes_admin = df_analises_existentes_admin[df_analises_existentes_admin["ID_Analise"] != analise_del_id_admin]
                    df_analises_existentes_admin.to_csv(analises_perguntas_csv, index=False, encoding='utf-8')
                    st.toast("Análise deletada.", icon="🗑️"); st.rerun()
                else:
                    st.warning("Selecione uma análise para deletar.")


    elif menu_admin == "Gerenciar Clientes":
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
            st.dataframe(df_usuarios_gc[cols_display_gc], use_container_width=True)

            st.markdown("#### Ações de Cliente")
            clientes_lista_gc_ops = df_usuarios_gc.apply(lambda row: f"{row['Empresa']} ({row['CNPJ']})", axis=1).tolist()
            cliente_selecionado_str_gc = st.selectbox("Selecione o cliente para gerenciar:", [""] + clientes_lista_gc_ops, key="sel_cliente_gc_v19")

            if cliente_selecionado_str_gc:
                cnpj_selecionado_gc_val = cliente_selecionado_str_gc.split('(')[-1].replace(')','').strip()
                cliente_data_gc_val = df_usuarios_gc[df_usuarios_gc["CNPJ"] == cnpj_selecionado_gc_val].iloc[0]

                st.markdown(f"""
                <div class="custom-card">
                    <h4>{cliente_data_gc_val['Empresa']}</h4>
                    <p><strong>CNPJ:</strong> {cliente_data_gc_val['CNPJ']}</p>
                    <p><strong>Diagnósticos Disponíveis (Slots):</strong> {cliente_data_gc_val['DiagnosticosDisponiveis']}</p>
                    <p><strong>Diagnósticos Já Realizados:</strong> {cliente_data_gc_val['TotalDiagnosticosRealizados']}</p>
                </div>
                """, unsafe_allow_html=True)

                action_cols = st.columns(2)
                with action_cols[0]:
                    if st.button(f"Conceder +1 Diagnóstico", key=f"conceder_diag_gc_v19_{cnpj_selecionado_gc_val}", icon="➕", use_container_width=True):
                        novos_disponiveis = cliente_data_gc_val['DiagnosticosDisponiveis'] + 1
                        if update_user_data(cnpj_selecionado_gc_val, "DiagnosticosDisponiveis", novos_disponiveis):
                            registrar_acao("ADMIN", "Concessão Diagnóstico", f"Admin concedeu +1 slot para {cliente_data_gc_val['Empresa']} ({cnpj_selecionado_gc_val}). Total agora: {novos_disponiveis}")
                            st.toast(f"+1 Slot de diagnóstico concedido. Total agora: {novos_disponiveis}.", icon="🎉"); st.rerun()
                        else:
                            st.error("Falha ao conceder diagnóstico.")

                with action_cols[1]:
                    try: bloqueados_df_gc_check = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                    except FileNotFoundError: bloqueados_df_gc_check = pd.DataFrame(columns=["CNPJ"])

                    is_blocked_gc_check = cnpj_selecionado_gc_val in bloqueados_df_gc_check["CNPJ"].values
                    if is_blocked_gc_check:
                        if st.button(f"Desbloquear Acesso", key=f"desbloq_total_gc_v19_{cnpj_selecionado_gc_val}", icon="🔓", use_container_width=True):
                            bloqueados_df_gc_check = bloqueados_df_gc_check[bloqueados_df_gc_check["CNPJ"] != cnpj_selecionado_gc_val]
                            bloqueados_df_gc_check.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                            st.toast(f"Acesso total desbloqueado.", icon="✅"); st.rerun()
                    else:
                        if st.button(f"Bloquear Acesso", type="primary", key=f"bloq_total_gc_v19_{cnpj_selecionado_gc_val}", icon="🔒", use_container_width=True):
                            nova_entrada_bloqueio_gc_val = pd.DataFrame([{"CNPJ": cnpj_selecionado_gc_val}])
                            bloqueados_df_gc_check = pd.concat([bloqueados_df_gc_check, nova_entrada_bloqueio_gc_val], ignore_index=True)
                            bloqueados_df_gc_check.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                            st.toast(f"Acesso total bloqueado.", icon="🚫"); st.rerun()
        else:
            st.info("Nenhum cliente cadastrado para gerenciar.")

        st.markdown("---")
        st.markdown("#### Adicionar Novo Cliente")
        with st.form("form_novo_cliente_v19", clear_on_submit=True):
            novo_cnpj_gc_form = st.text_input("CNPJ do Novo Cliente:")
            nova_senha_gc_form = st.text_input("Senha para o Novo Cliente:", type="password")
            nova_empresa_gc_form = st.text_input("Nome da Empresa do Novo Cliente:")
            novo_contato_gc_form = st.text_input("Nome do Contato (opcional):")
            novo_telefone_gc_form = st.text_input("Telefone do Contato (opcional):")
            submit_novo_cliente_gc_form = st.form_submit_button("Cadastrar Novo Cliente", icon="➕", use_container_width=True)

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
                        st.toast(f"Cliente {nova_empresa_gc_form} cadastrado com sucesso!", icon="🎉"); st.rerun()
                    else: st.error("CNPJ já cadastrado.")
                else: st.error("CNPJ, Senha e Nome da Empresa são obrigatórios.")

    elif menu_admin == "Gerenciar Administradores":
        try:
            admins_df_mng = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
        except (FileNotFoundError, pd.errors.EmptyDataError):
            admins_df_mng = pd.DataFrame(columns=["Usuario", "Senha"])

        st.dataframe(admins_df_mng[["Usuario"]], use_container_width=True)
        st.markdown("---"); st.subheader("➕ Adicionar Novo Admin")
        with st.form("form_novo_admin_mng_v19"):
            novo_admin_user_mng = st.text_input("Usuário do Admin")
            novo_admin_pass_mng = st.text_input("Senha do Admin", type="password")
            adicionar_admin_btn_mng = st.form_submit_button("Adicionar Admin", icon="➕", use_container_width=True)
        if adicionar_admin_btn_mng:
            if novo_admin_user_mng and novo_admin_pass_mng:
                if novo_admin_user_mng in admins_df_mng["Usuario"].values:
                    st.error(f"Usuário '{novo_admin_user_mng}' já existe.")
                else:
                    novo_admin_data_mng = pd.DataFrame([[novo_admin_user_mng, novo_admin_pass_mng]], columns=["Usuario", "Senha"])
                    admins_df_mng = pd.concat([admins_df_mng, novo_admin_data_mng], ignore_index=True)
                    admins_df_mng.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                    st.toast(f"Admin '{novo_admin_user_mng}' adicionado!", icon="🎉"); st.rerun()
            else: st.warning("Preencha todos os campos.")

        st.markdown("---"); st.subheader("🗑️ Remover Admin")
        if not admins_df_mng.empty:
            admin_para_remover_mng = st.selectbox("Remover Admin:", options=[""] + admins_df_mng["Usuario"].tolist(), key="remove_admin_select_mng_v19")
            if st.button("Remover Admin Selecionado", type="primary", key="btn_remove_admin_v19", icon="🗑️"):
                if admin_para_remover_mng:
                    if len(admins_df_mng) == 1 and admin_para_remover_mng == admins_df_mng["Usuario"].iloc[0]:
                        st.error("Não é possível remover o único administrador.")
                    else:
                        admins_df_mng = admins_df_mng[admins_df_mng["Usuario"] != admin_para_remover_mng]
                        admins_df_mng.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                        st.toast(f"Admin '{admin_para_remover_mng}' removido.", icon="🗑️"); st.rerun()
                else:
                    st.warning("Selecione um administrador para remover.")
        else: st.info("Nenhum administrador para remover.")

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()