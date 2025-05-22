import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import time
from fpdf import FPDF # Certifique-se que está instalado: pip install fpdf2
import tempfile
import re
import json
import plotly.express as px
import uuid

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", page_icon="📊")

# --- CSS Melhorado ---
st.markdown("""
<style>
body {font-family: 'Segoe UI', sans-serif;}
.login-container {max-width: 450px; margin: 40px auto 0 auto; padding: 40px; border-radius: 10px; background-color: #ffffff; box-shadow: 0 4px 20px rgba(0,0,0,0.1); font-family: 'Segoe UI', sans-serif;}
.login-container img {display: block; margin-left: auto; margin-right: auto; margin-bottom: 20px;}
.login-container h2 {text-align: center; margin-bottom: 30px; font-weight: 600; font-size: 26px; color: #2563eb;}
.stButton>button {border-radius: 6px; background-color: #2563eb; color: white; font-weight: 500; padding: 0.6rem 1.3rem; margin-top: 0.5rem; border: none; transition: background-color 0.3s ease;}
.stButton>button:hover {background-color: #1d4ed8;}
.stButton>button.secondary {background-color: #e5e7eb; color: #374151;}
.stButton>button.secondary:hover {background-color: #d1d5db;}
.stDownloadButton>button {background-color: #10b981; color: white; font-weight: 600; border-radius: 6px; margin-top: 10px; padding: 0.6rem 1.3rem; border: none; transition: background-color 0.3s ease;}
.stDownloadButton>button:hover {background-color: #059669;}
.stTextInput>div>input, .stTextArea>div>textarea, .stDateInput>div>input, .stSelectbox>div>div {border-radius: 6px; padding: 0.6rem; border: 1px solid #d1d5db; background-color: #f9fafb; transition: border-color 0.3s ease, box-shadow 0.3s ease;}
.stTextInput>div>input:focus, .stTextArea>div>textarea:focus, .stDateInput>div>input:focus, .stSelectbox>div>div:focus-within {border-color: #2563eb; box-shadow: 0 0 0 0.1rem rgba(37, 99, 235, 0.25);}
.stTabs [data-baseweb="tab"] {font-size: 16px; font-weight: 600; padding: 12px 22px; border-radius: 6px 6px 0 0;}
.stTabs [data-baseweb="tab"][aria-selected="true"] {background-color: #2563eb; color: white;}
.custom-card {border: 1px solid #e0e0e0; border-left: 5px solid #2563eb; padding: 20px; margin-bottom: 15px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 2px 5px rgba(0,0,0,0.07);}
.custom-card h4 {margin-top: 0; color: #2563eb; font-size: 1.1em;}
.feedback-saved {font-size: 0.85em; color: #10b981; font-style: italic; margin-top: -8px; margin-bottom: 8px;}
.analise-pergunta-cliente {font-size: 0.9em; color: #333; background-color: #eef2ff; border-left: 3px solid #6366f1; padding: 10px; margin-top: 8px; margin-bottom:12px; border-radius: 4px;}
[data-testid="stMetric"] {background-color: #ffffff; border-radius: 8px; padding: 15px 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.07); border: 1px solid #e0e0e0;}
[data-testid="stMetricLabel"] {font-weight: 500; color: #4b5563;}
[data-testid="stMetricValue"] {font-size: 1.8em;}
[data-testid="stMetricDelta"] {font-size: 0.9em;}
.stExpander {border: 1px solid #e0e0e0 !important; border-radius: 8px !important; box-shadow: 0 2px 5px rgba(0,0,0,0.07) !important; margin-bottom: 15px !important;}
.stExpander header {font-weight: 600 !important; border-radius: 8px 8px 0 0 !important; padding: 10px 15px !important;}
.dashboard-item {background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.07); margin-bottom: 20px; border: 1px solid #e0e0e0; height: 100%;}
.dashboard-item h5 {margin-top: 0; margin-bottom: 15px; color: #2563eb; font-size: 1.1em; border-bottom: 1px solid #eee; padding-bottom: 8px;}
.sac-feedback-button button {background-color: #f0f0f0; color: #333; border: 1px solid #ccc; margin-right: 5px; padding: 0.3rem 0.8rem;}
.sac-feedback-button button:hover {background-color: #e0e0e0;}
.sac-feedback-button button.active {background-color: #2563eb; color: white; border-color: #2563eb;}
</style>
""", unsafe_allow_html=True)

# --- Funções de Gráficos ---
def create_radar_chart(data_dict, title="Radar Chart"):
    if not data_dict or not isinstance(data_dict, dict): return None
    categories = []
    values = []
    for k, v_raw in data_dict.items():
        val_num = pd.to_numeric(v_raw, errors='coerce')
        if pd.notna(val_num):
            categories.append(k)
            values.append(val_num)
    if not categories or not values or len(categories) < 3: return None
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]
    df_radar = pd.DataFrame(dict(r=values_closed, theta=categories_closed))
    fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True, template="seaborn")
    fig.update_traces(fill='toself', line=dict(color='#2563eb'))
    fig.update_layout(title={'text': title, 'x':0.5, 'xanchor': 'center'}, polar=dict(radialaxis=dict(visible=True, range=[0, 5])), font=dict(family="Segoe UI, sans-serif"), margin=dict(l=50, r=50, t=70, b=50))
    return fig

def create_gut_barchart(gut_data_list, title="Top Prioridades (GUT)"):
    if not gut_data_list: return None
    df_gut = pd.DataFrame(gut_data_list)
    if df_gut.empty or not all(col in df_gut.columns for col in ["Tarefa", "Score"]): return None
    df_gut["Score"] = pd.to_numeric(df_gut["Score"], errors='coerce')
    df_gut.dropna(subset=["Score"], inplace=True)
    df_gut = df_gut.sort_values(by="Score", ascending=False).head(10)
    if df_gut.empty: return None
    max_len_tarefa = df_gut['Tarefa'].astype(str).map(len).max() if not df_gut.empty else 20
    margin_l_dynamic = max(150, int(max_len_tarefa * 7.5)) # Ajuste o multiplicador
    fig = px.bar(df_gut, x="Score", y="Tarefa", title=title, orientation='h', color="Score", color_continuous_scale=px.colors.sequential.Blues_r, labels={'Tarefa':'Tarefa/Pergunta', 'Score':'Score GUT'})
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Score GUT", yaxis_title="", font=dict(family="Segoe UI, sans-serif"), height=max(400, 200 + len(df_gut)*30), margin=dict(l=margin_l_dynamic, r=20, t=70, b=20))
    return fig

def create_diagnostics_timeline_chart(df_diagnostics, title="Diagnósticos Realizados ao Longo do Tempo"):
    if df_diagnostics.empty or 'Data_dt' not in df_diagnostics.columns: return None
    df_diag_copy = df_diagnostics.dropna(subset=['Data_dt']).copy()
    if df_diag_copy.empty : return None
    diag_counts_monthly = df_diag_copy.groupby(pd.Grouper(key='Data_dt', freq='M')).size().reset_index(name='Contagem')
    diag_counts_monthly['Mês'] = diag_counts_monthly['Data_dt'].dt.strftime('%Y-%m')
    if diag_counts_monthly.empty: return None
    fig = px.line(diag_counts_monthly, x='Mês', y='Contagem', title=title, markers=True, labels={'Mês':'Mês', 'Contagem':'Nº de Diagnósticos'}, line_shape="spline")
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
            avg_scores_data.append({'Categoria': col.replace("Media_Cat_", "").replace("_", " "), 'Média_Score': numeric_scores.mean()})
    if not avg_scores_data: return None
    avg_scores = pd.DataFrame(avg_scores_data)
    if avg_scores.empty : return None
    avg_scores = avg_scores.sort_values(by="Média_Score", ascending=False)
    max_y_val = 5.5
    if not avg_scores.empty and 'Média_Score' in avg_scores.columns and avg_scores['Média_Score'].notna().any():
        max_y_val = max(5.5, avg_scores['Média_Score'].max() + 0.5)
    fig = px.bar(avg_scores, x='Categoria', y='Média_Score', title=title, color='Média_Score', color_continuous_scale=px.colors.sequential.Blues_r, labels={'Categoria':'Categoria', 'Média_Score':'Média do Score'})
    fig.update_layout(xaxis_tickangle=-45, font=dict(family="Segoe UI, sans-serif"), yaxis=dict(range=[0, max_y_val]))
    return fig

def create_client_engagement_pie(df_usuarios, title="Engajamento de Clientes (Nº de Diagnósticos)"):
    if df_usuarios.empty or 'TotalDiagnosticosRealizados' not in df_usuarios.columns: return None
    def categorize_diagnostics(count):
        if count == 0: return "0 Diagnósticos"
        if count == 1: return "1 Diagnóstico"
        if count == 2: return "2 Diagnósticos"
        return "3+ Diagnósticos"
    df_usuarios_copy = df_usuarios.copy()
    df_usuarios_copy['TotalDiagnosticosRealizados'] = pd.to_numeric(df_usuarios_copy['TotalDiagnosticosRealizados'], errors='coerce').fillna(0).astype(int)
    df_usuarios_copy['Engajamento'] = df_usuarios_copy['TotalDiagnosticosRealizados'].apply(categorize_diagnostics)
    engagement_counts = df_usuarios_copy['Engajamento'].value_counts().reset_index()
    engagement_counts.columns = ['Categoria_Engajamento', 'Numero_Clientes']
    if engagement_counts.empty: return None
    fig = px.pie(engagement_counts, values='Numero_Clientes', names='Categoria_Engajamento', title=title, color_discrete_sequence=px.colors.sequential.Blues_r)
    fig.update_traces(textposition='inside', textinfo='percent+label', insidetextorientation='radial')
    fig.update_layout(font=dict(family="Segoe UI, sans-serif"), legend_title_text='Nível de Engajamento')
    return fig

# --- Configuração de Arquivos e Variáveis Globais ---
admin_credenciais_csv = "admins.csv"; usuarios_csv = "usuarios.csv"; arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"; perguntas_csv = "perguntas_formulario.csv"; historico_csv = "historico_clientes.csv"
analises_perguntas_csv = "analises_perguntas.csv"; notificacoes_csv = "notificacoes.csv"; instrucoes_custom_path = "instrucoes_portal.md"
instrucoes_default_path = "instrucoes_portal_default.md"; sac_perguntas_respostas_csv = "sac_perguntas_respostas.csv"
sac_uso_feedback_csv = "sac_uso_feedback.csv"; pesquisa_satisfacao_perguntas_csv = "pesquisa_satisfacao_perguntas.csv"
pesquisa_satisfacao_respostas_csv = "pesquisa_satisfacao_respostas.csv"; LOGOS_DIR = "client_logos"

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None, "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {}, "sac_feedback_registrado": {}, "force_sidebar_rerun_after_notif_read_v19": False,
    "target_diag_data_for_expansion": None, "id_diagnostico_concluido_para_satisfacao": None,
    "respostas_pesquisa_satisfacao_atual": {}, "pesquisa_satisfacao_enviada": False,
}
for key, value in default_session_state.items():
    if key not in st.session_state: st.session_state[key] = value

# --- Funções Utilitárias ---
def sanitize_column_name(name): s = str(name).strip().replace(' ', '_'); s = re.sub(r'(?u)[^-\w.]', '', s); return s
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
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone", "JaVisualizouInstrucoes", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Timestamp", "Mensagem", "Lida", "ID_Diagnostico_Relacionado"]
colunas_base_sac_perguntas = ["ID_SAC_Pergunta", "Pergunta_SAC", "Resposta_SAC", "Categoria_SAC", "DataCriacao"]
colunas_base_sac_uso_feedback = ["ID_Uso_SAC", "Timestamp", "CNPJ_Cliente", "ID_SAC_Pergunta", "Feedback_Util"]
colunas_base_pesquisa_satisfacao_perguntas = ["ID_Pergunta_Satisfacao", "Texto_Pergunta", "Tipo_Pergunta", "Opcoes_Pergunta", "Ordem", "Ativa"]
colunas_base_pesquisa_satisfacao_respostas = ["ID_Resposta_Satisfacao", "ID_Diagnostico_Cliente", "ID_Pergunta_Satisfacao", "CNPJ_Cliente", "Timestamp_Resposta", "Resposta_Valor"]

def inicializar_csv(filepath, columns, defaults=None):
    try:
        dtype_spec = {}
        str_cols_map = {usuarios_csv: ['CNPJ'], usuarios_bloqueados_csv: ['CNPJ'], arquivo_csv: ['CNPJ', 'Data'], notificacoes_csv: ['CNPJ_Cliente', 'ID_Diagnostico_Relacionado'], sac_uso_feedback_csv: ['CNPJ_Cliente'], pesquisa_satisfacao_respostas_csv: ['CNPJ_Cliente', 'ID_Diagnostico_Cliente', 'ID_Pergunta_Satisfacao', 'Resposta_Valor']}
        if filepath in str_cols_map:
            for col_str in str_cols_map[filepath]:
                if col_str in columns: dtype_spec[col_str] = str
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if defaults:
                for col, default_val in defaults.items():
                    if col in columns: df_init[col] = default_val
            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else:
            try: df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)
            except (ValueError, TypeError): df_init = pd.read_csv(filepath, encoding='utf-8') # Fallback
            except Exception as read_e: st.error(f"Erro crítico ao ler {filepath}: {read_e}."); return pd.DataFrame(columns=columns)
            made_changes = False; current_df_cols = df_init.columns.tolist()
            for col_idx, col_name in enumerate(columns):
                if col_name not in current_df_cols:
                    default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                    df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=default_val); made_changes = True
            if made_changes: df_init.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError:
        df_init = pd.DataFrame(columns=columns)
        if defaults:
            for col, default_val in defaults.items():
                if col in columns: df_init[col] = default_val
        df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e: st.error(f"Erro fatal na inicializar_csv para {filepath}: {e}"); st.stop()

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"]); inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios, defaults={"JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"}); inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos); inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False, "ID_Diagnostico_Relacionado": None})
    inicializar_csv(sac_perguntas_respostas_csv, colunas_base_sac_perguntas, defaults={"Categoria_SAC": "Geral", "DataCriacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    inicializar_csv(sac_uso_feedback_csv, colunas_base_sac_uso_feedback, defaults={"Feedback_Util": pd.NA})
    inicializar_csv(pesquisa_satisfacao_perguntas_csv, colunas_base_pesquisa_satisfacao_perguntas, defaults={"Ordem": 0, "Ativa": True, "Opcoes_Pergunta": None})
    inicializar_csv(pesquisa_satisfacao_respostas_csv, colunas_base_pesquisa_satisfacao_respostas)
except Exception as e_init: st.error(f"Falha crítica na inicialização de arquivos CSV: {e_init}."); st.stop()

def registrar_acao(cnpj, acao, desc):
    try: hist_df = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ':str})
    except (FileNotFoundError, pd.errors.EmptyDataError): hist_df = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    new_entry = {"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": str(cnpj), "Ação": acao, "Descrição": desc}
    hist_df = pd.concat([hist_df, pd.DataFrame([new_entry])], ignore_index=True); hist_df.to_csv(historico_csv, index=False, encoding='utf-8')

def update_user_data(cnpj, field, value):
    try:
        users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        idx = users_df[users_df['CNPJ'] == str(cnpj)].index
        if not idx.empty:
            users_df.loc[idx, field] = value; users_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
            if 'user' in st.session_state and st.session_state.user and str(st.session_state.user.get('CNPJ')) == str(cnpj):
                if field in ["DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]: st.session_state.user[field] = int(value)
                elif field == "JaVisualizouInstrucoes": st.session_state.user[field] = str(value).lower() == "true"
                else: st.session_state.user[field] = value
            st.cache_data.clear(); return True
    except Exception as e: st.error(f"Erro ao atualizar usuário ({field}): {e}")
    return False

@st.cache_data
def carregar_analises_perguntas():
    try: return pd.read_csv(analises_perguntas_csv, encoding='utf-8')
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_analises)
@st.cache_data
def carregar_sac_perguntas_respostas():
    try:
        df = pd.read_csv(sac_perguntas_respostas_csv, encoding='utf-8')
        for col, default in [("Categoria_SAC", "Geral"), ("DataCriacao", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))]:
            if col not in df.columns: df[col] = default
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_sac_perguntas)
@st.cache_data
def carregar_sac_uso_feedback():
    try:
        df = pd.read_csv(sac_uso_feedback_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str})
        if 'Feedback_Util' in df.columns: df['Feedback_Util'] = df['Feedback_Util'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': pd.NA, 'none': pd.NA, '': pd.NA}).astype('boolean')
        else: df['Feedback_Util'] = pd.Series(dtype='boolean')
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_sac_uso_feedback)
@st.cache_data
def carregar_perguntas_satisfacao(apenas_ativas=True):
    try:
        df = pd.read_csv(pesquisa_satisfacao_perguntas_csv, encoding='utf-8')
        if df.empty: return pd.DataFrame(columns=colunas_base_pesquisa_satisfacao_perguntas)
        for col, default in [('Ativa', True), ('Ordem', 0), ('Opcoes_Pergunta', None)]:
            if col not in df.columns: df[col] = default
        df['Ativa'] = df['Ativa'].fillna(True).astype(bool); df['Ordem'] = pd.to_numeric(df['Ordem'], errors='coerce').fillna(0).astype(int)
        if apenas_ativas: df = df[df['Ativa'] == True]
        return df.sort_values(by="Ordem", ascending=True)
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_pesquisa_satisfacao_perguntas)
@st.cache_data
def carregar_respostas_satisfacao(cnpj_cliente=None, id_diagnostico=None):
    try:
        df = pd.read_csv(pesquisa_satisfacao_respostas_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Cliente': str, 'ID_Pergunta_Satisfacao': str, 'Resposta_Valor':str})
        if cnpj_cliente: df = df[df['CNPJ_Cliente'] == str(cnpj_cliente)]
        if id_diagnostico: df = df[df['ID_Diagnostico_Cliente'] == str(id_diagnostico)]
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_pesquisa_satisfacao_respostas)

def verificar_pesquisa_satisfacao_pendente(cnpj_cliente, id_diagnostico_cliente): return carregar_respostas_satisfacao(cnpj_cliente=cnpj_cliente, id_diagnostico=id_diagnostico_cliente).empty

def obter_analise_para_resposta(pergunta_texto, resposta_valor, df_analises):
    if df_analises.empty: return None
    analises_da_pergunta = df_analises[df_analises['TextoPerguntaOriginal'] == pergunta_texto]
    if analises_da_pergunta.empty: return None
    default_analise = None
    for _, row_analise in analises_da_pergunta.iterrows():
        tipo_cond = row_analise.get('TipoCondicao'); analise_txt = row_analise.get('TextoAnalise')
        if pd.isna(tipo_cond) or pd.isna(analise_txt): continue
        if tipo_cond == 'Default': default_analise = analise_txt; continue
        try:
            if tipo_cond == 'FaixaNumerica':
                min_val=pd.to_numeric(row_analise.get('CondicaoValorMin'),errors='raise'); max_val=pd.to_numeric(row_analise.get('CondicaoValorMax'),errors='raise'); resp_num=pd.to_numeric(resposta_valor,errors='raise')
                if min_val <= resp_num <= max_val: return analise_txt
            elif tipo_cond == 'ValorExatoEscala':
                cond_exato = row_analise.get('CondicaoValorExato')
                if pd.notna(cond_exato) and str(resposta_valor).strip().lower() == str(cond_exato).strip().lower(): return analise_txt
            elif tipo_cond == 'ScoreGUT':
                min_s=pd.to_numeric(row_analise.get('CondicaoValorMin'),errors='raise'); max_s_raw=row_analise.get('CondicaoValorMax'); max_s=pd.to_numeric(max_s_raw,errors='coerce') if pd.notna(max_s_raw) else pd.NA; resp_s_gut=pd.to_numeric(resposta_valor,errors='raise')
                is_min = resp_s_gut >= min_s; is_max_ok = pd.isna(max_s) or (resp_s_gut <= max_s)
                if is_min and is_max_ok: return analise_txt
        except: continue
    return default_analise

def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df_diagnostico, respostas_coletadas, medias_cat, analises_df):
    try:
        with st.spinner("Gerando PDF do diagnóstico... Aguarde."):
            pdf = FPDF(); pdf.add_page()
            empresa_nome = user_data.get("Empresa", "N/D"); cnpj_pdf = user_data.get("CNPJ", "N/D")
            logo_path = find_client_logo_path(cnpj_pdf)
            if logo_path:
                try: current_y = pdf.get_y(); pdf.image(logo_path, x=10, y=current_y, h=20); pdf.set_y(current_y + 20 + 5)
                except Exception as e_logo_pdf: st.warning(f"PDF: Logo não pôde ser adicionado: {e_logo_pdf}")
            pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome}"), 0, 1, 'C'); pdf.ln(5)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 7, pdf_safe_text_output(f"ID/Data Diagnóstico: {diag_data.get('Data','N/D')} | Empresa: {empresa_nome} (CNPJ: {cnpj_pdf})"))
            if user_data.get("NomeContato"): pdf.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {user_data.get('NomeContato')}"))
            if user_data.get("Telefone"): pdf.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {user_data.get('Telefone')}"))
            pdf.ln(3)
            mg_pdf = diag_data.get('Média Geral'); gut_pdf = diag_data.get('GUT Média')
            pdf.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral: {mg_pdf:.2f if pd.notna(mg_pdf) else 'N/A'} | GUT Média: {gut_pdf:.2f if pd.notna(gut_pdf) else 'N/A'}")); pdf.ln(3)
            if medias_cat:
                pdf.set_font("Arial", 'B', 11); pdf.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria:"))
                pdf.set_font("Arial", size=10)
                for cat, media_val in medias_cat.items():
                    media_str = f"{media_val:.2f}" if isinstance(media_val, (int, float)) and pd.notna(media_val) else str(media_val)
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat}: {media_str}"))
                pdf.ln(1); pdf.ln(5)
            for titulo, campo in [("Resumo (Cliente):", "Diagnóstico"), ("Análise (Cliente):", "Análise do Cliente"), ("Comentários (Consultor):", "Comentarios_Admin")]:
                valor = diag_data.get(campo, "")
                if valor and not pd.isna(valor) and str(valor).strip():
                    pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output(titulo))
                    pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(str(valor))); pdf.ln(3)
            pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas e Análises:"))
            if perguntas_df_diagnostico.empty or not all(col in perguntas_df_diagnostico.columns for col in ["Pergunta", "Categoria"]):
                 pdf.set_font("Arial", 'I', 10); pdf.multi_cell(0, 7, pdf_safe_text_output("Perguntas do diagnóstico não disponíveis.")); pdf.ln(3)
            else:
                for categoria in perguntas_df_diagnostico["Categoria"].unique():
                    pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria}")); pdf.set_font("Arial", size=9)
                    for _, p_row in perguntas_df_diagnostico[perguntas_df_diagnostico["Categoria"] == categoria].iterrows():
                        p_texto = p_row["Pergunta"]; resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto, "N/R")); analise_texto = None
                        if "[Matriz GUT]" in p_texto:
                            g,u,t,score=0,0,0,0
                            if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                            elif isinstance(resp, str) and resp.strip().startswith("{") and resp.strip().endswith("}"):
                                try: data_gut=json.loads(resp.replace("'",'"'));g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                                except: pass
                            score = g*u*t
                            pdf.multi_cell(0,6,pdf_safe_text_output(f"  - {p_texto.replace(' [Matriz GUT]','')}: G={g}, U={u}, T={t} (Score: {score})"))
                            analise_texto = obter_analise_para_resposta(p_texto, score, analises_df)
                        else:
                            pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {p_texto}: {resp}"))
                            analise_texto = obter_analise_para_resposta(p_texto, resp, analises_df)
                        if analise_texto: pdf.set_font("Arial", 'I', 8); pdf.set_text_color(100,100,100); pdf.multi_cell(0, 5, pdf_safe_text_output(f"    Análise: {analise_texto}")); pdf.set_text_color(0,0,0); pdf.set_font("Arial", size=9)
                    pdf.ln(2)
                pdf.ln(3)
            if not perguntas_df_diagnostico.empty:
                pdf.add_page(); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf.ln(5); pdf.set_font("Arial", size=10)
                gut_cards = []
                for _, p_row in perguntas_df_diagnostico.iterrows():
                    p_texto = p_row["Pergunta"]
                    if "[Matriz GUT]" in p_texto:
                        resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto)); g,u,t,score=0,0,0,0
                        if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                        elif isinstance(resp, str) and resp.strip().startswith("{") and resp.strip().endswith("}"):
                            try:data_gut=json.loads(resp.replace("'",'"'));g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                            except: pass
                        score = g*u*t; prazo = "N/A"
                        if score >= 75: prazo = "15 dias"
                        elif score >= 40: prazo = "30 dias"
                        elif score >= 20: prazo = "45 dias"
                        elif score > 0: prazo = "60 dias"
                        if prazo != "N/A": gut_cards.append({"Tarefa": p_texto.replace(" [Matriz GUT]", ""),"Prazo": prazo, "Score": score})
                if gut_cards:
                    for card in sorted(gut_cards, key=lambda x: (int(x["Prazo"].split(" ")[0]), -x["Score"])): pdf.multi_cell(0,6,pdf_safe_text_output(f"Prazo: {card['Prazo']} - Tarefa: {card['Tarefa']} (Score GUT: {card['Score']})"))
                else: pdf.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile: pdf_path = tmpfile.name; pdf.output(pdf_path)
        return pdf_path
    except Exception as e: st.error(f"Erro crítico ao gerar PDF: {e}"); st.exception(e); return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()
if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v20")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v20"):
        u = st.text_input("Usuário", key="admin_u_v20"); p = st.text_input("Senha", type="password", key="admin_p_v20")
        if st.form_submit_button("Entrar", use_container_width=True, icon="🔑"):
            try:
                df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                if not df_creds[(df_creds["Usuario"] == u) & (df_creds["Senha"] == p)].empty:
                    st.session_state.admin_logado = True; st.toast("Login de admin bem-sucedido!", icon="🎉"); st.rerun()
                else: st.error("Usuário/senha admin inválidos.")
            except Exception as e: st.error(f"Erro login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_v20"):
        c = st.text_input("CNPJ", key="cli_c_v20", value=st.session_state.get("last_cnpj_input",""))
        s = st.text_input("Senha", type="password", key="cli_s_v20")
        if st.form_submit_button("Entrar", use_container_width=True, icon="👤"):
            st.session_state.last_cnpj_input = c
            try:
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                for col, default, dtype_func_str in [("JaVisualizouInstrucoes", "False", "bool"), ("DiagnosticosDisponiveis", 1, "int"), ("TotalDiagnosticosRealizados", 0, "int")]:
                    if col not in users_df.columns: users_df[col] = default
                    if dtype_func_str == "int": users_df[col] = pd.to_numeric(users_df[col], errors='coerce').fillna(default).astype(int)
                    elif dtype_func_str == "bool": users_df[col] = users_df[col].astype(str).str.lower().map({'true': True, 'false': False, 'nan':False,'none':False,'':False}).fillna(default.lower()=='true' if isinstance(default,str) else False)
                blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                if c in blocked_df["CNPJ"].values: st.error("CNPJ bloqueado."); st.stop()
                match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                if match.empty: st.error("CNPJ/senha inválidos."); st.stop()
                st.session_state.cliente_logado = True; st.session_state.cnpj = c; st.session_state.user = match.iloc[0].to_dict()
                st.session_state.user["JaVisualizouInstrucoes"] = bool(st.session_state.user.get("JaVisualizouInstrucoes", False))
                st.session_state.user["DiagnosticosDisponiveis"] = int(st.session_state.user.get("DiagnosticosDisponiveis", 1))
                st.session_state.user["TotalDiagnosticosRealizados"] = int(st.session_state.user.get("TotalDiagnosticosRealizados", 0))
                st.session_state.inicio_sessao_cliente = time.time(); registrar_acao(c, "Login", "Usuário logou.")
                st.session_state.cliente_page = "Instruções" if not st.session_state.user["JaVisualizouInstrucoes"] else ("Novo Diagnóstico" if st.session_state.user["DiagnosticosDisponiveis"] > st.session_state.user["TotalDiagnosticosRealizados"] else "Painel Principal")
                st.session_state.id_formulario_atual = f"{st.session_state.cnpj}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                st.session_state.respostas_atuais_diagnostico = {}; st.session_state.progresso_diagnostico_percentual = 0; st.session_state.progresso_diagnostico_contagem = (0,0)
                st.session_state.feedbacks_respostas = {}; st.session_state.sac_feedback_registrado = {}
                st.session_state.diagnostico_enviado_sucesso = False; st.session_state.target_diag_data_for_expansion = None
                st.session_state.id_diagnostico_concluido_para_satisfacao = None; st.session_state.respostas_pesquisa_satisfacao_atual = {}; st.session_state.pesquisa_satisfacao_enviada = False
                st.toast("Login de cliente bem-sucedido!", icon="👋"); st.rerun()
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    if not st.session_state.user.get("JaVisualizouInstrucoes", False): st.session_state.cliente_page = "Instruções"
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    with st.sidebar.expander("👤 Meu Perfil", expanded=True):
        logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
        if logo_cliente_path: st.image(logo_cliente_path, width=100)
        st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
        st.write(f"**CNPJ:** {st.session_state.cnpj}")
        st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
        st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")
        total_slots = st.session_state.user.get('DiagnosticosDisponiveis', 0); realizados = st.session_state.user.get('TotalDiagnosticosRealizados', 0); restantes = max(0, total_slots - realizados)
        st.markdown(f"**Diagnósticos Contratados (Slots):** `{total_slots}`\n\n**Diagnósticos Realizados:** `{realizados}`\n\n**Diagnósticos Restantes:** `{restantes}`")
    notificacoes_nao_lidas_count = 0
    if os.path.exists(notificacoes_csv):
        try:
            df_notif_check = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str})
            if not df_notif_check.empty and 'Lida' in df_notif_check.columns:
                df_notif_check['Lida'] = df_notif_check['Lida'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': False, '': False}).fillna(False)
                notificacoes_nao_lidas_count = len(df_notif_check[(df_notif_check["CNPJ_Cliente"] == st.session_state.cnpj) & (df_notif_check["Lida"] == False)])
        except: pass
    notificacoes_label = "🔔 Notificações" + (f" ({notificacoes_nao_lidas_count} Nova(s))" if notificacoes_nao_lidas_count > 0 else "")
    menu_options_cli_map_full = {"Instruções": "📖 Instruções", "Novo Diagnóstico": "📋 Novo Diagnóstico", "Painel Principal": "🏠 Painel Principal", "Notificações": notificacoes_label, "SAC": "❓ SAC - Perguntas Frequentes"}
    menu_options_cli_map = menu_options_cli_map_full.copy()
    if not st.session_state.user.get("JaVisualizouInstrucoes", False): menu_options_cli_map = {"Instruções": "📖 Instruções"}; st.session_state.cliente_page = "Instruções"
    else:
        if not (st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)) and "Novo Diagnóstico" in menu_options_cli_map:
            if st.session_state.cliente_page == "Novo Diagnóstico": st.session_state.cliente_page = "Painel Principal"
            del menu_options_cli_map["Novo Diagnóstico"]
    menu_options_cli_display = list(menu_options_cli_map.values())
    if st.session_state.cliente_page not in menu_options_cli_map.keys(): st.session_state.cliente_page = "Instruções" if not st.session_state.user.get("JaVisualizouInstrucoes", False) else "Painel Principal"
    default_display_option = menu_options_cli_map.get(st.session_state.cliente_page)
    current_idx_cli = 0
    if default_display_option and default_display_option in menu_options_cli_display: current_idx_cli = menu_options_cli_display.index(default_display_option)
    elif menu_options_cli_display:
        current_idx_cli = 0
        try: st.session_state.cliente_page = [k for k,v in menu_options_cli_map.items() if v == menu_options_cli_display[0]][0]
        except IndexError: st.session_state.cliente_page = "Painel Principal"
    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v20_radio")
    selected_page_cli_clean = ""
    for key_page, val_page_display in menu_options_cli_map.items():
        if val_page_display == selected_page_cli_raw: selected_page_cli_clean = key_page; break
    if selected_page_cli_clean and selected_page_cli_clean != st.session_state.cliente_page :
        st.session_state.cliente_page = selected_page_cli_clean; st.rerun()
    if st.sidebar.button("Sair do Portal Cliente", icon="⬅️", key="logout_cliente_v20_btn", use_container_width=True):
        for key_item in list(st.session_state.keys()):
            if key_item not in ['admin_logado', 'last_cnpj_input']: del st.session_state[key_item]
        for key_d, value_d in default_session_state.items():
            if key_d not in ['admin_logado', 'last_cnpj_input']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False; st.toast("Logout realizado.", icon="👋"); st.rerun()

    # --- Páginas do Cliente ---
    if st.session_state.cliente_page == "Instruções":
        st.subheader(menu_options_cli_map_full["Instruções"])
        instrucoes_content_md = ("# Bem-vindo ao Portal de Diagnóstico!\n\nSiga as instruções para completar seu diagnóstico.\n\nEm caso de dúvidas, entre em contato com o administrador.")
        try:
            if os.path.exists(instrucoes_custom_path):
                with open(instrucoes_custom_path, "r", encoding="utf-8") as f: instrucoes_content_md = f.read()
            elif os.path.exists(instrucoes_default_path):
                with open(instrucoes_default_path, "r", encoding="utf-8") as f: instrucoes_content_md = f.read()
                st.caption("Exibindo instruções padrão. O administrador pode personalizar este texto.")
        except Exception as e_instr: st.warning(f"Erro ao carregar instruções: {e_instr}")
        st.markdown(instrucoes_content_md, unsafe_allow_html=True)
        if st.button("Entendi, prosseguir", key="btn_instrucoes_v20_btn", icon="👍"):
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True")
            if st.session_state.user: st.session_state.user["JaVisualizouInstrucoes"] = True
            pode_fazer_novo_inst = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_inst else "Painel Principal"
            st.rerun()

    elif st.session_state.cliente_page == "SAC":
        st.subheader(menu_options_cli_map_full["SAC"])
        df_sac_qa = carregar_sac_perguntas_respostas()
        if df_sac_qa.empty: st.info("Nenhuma pergunta frequente cadastrada no momento.")
        else:
            df_sac_qa_sorted = df_sac_qa.sort_values(by=["Categoria_SAC", "Pergunta_SAC"])
            categorias_sac = df_sac_qa_sorted["Categoria_SAC"].unique()
            search_term_sac = st.text_input("🔎 Procurar nas Perguntas Frequentes:", key="search_sac_cliente_v20")
            if search_term_sac:
                df_sac_qa_sorted = df_sac_qa_sorted[df_sac_qa_sorted["Pergunta_SAC"].str.contains(search_term_sac, case=False, na=False) | df_sac_qa_sorted["Resposta_SAC"].str.contains(search_term_sac, case=False, na=False) | df_sac_qa_sorted["Categoria_SAC"].str.contains(search_term_sac, case=False, na=False)]
                categorias_sac = df_sac_qa_sorted["Categoria_SAC"].unique()
            if df_sac_qa_sorted.empty and search_term_sac: st.info(f"Nenhuma pergunta encontrada para '{search_term_sac}'.")
            for categoria in categorias_sac:
                st.markdown(f"#### {categoria}")
                for idx_sac, row_sac in df_sac_qa_sorted[df_sac_qa_sorted["Categoria_SAC"] == categoria].iterrows():
                    with st.expander(f"{row_sac['Pergunta_SAC']}"):
                        st.markdown(row_sac['Resposta_SAC'], unsafe_allow_html=True)
                        feedback_key_base = f"sac_feedback_{row_sac['ID_SAC_Pergunta']}_v20"; feedback_dado = st.session_state.sac_feedback_registrado.get(row_sac['ID_SAC_Pergunta'])
                        cols_feedback = st.columns([1,1,8])
                        if cols_feedback[0].button("👍 Útil", key=f"{feedback_key_base}_util", type="secondary" if feedback_dado != "util" else "primary"):
                            try: # ... (lógica de salvar feedback útil)
                                pass
                            except: pass
                        if cols_feedback[1].button("👎 Não útil", key=f"{feedback_key_base}_nao_util", type="secondary" if feedback_dado != "nao_util" else "primary"):
                            try: # ... (lógica de salvar feedback não útil)
                                pass
                            except: pass
                        if feedback_dado: cols_feedback[2].caption(f"Feedback ('{feedback_dado.replace('_', ' ').capitalize()}') registrado.")
                st.markdown("---")

    elif st.session_state.cliente_page == "Notificações":
        st.subheader(menu_options_cli_map_full["Notificações"].split(" (")[0])
        # ... (Código completo da página de Notificações)
        pass

    elif st.session_state.cliente_page == "Painel Principal":
        st.subheader(menu_options_cli_map_full["Painel Principal"])
        target_diag_to_expand = st.session_state.pop("target_diag_data_for_expansion", None)
        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                try:
                    with open(st.session_state.pdf_gerado_path, "rb") as f_pdf: st.download_button(label="Baixar PDF do Diagnóstico", data=f_pdf, file_name=st.session_state.pdf_gerado_filename, mime="application/pdf", key="dl_novo_diag_painel_v20_dlbtn", icon="📄")
                    st.session_state.pdf_gerado_path = None; st.session_state.pdf_gerado_filename = None
                except Exception as e_pdf_dl: st.warning(f"Erro ao disponibilizar PDF: {e_pdf_dl}")
            if st.session_state.id_diagnostico_concluido_para_satisfacao and not st.session_state.pesquisa_satisfacao_enviada:
                id_diag_atual_s = st.session_state.id_diagnostico_concluido_para_satisfacao
                if verificar_pesquisa_satisfacao_pendente(st.session_state.cnpj, id_diag_atual_s):
                    st.markdown("---"); st.subheader("⭐ Pesquisa de Satisfação Rápida")
                    perguntas_s_df = carregar_perguntas_satisfacao(apenas_ativas=True)
                    if not perguntas_s_df.empty:
                         with st.form(key="form_pesquisa_s_cliente_final_submit_panel_v20"): # ... (renderização e envio da pesquisa de satisfação)
                            pass
                    else: st.info("Pesquisa de satisfação sem perguntas ativas.")
                elif not st.session_state.pesquisa_satisfacao_enviada : st.success("Feedback de satisfação já recebido para este diagnóstico. Obrigado!")
            st.session_state.diagnostico_enviado_sucesso = False
        # ... (Código restante do Painel Principal: gráficos, lista de diagnósticos, etc.)
        pass

    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader("📋 Novo Diagnóstico")
        if st.session_state.diagnostico_enviado_sucesso: st.session_state.cliente_page = "Painel Principal"; st.rerun()
        try: perguntas_df_formulario = pd.read_csv(perguntas_csv, encoding='utf-8')
        except Exception as e: st.error(f"Erro ao carregar perguntas: {e}"); st.stop()
        if perguntas_df_formulario.empty: st.warning("Nenhuma pergunta de diagnóstico cadastrada."); st.stop()
        if "Categoria" not in perguntas_df_formulario.columns: perguntas_df_formulario["Categoria"] = "Geral"
        total_perguntas_form = len(perguntas_df_formulario)
        if 'progresso_diagnostico_contagem' not in st.session_state or st.session_state.progresso_diagnostico_contagem[1] != total_perguntas_form:
             st.session_state.progresso_diagnostico_contagem = (st.session_state.get('progresso_diagnostico_contagem', (0,0))[0], total_perguntas_form)
        progresso_ph_novo = st.empty()
        # ... (Definições de calcular_e_mostrar_progresso_novo e on_change_resposta_novo)
        # ... (Loop de renderização do formulário)
        if st.button("Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v20_submit_btn", icon="✔️", use_container_width=True):
            with st.spinner("Processando e salvando seu diagnóstico..."):
                # !!! ESTA É A LÓGICA CRÍTICA ONDE O NameError ANTERIOR FOI RELATADO !!!
                # Certifique-se de que TODAS as variáveis usadas abaixo estão definidas NESTE ESCOPO
                respostas_finais_envio_novo = st.session_state.respostas_atuais_diagnostico.copy()
                cont_resp_n, total_para_resp_n = st.session_state.progresso_diagnostico_contagem
                if cont_resp_n < total_para_resp_n: st.warning("Por favor, responda todas as perguntas.")
                elif not respostas_finais_envio_novo.get("__resumo_cliente__","").strip(): st.error("O campo 'Resumo/principais insights' é obrigatório.")
                else:
                    soma_gut_n, count_gut_n = 0,0; respostas_csv_n = {}
                    for p_n,r_n in respostas_finais_envio_novo.items():
                        if p_n.startswith("__"): continue
                        if "[Matriz GUT]" in p_n and isinstance(r_n, dict):
                            respostas_csv_n[p_n] = json.dumps(r_n); g,u,t_val = int(r_n.get("G",0)), int(r_n.get("U",0)), int(r_n.get("T",0)); soma_gut_n += (g*u*t_val); count_gut_n +=1
                        else: respostas_csv_n[p_n] = r_n
                    gut_media_n = round(soma_gut_n/count_gut_n,2) if count_gut_n > 0 else 0.0
                    num_resp_n = [pd.to_numeric(v_n, errors='coerce') for k_n,v_n in respostas_finais_envio_novo.items() if not k_n.startswith("__") and ("[Matriz GUT]" not in k_n) and ("Pontuação" in k_n or "Escala" in k_n) ]
                    num_resp_n = [v for v in num_resp_n if pd.notna(v)] # Remove NaNs após conversão
                    media_geral_n = round(sum(num_resp_n)/len(num_resp_n),2) if num_resp_n else 0.0
                    emp_nome_n = st.session_state.user.get("Empresa","N/D")
                    id_diagnostico_salvo = str(st.session_state.id_formulario_atual)

                    nova_linha_diag_final_n = {
                        "Data": id_diagnostico_salvo, "CNPJ": str(st.session_state.cnpj),
                        "Nome": str(st.session_state.user.get("NomeContato", "")), "Email": str(st.session_state.user.get("Email", "")),
                        "Empresa": str(emp_nome_n), "Média Geral": media_geral_n, "GUT Média": gut_media_n,
                        "Observações": str(respostas_finais_envio_novo.get("__obs_cliente__","")),
                        "Diagnóstico": str(respostas_finais_envio_novo.get("__resumo_cliente__","")),
                        "Análise do Cliente": str(respostas_finais_envio_novo.get("__obs_cliente__","")),
                        "Comentarios_Admin": ""
                    }
                    nova_linha_diag_final_n.update(respostas_csv_n) # Adiciona respostas das perguntas
                    medias_cat_final_n = {}
                    # 'perguntas_df_formulario' DEVE estar definido aqui (carregado no início da página)
                    for cat_iter_n in perguntas_df_formulario["Categoria"].unique():
                        soma_c_n, cont_c_n = 0,0
                        for _,pr_n in perguntas_df_formulario[perguntas_df_formulario["Categoria"]==cat_iter_n].iterrows():
                            pt_n = pr_n["Pergunta"]; rv_n = respostas_finais_envio_novo.get(pt_n)
                            val_num_cat = pd.to_numeric(rv_n, errors='coerce')
                            if pd.notna(val_num_cat) and ("[Matriz GUT]" not in pt_n):
                                soma_c_n+=val_num_cat; cont_c_n+=1
                        mc_n = round(soma_c_n/cont_c_n,2) if cont_c_n>0 else 0.0
                        nova_linha_diag_final_n[f"Media_Cat_{sanitize_column_name(cat_iter_n)}"] = mc_n
                        medias_cat_final_n[cat_iter_n] = mc_n
                    try: df_todos_diags_n_leitura = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str, 'Data': str})
                    except (FileNotFoundError, pd.errors.EmptyDataError): df_todos_diags_n_leitura = pd.DataFrame(columns=list(nova_linha_diag_final_n.keys()))
                    for col_add in nova_linha_diag_final_n.keys():
                        if col_add not in df_todos_diags_n_leitura.columns: df_todos_diags_n_leitura[col_add] = pd.NA
                    df_todos_diags_n_escrita = pd.concat([df_todos_diags_n_leitura, pd.DataFrame([nova_linha_diag_final_n])], ignore_index=True)
                    df_todos_diags_n_escrita.to_csv(arquivo_csv, index=False, encoding='utf-8')
                    st.cache_data.clear()
                    update_user_data(st.session_state.cnpj, "TotalDiagnosticosRealizados", st.session_state.user.get("TotalDiagnosticosRealizados", 0) + 1)
                    registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", f"ID: {id_diagnostico_salvo}.")
                    analises_df_pdf = carregar_analises_perguntas()
                    perg_df_pdf = pd.read_csv(perguntas_csv, encoding='utf-8') if os.path.exists(perguntas_csv) else pd.DataFrame()
                    pdf_path_gerado_n = gerar_pdf_diagnostico_completo(nova_linha_diag_final_n, st.session_state.user, perg_df_pdf, respostas_finais_envio_novo, medias_cat_final_n, analises_df_pdf)
                    st.session_state.diagnostico_enviado_sucesso = True
                    st.session_state.id_diagnostico_concluido_para_satisfacao = id_diagnostico_salvo
                    st.session_state.pesquisa_satisfacao_enviada = False
                    if pdf_path_gerado_n: st.session_state.pdf_gerado_path = pdf_path_gerado_n; st.session_state.pdf_gerado_filename = f"diagnostico_{sanitize_column_name(emp_nome_n)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.session_state.respostas_atuais_diagnostico = {}; st.session_state.progresso_diagnostico_percentual = 0; st.session_state.progresso_diagnostico_contagem = (0,total_perguntas_form); st.session_state.feedbacks_respostas = {}; st.session_state.sac_feedback_registrado = {}
                    st.session_state.cliente_page = "Painel Principal"; st.rerun()

# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    try: st.sidebar.image("https://via.placeholder.com/200x80.png?text=Logo+Admin", use_container_width=True)
    except Exception as e_img_admin: st.sidebar.caption(f"Logo admin não carregada: {e_img_admin}")
    st.sidebar.success("🟢 Admin Logado")
    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v20_final_btn", use_container_width=True):
        st.session_state.admin_logado = False; st.toast("Logout de admin realizado.", icon="👋"); st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": "📊", "Relatório de Engajamento": "📈", "Gerenciar Notificações": "🔔",
        "Gerenciar Clientes": "👥", "Gerenciar Perguntas (Diagnóstico)": "📝", "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar SAC": "📞", "⭐ Gerenciar Pesquisa de Satisfação": "⭐", "📊 Relatório Pesquisa de Satisfação": "📊",
        "Gerenciar Instruções": "⚙️", "Histórico de Usuários": "📜", "Gerenciar Administradores": "👮"
    }
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key]} {key}" for key in admin_page_text_keys]
    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_key_v20_final"
    WIDGET_KEY_SB_ADMIN_MENU = "admin_sidebar_menu_v20_final"

    def admin_menu_on_change():
        selected_display_value = st.session_state.get(WIDGET_KEY_SB_ADMIN_MENU)
        if selected_display_value:
            new_text_key = next((text_key for text_key, emoji in menu_admin_options_map.items() if f"{emoji} {text_key}" == selected_display_value), None)
            if new_text_key and new_text_key != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
                st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key

    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE) not in admin_page_text_keys:
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]
    current_admin_page_text_key_for_index = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE, admin_page_text_keys[0])
    current_admin_menu_index = 0
    try:
        expected_display_value = f"{menu_admin_options_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
        current_admin_menu_index = admin_options_for_display.index(expected_display_value) if expected_display_value in admin_options_for_display else 0
    except (ValueError, KeyError): st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]; current_admin_menu_index = 0
    if current_admin_page_text_key_for_index not in admin_page_text_keys: # Double check
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]
        current_admin_menu_index = 0

    st.sidebar.selectbox("Funcionalidades Admin:", options=admin_options_for_display, index=current_admin_menu_index, key=WIDGET_KEY_SB_ADMIN_MENU, on_change=admin_menu_on_change)
    menu_admin = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE, admin_page_text_keys[0])
    if menu_admin not in menu_admin_options_map: menu_admin = admin_page_text_keys[0] # Final fallback
    st.header(f"{menu_admin_options_map.get(menu_admin, '❓')} {menu_admin}")

    df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios)
    try:
        df_temp_users = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        for col, default, dtype_func_str in [("JaVisualizouInstrucoes", "False", "bool"), ("DiagnosticosDisponiveis", 1, "int"), ("TotalDiagnosticosRealizados", 0, "int")]:
            if col not in df_temp_users.columns: df_temp_users[col] = default
            if dtype_func_str == "int": df_temp_users[col] = pd.to_numeric(df_temp_users[col], errors='coerce').fillna(default).astype(int)
            elif dtype_func_str == "bool": df_temp_users[col] = df_temp_users[col].astype(str).str.lower().map({'true': True, 'false': False, 'nan': False, 'none': False, '': False}).fillna(default.lower() == 'true' if isinstance(default, str) else False)
        df_usuarios_admin_geral = df_temp_users
    except FileNotFoundError: st.sidebar.error(f"Arquivo '{usuarios_csv}' não encontrado.")
    except Exception as e_load_users_adm: st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm}")

    if menu_admin == "Visão Geral e Diagnósticos":
        # ... (Código completo da Visão Geral e Diagnósticos)
        pass
    elif menu_admin == "Relatório de Engajamento":
        # ... (Código completo do Relatório de Engajamento)
        pass
    elif menu_admin == "Gerenciar Notificações":
        # ... (Código completo de Gerenciar Notificações)
        pass
    elif menu_admin == "Gerenciar Clientes":
        # ... (Código completo de Gerenciar Clientes)
        pass
    elif menu_admin == "Gerenciar Perguntas (Diagnóstico)":
        # ... (Código completo de Gerenciar Perguntas (Diagnóstico))
        pass
    elif menu_admin == "Gerenciar Análises de Perguntas":
        # ... (Código completo de Gerenciar Análises de Perguntas)
        pass
    elif menu_admin == "Gerenciar SAC":
        # ... (Código completo de Gerenciar SAC)
        pass
    elif menu_admin == "⭐ Gerenciar Pesquisa de Satisfação":
        # ... (Código completo de Gerenciar Pesquisa de Satisfação)
        pass
    elif menu_admin == "📊 Relatório Pesquisa de Satisfação":
        # ... (Código completo do Relatório Pesquisa de Satisfação)
        pass
    elif menu_admin == "Gerenciar Instruções":
        # ... (Código completo de Gerenciar Instruções)
        pass
    elif menu_admin == "Histórico de Usuários":
        # ... (Código completo do Histórico de Usuários)
        pass
    elif menu_admin == "Gerenciar Administradores":
        # ... (Código completo de Gerenciar Administradores)
        pass
    else: st.error(f"Página admin desconhecida: {menu_admin}")

elif not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()