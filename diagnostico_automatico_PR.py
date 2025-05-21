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
ST_KEY_VERSION = "v22"

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
            elif filepath == usuarios_bloqueados_csv: dtype_spec = {'CNPJ': str}
            elif filepath == arquivo_csv: dtype_spec = {'CNPJ': str}
            elif filepath == notificacoes_csv: dtype_spec = {'CNPJ_Cliente': str}
            elif filepath == historico_csv: dtype_spec = {'CNPJ': str}
            
            if filepath == notificacoes_csv:
                try: 
                    temp_df_cols = pd.read_csv(filepath, encoding='utf-8', nrows=0).columns
                    if 'CNPJ_Cliente' not in temp_df_cols and 'CNPJ_Cliente' in dtype_spec: 
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
            f.write("""**Bem-vindo ao Portal de Diagnóstico Empresarial!** (Conteúdo padrão das instruções)""")
except Exception as e_init_global:
    st.error(f"⚠️ ERRO CRÍTICO NA INICIALIZAÇÃO DO APP: {e_init_global}")
    st.exception(e_init_global) 
    st.stop() 

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
            except Exception as e_logo: st.warning(f"Não foi possível adicionar logo ao PDF: {e_logo}")

        pdf.set_font("Arial", 'B', 16)
        pdf.multi_cell(w=0, h=10, txt=pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome}"), border=0, align='C', ln=1)
        
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(w=0, h=7, txt=pdf_safe_text_output(f"Data: {diag_data.get('Data','N/D')} | Empresa: {empresa_nome} (CNPJ: {cnpj_pdf})"), border=0, align='L', ln=1)
        if user_data.get("NomeContato"): 
            pdf.multi_cell(w=0, h=7, txt=pdf_safe_text_output(f"Contato: {user_data.get('NomeContato')}"), border=0, align='L', ln=1)
        if user_data.get("Telefone"): 
            pdf.multi_cell(w=0, h=7, txt=pdf_safe_text_output(f"Telefone: {user_data.get('Telefone')}"), border=0, align='L', ln=1)
        pdf.ln(3)
        pdf.multi_cell(w=0, h=7, txt=pdf_safe_text_output(f"Média Geral: {diag_data.get('Média Geral','N/A')} | GUT Média: {diag_data.get('GUT Média','N/A')}"), border=0, align='L', ln=1)
        pdf.ln(3)

        if medias_cat:
            pdf.set_font("Arial", 'B', 11)
            pdf.multi_cell(w=0, h=7, txt=pdf_safe_text_output("Médias por Categoria:"), border=0, align='L', ln=1)
            pdf.set_font("Arial", size=10)
            for cat, media in sorted(medias_cat.items()): 
                pdf.multi_cell(w=0, h=6, txt=pdf_safe_text_output(f"  - {cat}: {media:.2f}"), border=0, align='L', ln=1)
            pdf.ln(5)

        for titulo, campo in [("Resumo (Cliente):", "Diagnóstico"), ("Análise (Cliente):", "Análise do Cliente"), ("Comentários (Consultor):", "Comentarios_Admin")]:
            valor = diag_data.get(campo, "")
            if valor and not pd.isna(valor) and str(valor).strip():
                pdf.set_font("Arial", 'B', 12)
                pdf.multi_cell(w=0, h=7, txt=pdf_safe_text_output(titulo), border=0, align='L', ln=1)
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(w=0, h=7, txt=pdf_safe_text_output(str(valor)), border=0, align='L', ln=1)
                pdf.ln(3)

        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(w=0, h=10, txt=pdf_safe_text_output("Respostas Detalhadas e Análises:"), border=0, align='L', ln=1)
        categorias = sorted(perguntas_df["Categoria"].unique()) if not perguntas_df.empty and "Categoria" in perguntas_df.columns else []
        for categoria in categorias:
            pdf.set_font("Arial", 'B', 10)
            pdf.multi_cell(w=0, h=7, txt=pdf_safe_text_output(f"Categoria: {categoria}"), border=0, align='L', ln=1)
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
                    pdf.multi_cell(w=0, h=6, txt=pdf_safe_text_output(f"  - {p_texto.replace(' [Matriz GUT]','')}: G={g}, U={u}, T={t} (Score: {score})"), border=0, align='L', ln=1)
                    analise_texto = obter_analise_para_resposta(p_texto, score, analises_df)
                else:
                    pdf.multi_cell(w=0, h=6, txt=pdf_safe_text_output(f"  - {p_texto}: {resp}"), border=0, align='L', ln=1)
                    analise_texto = obter_analise_para_resposta(p_texto, resp, analises_df)
                if analise_texto:
                    pdf.set_font("Arial", 'I', 8); pdf.set_text_color(100,100,100)
                    pdf.multi_cell(w=0, h=5, txt=pdf_safe_text_output(f"    Análise: {analise_texto}"), border=0, align='L', ln=1)
                    pdf.set_text_color(0,0,0); pdf.set_font("Arial", size=9) 
            pdf.ln(2)
        pdf.ln(3)
        pdf.add_page(); pdf.set_font("Arial", 'B', 12)
        pdf.cell(w=0, h=10, txt=pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), border=0, ln=1, align='C')
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
            for card in sorted_cards: 
                pdf.multi_cell(w=0, h=6, txt=pdf_safe_text_output(f"Prazo: {card['Prazo']} - Tarefa: {card['Tarefa']} (Score GUT: {card['Score']})"), border=0, align='L', ln=1)
        else: 
            pdf.multi_cell(w=0, h=6, txt=pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."), border=0, align='L', ln=1)

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

        pdf.set_fill_color(200, 220, 255) # Definir cor de preenchimento para o cabeçalho uma vez

        for header in headers_to_print_hist:
            pdf.cell(w=col_widths_config.get(header, 30), h=7, txt=pdf_safe_text_output(header), border=1, ln=0, align="C", fill=True)
        pdf.ln(7) 
        # Não é necessário restaurar a cor de preenchimento se as células de dados não usarem fill=True ou se definirem sua própria cor

        pdf.set_font("Arial", "", 8)
        line_height_for_multicell = 5 

        for _, row_data in df_historico_filtrado.iterrows():
            y_start_current_row = pdf.get_y()
            max_cell_height_in_row = line_height_for_multicell # Altura mínima

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
                pdf.multi_cell(w=cell_w, h=line_height_for_multicell, txt=pdf_safe_text_output(cell_content), border=0, align="L", ln=0) 
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
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador 🔑</h2>', unsafe_allow_html=True)
    with st.form(f"form_admin_login_{ST_KEY_VERSION}"): 
        u = st.text_input("Usuário", key=f"admin_u_{ST_KEY_VERSION}")
        p = st.text_input("Senha", type="password", key=f"admin_p_{ST_KEY_VERSION}") 
        if st.form_submit_button("Entrar"):
            try:
                df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                admin_encontrado = df_creds[df_creds["Usuario"] == u]
                if not admin_encontrado.empty and admin_encontrado.iloc[0]["Senha"] == p:
                    st.session_state.admin_logado = True
                    st.session_state.admin_user_login_identifier = u 
                    st.success("Login de administrador bem-sucedido! ✅"); st.rerun()
                else: st.error("Usuário ou senha inválidos.")
            except FileNotFoundError: st.error(f"Arquivo de credenciais de admin não encontrado: {admin_credenciais_csv}")
            except Exception as e: st.error(f"Erro no login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DE LOGIN DO CLIENTE ---
if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente 🏢</h2>', unsafe_allow_html=True)
    with st.form(f"form_cliente_login_{ST_KEY_VERSION}"): 
        c = st.text_input("CNPJ", key=f"cli_c_{ST_KEY_VERSION}", value=st.session_state.get("last_cnpj_input","")) 
        s = st.text_input("Senha", type="password", key=f"cli_s_{ST_KEY_VERSION}") 
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
                # ... (resto da lógica de login do cliente) ...
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
    # ... (Lógica da área do cliente com chaves _v21 - OMITIDO PARA BREVIDADE)
    # Certifique-se de atualizar todas as chaves de widget aqui para f"..._{ST_KEY_VERSION}"
    # Por exemplo, a lógica do menu:
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}! 👋")
    # ... (expander de perfil) ...
    unread_notif_count_val = get_unread_notifications_count(st.session_state.cnpj)
    notif_menu_label_val = "🔔 Notificações"
    if unread_notif_count_val > 0: notif_menu_label_val = f"🔔 Notificações ({unread_notif_count_val})"
    menu_options_cli_val = ["📖 Instruções", "📝 Novo Diagnóstico", "📊 Painel Principal", notif_menu_label_val]
    # ... (lógica para determinar current_idx_cli_val) ...
    try: current_idx_cli_val = menu_options_cli_val.index(st.session_state.get("cliente_page", "Instruções")) # Simplificado
    except ValueError: current_idx_cli_val = 0 
    selected_page_cli_raw_val = st.sidebar.radio("Menu Cliente", menu_options_cli_val, index=current_idx_cli_val, key=f"cli_menu_{ST_KEY_VERSION}") 
    # ... (resto da lógica do menu cliente e páginas)
    # O conteúdo específico de cada página do cliente (Instruções, Painel Principal, etc.)
    # foi omitido aqui, mas deve usar chaves com ST_KEY_VERSION.
    if st.session_state.cliente_page == "Instruções":
        st.subheader("📖 Instruções do Sistema de Diagnóstico")
        st.markdown("Conteúdo da página de instruções aqui...")
        # (Exemplo de chave)
        st.checkbox("Li e concordo", key=f"cliente_inst_check_{ST_KEY_VERSION}")
    elif st.session_state.cliente_page == "Painel Principal":
        st.subheader("📊 Painel Principal do Cliente")
        st.markdown("Conteúdo do painel principal aqui...")
    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader("📝 Formulário de Novo Diagnóstico")
        st.markdown("Conteúdo do novo diagnóstico aqui...")
    elif st.session_state.cliente_page == "Notificações":
        st.subheader("🔔 Minhas Notificações")
        st.markdown("Conteúdo das notificações aqui...")
    pass # Fim da área do cliente (omitida para brevidade)


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
        st.header(f"{menu_admin.split(' ')[0]} {menu_admin.split(' ', 1)[1]}")
        
        df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios) 
        try:
            if os.path.exists(usuarios_csv) and os.path.getsize(usuarios_csv) > 0:
                df_usuarios_admin_temp_load = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                for col, default, dtype_col in [("ConfirmouInstrucoesParaSlotAtual", "False", str), ("DiagnosticosDisponiveis", 1, int), ("TotalDiagnosticosRealizados", 0, int), ("LiberacoesExtrasConcedidas", 0, int)]:
                    if col not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load[col] = default
                    if dtype_col == int: df_usuarios_admin_temp_load[col] = pd.to_numeric(df_usuarios_admin_temp_load[col], errors='coerce').fillna(default).astype(int)
                    else: df_usuarios_admin_temp_load[col] = df_usuarios_admin_temp_load[col].astype(str)
                df_usuarios_admin_geral = df_usuarios_admin_temp_load
        except FileNotFoundError: st.sidebar.warning(f"Arquivo de usuários '{usuarios_csv}' não encontrado.") # Mudado para warning
        except Exception as e_load_users_adm_global: st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm_global}")

        diagnosticos_df_admin_orig_view = pd.DataFrame() 
        admin_data_carregada_view_sucesso = False
        if not os.path.exists(arquivo_csv) or os.path.getsize(arquivo_csv) == 0 : 
            st.warning(f"Arquivo de diagnósticos ('{arquivo_csv}') não encontrado ou vazio.")
        else:
            try:
                diagnosticos_df_admin_orig_view = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                if 'Data' in diagnosticos_df_admin_orig_view.columns: diagnosticos_df_admin_orig_view['Data'] = pd.to_datetime(diagnosticos_df_admin_orig_view['Data'], errors='coerce')
                if not diagnosticos_df_admin_orig_view.empty: admin_data_carregada_view_sucesso = True
            except Exception as e_adm_load_diag: 
                st.error(f"ERRO AO CARREGAR ARQUIVO DE DIAGNÓSTICOS ('{arquivo_csv}'): {e_adm_load_diag}")
                # Não usar st.exception() aqui para não parar o script completamente, permitindo que outras partes do menu funcionem.

        try:
            if menu_admin == "📊 Visão Geral e Diagnósticos":
                st.subheader("Visão Geral e Indicadores de Diagnósticos")
                # ... (Lógica completa desta seção com chaves ST_KEY_VERSION)
                st.markdown("Conteúdo da Visão Geral e Diagnósticos aqui...")
            
            elif menu_admin == "🚦 Status dos Clientes":
                st.subheader("Status de Diagnósticos dos Clientes")
                # ... (Lógica completa desta seção com chaves ST_KEY_VERSION)
                st.markdown("Conteúdo do Status dos Clientes aqui...")

            elif menu_admin == "📜 Histórico de Usuários":
                st.subheader("📜 Histórico de Ações")
                df_historico_completo_hu = pd.DataFrame()
                df_usuarios_para_filtro_hu = pd.DataFrame()
                try:
                    if os.path.exists(historico_csv) and os.path.getsize(historico_csv) > 0:
                        df_historico_completo_hu = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
                    if os.path.exists(usuarios_csv) and os.path.getsize(usuarios_csv) > 0:
                        df_usuarios_para_filtro_hu = pd.read_csv(usuarios_csv, encoding='utf-8', usecols=['CNPJ', 'Empresa', 'NomeContato'], dtype={'CNPJ': str})
                except Exception as e_hu: 
                    st.error(f"Erro ao carregar dados para o histórico: {e_hu}")
                
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
                    cnpjs_match_nome_hu = []
                    if not df_usuarios_para_filtro_hu.empty and 'NomeContato' in df_usuarios_para_filtro_hu.columns:
                         cnpjs_match_nome_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['NomeContato'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)]['CNPJ'].tolist()
                    
                    df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[
                        df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_match_nome_hu) | 
                        df_historico_filtrado_view_hu['CNPJ'].astype(str).str.lower().str.contains(busca_lower_hu) | 
                        df_historico_filtrado_view_hu['Ação'].astype(str).str.lower().str.contains(busca_lower_hu, na=False) | 
                        df_historico_filtrado_view_hu['Descrição'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)
                    ]
                
                st.markdown("#### Registros do Histórico")
                if not df_historico_filtrado_view_hu.empty:
                    st.dataframe(df_historico_filtrado_view_hu.sort_values(by="Data", ascending=False))
                    if st.button("📄 Baixar Histórico Filtrado (PDF)", key=f"download_hist_filtrado_pdf_{ST_KEY_VERSION}_hu_adm"):
                        titulo_pdf_hist = f"Historico_Acoes_{sanitize_column_name(emp_sel_hu)}_{sanitize_column_name(termo_busca_hu) if termo_busca_hu else 'Todos'}_{datetime.now().strftime('%Y%m%d')}.pdf"
                        pdf_path_hist = gerar_pdf_historico(df_historico_filtrado_view_hu, titulo=f"Histórico ({emp_sel_hu} - Busca: {termo_busca_hu or 'N/A'})")
                        if pdf_path_hist:
                            with open(pdf_path_hist, "rb") as f_pdf_hist: 
                                st.download_button(label="Download Confirmado", data=f_pdf_hist, file_name=titulo_pdf_hist, mime="application/pdf", key=f"confirm_download_hist_pdf_{ST_KEY_VERSION}_hu_adm")
                            try: os.remove(pdf_path_hist) 
                            except: pass
                    
                    if emp_sel_hu != "Todas" and not df_historico_filtrado_view_hu.empty and cnpjs_da_empresa_selecionada_hu:
                        st.markdown("---")
                        st.markdown(f"#### 🗑️ Resetar Histórico da Empresa: {emp_sel_hu}")
                        with st.expander(f"⚠️ ATENÇÃO: Excluir TODO o histórico da Empresa '{emp_sel_hu}'"):
                            st.warning(f"Esta ação é irreversível e removerá TODOS os registros de histórico associados à empresa '{emp_sel_hu}' (CNPJs: {', '.join(cnpjs_da_empresa_selecionada_hu)}).")
                            
                            confirm_text_delete_hist = st.text_input(f"Para confirmar, digite o nome da empresa '{emp_sel_hu}' exatamente como mostrado:", key=f"confirm_text_delete_hist_emp_{emp_sel_hu}_{ST_KEY_VERSION}").strip()
                            
                            if st.button(f"🗑️ Excluir Histórico de '{emp_sel_hu}' AGORA", type="primary", key=f"btn_delete_hist_emp_{emp_sel_hu}_{ST_KEY_VERSION}", disabled=(confirm_text_delete_hist != emp_sel_hu)):
                                if confirm_text_delete_hist == emp_sel_hu:
                                    try:
                                        if os.path.exists(historico_csv):
                                            df_hist_full = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
                                            df_hist_full_updated = df_hist_full[~df_hist_full['CNPJ'].isin(cnpjs_da_empresa_selecionada_hu)]
                                            df_hist_full_updated.to_csv(historico_csv, index=False, encoding='utf-8')
                                            registrar_acao("ADMIN_ACTION", "Exclusão Histórico Empresa", f"Admin excluiu todo o histórico da empresa '{emp_sel_hu}' (CNPJs: {', '.join(cnpjs_da_empresa_selecionada_hu)}).")
                                            st.success(f"Todo o histórico da empresa '{emp_sel_hu}' foi excluído com sucesso.")
                                            st.rerun()
                                        else:
                                            st.error("Arquivo de histórico não encontrado para realizar a exclusão.")
                                    except Exception as e_del_hist:
                                        st.error(f"Erro ao excluir o histórico da empresa: {e_del_hist}")
                                else:
                                    st.error("O nome da empresa digitado para confirmação está incorreto.")
                else:
                    st.info("Nenhum registro de histórico encontrado para os filtros aplicados.")
            
            elif menu_admin == "📝 Gerenciar Perguntas":
                st.subheader("Gerenciar Perguntas do Diagnóstico")
                st.markdown("Conteúdo de Gerenciar Perguntas aqui...")
                # ... (Lógica completa desta seção com chaves ST_KEY_VERSION)
            elif menu_admin == "💡 Gerenciar Análises de Perguntas":
                st.subheader("Gerenciar Análises Vinculadas às Perguntas")
                st.markdown("Conteúdo de Gerenciar Análises aqui...")
                # ... (Lógica completa desta seção com chaves ST_KEY_VERSION)
            elif menu_admin == "✍️ Gerenciar Instruções Clientes":
                st.subheader("Gerenciar Instruções para Clientes")
                st.markdown("Conteúdo de Gerenciar Instruções aqui...")
                # ... (Lógica completa desta seção com chaves ST_KEY_VERSION)
            elif menu_admin == "👥 Gerenciar Clientes":
                st.subheader("Gerenciar Clientes")
                st.markdown("Conteúdo de Gerenciar Clientes aqui...")
                # ... (Lógica completa desta seção com chaves ST_KEY_VERSION)
            elif menu_admin == "👮 Gerenciar Administradores":
                st.subheader("Gerenciar Administradores")
                st.markdown("Conteúdo de Gerenciar Administradores aqui...")
                # ... (Lógica completa desta seção com chaves ST_KEY_VERSION)
            elif menu_admin == "💾 Backup de Dados":
                st.subheader("Backup de Dados do Sistema")
                st.markdown("Conteúdo de Backup de Dados aqui...")
                # ... (Lógica completa desta seção com chaves ST_KEY_VERSION)
            else:
                st.warning(f"Opção de menu '{menu_admin}' não reconhecida ou em desenvolvimento.")

        except Exception as e_admin_menu_dispatch:
            st.error(f"Ocorreu um erro na funcionalidade '{menu_admin}': {e_admin_menu_dispatch}")
            # st.exception(e_admin_menu_dispatch) # Mostrar o traceback pode ajudar a depurar
            
    except Exception as e_outer_admin_critical:
        st.error(f"Um erro crítico e inesperado ocorreu na área administrativa: {e_outer_admin_critical}")
        st.exception(e_outer_admin_critical) 

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")