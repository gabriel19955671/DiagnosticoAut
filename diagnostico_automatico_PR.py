import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import time
from fpdf import FPDF
from fpdf.enums import XPos, YPos # Importar XPos e YPos
import tempfile
import re
import json
import plotly.express as px
import plotly.graph_objects as go # Para gráfico de radar
import uuid

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", initial_sidebar_state="expanded")

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
.notification-dot { height: 8px; width: 8px; background-color: red; border-radius: 50%; display: inline-block; margin-left: 5px; }
.kpi-card { background-color: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; text-align: center; margin-bottom: 10px; }
.kpi-card h4 { font-size: 1.1em; color: #333; margin-bottom: 5px; }
.kpi-card .value { font-size: 1.8em; font-weight: bold; color: #2563eb; }
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
notificacoes_csv = "notificacoes.csv"
instrucoes_txt_file = "instrucoes_clientes.txt"
LOGOS_DIR = "client_logos"

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "confirmou_instrucoes_checkbox_cliente": False
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
            dtype_spec = {} # Initialize as empty dict
            if filepath == usuarios_csv: dtype_spec = {'CNPJ': str}
            elif filepath == usuarios_bloqueados_csv: dtype_spec = {'CNPJ': str}
            elif filepath == arquivo_csv: dtype_spec = {'CNPJ': str}
            elif filepath == notificacoes_csv: dtype_spec = {'CNPJ_Cliente': str}
            elif filepath == historico_csv: dtype_spec = {'CNPJ': str}
            
            if filepath == notificacoes_csv:
                try: 
                    temp_df_cols = pd.read_csv(filepath, encoding='utf-8', nrows=0).columns
                    if 'CNPJ_Cliente' not in temp_df_cols:
                            if 'CNPJ_Cliente' in dtype_spec: 
                                del dtype_spec['CNPJ_Cliente']
                except pd.errors.EmptyDataError: 
                    pass

            df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)
            made_changes = False
            expected_cols_df = pd.DataFrame(columns=columns)
            for col_idx, col_name in enumerate(expected_cols_df.columns):
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
    except Exception as e:
        st.error(f"Erro ao inicializar ou ler o arquivo {filepath}: {e}")
        st.info(f"Verifique se o arquivo '{filepath}' não está corrompido ou se o programa tem permissão para acessá-lo.")
        raise

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
            f.write("""**Bem-vindo ao Portal de Diagnóstico Empresarial!**

Este sistema foi projetado para ajudar a sua empresa a identificar pontos fortes e áreas de melhoria através de um questionário estruturado. Por favor, leia as seguintes instruções cuidadosamente antes de iniciar:

1.  **Preparação**:
    * Reserve um tempo adequado para responder todas as perguntas com atenção. A qualidade das suas respostas impactará diretamente a precisão do diagnóstico.
    * Tenha em mãos informações relevantes sobre os diversos setores da sua empresa (Finanças, Marketing, Operações, RH, etc.), se aplicável.

2.  **Respondendo ao Questionário**:
    * O questionário é dividido em categorias. Procure responder todas as perguntas de cada categoria.
    * **Perguntas de Pontuação (0-5 ou 0-10)**: Avalie o item da pergunta de acordo com a realidade da sua empresa, onde 0 geralmente representa "Não se aplica" ou "Muito Ruim" e a pontuação máxima (5 ou 10) representa "Excelente" ou "Totalmente Implementado".
    * **Matriz GUT (Gravidade, Urgência, Tendência)**: Para estas perguntas, você avaliará três aspectos:
        * **Gravidade (G)**: O quão sério é o impacto do problema/item se não for tratado? (0=Nenhum, 5=Extremamente Grave)
        * **Urgência (U)**: Com que rapidez uma ação precisa ser tomada? (0=Pode esperar, 5=Imediata)
        * **Tendência (T)**: Se nada for feito, o problema tende a piorar, manter-se estável ou melhorar? (0=Melhorar sozinho, 5=Piorar rapidamente)
        * O sistema calculará um score (G x U x T) para priorização.
    * **Perguntas de Texto Aberto**: Forneça respostas claras e concisas, detalhando a situação conforme solicitado.
    * **Perguntas de Escala**: Selecione a opção que melhor descreve a situação na sua empresa (ex: Muito Baixo, Baixo, Médio, Alto, Muito Alto).

3.  **Progresso e Envio**:
    * Seu progresso é salvo automaticamente à medida que você responde.
    * Você pode ver uma barra de progresso indicando quantas perguntas foram respondidas.
    * Ao final, revise suas respostas antes de clicar em "Concluir e Enviar Diagnóstico".
    * **O campo "Resumo/principais insights (para PDF)" é obrigatório.** Preencha com suas considerações gerais sobre o diagnóstico realizado.

4.  **Pós-Diagnóstico**:
    * Após o envio, um PDF do seu diagnóstico será gerado e disponibilizado para download.
    * Você poderá visualizar seus diagnósticos anteriores e acompanhar a evolução no "Painel Principal".
    * O consultor poderá adicionar comentários e análises ao seu diagnóstico, que ficarão visíveis no seu painel.

5.  **Confirmação**:
    * Ao marcar a caixa de seleção abaixo e prosseguir, você declara que leu, compreendeu e concorda em seguir estas instruções para a realização do diagnóstico.

Em caso de dúvidas, entre em contato com o consultor responsável.
""")
except Exception as e_init_global:
    st.error(f"⚠️ ERRO CRÍTICO NA INICIALIZAÇÃO DO APP:")
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
    - Verifique se todos os arquivos CSV esperados existem ou podem ser criados.
    """)
    st.stop() 


# --- Funções de Notificação ---
def criar_notificacao(cnpj_cliente, mensagem, data_diag_ref=None):
    try:
        df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df_notificacoes = pd.DataFrame(columns=colunas_base_notificacoes)
    msg_final = mensagem
    if data_diag_ref:
        msg_final = f"O consultor adicionou comentários ao seu diagnóstico de {data_diag_ref}."
    nova_notificacao = {"ID_Notificacao": str(uuid.uuid4()), "CNPJ_Cliente": str(cnpj_cliente), "Mensagem": msg_final, "DataHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Lida": False}
    df_notificacoes = pd.concat([df_notificacoes, pd.DataFrame([nova_notificacao])], ignore_index=True)
    df_notificacoes.to_csv(notificacoes_csv, index=False, encoding='utf-8')

def get_unread_notifications_count(cnpj_cliente):
    try:
        df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
        unread_count = len(df_notificacoes[(df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente)) & (df_notificacoes['Lida'] == False)])
        return unread_count
    except: return 0

def marcar_notificacoes_como_lidas(cnpj_cliente, ids_notificacoes=None):
    try:
        df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
        if ids_notificacoes:
            df_notificacoes.loc[(df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente)) & (df_notificacoes['ID_Notificacao'].isin(ids_notificacoes)), 'Lida'] = True
        else:
            df_notificacoes.loc[df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente), 'Lida'] = True
        df_notificacoes.to_csv(notificacoes_csv, index=False, encoding='utf-8')
        return True
    except Exception as e: st.error(f"Erro ao marcar notificações como lidas: {e}"); return False

# --- Demais Funções Utilitárias ---
def registrar_acao(cnpj, acao, desc):
    try: hist_df = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
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
                if field in ["DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "LiberacoesExtrasConcedidas"]:
                    st.session_state.user[field] = int(value)
                elif field == "ConfirmouInstrucoesParaSlotAtual":
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
        pdf = FPDF()
        pdf.add_page()
        empresa_nome = user_data.get("Empresa", "N/D")
        cnpj_pdf = user_data.get("CNPJ", "N/D")
        logo_path = find_client_logo_path(cnpj_pdf)
        if logo_path:
            try:
                current_y_logo = pdf.get_y(); max_h_logo = 20
                pdf.image(logo_path, x=10, y=current_y_logo, h=max_h_logo)
                pdf.set_y(current_y_logo + max_h_logo + 5)
            except Exception: pass 

        pdf.set_font("Arial", 'B', 16)
        pdf.multi_cell(w=0, h=10, text=pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome}"), border=0, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(w=0, h=7, text=pdf_safe_text_output(f"Data: {diag_data.get('Data','N/D')} | Empresa: {empresa_nome} (CNPJ: {cnpj_pdf})"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if user_data.get("NomeContato"): pdf.multi_cell(w=0, h=7, text=pdf_safe_text_output(f"Contato: {user_data.get('NomeContato')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if user_data.get("Telefone"): pdf.multi_cell(w=0, h=7, text=pdf_safe_text_output(f"Telefone: {user_data.get('Telefone')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)
        pdf.multi_cell(w=0, h=7, text=pdf_safe_text_output(f"Média Geral: {diag_data.get('Média Geral','N/A')} | GUT Média: {diag_data.get('GUT Média','N/A')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

        if medias_cat:
            pdf.set_font("Arial", 'B', 11)
            pdf.multi_cell(w=0, h=7, text=pdf_safe_text_output("Médias por Categoria:"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Arial", size=10)
            for cat, media in sorted(medias_cat.items()): 
                pdf.multi_cell(w=0, h=6, text=pdf_safe_text_output(f"  - {cat}: {media:.2f}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)

        for titulo, campo in [("Resumo (Cliente):", "Diagnóstico"), ("Análise (Cliente):", "Análise do Cliente"), ("Comentários (Consultor):", "Comentarios_Admin")]:
            valor = diag_data.get(campo, "")
            if valor and not pd.isna(valor) and str(valor).strip():
                pdf.set_font("Arial", 'B', 12)
                pdf.multi_cell(w=0, h=7, text=pdf_safe_text_output(titulo), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(w=0, h=7, text=pdf_safe_text_output(str(valor)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(3)

        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(w=0, h=10, text=pdf_safe_text_output("Respostas Detalhadas e Análises:"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        categorias = sorted(perguntas_df["Categoria"].unique()) if not perguntas_df.empty and "Categoria" in perguntas_df.columns else []
        for categoria in categorias:
            pdf.set_font("Arial", 'B', 10)
            pdf.multi_cell(w=0, h=7, text=pdf_safe_text_output(f"Categoria: {categoria}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Arial", size=9)
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
                        except json.JSONDecodeError: pass 
                    score = g*u*t
                    pdf.multi_cell(w=0, h=6, text=pdf_safe_text_output(f"  - {p_texto.replace(' [Matriz GUT]','')}: G={g}, U={u}, T={t} (Score: {score})"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    analise_texto = obter_analise_para_resposta(p_texto, score, analises_df)
                else:
                    pdf.multi_cell(w=0, h=6, text=pdf_safe_text_output(f"  - {p_texto}: {resp}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    analise_texto = obter_analise_para_resposta(p_texto, resp, analises_df)
                if analise_texto:
                    pdf.set_font("Arial", 'I', 8); pdf.set_text_color(100,100,100)
                    pdf.multi_cell(w=0, h=5, text=pdf_safe_text_output(f"    Análise: {analise_texto}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    pdf.set_text_color(0,0,0); pdf.set_font("Arial", size=9)
            pdf.ln(2)
        pdf.ln(3)
        pdf.add_page(); pdf.set_font("Arial", 'B', 12)
        pdf.cell(w=0, h=10, text=pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(5); pdf.set_font("Arial", size=10)
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
                        except json.JSONDecodeError: pass
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
            for card in sorted_cards: pdf.multi_cell(w=0, h=6, text=pdf_safe_text_output(f"Prazo: {card['Prazo']} - Tarefa: {card['Tarefa']} (Score GUT: {card['Score']})"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else: pdf.multi_cell(w=0, h=6, text=pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf_path = tmpfile.name; pdf.output(pdf_path)
        return pdf_path
    except Exception as e: st.error(f"Erro crítico ao gerar PDF: {e}"); return None

def gerar_pdf_historico(df_historico_filtrado, titulo="Histórico de Ações"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(w=0, h=10, text=pdf_safe_text_output(titulo), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 10)
    col_widths = {"Data": 35, "CNPJ": 35, "Ação": 40, "Descrição": 75} # Ajustar larguras conforme necessário
    page_width = pdf.epw # Effective page width (page width - margins)
    
    # Ajustar larguras se a soma exceder a largura da página, ou para preencher
    total_defined_width = sum(col_widths.get(h, 0) for h in ["Data", "CNPJ", "Ação", "Descrição"])
    available_width_for_desc = page_width - col_widths["Data"] - col_widths["CNPJ"] - col_widths["Ação"]
    if available_width_for_desc > 0 :
         col_widths["Descrição"] = max(col_widths["Descrição"], available_width_for_desc) # Garante que a descrição use o espaço restante
    
    headers_to_print_hist = [col for col in ["Data", "CNPJ", "Ação", "Descrição"] if col in df_historico_filtrado.columns]

    for header in headers_to_print_hist:
        pdf.cell(w=col_widths.get(header, 30), h=10, text=pdf_safe_text_output(header), border=1, align="C")
    pdf.ln() # Mover para a próxima linha após o cabeçalho

    pdf.set_font("Arial", "", 8)
    line_height_text = 5 # Altura base para uma linha de texto

    # Helper para calcular altura da célula de texto com quebra de linha
    def get_cell_text_height(text_content, cell_width):
        if not text_content or cell_width <= 0:
            return line_height_text # Altura mínima
        
        # Salvar estado da fonte
        current_font_family = pdf.font_family
        current_font_style = pdf.font_style
        current_font_size = pdf.font_size_pt / pdf.k # Convert to user unit

        pdf.set_font("Arial", "", 8) # Garantir a fonte correta para cálculo
        
        lines = pdf.multi_cell( # Usar a instância pdf principal para cálculo
            w=cell_width, 
            h=line_height_text, 
            text=text_content, 
            border=0, 
            align="L", 
            new_x=XPos.RIGHT, # Não importa muito para split_only
            new_y=YPos.TOP,   # Não importa muito para split_only
            split_only=True
        )
        # Restaurar estado da fonte
        pdf.set_font(current_font_family, current_font_style, current_font_size * pdf.k)
        return len(lines) * line_height_text

    for _, row in df_historico_filtrado.iterrows():
        row_start_y = pdf.get_y()
        
        max_h_for_this_row = line_height_text 
        for header in headers_to_print_hist:
            cell_text_for_calc = str(row.get(header, ""))
            col_w_calc = col_widths.get(header, 30)
            
            # Salvar posição atual, pois multi_cell com split_only pode alterá-la
            prev_x_calc, prev_y_calc = pdf.get_x(), pdf.get_y()
            
            height_needed = get_cell_text_height(pdf_safe_text_output(cell_text_for_calc), col_w_calc)
            max_h_for_this_row = max(max_h_for_this_row, height_needed)

            pdf.set_xy(prev_x_calc, prev_y_calc) # Restaurar posição

        current_x_for_cell = pdf.l_margin
        for header in headers_to_print_hist:
            cell_text_to_draw = str(row.get(header, ""))
            pdf.set_xy(current_x_for_cell, row_start_y) 
            
            col_w_draw = col_widths.get(header, 30)

            pdf.multi_cell(
                w=col_w_draw,
                h=max_h_for_this_row, 
                text=pdf_safe_text_output(cell_text_to_draw),
                border=1,
                align="L",
                new_x=XPos.NO_CHANGE, 
                new_y=YPos.NO_CHANGE  
            )
            current_x_for_cell += col_w_draw
            
        pdf.set_y(row_start_y + max_h_for_this_row) # Mover para a próxima linha

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf_path = tmpfile.name
        pdf.output(pdf_path)
    return pdf_path

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v16") # Key updated
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador 🔑</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v16"): # Key updated
        u = st.text_input("Usuário", key="admin_u_v16"); p = st.text_input("Senha", type="password", key="admin_p_v16") # Keys updated
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
    with st.form("form_cliente_login_v16"): # Key updated
        c = st.text_input("CNPJ", key="cli_c_v16", value=st.session_state.get("last_cnpj_input","")) # Key updated
        s = st.text_input("Senha", type="password", key="cli_s_v16") # Key updated
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
                registrar_acao(c, "Login", "Usuário logou.")

                pode_fazer_novo_login = st.session_state.user["DiagnosticosDisponiveis"] > st.session_state.user["TotalDiagnosticosRealizados"]
                if pode_fazer_novo_login and not st.session_state.user["ConfirmouInstrucoesParaSlotAtual"]: st.session_state.cliente_page = "Instruções"
                elif pode_fazer_novo_login and st.session_state.user["ConfirmouInstrucoesParaSlotAtual"]: st.session_state.cliente_page = "Novo Diagnóstico"
                else: st.session_state.cliente_page = "Painel Principal"

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
        keys_to_clear_on_error = ['cliente_logado', 'user', 'cnpj', 'cliente_page', 'respostas_atuais_diagnostico', 'id_formulario_atual', 'progresso_diagnostico_percentual', 'progresso_diagnostico_contagem']
        for key_to_clear in keys_to_clear_on_error:
            if key_to_clear in st.session_state: del st.session_state[key_to_clear]
        for key_d, value_d in default_session_state.items():
            st.session_state[key_d] = value_d 
        st.session_state.cliente_logado = False 
        st.rerun()

    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}! 👋")
    with st.sidebar.expander("Meu Perfil", expanded=False):
        logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
        if logo_cliente_path: st.image(logo_cliente_path, width=100)
        st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
        st.write(f"**CNPJ:** {st.session_state.cnpj}")
        st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
        st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")
        diagnosticos_restantes_perfil = st.session_state.user.get('DiagnosticosDisponiveis', 0) - st.session_state.user.get('TotalDiagnosticosRealizados', 0)
        st.write(f"**Diagnósticos Restantes:** {max(0, diagnosticos_restantes_perfil)}")
        st.write(f"**Total Realizados:** {st.session_state.user.get('TotalDiagnosticosRealizados', 0)}")

    unread_notif_count_val = get_unread_notifications_count(st.session_state.cnpj)
    notif_menu_label_val = "🔔 Notificações"
    if unread_notif_count_val > 0: notif_menu_label_val = f"🔔 Notificações ({unread_notif_count_val})"
    menu_options_cli_val = ["📖 Instruções", "📝 Novo Diagnóstico", "📊 Painel Principal", notif_menu_label_val]
    pode_fazer_novo_sidebar_val = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
    confirmou_instrucoes_sidebar_val = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)
    instrucoes_pendentes_obrigatorias_val = pode_fazer_novo_sidebar_val and not confirmou_instrucoes_sidebar_val
    effective_cliente_page = st.session_state.cliente_page
    if instrucoes_pendentes_obrigatorias_val and st.session_state.cliente_page != "Instruções": effective_cliente_page = "Instruções"
    current_page_for_radio = effective_cliente_page
    if current_page_for_radio == "Notificações": current_page_for_radio = notif_menu_label_val
    try: current_idx_cli_val = menu_options_cli_val.index(current_page_for_radio)
    except ValueError: current_idx_cli_val = 0; st.session_state.cliente_page = "Instruções" 
    selected_page_cli_raw_val = st.sidebar.radio("Menu Cliente", menu_options_cli_val, index=current_idx_cli_val, key="cli_menu_v16") # Key updated
    selected_page_cli_actual = "Notificações" if "Notificações" in selected_page_cli_raw_val else selected_page_cli_raw_val
    if selected_page_cli_actual != st.session_state.cliente_page:
        if instrucoes_pendentes_obrigatorias_val and selected_page_cli_actual != "Instruções": st.sidebar.warning("Por favor, confirme a leitura das instruções para prosseguir.")
        else: st.session_state.cliente_page = selected_page_cli_actual; st.rerun()
    if st.sidebar.button("⬅️ Sair do Portal Cliente", key="logout_cliente_v16"): # Key updated
        client_keys_to_clear = [k for k in default_session_state.keys() if k not in ['admin_logado']]
        for key_to_clear in client_keys_to_clear:
            if key_to_clear in st.session_state:
                del st.session_state[key_to_clear] 
        for key_d, value_d in default_session_state.items(): 
            if key_d not in ['admin_logado']:
                st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.rerun()

    # --- Conteúdo da Página do Cliente ---
    if st.session_state.cliente_page == "Instruções":
        st.subheader("📖 Instruções do Sistema de Diagnóstico")
        default_instructions_text = """**Bem-vindo ao Portal de Diagnóstico Empresarial!** (Texto Padrão) ... """ 
        instructions_to_display = default_instructions_text
        try:
            if os.path.exists(instrucoes_txt_file) and os.path.getsize(instrucoes_txt_file) > 0:
                with open(instrucoes_txt_file, "r", encoding="utf-8") as f:
                    custom_instructions = f.read()
                    if custom_instructions.strip(): instructions_to_display = custom_instructions
        except Exception as e: st.warning(f"Não foi possível carregar as instruções personalizadas: {e}. Exibindo instruções padrão.")
        st.markdown(instructions_to_display)
        if st.session_state.user:
            pode_fazer_novo_inst_page_val = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            if pode_fazer_novo_inst_page_val:
                st.session_state.confirmou_instrucoes_checkbox_cliente = st.checkbox("Declaro que li e compreendi todas as instruções fornecidas para a realização deste diagnóstico.", value=st.session_state.get("confirmou_instrucoes_checkbox_cliente", False), key="confirma_leitura_inst_v16_cb") # Key updated
                if st.button("Prosseguir para o Diagnóstico", key="btn_instrucoes_v16_prosseguir", disabled=not st.session_state.confirmou_instrucoes_checkbox_cliente): # Key updated
                    if st.session_state.confirmou_instrucoes_checkbox_cliente:
                        update_user_data(st.session_state.cnpj, "ConfirmouInstrucoesParaSlotAtual", "True")
                        st.session_state.cliente_page = "Novo Diagnóstico"; st.session_state.confirmou_instrucoes_checkbox_cliente = False; st.rerun()
            else:
                st.info("Você não possui diagnósticos disponíveis no momento.")
                if st.button("Ir para o Painel Principal", key="ir_painel_inst_sem_diag_v16"): st.session_state.cliente_page = "Painel Principal"; st.rerun() # Key updated
        else: st.error("Erro de sessão do usuário. Por favor, faça login novamente.")


    elif st.session_state.cliente_page == "Painel Principal":
        st.subheader("📊 Painel Principal do Cliente")
        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                try:
                    with open(st.session_state.pdf_gerado_path, "rb") as f_pdf:
                        st.download_button(label="📄 Baixar PDF do Diagnóstico Recém-Enviado", data=f_pdf, file_name=st.session_state.pdf_gerado_filename, mime="application/pdf", key="dl_novo_diag_painel_v16_pp") # Key updated
                except FileNotFoundError:
                    st.error("Arquivo PDF do diagnóstico recente não encontrado. Pode ter sido movido ou excluído.")
                except Exception as e_pdf_dl:
                    st.error(f"Erro ao preparar download do PDF: {e_pdf_dl}")

            st.session_state.pdf_gerado_path = None; st.session_state.pdf_gerado_filename = None 
            st.session_state.diagnostico_enviado_sucesso = False 
        with st.expander("📖 Instruções e Informações", expanded=False):
            st.markdown("- Visualize seus diagnósticos anteriores e sua evolução.\n- Acompanhe seu plano de ação no Kanban.\n- Para um novo diagnóstico (se liberado), selecione 'Novo Diagnóstico' no menu ao lado.")
        st.markdown("#### 📁 Diagnósticos Anteriores")
        df_cliente_diags = pd.DataFrame()
        try:
            if st.session_state.get("cnpj") is None:
                st.error("Erro: CNPJ do cliente não identificado. Não é possível carregar o painel. Por favor, faça login novamente.")
            elif not os.path.exists(arquivo_csv):
                st.warning(f"Arquivo de diagnósticos ('{arquivo_csv}') não encontrado. Nenhum diagnóstico anterior para exibir.")
            else:
                df_antigos = pd.read_csv(arquivo_csv, dtype={'CNPJ': str}, encoding='utf-8')
                if not df_antigos.empty:
                    df_cliente_diags = df_antigos[df_antigos["CNPJ"] == str(st.session_state.cnpj)].copy()
                else:
                    st.info("O arquivo de diagnósticos está vazio. Nenhum diagnóstico para exibir.")
        except pd.errors.EmptyDataError: st.info(f"O arquivo de diagnósticos ('{arquivo_csv}') está vazio ou contém apenas cabeçalhos. Nenhum diagnóstico para exibir.")
        except Exception as e: st.error(f"Erro ao carregar dados para o painel do cliente: {e}"); st.exception(e)

        if df_cliente_diags.empty:
            if st.session_state.get("cnpj"): st.info("Nenhum diagnóstico anterior encontrado para sua empresa.")
        else:
            df_cliente_diags = df_cliente_diags.sort_values(by="Data", ascending=False)
            perguntas_df_para_painel = pd.DataFrame()
            try:
                if os.path.exists(perguntas_csv):
                    perguntas_df_para_painel = pd.read_csv(perguntas_csv, encoding='utf-8')
                    if "Categoria" not in perguntas_df_para_painel.columns: perguntas_df_para_painel["Categoria"] = "Geral"
                else: st.warning(f"Arquivo de perguntas '{perguntas_csv}' não encontrado. Detalhes das respostas podem ser limitados.")
            except Exception as e_perg: st.warning(f"Erro ao carregar arquivo de perguntas: {e_perg}")
            analises_df_para_painel = carregar_analises_perguntas()
            for idx_row_diag, row_diag_data in df_cliente_diags.iterrows():
                with st.expander(f"📅 {row_diag_data.get('Data','Data Indisponível')} - {row_diag_data.get('Empresa','Empresa Indisponível')}"):
                    cols_metricas = st.columns(2)
                    media_geral_val = pd.to_numeric(row_diag_data.get('Média Geral'), errors='coerce')
                    gut_media_val = pd.to_numeric(row_diag_data.get('GUT Média'), errors='coerce')
                    cols_metricas[0].metric("Média Geral", f"{media_geral_val:.2f}" if pd.notna(media_geral_val) else "N/A")
                    cols_metricas[1].metric("GUT Média (G*U*T)", f"{gut_media_val:.2f}" if pd.notna(gut_media_val) else "N/A")
                    st.write(f"**Resumo (Cliente):** {row_diag_data.get('Diagnóstico', 'N/P')}") 
                    st.markdown("**Respostas e Análises Detalhadas:**")
                    if not perguntas_df_para_painel.empty:
                        for cat_loop in sorted(perguntas_df_para_painel["Categoria"].unique()):
                            st.markdown(f"##### Categoria: {cat_loop}")
                            perg_cat_loop = perguntas_df_para_painel[perguntas_df_para_painel["Categoria"] == cat_loop]
                            for _, p_row_loop in perg_cat_loop.iterrows():
                                p_texto_loop = p_row_loop["Pergunta"]; resp_loop = row_diag_data.get(p_texto_loop, "N/R") 
                                st.markdown(f"**{p_texto_loop.split('[')[0].strip()}:**"); st.markdown(f"> {resp_loop}")
                                valor_para_analise = resp_loop
                                if "[Matriz GUT]" in p_texto_loop:
                                    g,u,t,score_gut_loop=0,0,0,0
                                    if isinstance(resp_loop, dict): g,u,t=int(resp_loop.get("G",0)),int(resp_loop.get("U",0)),int(resp_loop.get("T",0))
                                    elif isinstance(resp_loop, str):
                                        try:
                                            data_gut_loop=json.loads(resp_loop.replace("'",'"'))
                                            g,u,t=int(data_gut_loop.get("G",0)),int(data_gut_loop.get("U",0)),int(data_gut_loop.get("T",0))
                                        except json.JSONDecodeError:
                                            pass 
                                    score_gut_loop = g*u*t; valor_para_analise = score_gut_loop
                                    st.caption(f"G={g}, U={u}, T={t} (Score GUT: {score_gut_loop})")
                                analise_texto_painel = obter_analise_para_resposta(p_texto_loop, valor_para_analise, analises_df_para_painel)
                                if analise_texto_painel: st.markdown(f"<div class='analise-pergunta-cliente'><b>Análise Consultor:</b> {analise_texto_painel}</div>", unsafe_allow_html=True)
                            st.markdown("---") 
                    else: st.caption("Estrutura de perguntas não carregada para detalhamento.")
                    analise_cli_val_cv_painel = row_diag_data.get("Análise do Cliente", ""); analise_cli_cv_input = st.text_area("🧠 Minha Análise sobre este Diagnóstico:", value=analise_cli_val_cv_painel, key=f"analise_cv_painel_v16_pp_{idx_row_diag}") # Key updated
                    if st.button("💾 Salvar Minha Análise", key=f"salvar_analise_cv_painel_v16_pp_{idx_row_diag}"): # Key updated
                        try:
                            df_antigos_upd = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ':str}); df_antigos_upd.loc[idx_row_diag, "Análise do Cliente"] = analise_cli_cv_input; df_antigos_upd.to_csv(arquivo_csv, index=False, encoding='utf-8')
                            registrar_acao(st.session_state.cnpj, "Análise Cliente (Edição Painel)", f"Editou análise do diagnóstico de {row_diag_data['Data']}"); st.success("Sua análise foi salva!"); st.rerun()
                        except Exception as e_save_analise_painel: st.error(f"Erro ao salvar sua análise: {e_save_analise_painel}")
                    com_admin_val_cv_painel = row_diag_data.get("Comentarios_Admin", "")
                    if com_admin_val_cv_painel and not pd.isna(com_admin_val_cv_painel) and str(com_admin_val_cv_painel).strip(): st.markdown("**Comentários do Consultor:**"); st.info(f"{com_admin_val_cv_painel}")
                    else: st.caption("Nenhum comentário do consultor para este diagnóstico.")
                    if st.button("📄 Baixar PDF deste Diagnóstico", key=f"dl_pdf_antigo_v16_pp_{idx_row_diag}"): # Key updated
                        medias_cat_pdf_antigo = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in row_diag_data.items() if "Media_Cat_" in k and pd.notna(v)}
                        pdf_path_antigo = gerar_pdf_diagnostico_completo(row_diag_data.to_dict(), st.session_state.user, perguntas_df_para_painel, row_diag_data.to_dict(), medias_cat_pdf_antigo, analises_df_para_painel)
                        if pdf_path_antigo:
                            try:
                                with open(pdf_path_antigo, "rb") as f_antigo: st.download_button("Download PDF Confirmado", f_antigo, file_name=f"diag_{sanitize_column_name(row_diag_data['Empresa'])}_{str(row_diag_data['Data']).replace(':','-').replace(' ','_')}.pdf", mime="application/pdf", key=f"dl_confirm_antigo_v16_pp_{idx_row_diag}") # Key updated
                                registrar_acao(st.session_state.cnpj, "Download PDF (Painel)", f"Baixou PDF de {row_diag_data['Data']}")
                            except FileNotFoundError: st.error("PDF gerado não encontrado para download.")
                            finally: 
                                if os.path.exists(pdf_path_antigo):
                                    try: os.remove(pdf_path_antigo)
                                    except: pass 
                        else: st.error("Erro ao gerar PDF.")
                    st.divider() 
            st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
            if not df_cliente_diags.empty:
                latest_diag_kanban = df_cliente_diags.iloc[0]; gut_cards_kanban = []
                for pergunta_k, resposta_k_str in latest_diag_kanban.items():
                    if isinstance(pergunta_k, str) and "[Matriz GUT]" in pergunta_k:
                        try:
                            if pd.notna(resposta_k_str) and isinstance(resposta_k_str, str):
                                gut_data_k = json.loads(resposta_k_str.replace("'", "\"")); g_k, u_k, t_k = int(gut_data_k.get("G",0)), int(gut_data_k.get("U",0)), int(gut_data_k.get("T",0)); score_gut_k = g_k*u_k*t_k
                                prazo_k = "N/A"
                                if score_gut_k >= 75: prazo_k = "15 dias"
                                elif score_gut_k >= 40: prazo_k = "30 dias"
                                elif score_gut_k >= 20: prazo_k = "45 dias"
                                elif score_gut_k > 0: prazo_k = "60 dias"
                                else: continue
                                if prazo_k != "N/A": gut_cards_kanban.append({"Tarefa": pergunta_k.replace(" [Matriz GUT]", ""), "Prazo": prazo_k, "Score": score_gut_k, "Responsável": st.session_state.user.get("Empresa", "N/D")})
                        except (json.JSONDecodeError, ValueError, TypeError) as e_kanban_painel: st.warning(f"Erro ao processar GUT para Kanban '{pergunta_k}': {e_kanban_painel}")
                if gut_cards_kanban: 
                    gut_cards_sorted_kanban = sorted(gut_cards_kanban, key=lambda x: x["Score"], reverse=True); prazos_unicos_kanban = sorted(list(set(card["Prazo"] for card in gut_cards_sorted_kanban)), key=lambda x_prazo: int(x_prazo.split(" ")[0]))
                    if prazos_unicos_kanban:
                        cols_kanban = st.columns(len(prazos_unicos_kanban))
                        for idx_col_k, prazo_k_col in enumerate(prazos_unicos_kanban):
                            with cols_kanban[idx_col_k]:
                                st.markdown(f"#### ⏱️ {prazo_k_col}")
                                for card_k_item in gut_cards_sorted_kanban:
                                    if card_k_item["Prazo"] == prazo_k_col: st.markdown(f"""<div class="custom-card"><b>{card_k_item['Tarefa']}</b> (Score GUT: {card_k_item['Score']})<br><small><i>👤 {card_k_item['Responsável']}</i></small></div>""", unsafe_allow_html=True)
                    else: st.info("Nenhuma ação prioritária (GUT > 0) identificada no último diagnóstico para o Kanban.")
                else: st.info("Nenhuma ação prioritária (GUT > 0) identificada no último diagnóstico para o Kanban.")
            else: st.info("Nenhum diagnóstico anterior encontrado para gerar o Kanban.")
            st.divider()
            st.subheader("📈 Comparativo de Evolução das Médias")
            if len(df_cliente_diags) > 1:
                df_evolucao = df_cliente_diags.sort_values(by="Data").copy();
                try: 
                    df_evolucao["Data"] = pd.to_datetime(df_evolucao["Data"])
                    cols_plot_evol = ['Média Geral', 'GUT Média']
                    for col_ev in df_evolucao.columns:
                        if str(col_ev).startswith("Media_Cat_"):
                            df_evolucao[col_ev] = pd.to_numeric(df_evolucao[col_ev], errors='coerce')
                            if not df_evolucao[col_ev].isnull().all():
                                cols_plot_evol.append(col_ev)
                    df_evolucao_plot = df_evolucao.set_index("Data")[cols_plot_evol].dropna(axis=1, how='all')
                    if not df_evolucao_plot.empty: st.line_chart(df_evolucao_plot)
                    else: st.info("Não há dados de médias para plotar o gráfico de evolução.")
                except Exception as e_evol:
                    st.warning(f"Não foi possível gerar o gráfico de evolução: {e_evol}")
            else: st.info("São necessários pelo menos dois diagnósticos para exibir o comparativo de evolução.")
            st.divider()
            st.subheader("📊 Comparação Detalhada Entre Diagnósticos")
            if len(df_cliente_diags) >= 1:
                datas_opts_comp_list = df_cliente_diags["Data"].astype(str).tolist(); default_selection_comp = datas_opts_comp_list[:2] if len(datas_opts_comp_list) >= 2 else datas_opts_comp_list[:1]
                diagnosticos_selecionados_comp = st.multiselect("Selecione os diagnósticos para comparar:", options=datas_opts_comp_list, default=default_selection_comp, key="cliente_multiselect_comparacao_v16_pp") # Key updated
                if len(diagnosticos_selecionados_comp) >= 1:
                    df_comparacao_cliente = df_cliente_diags[df_cliente_diags["Data"].isin(diagnosticos_selecionados_comp)]
                    if len(diagnosticos_selecionados_comp) in [1,2,3] and not perguntas_df_para_painel.empty:
                        fig_radar_comp = go.Figure(); categorias_radar = sorted(perguntas_df_para_painel["Categoria"].unique()) if "Categoria" in perguntas_df_para_painel.columns else []
                        if categorias_radar:
                            for _, diag_row_comp in df_comparacao_cliente.iterrows():
                                medias_cat_comp = {cat_r: pd.to_numeric(diag_row_comp.get(f"Media_Cat_{sanitize_column_name(cat_r)}"), errors='coerce') for cat_r in categorias_radar}
                                values_radar = [medias_cat_comp.get(cat, 0) for cat in categorias_radar] 
                                fig_radar_comp.add_trace(go.Scatterpolar(r=values_radar, theta=categorias_radar, fill='toself', name=f"Diag. {pd.to_datetime(diag_row_comp['Data']).strftime('%d/%m/%y') if pd.notna(diag_row_comp['Data']) else 'Data Inválida'}"))
                            fig_radar_comp.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=True, title="Comparativo de Médias por Categoria (Radar)")
                            st.plotly_chart(fig_radar_comp, use_container_width=True)
                        else: st.caption("Não há categorias definidas para gerar o gráfico de radar.")
                    metricas_interesse_comp = ["Média Geral", "GUT Média"] + [col for col in df_comparacao_cliente.columns if col.startswith("Media_Cat_")]
                    cols_para_pivot = ["Data"] + [m for m in metricas_interesse_comp if m in df_comparacao_cliente.columns]
                    if "Data" in df_comparacao_cliente and len(cols_para_pivot) > 1:
                        df_pivot_comp = df_comparacao_cliente[cols_para_pivot].set_index("Data").T; df_pivot_comp.index.name = "Métrica"
                        try: df_pivot_comp.columns = [pd.to_datetime(col).strftime('%d/%m/%y %H:%M') if pd.notna(col) else 'Data Inválida' for col in df_pivot_comp.columns]
                        except: df_pivot_comp.columns = [str(col).split(" ")[0] for col in df_pivot_comp.columns] # Fallback
                        df_pivot_comp.index = df_pivot_comp.index.str.replace("Media_Cat_", "Média ").str.replace("_", " ")
                        for col_pivot in df_pivot_comp.columns: df_pivot_comp[col_pivot] = pd.to_numeric(df_pivot_comp[col_pivot], errors='coerce')
                        st.dataframe(df_pivot_comp.style.format("{:.2f}", na_rep="N/A"))
                    elif not ("Data" in df_comparacao_cliente): st.warning("Coluna 'Data' não encontrada para comparação.")
                    if len(diagnosticos_selecionados_comp) < 2 and len(df_cliente_diags) >=2 : st.info("Selecione pelo menos dois diagnósticos para uma comparação efetiva.")
                else: st.info("Selecione diagnósticos para comparar (pelo menos um).")
            else: st.info("É necessário pelo menos um diagnóstico para esta funcionalidade.")

    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader("📝 Formulário de Novo Diagnóstico")
        if not st.session_state.user: st.error("Erro: Dados do usuário não encontrados. Faça login novamente."); st.stop()
        pode_fazer_novo_form = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
        confirmou_inst_form = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)
        if not pode_fazer_novo_form:
            st.warning("Você não tem diagnósticos disponíveis. Para realizar um novo, por favor, entre em contato com o administrador para liberação.")
            if st.button("Voltar ao Painel Principal", key="voltar_painel_novo_diag_bloq_v16_nd"): st.session_state.cliente_page = "Painel Principal"; st.rerun() # Key updated
            st.stop()
        elif not confirmou_inst_form: 
            st.warning("Por favor, confirme a leitura das instruções antes de iniciar um novo diagnóstico.")
            if st.button("Ir para Instruções", key="ir_instrucoes_novo_diag_v16_nd"): st.session_state.cliente_page = "Instruções"; st.rerun() # Key updated
            st.stop()
        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu diagnóstico foi enviado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                try:
                    with open(st.session_state.pdf_gerado_path, "rb") as f_pdf_dl_sucesso:
                        st.download_button(label="📄 Baixar PDF do Diagnóstico Enviado", data=f_pdf_dl_sucesso, file_name=st.session_state.pdf_gerado_filename, mime="application/pdf", key="dl_pdf_sucesso_novo_diag_v16_nd") # Key updated
                except FileNotFoundError: st.error("Arquivo PDF gerado não encontrado para download.")
                except Exception as e_dl_new_diag: st.error(f"Erro ao preparar download do PDF: {e_dl_new_diag}")

            if st.button("Ir para o Painel Principal", key="ir_painel_apos_envio_sucesso_v16_nd"): # Key updated
                st.session_state.cliente_page = "Painel Principal";
                st.session_state.diagnostico_enviado_sucesso = False;
                st.session_state.pdf_gerado_path = None;
                st.session_state.pdf_gerado_filename = None;
                st.rerun()
            st.stop()

        perguntas_df_formulario = pd.DataFrame()
        try:
            if not os.path.exists(perguntas_csv): st.error(f"Arquivo de perguntas ('{perguntas_csv}') não encontrado. Não é possível iniciar um novo diagnóstico."); st.stop()
            perguntas_df_formulario = pd.read_csv(perguntas_csv, encoding='utf-8')
            if perguntas_df_formulario.empty: st.warning("Nenhuma pergunta cadastrada no sistema. Não é possível iniciar um novo diagnóstico."); st.stop()
            if "Categoria" not in perguntas_df_formulario.columns: perguntas_df_formulario["Categoria"] = "Geral"
        except pd.errors.EmptyDataError: st.error(f"O arquivo de perguntas ('{perguntas_csv}') está vazio ou contém apenas cabeçalhos. Não é possível iniciar um novo diagnóstico."); st.stop()
        except Exception as e: st.error(f"Erro crítico ao carregar formulário de perguntas: {e}"); st.exception(e); st.stop()

        total_perguntas_form = len(perguntas_df_formulario)
        if st.session_state.progresso_diagnostico_contagem[1] != total_perguntas_form: st.session_state.progresso_diagnostico_contagem = (st.session_state.progresso_diagnostico_contagem[0], total_perguntas_form)
        progresso_ph_novo = st.empty()
        def calcular_e_mostrar_progresso_novo():
            respondidas_novo = 0; total_q_novo = st.session_state.progresso_diagnostico_contagem[1]
            if total_q_novo == 0: st.session_state.progresso_diagnostico_percentual = 0; progresso_ph_novo.info(f"📊 Progresso: 0 de 0 respondidas (0%)"); return
            for _, p_row_prog_novo in perguntas_df_formulario.iterrows():
                p_texto_prog_novo = p_row_prog_novo["Pergunta"]; resp_prog_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_prog_novo)
                if resp_prog_novo is not None:
                    if "[Matriz GUT]" in p_texto_prog_novo:
                        if isinstance(resp_prog_novo, dict) and (int(resp_prog_novo.get("G",0)) > 0 or int(resp_prog_novo.get("U",0)) > 0 or int(resp_prog_novo.get("T",0)) > 0 or len(resp_prog_novo) == 3): respondidas_novo +=1
                    elif "Escala" in p_texto_prog_novo:
                        if resp_prog_novo != "Selecione": respondidas_novo +=1
                    elif "Texto Aberto" in p_texto_prog_novo: 
                        if isinstance(resp_prog_novo, str) and resp_prog_novo.strip() : respondidas_novo +=1
                    elif isinstance(resp_prog_novo, (int,float)) and ("Pontuação" in p_texto_prog_novo): 
                        if resp_prog_novo != 0 : respondidas_novo +=1 
            st.session_state.progresso_diagnostico_contagem = (respondidas_novo, total_q_novo); st.session_state.progresso_diagnostico_percentual = round((respondidas_novo / total_q_novo) * 100) if total_q_novo > 0 else 0
            progresso_ph_novo.info(f"📊 Progresso: {respondidas_novo} de {total_q_novo} respondidas ({st.session_state.progresso_diagnostico_percentual}%)")
        def on_change_resposta_novo(pergunta_txt_key_novo, widget_st_key_novo, tipo_pergunta_onchange_novo):
            valor_widget_novo = st.session_state.get(widget_st_key_novo)
            current_gut_novo = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key_novo, {"G":0,"U":0,"T":0}) 
            if tipo_pergunta_onchange_novo == "GUT_G": current_gut_novo["G"] = valor_widget_novo; st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
            elif tipo_pergunta_onchange_novo == "GUT_U": current_gut_novo["U"] = valor_widget_novo; st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
            elif tipo_pergunta_onchange_novo == "GUT_T": current_gut_novo["T"] = valor_widget_novo; st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
            else: st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = valor_widget_novo
            st.session_state.feedbacks_respostas[pergunta_txt_key_novo] = "Resposta registrada ✓"; calcular_e_mostrar_progresso_novo()
        calcular_e_mostrar_progresso_novo() 
        for categoria_novo in sorted(perguntas_df_formulario["Categoria"].unique()):
            st.markdown(f"#### Categoria: {categoria_novo}")
            perg_cat_df_novo = perguntas_df_formulario[perguntas_df_formulario["Categoria"] == categoria_novo]
            for idx_novo, row_q_novo in perg_cat_df_novo.iterrows():
                p_texto_novo = str(row_q_novo["Pergunta"]); w_key_novo = f"q_{st.session_state.id_formulario_atual}_{idx_novo}"; cols_q_feedback = st.columns([0.9, 0.1])
                with cols_q_feedback[0]:
                    if "[Matriz GUT]" in p_texto_novo:
                        st.markdown(f"**{p_texto_novo.replace(' [Matriz GUT]', '')}**"); cols_gut_w_novo = st.columns(3); gut_vals_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_novo, {"G":0,"U":0,"T":0}); key_g_n, key_u_n, key_t_n = f"{w_key_novo}_G", f"{w_key_novo}_U", f"{w_key_novo}_T"
                        cols_gut_w_novo[0].slider("Gravidade (0-5)",0,5,value=int(gut_vals_novo.get("G",0)), key=key_g_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_g_n, "GUT_G"))
                        cols_gut_w_novo[1].slider("Urgência (0-5)",0,5,value=int(gut_vals_novo.get("U",0)), key=key_u_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_u_n, "GUT_U"))
                        cols_gut_w_novo[2].slider("Tendência (0-5)",0,5,value=int(gut_vals_novo.get("T",0)), key=key_t_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_t_n, "GUT_T"))
                    elif "Pontuação (0-5)" in p_texto_novo: st.slider(p_texto_novo,0,5,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Slider05"))
                    elif "Pontuação (0-10)" in p_texto_novo: st.slider(p_texto_novo,0,10,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Slider010"))
                    elif "Texto Aberto" in p_texto_novo: st.text_area(p_texto_novo,value=str(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,"")), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Texto"))
                    elif "Escala" in p_texto_novo:
                        opts_novo = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]; curr_val_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_novo, "Selecione")
                        st.selectbox(p_texto_novo, opts_novo, index=opts_novo.index(curr_val_novo) if curr_val_novo in opts_novo else 0, key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Escala"))
                    else: 
                        st.slider(p_texto_novo.replace("[]","").strip(),0,10,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "SliderDefault"))
                with cols_q_feedback[1]:
                    if st.session_state.feedbacks_respostas.get(p_texto_novo): st.caption(f'<p class="feedback-saved" style="white-space: nowrap;">{st.session_state.feedbacks_respostas[p_texto_novo]}</p>', unsafe_allow_html=True)
                st.divider()
        key_obs_cli_n = f"obs_cli_diag_{st.session_state.id_formulario_atual}"; st.text_area("Sua Análise/Observações (opcional):", value=st.session_state.respostas_atuais_diagnostico.get("__obs_cliente__", ""), key=key_obs_cli_n, on_change=on_change_resposta_novo, args=("__obs_cliente__", key_obs_cli_n, "ObsCliente"))
        key_res_cli_n = f"diag_resumo_diag_{st.session_state.id_formulario_atual}"; st.text_area("✍️ Resumo/principais insights (para PDF):", value=st.session_state.respostas_atuais_diagnostico.get("__resumo_cliente__", ""), key=key_res_cli_n, on_change=on_change_resposta_novo, args=("__resumo_cliente__", key_res_cli_n, "ResumoCliente"))
        if st.button("✔️ Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v16_nd"): # Key updated
            respostas_finais_envio_novo = st.session_state.respostas_atuais_diagnostico; cont_resp_n, total_para_resp_n = st.session_state.progresso_diagnostico_contagem
            if cont_resp_n < total_para_resp_n: st.warning("Por favor, responda todas as perguntas para um diagnóstico completo.")
            elif not respostas_finais_envio_novo.get("__resumo_cliente__","").strip(): st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
            else:
                soma_gut_n, count_gut_n = 0,0; respostas_csv_n = {}
                for p_n,r_n in respostas_finais_envio_novo.items():
                    if p_n.startswith("__"): continue
                    if "[Matriz GUT]" in p_n and isinstance(r_n, dict): respostas_csv_n[p_n] = json.dumps(r_n); g_n,u_n,t_n = int(r_n.get("G",0)), int(r_n.get("U",0)), int(r_n.get("T",0)); soma_gut_n += (g_n*u_n*t_n); count_gut_n +=1
                    else: respostas_csv_n[p_n] = r_n
                gut_media_n = round(soma_gut_n/count_gut_n,2) if count_gut_n > 0 else 0.0;
                num_resp_n = [v_n for k_n,v_n in respostas_finais_envio_novo.items() if not k_n.startswith("__") and isinstance(v_n,(int,float)) and ("[Matriz GUT]" not in k_n) and (any(keyword in k_n for keyword in ["Pontuação (0-5)", "Pontuação (0-10)"]))]; 
                media_geral_n = round(sum(num_resp_n)/len(num_resp_n),2) if num_resp_n else 0.0; emp_nome_n = st.session_state.user.get("Empresa","N/D")
                nova_linha_diag_final_n = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": st.session_state.cnpj, "Nome": st.session_state.user.get("NomeContato", st.session_state.cnpj), "Email": "", "Empresa": emp_nome_n, "Média Geral": media_geral_n, "GUT Média": gut_media_n, "Observações": "", "Análise do Cliente": respostas_finais_envio_novo.get("__obs_cliente__",""), "Diagnóstico": respostas_finais_envio_novo.get("__resumo_cliente__",""), "Comentarios_Admin": "" }; nova_linha_diag_final_n.update(respostas_csv_n); medias_cat_final_n = {}
                for cat_iter_n in perguntas_df_formulario["Categoria"].unique():
                    soma_c_n, cont_c_n = 0,0
                    for _,pr_n in perguntas_df_formulario[perguntas_df_formulario["Categoria"]==cat_iter_n].iterrows():
                        pt_n = pr_n["Pergunta"]; rv_n = respostas_finais_envio_novo.get(pt_n)
                        if isinstance(rv_n,(int,float)) and ("[Matriz GUT]" not in pt_n) and (any(keyword in pt_n for keyword in ["Pontuação (0-5)", "Pontuação (0-10)"])): soma_c_n+=rv_n; cont_c_n+=1
                    mc_n = round(soma_c_n/cont_c_n,2) if cont_c_n>0 else 0.0; nova_linha_diag_final_n[f"Media_Cat_{sanitize_column_name(cat_iter_n)}"] = mc_n; medias_cat_final_n[cat_iter_n] = mc_n
                try: df_todos_diags_n = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                except (FileNotFoundError, pd.errors.EmptyDataError): df_todos_diags_n = pd.DataFrame()
                for col_n_n in nova_linha_diag_final_n.keys(): 
                    if col_n_n not in df_todos_diags_n.columns: df_todos_diags_n[col_n_n] = pd.NA
                df_todos_diags_n = pd.concat([df_todos_diags_n, pd.DataFrame([nova_linha_diag_final_n])], ignore_index=True); df_todos_diags_n.to_csv(arquivo_csv, index=False, encoding='utf-8')
                total_realizados_atual = st.session_state.user.get("TotalDiagnosticosRealizados", 0); update_user_data(st.session_state.cnpj, "TotalDiagnosticosRealizados", total_realizados_atual + 1)
                # update_user_data(st.session_state.cnpj, "ConfirmouInstrucoesParaSlotAtual", "False") # Reset for next potential diagnostic slot
                registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", "Cliente enviou novo diagnóstico."); analises_df_para_pdf_n = carregar_analises_perguntas()
                pdf_path_gerado_n = gerar_pdf_diagnostico_completo(nova_linha_diag_final_n, st.session_state.user, perguntas_df_formulario, respostas_finais_envio_novo, medias_cat_final_n, analises_df_para_pdf_n)
                st.session_state.diagnostico_enviado_sucesso = True
                if pdf_path_gerado_n: st.session_state.pdf_gerado_path = pdf_path_gerado_n; st.session_state.pdf_gerado_filename = f"diagnostico_{sanitize_column_name(emp_nome_n)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                else: st.warning("Diagnóstico salvo, mas houve um erro ao gerar o PDF.")
                st.session_state.respostas_atuais_diagnostico = {}; st.session_state.progresso_diagnostico_percentual = 0; st.session_state.progresso_diagnostico_contagem = (0,total_perguntas_form); st.session_state.feedbacks_respostas = {}; st.rerun()

    elif st.session_state.cliente_page == "Notificações":
        st.subheader("🔔 Minhas Notificações")
        try:
            df_notif_cliente_view = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
            df_notif_cliente_view = df_notif_cliente_view[df_notif_cliente_view['CNPJ_Cliente'] == st.session_state.cnpj]
            if not df_notif_cliente_view.empty: df_notif_cliente_view['DataHora'] = pd.to_datetime(df_notif_cliente_view['DataHora']); df_notif_cliente_view = df_notif_cliente_view.sort_values(by="DataHora", ascending=False)
        except (FileNotFoundError, pd.errors.EmptyDataError): df_notif_cliente_view = pd.DataFrame()
        if df_notif_cliente_view.empty: st.info("Você não tem nenhuma notificação no momento.")
        else:
            ids_nao_lidas_para_marcar_view = []
            for _, row_notif_view in df_notif_cliente_view.iterrows():
                lida_status_view = "Lida" if row_notif_view['Lida'] else "Nova!"; cor_status_view = "green" if row_notif_view['Lida'] else "red"
                st.markdown(f"""<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 10px; {'font-weight: bold;' if not row_notif_view['Lida'] else ''}"> <small>{pd.to_datetime(row_notif_view['DataHora']).strftime('%d/%m/%Y %H:%M')} - <span style="color:{cor_status_view};">{lida_status_view}</span></small><br> {row_notif_view['Mensagem']} </div> """, unsafe_allow_html=True)
                if not row_notif_view['Lida']: ids_nao_lidas_para_marcar_view.append(row_notif_view['ID_Notificacao'])
            if ids_nao_lidas_para_marcar_view:
                if 'notif_page_loaded_once_v16_c' not in st.session_state: # Key updated 
                    if marcar_notificacoes_como_lidas(st.session_state.cnpj, ids_notificacoes=ids_nao_lidas_para_marcar_view):
                        st.session_state.notif_page_loaded_once_v16_c = True; # Key updated
                        st.rerun() 
            elif 'notif_page_loaded_once_v16_c' in st.session_state and not ids_nao_lidas_para_marcar_view: # Key updated
                del st.session_state.notif_page_loaded_once_v16_c # Key updated


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    try:
        try: st.sidebar.image("https://via.placeholder.com/150x75.png?text=Sua+Logo+Admin", width=150) 
        except Exception as e_img_admin: st.sidebar.caption(f"Logo admin não carregada: {e_img_admin}")
        st.sidebar.success("🟢 Admin Logado")
        if st.sidebar.button("🚪 Sair do Painel Admin", key="logout_admin_v16_adm"): st.session_state.admin_logado = False; st.rerun() # Key updated
        menu_admin_options = ["📊 Visão Geral e Diagnósticos", "🚦 Status dos Clientes", "📜 Histórico de Usuários",
                              "📝 Gerenciar Perguntas", "💡 Gerenciar Análises de Perguntas",
                              "✍️ Gerenciar Instruções Clientes",
                              "👥 Gerenciar Clientes", "👮 Gerenciar Administradores", "💾 Backup de Dados"]
        menu_admin = st.sidebar.selectbox("Funcionalidades Admin:", menu_admin_options, key="admin_menu_selectbox_v16_adm") # Key updated
        st.header(f"{menu_admin.split(' ')[0]} {menu_admin.split(' ', 1)[1]}")
        df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios)
        try:
            df_usuarios_admin_temp_load = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
            for col, default, dtype_col in [("ConfirmouInstrucoesParaSlotAtual", "False", str), ("DiagnosticosDisponiveis", 1, int), ("TotalDiagnosticosRealizados", 0, int), ("LiberacoesExtrasConcedidas", 0, int)]:
                if col not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load[col] = default
                if dtype_col == int: df_usuarios_admin_temp_load[col] = pd.to_numeric(df_usuarios_admin_temp_load[col], errors='coerce').fillna(default).astype(int)
                else: df_usuarios_admin_temp_load[col] = df_usuarios_admin_temp_load[col].astype(str)
            df_usuarios_admin_geral = df_usuarios_admin_temp_load
        except FileNotFoundError: st.sidebar.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado. Funcionalidades de gestão de clientes podem ser limitadas.")
        except Exception as e_load_users_adm_global: st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm_global}")

        diagnosticos_df_admin_orig_view = pd.DataFrame()
        admin_data_carregada_view_sucesso = False
        if not os.path.exists(arquivo_csv): st.error(f"ATENÇÃO: O arquivo de diagnósticos '{arquivo_csv}' não foi encontrado. Funcionalidades de visualização de diagnósticos serão limitadas.")
        elif os.path.getsize(arquivo_csv) == 0: st.warning(f"O arquivo de diagnósticos '{arquivo_csv}' está completamente vazio (0 bytes). Não há dados de diagnóstico para carregar.")
        else:
            try:
                diagnosticos_df_admin_orig_view = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                if 'Data' in diagnosticos_df_admin_orig_view.columns: diagnosticos_df_admin_orig_view['Data'] = pd.to_datetime(diagnosticos_df_admin_orig_view['Data'], errors='coerce')
                if not diagnosticos_df_admin_orig_view.empty: admin_data_carregada_view_sucesso = True
            except pd.errors.EmptyDataError: st.warning(f"Arquivo de diagnósticos '{arquivo_csv}' parece vazio ou contém apenas cabeçalhos. Não foi possível carregar dados de diagnóstico.")
            except Exception as e_adm_load_diag: st.error(f"ERRO CRÍTICO AO CARREGAR ARQUIVO DE DIAGNÓSTICOS ('{arquivo_csv}'): {e_adm_load_diag}"); st.exception(e_adm_load_diag)

        # Admin menu dispatch logic
        try:
            if menu_admin == "📊 Visão Geral e Diagnósticos":
                st.subheader("Visão Geral e Indicadores de Diagnósticos")
                st.markdown("#### Métricas Gerais do Sistema (Todos os Clientes)")
                col_mg1_vg, col_mg2_vg, col_mg3_vg, col_mg4_vg = st.columns(4)
                total_clientes_cadastrados_vg = len(df_usuarios_admin_geral) if not df_usuarios_admin_geral.empty else 0
                with col_mg1_vg: st.markdown(f"<div class='kpi-card'><h4>👥 Clientes Cadastrados</h4><p class='value'>{total_clientes_cadastrados_vg}</p></div>", unsafe_allow_html=True)
                if admin_data_carregada_view_sucesso and not diagnosticos_df_admin_orig_view.empty:
                    total_diagnosticos_sistema_vg = len(diagnosticos_df_admin_orig_view); media_geral_global_adm_vg = pd.to_numeric(diagnosticos_df_admin_orig_view.get("Média Geral"), errors='coerce').mean(); gut_media_global_adm_vg = pd.to_numeric(diagnosticos_df_admin_orig_view.get("GUT Média"), errors='coerce').mean()
                    with col_mg2_vg: st.markdown(f"<div class='kpi-card'><h4>📋 Total de Diagnósticos</h4><p class='value'>{total_diagnosticos_sistema_vg}</p></div>", unsafe_allow_html=True)
                    with col_mg3_vg: st.markdown(f"<div class='kpi-card'><h4>📈 Média Geral Global</h4><p class='value'>{media_geral_global_adm_vg:.2f if pd.notna(media_geral_global_adm_vg) else 'N/A'}</p></div>", unsafe_allow_html=True)
                    with col_mg4_vg: st.markdown(f"<div class='kpi-card'><h4>🔥 GUT Média Global</h4><p class='value'>{gut_media_global_adm_vg:.2f if pd.notna(gut_media_global_adm_vg) else 'N/A'}</p></div>", unsafe_allow_html=True)
                else:
                    with col_mg2_vg: st.markdown(f"<div class='kpi-card'><h4>📋 Total de Diagnósticos</h4><p class='value'>0</p></div>", unsafe_allow_html=True)
                    with col_mg3_vg: st.markdown(f"<div class='kpi-card'><h4>📈 Média Geral Global</h4><p class='value'>N/A</p></div>", unsafe_allow_html=True)
                    with col_mg4_vg: st.markdown(f"<div class='kpi-card'><h4>🔥 GUT Média Global</h4><p class='value'>N/A</p></div>", unsafe_allow_html=True)
                st.divider()
                st.markdown("#### Filtros para Análise Detalhada de Diagnósticos")
                col_f1_vg, col_f2_vg, col_f3_vg = st.columns(3)
                empresas_lista_admin_filtro_vg = sorted(df_usuarios_admin_geral["Empresa"].astype(str).unique().tolist()) if not df_usuarios_admin_geral.empty and "Empresa" in df_usuarios_admin_geral.columns else []
                with col_f1_vg: emp_sel_admin_vg = st.selectbox("Filtrar por Empresa:", ["Todos os Clientes"] + empresas_lista_admin_filtro_vg, key="admin_filtro_emp_v16_vg") # Key updated
                with col_f2_vg: dt_ini_admin_vg = st.date_input("Data Início dos Diagnósticos:", value=None, key="admin_dt_ini_v16_vg") # Key updated
                with col_f3_vg: dt_fim_admin_vg = st.date_input("Data Fim dos Diagnósticos:", value=None, key="admin_dt_fim_v16_vg") # Key updated
                st.divider()
                df_diagnosticos_contexto_filtro_vg = diagnosticos_df_admin_orig_view.copy() if admin_data_carregada_view_sucesso and not diagnosticos_df_admin_orig_view.empty else pd.DataFrame(columns=colunas_base_diagnosticos)
                df_usuarios_contexto_filtro_vg = df_usuarios_admin_geral.copy()
                if emp_sel_admin_vg != "Todos os Clientes":
                    if not df_diagnosticos_contexto_filtro_vg.empty: df_diagnosticos_contexto_filtro_vg = df_diagnosticos_contexto_filtro_vg[df_diagnosticos_contexto_filtro_vg["Empresa"] == emp_sel_admin_vg]
                    if not df_usuarios_contexto_filtro_vg.empty: df_usuarios_contexto_filtro_vg = df_usuarios_contexto_filtro_vg[df_usuarios_contexto_filtro_vg["Empresa"] == emp_sel_admin_vg]

                df_diagnosticos_filtrados_view_final_vg = df_diagnosticos_contexto_filtro_vg.copy()
                if not df_diagnosticos_filtrados_view_final_vg.empty and 'Data' in df_diagnosticos_filtrados_view_final_vg.columns:
                    if dt_ini_admin_vg: df_diagnosticos_filtrados_view_final_vg = df_diagnosticos_filtrados_view_final_vg[df_diagnosticos_filtrados_view_final_vg['Data'] >= pd.to_datetime(dt_ini_admin_vg)]
                    if dt_fim_admin_vg: df_diagnosticos_filtrados_view_final_vg = df_diagnosticos_filtrados_view_final_vg[df_diagnosticos_filtrados_view_final_vg['Data'] < pd.to_datetime(dt_fim_admin_vg) + pd.Timedelta(days=1)]
                st.markdown(f"#### Análise para: **{emp_sel_admin_vg}** (Período de Diagnósticos: {dt_ini_admin_vg or 'Início'} a {dt_fim_admin_vg or 'Fim'})")
                cnpjs_usuarios_no_contexto_empresa_vg = set(df_usuarios_contexto_filtro_vg['CNPJ'].unique()) if not df_usuarios_contexto_filtro_vg.empty else set()
                cnpjs_com_diagnostico_no_periodo_e_empresa_vg = set(df_diagnosticos_filtrados_view_final_vg['CNPJ'].unique()) if not df_diagnosticos_filtrados_view_final_vg.empty else set()
                clientes_sem_diagnostico_final_vg = len(cnpjs_usuarios_no_contexto_empresa_vg - cnpjs_com_diagnostico_no_periodo_e_empresa_vg)
                clientes_com_pelo_menos_um_diag_final_vg = len(cnpjs_com_diagnostico_no_periodo_e_empresa_vg)
                clientes_com_mais_de_um_diag_final_vg = 0
                if not df_diagnosticos_filtrados_view_final_vg.empty: contagem_diag_por_cliente_final_vg = df_diagnosticos_filtrados_view_final_vg.groupby('CNPJ').size(); clientes_com_mais_de_um_diag_final_vg = len(contagem_diag_por_cliente_final_vg[contagem_diag_por_cliente_final_vg > 1])
                col_pm1_f_vg, col_pm2_f_vg, col_pm3_f_vg = st.columns(3)
                with col_pm1_f_vg: st.markdown(f"<div class='kpi-card'><h4>Clientes SEM Diag. (filtro)</h4><p class='value'>{clientes_sem_diagnostico_final_vg}</p></div>", unsafe_allow_html=True)
                with col_pm2_f_vg: st.markdown(f"<div class='kpi-card'><h4>Clientes COM Diag. (filtro)</h4><p class='value'>{clientes_com_pelo_menos_um_diag_final_vg}</p></div>", unsafe_allow_html=True)
                with col_pm3_f_vg: st.markdown(f"<div class='kpi-card'><h4>Clientes COM MAIS DE 1 Diag. (filtro)</h4><p class='value'>{clientes_com_mais_de_um_diag_final_vg}</p></div>", unsafe_allow_html=True)
                st.divider()
                if not admin_data_carregada_view_sucesso or df_diagnosticos_admin_orig_view.empty : st.warning("Nenhum dado de diagnóstico foi carregado. Funcionalidades de visualização detalhada estão limitadas.")
                elif df_diagnosticos_filtrados_view_final_vg.empty: st.info(f"Nenhum diagnóstico encontrado para os filtros aplicados.")
                else:
                    st.markdown(f"##### Indicadores da Seleção Filtrada de Diagnósticos")
                    col_if_adm1_vg, col_if_adm2_vg, col_if_adm3_vg = st.columns(3)
                    with col_if_adm1_vg: st.markdown(f"<div class='kpi-card'><h4>📦 Diags. na Seleção</h4><p class='value'>{len(df_diagnosticos_filtrados_view_final_vg)}</p></div>", unsafe_allow_html=True)
                    media_geral_filtrada_adm_vg = pd.to_numeric(df_diagnosticos_filtrados_view_final_vg.get("Média Geral"), errors='coerce').mean()
                    with col_if_adm2_vg: st.markdown(f"<div class='kpi-card'><h4>📈 Média Geral Seleção</h4><p class='value'>{media_geral_filtrada_adm_vg:.2f if pd.notna(media_geral_filtrada_adm_vg) else 'N/A'}</p></div>", unsafe_allow_html=True)
                    gut_media_filtrada_adm_vg = pd.to_numeric(df_diagnosticos_filtrados_view_final_vg.get("GUT Média"), errors='coerce').mean()
                    with col_if_adm3_vg: st.markdown(f"<div class='kpi-card'><h4>🔥 GUT Média Seleção</h4><p class='value'>{gut_media_filtrada_adm_vg:.2f if pd.notna(gut_media_filtrada_adm_vg) else 'N/A'}</p></div>", unsafe_allow_html=True)
                    st.divider()
                    st.markdown(f"##### Diagnósticos Detalhados (Seleção Filtrada)")
                    st.dataframe(df_diagnosticos_filtrados_view_final_vg.sort_values(by="Data", ascending=False).reset_index(drop=True))
                    st.markdown("##### 🔍 Detalhar, Comentar e Baixar PDF de Diagnóstico Específico")
                    if not df_diagnosticos_filtrados_view_final_vg.empty:
                        diagnosticos_para_detalhe_admin = df_diagnosticos_filtrados_view_final_vg.apply(lambda row: f"{pd.to_datetime(row['Data']).strftime('%Y-%m-%d %H:%M') if pd.notna(row['Data']) else 'Data Inv.'} - {row.get('Empresa','N/A')} (Índice Original: {row.name})", axis=1).tolist()
                        diag_selecionado_str_admin = st.selectbox("Selecione um Diagnóstico para Detalhar:", [""] + diagnosticos_para_detalhe_admin, key="admin_select_diag_detalhe_v16") # Key updated
                        if diag_selecionado_str_admin:
                            try:
                                diag_original_index_admin = int(diag_selecionado_str_admin.split("(Índice Original: ")[1].replace(")", ""))
                                diag_row_detalhe_admin = diagnosticos_df_admin_orig_view.loc[diag_original_index_admin]
                                st.markdown(f"###### Detalhes do Diagnóstico: {diag_row_detalhe_admin.get('Data','N/A')} - {diag_row_detalhe_admin.get('Empresa','N/A')}")
                                comentarios_admin_atuais_det = diag_row_detalhe_admin.get('Comentarios_Admin', "")
                                novos_comentarios_admin_det = st.text_area("Comentários do Consultor:", value=comentarios_admin_atuais_det if pd.notna(comentarios_admin_atuais_det) else "", key=f"com_admin_det_{diag_original_index_admin}")
                                if st.button("Salvar Comentários do Consultor 💬", key=f"save_com_admin_det_{diag_original_index_admin}"):
                                    df_all_diags_update = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ':str}); df_all_diags_update.loc[diag_original_index_admin, 'Comentarios_Admin'] = novos_comentarios_admin_det; df_all_diags_update.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                    criar_notificacao(diag_row_detalhe_admin['CNPJ'], "Novos comentários do consultor disponíveis.", str(diag_row_detalhe_admin['Data'])); st.success("Comentários salvos e cliente notificado!"); st.rerun()
                                if st.button("📄 Baixar PDF deste Diagnóstico", key=f"dl_pdf_admin_detalhe_v16_{diag_original_index_admin}"): # Key updated
                                    try: usuario_do_diag_pdf_adm = df_usuarios_admin_geral[df_usuarios_admin_geral['CNPJ'] == diag_row_detalhe_admin['CNPJ']].iloc[0].to_dict()
                                    except: usuario_do_diag_pdf_adm = {"Empresa": diag_row_detalhe_admin.get("Empresa","N/A"), "CNPJ": diag_row_detalhe_admin.get("CNPJ","N/A")} # Fallback
                                    perguntas_df_pdf_admin_det = pd.read_csv(perguntas_csv, encoding='utf-8'); analises_df_pdf_admin_det = carregar_analises_perguntas(); medias_cat_pdf_admin_det = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in diag_row_detalhe_admin.items() if "Media_Cat_" in k and pd.notna(v)}
                                    pdf_path_admin_det = gerar_pdf_diagnostico_completo(diag_row_detalhe_admin.to_dict(), usuario_do_diag_pdf_adm, perguntas_df_pdf_admin_det, diag_row_detalhe_admin.to_dict(), medias_cat_pdf_admin_det, analises_df_pdf_admin_det)
                                    if pdf_path_admin_det:
                                        with open(pdf_path_admin_det, "rb") as f_pdf_admin_det: st.download_button("Download PDF Confirmado", f_pdf_admin_det, file_name=f"diagnostico_admin_{sanitize_column_name(diag_row_detalhe_admin.get('Empresa','N_A'))}_{str(diag_row_detalhe_admin.get('Data','N_A')).replace(':','-').replace(' ','_')}.pdf", mime="application/pdf", key=f"dl_conf_admin_detalhe_v16_{diag_original_index_admin}") # Key updated
                                        try: os.remove(pdf_path_admin_det) 
                                        except: pass
                                    else: st.error("Falha ao gerar PDF.")
                            except (IndexError, KeyError, ValueError) as e_lookup: st.warning(f"Não foi possível carregar os detalhes do diagnóstico selecionado. Pode ter sido removido ou o índice é inválido. Erro: {e_lookup}")
                            except Exception as e_detalhe: st.error(f"Erro ao tentar detalhar diagnóstico: {e_detalhe}")
                    else: st.caption("Nenhum diagnóstico na seleção atual para detalhar.")
            
            elif menu_admin == "🚦 Status dos Clientes":
                st.subheader("Status de Diagnósticos dos Clientes")
                df_usuarios_status_view = df_usuarios_admin_geral.copy()
                df_diagnosticos_status_geral = diagnosticos_df_admin_orig_view.copy() if admin_data_carregada_view_sucesso and not diagnosticos_df_admin_orig_view.empty else pd.DataFrame()
                empresas_status_list_view = ["Todas"] + (sorted(df_usuarios_status_view['Empresa'].astype(str).unique().tolist()) if not df_usuarios_status_view.empty and "Empresa" in df_usuarios_status_view.columns else [])
                emp_sel_status_view = st.selectbox("Filtrar por Empresa:", empresas_status_list_view, key="status_emp_sel_v16") # Key updated
                df_usuarios_status_filtrado = df_usuarios_status_view.copy()
                df_diagnosticos_status_filtrado_local = df_diagnosticos_status_geral.copy()
                if emp_sel_status_view != "Todas":
                    df_usuarios_status_filtrado = df_usuarios_status_view[df_usuarios_status_view["Empresa"] == emp_sel_status_view]
                    if not df_diagnosticos_status_filtrado_local.empty: df_diagnosticos_status_filtrado_local = df_diagnosticos_status_filtrado_local[df_diagnosticos_status_filtrado_local["Empresa"] == emp_sel_status_view]
                if df_usuarios_status_filtrado.empty: st.info(f"Nenhum cliente encontrado para a empresa '{emp_sel_status_view}'.")
                else:
                    st.markdown("##### Clientes que JÁ REALIZARAM pelo menos um diagnóstico (no contexto da empresa filtrada):")
                    if not df_diagnosticos_status_filtrado_local.empty:
                        cnpjs_com_diagnostico_status = df_diagnosticos_status_filtrado_local['CNPJ'].unique()
                        clientes_que_fizeram_status = df_usuarios_status_filtrado[df_usuarios_status_filtrado['CNPJ'].isin(cnpjs_com_diagnostico_status)]
                        if not clientes_que_fizeram_status.empty: st.dataframe(clientes_que_fizeram_status[['CNPJ', 'Empresa', 'NomeContato', 'TotalDiagnosticosRealizados', 'DiagnosticosDisponiveis']])
                        else: st.info(f"Nenhum cliente da empresa '{emp_sel_status_view}' realizou diagnósticos.")
                    elif admin_data_carregada_view_sucesso: st.info(f"Nenhum diagnóstico registrado para a empresa '{emp_sel_status_view}'.")
                    else: st.info("Dados de diagnóstico não disponíveis para consulta.")
                    st.markdown("---")
                    st.markdown("##### Clientes com Diagnósticos LIBERADOS e AINDA NÃO REALIZADOS (ou com slots pendentes):")
                    clientes_liberados_pendentes_status = df_usuarios_status_filtrado[df_usuarios_status_filtrado['DiagnosticosDisponiveis'] > df_usuarios_status_filtrado['TotalDiagnosticosRealizados']]
                    if not clientes_liberados_pendentes_status.empty: st.dataframe(clientes_liberados_pendentes_status[['CNPJ', 'Empresa', 'NomeContato', 'DiagnosticosDisponiveis', 'TotalDiagnosticosRealizados']])
                    else: st.info(f"Nenhum cliente da empresa '{emp_sel_status_view}' com diagnósticos liberados pendentes.")

            elif menu_admin == "📜 Histórico de Usuários":
                st.subheader("📜 Histórico de Ações")
                df_historico_completo_hu = pd.DataFrame()
                df_usuarios_para_filtro_hu = pd.DataFrame()
                try:
                    df_historico_completo_hu = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
                    df_usuarios_para_filtro_hu = pd.read_csv(usuarios_csv, encoding='utf-8', usecols=['CNPJ', 'Empresa', 'NomeContato'], dtype={'CNPJ': str})
                except FileNotFoundError: st.error("Arquivo de histórico ou usuários não encontrado."); df_historico_completo_hu = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"]); df_usuarios_para_filtro_hu = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato'])
                except Exception as e_hu: st.error(f"Erro ao carregar dados para o histórico: {e_hu}"); df_historico_completo_hu = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"]); df_usuarios_para_filtro_hu = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato'])
                st.markdown("#### Filtros do Histórico"); col_hu_f1, col_hu_f2 = st.columns(2); empresas_hist_list_hu = ["Todas"]
                if not df_usuarios_para_filtro_hu.empty and 'Empresa' in df_usuarios_para_filtro_hu.columns: empresas_hist_list_hu.extend(sorted(df_usuarios_para_filtro_hu['Empresa'].astype(str).unique().tolist()))
                emp_sel_hu = col_hu_f1.selectbox("Filtrar por Empresa:", empresas_hist_list_hu, key="hist_emp_sel_v16_hu_adm"); termo_busca_hu = col_hu_f2.text_input("Buscar por Nome do Contato, CNPJ, Ação ou Descrição:", key="hist_termo_busca_v16_hu_adm") # Keys updated
                df_historico_filtrado_view_hu = df_historico_completo_hu.copy()
                if emp_sel_hu != "Todas" and not df_usuarios_para_filtro_hu.empty: cnpjs_da_empresa_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['Empresa'] == emp_sel_hu]['CNPJ'].tolist(); df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_da_empresa_hu)]
                if termo_busca_hu.strip():
                    busca_lower_hu = termo_busca_hu.strip().lower(); cnpjs_match_nome_hu = []
                    if not df_usuarios_para_filtro_hu.empty and 'NomeContato' in df_usuarios_para_filtro_hu.columns: cnpjs_match_nome_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['NomeContato'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)]['CNPJ'].tolist()
                    df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_match_nome_hu) | df_historico_filtrado_view_hu['CNPJ'].astype(str).str.lower().str.contains(busca_lower_hu) | df_historico_filtrado_view_hu['Ação'].astype(str).str.lower().str.contains(busca_lower_hu, na=False) | df_historico_filtrado_view_hu['Descrição'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)]
                st.markdown("#### Registros do Histórico")
                if not df_historico_filtrado_view_hu.empty:
                    st.dataframe(df_historico_filtrado_view_hu.sort_values(by="Data", ascending=False))
                    if st.button("📄 Baixar Histórico Filtrado (PDF)", key="download_hist_filtrado_pdf_v16_hu_adm"): # Key updated
                        titulo_pdf_hist = f"Historico_Acoes_{sanitize_column_name(emp_sel_hu)}_{sanitize_column_name(termo_busca_hu) if termo_busca_hu else 'Todos'}_{datetime.now().strftime('%Y%m%d')}.pdf"; pdf_path_hist = gerar_pdf_historico(df_historico_filtrado_view_hu, titulo=f"Histórico ({emp_sel_hu} - Busca: {termo_busca_hu or 'N/A'})")
                        if pdf_path_hist:
                            with open(pdf_path_hist, "rb") as f_pdf_hist: st.download_button(label="Download Confirmado", data=f_pdf_hist, file_name=titulo_pdf_hist, mime="application/pdf", key="confirm_download_hist_pdf_v16_hu_adm") # Key updated
                            try: os.remove(pdf_path_hist) 
                            except: pass
                else: st.info("Nenhum registro de histórico encontrado para os filtros aplicados.")

            elif menu_admin == "📝 Gerenciar Perguntas":
                st.subheader("Gerenciar Perguntas do Diagnóstico"); tabs_perg_admin = st.tabs(["📋 Perguntas Atuais", "➕ Adicionar Nova Pergunta"])
                try:
                    perguntas_df_admin_gp = pd.read_csv(perguntas_csv, encoding='utf-8')
                    if "Categoria" not in perguntas_df_admin_gp.columns:
                        perguntas_df_admin_gp["Categoria"] = "Geral"
                except (FileNotFoundError, pd.errors.EmptyDataError):
                    perguntas_df_admin_gp = pd.DataFrame(columns=colunas_base_perguntas)
                with tabs_perg_admin[0]:
                    if perguntas_df_admin_gp.empty: st.info("Nenhuma pergunta cadastrada.")
                    else:
                        for i_p_admin, row_p_admin in perguntas_df_admin_gp.iterrows():
                            cols_p_admin = st.columns([4, 2, 0.5, 0.5]) 
                            with cols_p_admin[0]: nova_p_text_admin = st.text_input("Pergunta", value=str(row_p_admin["Pergunta"]), key=f"edit_p_txt_v16_gp_{i_p_admin}") # Key updated
                            with cols_p_admin[1]: nova_cat_text_admin = st.text_input("Categoria", value=str(row_p_admin.get("Categoria", "Geral")), key=f"edit_p_cat_v16_gp_{i_p_admin}") # Key updated
                            with cols_p_admin[2]:
                                st.markdown("<br/>", unsafe_allow_html=True) 
                                if st.button("💾", key=f"salvar_p_adm_v16_gp_{i_p_admin}", help="Salvar Alterações"): # Key updated
                                    perguntas_df_admin_gp.loc[i_p_admin, "Pergunta"] = nova_p_text_admin
                                    perguntas_df_admin_gp.loc[i_p_admin, "Categoria"] = nova_cat_text_admin
                                    perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                    st.success(f"Pergunta {i_p_admin+1} atualizada."); st.rerun()
                            with cols_p_admin[3]:
                                st.markdown("<br/>", unsafe_allow_html=True) 
                                if st.button("🗑️", key=f"deletar_p_adm_v16_gp_{i_p_admin}", help="Deletar Pergunta"): # Key updated
                                    perguntas_df_admin_gp = perguntas_df_admin_gp.drop(i_p_admin).reset_index(drop=True)
                                    perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                    st.warning(f"Pergunta {i_p_admin+1} removida."); st.rerun()
                            st.divider()
                with tabs_perg_admin[1]:
                    with st.form("form_nova_pergunta_admin_v16_gp"): # Key updated
                        st.subheader("➕ Adicionar Nova Pergunta"); nova_p_form_txt_admin = st.text_input("Texto da Pergunta (sem incluir o tipo, ex: 'Qual o nível de satisfação?')", key="nova_p_input_admin_txt_v16_gp") # Key updated
                        cat_existentes_gp = sorted(list(perguntas_df_admin_gp['Categoria'].astype(str).unique())) if not perguntas_df_admin_gp.empty and "Categoria" in perguntas_df_admin_gp.columns else []; cat_options_gp = ["Nova Categoria"] + cat_existentes_gp; cat_selecionada_gp = st.selectbox("Categoria:", cat_options_gp, key="cat_select_admin_new_q_v16_gp") # Key updated
                        nova_cat_form_admin_gp = st.text_input("Nome da Nova Categoria (se 'Nova Categoria' selecionada acima):", key="nova_cat_input_admin_new_q_v16_gp") if cat_selecionada_gp == "Nova Categoria" else cat_selecionada_gp # Key updated
                        tipo_p_form_admin = st.selectbox("Tipo de Pergunta (será adicionado ao final do texto da pergunta):", ["Pontuação (0-10)", "Pontuação (0-5)", "Texto Aberto", "Escala", "[Matriz GUT]"], key="tipo_p_select_admin_new_q_v16_gp") # Key updated
                        if st.form_submit_button("➕ Adicionar Pergunta"):
                            if nova_p_form_txt_admin.strip() and nova_cat_form_admin_gp.strip():
                                p_completa_add_admin = f"{nova_p_form_txt_admin.strip()} [{tipo_p_form_admin.replace('[','').replace(']','') if tipo_p_form_admin != 'Escala' else 'Escala'}]"
                                if tipo_p_form_admin == "Escala": p_completa_add_admin = f"{nova_p_form_txt_admin.strip()} [Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)]" 
                                nova_entrada_p_add_admin = pd.DataFrame([[p_completa_add_admin, nova_cat_form_admin_gp.strip()]], columns=["Pergunta", "Categoria"]); perguntas_df_admin_gp = pd.concat([perguntas_df_admin_gp, nova_entrada_p_add_admin], ignore_index=True); perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8'); st.success(f"Pergunta adicionada!"); st.rerun()
                            else: st.warning("Texto da pergunta e categoria são obrigatórios.")

            elif menu_admin == "💡 Gerenciar Análises de Perguntas":
                st.subheader("Gerenciar Análises Vinculadas às Perguntas"); df_analises_existentes_admin = carregar_analises_perguntas()
                try: df_perguntas_formulario_admin = pd.read_csv(perguntas_csv, encoding='utf-8')
                except: df_perguntas_formulario_admin = pd.DataFrame(columns=colunas_base_perguntas)
                st.markdown("#### Adicionar Nova Análise")
                if df_perguntas_formulario_admin.empty: st.warning("Nenhuma pergunta cadastrada no formulário. Adicione perguntas primeiro em 'Gerenciar Perguntas'.")
                else:
                    lista_perguntas_txt_admin = [""] + df_perguntas_formulario_admin["Pergunta"].unique().tolist(); pergunta_selecionada_analise_admin = st.selectbox("Selecione a Pergunta para adicionar análise:", lista_perguntas_txt_admin, key="sel_perg_analise_v16_ga") # Key updated
                    if pergunta_selecionada_analise_admin:
                        st.caption(f"Pergunta selecionada: {pergunta_selecionada_analise_admin}"); tipo_condicao_analise_display_admin = st.selectbox("Tipo de Condição para a Análise:", ["Faixa Numérica (p/ Pontuação 0-X)", "Valor Exato (p/ Escala)", "Faixa de Score (p/ Matriz GUT)", "Análise Padrão (default para a pergunta)"], key="tipo_cond_analise_v16_ga") # Key updated
                        map_tipo_cond_to_csv_admin = { "Faixa Numérica (p/ Pontuação 0-X)": "FaixaNumerica", "Valor Exato (p/ Escala)": "ValorExatoEscala", "Faixa de Score (p/ Matriz GUT)": "ScoreGUT", "Análise Padrão (default para a pergunta)": "Default" }; tipo_condicao_csv_val_admin = map_tipo_cond_to_csv_admin[tipo_condicao_analise_display_admin]
                        cond_val_min_ui_admin, cond_val_max_ui_admin, cond_val_exato_ui_admin = None, None, None
                        if tipo_condicao_csv_val_admin == "FaixaNumerica": cols_faixa_ui_admin = st.columns(2); cond_val_min_ui_admin = cols_faixa_ui_admin[0].number_input("Valor Mínimo da Faixa", step=1.0, format="%.2f", key="cond_min_analise_v16_ga"); cond_val_max_ui_admin = cols_faixa_ui_admin[1].number_input("Valor Máximo da Faixa", step=1.0, format="%.2f", key="cond_max_analise_v16_ga") # Keys updated
                        elif tipo_condicao_csv_val_admin == "ValorExatoEscala": cond_val_exato_ui_admin = st.text_input("Valor Exato da Escala (ex: Baixo, Médio, Alto)", key="cond_exato_analise_v16_ga") # Key updated
                        elif tipo_condicao_csv_val_admin == "ScoreGUT": cols_faixa_gut_ui_admin = st.columns(2); cond_val_min_ui_admin = cols_faixa_gut_ui_admin[0].number_input("Score GUT Mínimo", step=1, key="cond_min_gut_analise_v16_ga"); cond_val_max_ui_admin = cols_faixa_gut_ui_admin[1].number_input("Score GUT Máximo (opcional, deixe 0 ou vazio se for 'acima de Mínimo')", value=0.0, step=1.0, format="%.0f", key="cond_max_gut_analise_v16_ga") # Keys updated 
                        texto_analise_nova_ui_admin = st.text_area("Texto da Análise:", height=150, key="txt_analise_nova_v16_ga") # Key updated
                        if st.button("💾 Salvar Nova Análise", key="salvar_analise_pergunta_v16_ga"): # Key updated
                            if texto_analise_nova_ui_admin.strip(): nova_id_analise_admin = str(uuid.uuid4()); nova_entrada_analise_admin = { "ID_Analise": nova_id_analise_admin, "TextoPerguntaOriginal": pergunta_selecionada_analise_admin, "TipoCondicao": tipo_condicao_csv_val_admin, "CondicaoValorMin": cond_val_min_ui_admin if cond_val_min_ui_admin is not None else pd.NA, "CondicaoValorMax": cond_val_max_ui_admin if cond_val_max_ui_admin is not None and cond_val_max_ui_admin !=0 else pd.NA, "CondicaoValorExato": cond_val_exato_ui_admin if cond_val_exato_ui_admin else pd.NA, "TextoAnalise": texto_analise_nova_ui_admin }; df_analises_existentes_admin = pd.concat([df_analises_existentes_admin, pd.DataFrame([nova_entrada_analise_admin])], ignore_index=True); df_analises_existentes_admin.to_csv(analises_perguntas_csv, index=False, encoding='utf-8'); st.success(f"Nova análise salva!"); st.markdown(f"**Pergunta:** {pergunta_selecionada_analise_admin}"); st.markdown(f"**Análise:** {texto_analise_nova_ui_admin}"); st.rerun()
                            else: st.error("O texto da análise não pode estar vazio.")
                st.markdown("---"); st.subheader("📜 Análises Cadastradas")
                df_analises_para_exibir = carregar_analises_perguntas() 
                if df_analises_para_exibir.empty: st.info("Nenhuma análise cadastrada.")
                else:
                    df_display_analises_view = df_analises_para_exibir.copy()
                    for col_num_format_view in ['CondicaoValorMin', 'CondicaoValorMax']:
                        if col_num_format_view in df_display_analises_view.columns: df_display_analises_view[col_num_format_view] = pd.to_numeric(df_display_analises_view[col_num_format_view], errors='coerce').fillna("") 
                    st.dataframe(df_display_analises_view)
                    analise_del_id_admin_view = st.selectbox("Deletar Análise por ID:", [""] + df_analises_para_exibir["ID_Analise"].astype(str).tolist(), key="del_analise_id_v16_ga_view") # Key updated
                    if st.button("🗑️ Deletar Análise Selecionada", key="btn_del_analise_v16_ga_view", type="primary") and analise_del_id_admin_view: df_analises_para_exibir = df_analises_para_exibir[df_analises_para_exibir["ID_Analise"] != analise_del_id_admin_view]; df_analises_para_exibir.to_csv(analises_perguntas_csv, index=False, encoding='utf-8'); st.warning("Análise deletada."); st.rerun() # Key updated

            elif menu_admin == "✍️ Gerenciar Instruções Clientes":
                st.subheader("Gerenciar Instruções para Clientes")
                current_instructions = ""
                try:
                    if os.path.exists(instrucoes_txt_file) and os.path.getsize(instrucoes_txt_file) > 0:
                        with open(instrucoes_txt_file, "r", encoding="utf-8") as f:
                            current_instructions = f.read()
                    elif not os.path.exists(instrucoes_txt_file): 
                        with open(instrucoes_txt_file, "w", encoding="utf-8") as f: 
                            default_text = """**Bem-vindo ao Portal de Diagnóstico Empresarial!** (Conteúdo padrão)""" # Resumido para brevidade
                            f.write(default_text) 
                            current_instructions = default_text
                except Exception as e: st.error(f"Erro ao ler arquivo de instruções: {e}")
                edited_instructions = st.text_area("Edite as instruções para os clientes (use Markdown para formatação):", value=current_instructions, height=400, key="admin_edit_instructions_ta_v16") # Key updated
                if st.button("💾 Salvar Instruções", key="admin_save_instructions_btn_v16"): # Key updated
                    try:
                        with open(instrucoes_txt_file, "w", encoding="utf-8") as f: f.write(edited_instructions)
                        st.success("Instruções salvas com sucesso!")
                    except Exception as e: st.error(f"Erro ao salvar instruções: {e}")

            elif menu_admin == "👥 Gerenciar Clientes":
                st.subheader("Gerenciar Clientes")
                try:
                    df_usuarios_gc = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                    for col, default, dtype_col in [("ConfirmouInstrucoesParaSlotAtual", "False", str), ("DiagnosticosDisponiveis", 1, int), ("TotalDiagnosticosRealizados", 0, int), ("LiberacoesExtrasConcedidas", 0, int)]:
                        if col not in df_usuarios_gc.columns: df_usuarios_gc[col] = default
                        if dtype_col == int: df_usuarios_gc[col] = pd.to_numeric(df_usuarios_gc[col], errors='coerce').fillna(default).astype(int)
                        else: df_usuarios_gc[col] = df_usuarios_gc[col].astype(str)
                except FileNotFoundError: st.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado."); df_usuarios_gc = pd.DataFrame(columns=colunas_base_usuarios)
                except Exception as e_gc_load_full: st.error(f"Erro ao carregar usuários: {e_gc_load_full}"); df_usuarios_gc = pd.DataFrame(columns=colunas_base_usuarios)
                st.markdown("#### Lista de Clientes Cadastrados")
                if not df_usuarios_gc.empty:
                    cols_display_gc = ["CNPJ", "Empresa", "NomeContato", "Telefone", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "LiberacoesExtrasConcedidas", "ConfirmouInstrucoesParaSlotAtual"]; st.dataframe(df_usuarios_gc[cols_display_gc])
                    st.markdown("#### Ações de Cliente"); clientes_lista_gc_ops = df_usuarios_gc.apply(lambda row: f"{row['Empresa']} ({row['CNPJ']})", axis=1).tolist(); cliente_selecionado_str_gc = st.selectbox("Selecione o cliente para gerenciar:", [""] + clientes_lista_gc_ops, key="sel_cliente_gc_v16_adm") # Key updated
                    if cliente_selecionado_str_gc:
                        cnpj_selecionado_gc_val = cliente_selecionado_str_gc.split('(')[-1].replace(')','').strip(); cliente_data_gc_val = df_usuarios_gc[df_usuarios_gc["CNPJ"] == cnpj_selecionado_gc_val].iloc[0]
                        st.write(f"**Empresa:** {cliente_data_gc_val['Empresa']}"); st.write(f"**Diagnósticos Disponíveis (Slots):** {cliente_data_gc_val['DiagnosticosDisponiveis']}"); st.write(f"**Diagnósticos Já Realizados:** {cliente_data_gc_val['TotalDiagnosticosRealizados']}"); st.write(f"**Liberações Extras Concedidas:** {cliente_data_gc_val['LiberacoesExtrasConcedidas']}")
                        st.write(f"**Confirmou Instruções para Slot Atual:** {cliente_data_gc_val['ConfirmouInstrucoesParaSlotAtual']}")
                        if st.button(f"➕ Conceder +1 Diagnóstico para {cliente_data_gc_val['Empresa']}", key=f"conceder_diag_gc_v16_adm_{cnpj_selecionado_gc_val}"): # Key updated
                            novos_disponiveis = cliente_data_gc_val['DiagnosticosDisponiveis'] + 1; liberacoes_extras_atuais = cliente_data_gc_val.get('LiberacoesExtrasConcedidas', 0)
                            update_user_data(cnpj_selecionado_gc_val, "DiagnosticosDisponiveis", novos_disponiveis); update_user_data(cnpj_selecionado_gc_val, "LiberacoesExtrasConcedidas", liberacoes_extras_atuais + 1); update_user_data(cnpj_selecionado_gc_val, "ConfirmouInstrucoesParaSlotAtual", "False") 
                            registrar_acao("ADMIN", "Concessão Diagnóstico", f"Admin concedeu +1 slot para {cliente_data_gc_val['Empresa']} ({cnpj_selecionado_gc_val}). Slots: {novos_disponiveis}. Extras: {liberacoes_extras_atuais + 1}."); st.success(f"+1 Slot concedido. Slots disponíveis: {novos_disponiveis}. Liberações extras: {liberacoes_extras_atuais + 1}. Instruções resetadas."); st.rerun()
                        if st.button(f"🔄 Resetar Confirmação de Instruções para {cliente_data_gc_val['Empresa']}", key=f"reset_inst_gc_v16_{cnpj_selecionado_gc_val}"): # Key updated
                            update_user_data(cnpj_selecionado_gc_val, "ConfirmouInstrucoesParaSlotAtual", "False")
                            registrar_acao("ADMIN", "Reset Instruções", f"Admin resetou confirmação de instruções para {cliente_data_gc_val['Empresa']} ({cnpj_selecionado_gc_val})."); st.success(f"Confirmação de instruções resetada para {cliente_data_gc_val['Empresa']}."); st.rerun()

                        try: bloqueados_df_gc_check = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                        except FileNotFoundError: bloqueados_df_gc_check = pd.DataFrame(columns=["CNPJ"])
                        is_blocked_gc_check = cnpj_selecionado_gc_val in bloqueados_df_gc_check["CNPJ"].values
                        if is_blocked_gc_check:
                            if st.button(f"🔓 Desbloquear Acesso Total para {cliente_data_gc_val['Empresa']}", key=f"desbloq_total_gc_v16_adm_{cnpj_selecionado_gc_val}"): bloqueados_df_gc_check = bloqueados_df_gc_check[bloqueados_df_gc_check["CNPJ"] != cnpj_selecionado_gc_val]; bloqueados_df_gc_check.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8'); st.success(f"Acesso total desbloqueado."); st.rerun() # Key updated
                        else:
                            if st.button(f"🚫 Bloquear Acesso Total para {cliente_data_gc_val['Empresa']}", type="primary", key=f"bloq_total_gc_v16_adm_{cnpj_selecionado_gc_val}"): nova_entrada_bloqueio_gc_val = pd.DataFrame([{"CNPJ": cnpj_selecionado_gc_val}]); bloqueados_df_gc_check = pd.concat([bloqueados_df_gc_check, nova_entrada_bloqueio_gc_val], ignore_index=True); bloqueados_df_gc_check.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8'); st.error(f"Acesso total bloqueado."); st.rerun() # Key updated
                else: st.info("Nenhum cliente cadastrado para gerenciar.")
                st.markdown("---"); st.markdown("#### Adicionar Novo Cliente")
                with st.form("form_novo_cliente_v16_adm", clear_on_submit=True): # Key updated
                    novo_cnpj_gc_form = st.text_input("CNPJ do Novo Cliente:"); nova_senha_gc_form = st.text_input("Senha para o Novo Cliente:", type="password"); nova_empresa_gc_form = st.text_input("Nome da Empresa do Novo Cliente:"); novo_contato_gc_form = st.text_input("Nome do Contato (opcional):"); novo_telefone_gc_form = st.text_input("Telefone do Contato (opcional):")
                    if st.form_submit_button("➕ Cadastrar Novo Cliente"):
                        if novo_cnpj_gc_form and nova_senha_gc_form and nova_empresa_gc_form:
                            try: current_users_df_for_check = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                            except (FileNotFoundError, pd.errors.EmptyDataError): current_users_df_for_check = pd.DataFrame(columns=colunas_base_usuarios)

                            if current_users_df_for_check.empty or (novo_cnpj_gc_form not in current_users_df_for_check["CNPJ"].values):
                                nova_linha_cliente_form = pd.DataFrame([{"CNPJ": novo_cnpj_gc_form, "Senha": nova_senha_gc_form, "Empresa": nova_empresa_gc_form, "NomeContato": novo_contato_gc_form, "Telefone": novo_telefone_gc_form, "ConfirmouInstrucoesParaSlotAtual": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0, "LiberacoesExtrasConcedidas": 0}])
                                df_usuarios_gc_updated = pd.concat([current_users_df_for_check, nova_linha_cliente_form], ignore_index=True);
                                df_usuarios_gc_updated.to_csv(usuarios_csv, index=False, encoding='utf-8'); st.success(f"Cliente {nova_empresa_gc_form} cadastrado com sucesso!"); st.rerun()
                            else: st.error("CNPJ já cadastrado.")
                        else: st.error("CNPJ, Senha e Nome da Empresa são obrigatórios.")

            elif menu_admin == "👮 Gerenciar Administradores":
                st.subheader("Gerenciar Administradores");
                try: admins_df_mng = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                except (FileNotFoundError, pd.errors.EmptyDataError): admins_df_mng = pd.DataFrame(columns=["Usuario", "Senha"])
                st.dataframe(admins_df_mng[["Usuario"]]); st.markdown("---"); st.subheader("➕ Adicionar Novo Admin")
                with st.form("form_novo_admin_mng_v16_adm"): # Key updated
                    novo_admin_user_mng = st.text_input("Usuário do Admin"); novo_admin_pass_mng = st.text_input("Senha do Admin", type="password")
                    if st.form_submit_button("Adicionar Admin"):
                        if novo_admin_user_mng and novo_admin_pass_mng:
                            if novo_admin_user_mng in admins_df_mng["Usuario"].values: st.error(f"Usuário '{novo_admin_user_mng}' já existe.")
                            else: novo_admin_data_mng = pd.DataFrame([[novo_admin_user_mng, novo_admin_pass_mng]], columns=["Usuario", "Senha"]); admins_df_mng = pd.concat([admins_df_mng, novo_admin_data_mng], ignore_index=True); admins_df_mng.to_csv(admin_credenciais_csv, index=False, encoding='utf-8'); st.success(f"Admin '{novo_admin_user_mng}' adicionado!"); st.rerun()
                        else: st.warning("Preencha todos os campos.")
                st.markdown("---"); st.subheader("🗑️ Remover Admin")
                if not admins_df_mng.empty:
                    admin_para_remover_mng = st.selectbox("Remover Admin:", options=[""] + admins_df_mng["Usuario"].tolist(), key="remove_admin_select_mng_v16_adm") # Key updated
                    if st.button("Remover Admin Selecionado", type="primary", key="btn_remove_admin_v16_adm") and admin_para_remover_mng: # Key updated
                        if len(admins_df_mng) == 1 and admin_para_remover_mng == admins_df_mng["Usuario"].iloc[0]: st.error("Não é possível remover o único administrador.")
                        elif admin_para_remover_mng == st.session_state.get('admin_user_login_identifier', ''): 
                            st.error("Não é possível remover a si mesmo.")
                        else: admins_df_mng = admins_df_mng[admins_df_mng["Usuario"] != admin_para_remover_mng]; admins_df_mng.to_csv(admin_credenciais_csv, index=False, encoding='utf-8'); st.warning(f"Admin '{admin_para_remover_mng}' removido."); st.rerun()
                else: st.info("Nenhum administrador para remover.")

            elif menu_admin == "💾 Backup de Dados":
                st.subheader("Backup de Dados do Sistema"); st.markdown("Clique nos botões abaixo para baixar cópias dos arquivos CSV do sistema.")
                arquivos_para_backup = { "Clientes (Usuários)": usuarios_csv, "Diagnósticos": arquivo_csv, "Perguntas do Formulário": perguntas_csv, "Análises das Perguntas": analises_perguntas_csv, "Histórico de Ações": historico_csv, "Administradores": admin_credenciais_csv, "Clientes Bloqueados": usuarios_bloqueados_csv, "Notificações": notificacoes_csv }
                for nome_amigavel, nome_arquivo in arquivos_para_backup.items():
                    if os.path.exists(nome_arquivo) and os.path.getsize(nome_arquivo) > 0:
                        with open(nome_arquivo, "rb") as fp: st.download_button(label=f"Baixar {nome_amigavel} ({os.path.getsize(nome_arquivo)} bytes)", data=fp, file_name=nome_arquivo, mime="text/csv", key=f"backup_btn_v16_{nome_arquivo.replace('.','_')}") # Key updated
                    elif os.path.exists(nome_arquivo): st.warning(f"Arquivo '{nome_arquivo}' encontrado, mas está vazio. Backup não gerado.")
                    else: st.warning(f"Arquivo '{nome_arquivo}' não encontrado para backup.")
        except Exception as e_admin_menu_dispatch:
            st.error(f"Ocorreu um erro na funcionalidade '{menu_admin}': {e_admin_menu_dispatch}")
            st.exception(e_admin_menu_dispatch) 
    except Exception as e_outer_admin_critical:
        st.error(f"Um erro crítico e inesperado ocorreu na área administrativa: {e_outer_admin_critical}")
        st.exception(e_outer_admin_critical) 

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")