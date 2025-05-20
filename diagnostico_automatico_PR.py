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
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0), # (respondidas, total)
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {} # Para feedback visual por pergunta
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias --- (sanitize_column_name, pdf_safe_text_output, find_client_logo_path - mantidas como antes)
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
            df_init = pd.read_csv(filepath, encoding='utf-8', dtype=str if filepath == usuarios_csv and "CNPJ" in columns else None) # Garante CNPJ como string
            made_changes = False
            for col_idx, col_name in enumerate(columns): # Usar enumerate para manter ordem se possível
                if col_name not in df_init.columns:
                    default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                    df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=default_val) # Tenta manter ordem
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
    inicializar_csv(usuarios_csv, colunas_base_usuarios, defaults={"PodeFazerNovoDiagnostico": True, "JaVisualizouInstrucoes": False})
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
                st.session_state.user[field] = value
            return True
    except Exception as e: st.error(f"Erro ao atualizar usuário ({field}): {e}")
    return False

def carregar_analises_perguntas():
    try: return pd.read_csv(analises_perguntas_csv, encoding='utf-8')
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_analises)

def obter_analise_para_resposta(pergunta_texto, resposta_valor, df_analises):
    # ... (Implementação anterior mantida, com atenção aos tipos de dados na comparação)
    if df_analises.empty: return None
    analises_da_pergunta = df_analises[df_analises['TextoPerguntaOriginal'] == pergunta_texto]
    if analises_da_pergunta.empty: return None

    default_analise = None
    for _, row_analise in analises_da_pergunta.iterrows():
        tipo_cond = row_analise['TipoCondicao']
        analise_txt = row_analise['TextoAnalise']
        
        if tipo_cond == 'Default': default_analise = analise_txt; continue # Salva default e continua procurando mais específico

        if tipo_cond == 'FaixaNumerica':
            min_val = pd.to_numeric(row_analise['CondicaoValorMin'], errors='coerce')
            max_val = pd.to_numeric(row_analise['CondicaoValorMax'], errors='coerce')
            resp_num = pd.to_numeric(resposta_valor, errors='coerce')
            if pd.notna(resp_num) and pd.notna(min_val) and pd.notna(max_val) and min_val <= resp_num <= max_val:
                return analise_txt
        elif tipo_cond == 'ValorExatoEscala':
            if str(resposta_valor).strip().lower() == str(row_analise['CondicaoValorExato']).strip().lower():
                return analise_txt
        elif tipo_cond == 'ScoreGUT':
            min_score = pd.to_numeric(row_analise['CondicaoValorMin'], errors='coerce')
            max_score = pd.to_numeric(row_analise['CondicaoValorMax'], errors='coerce')
            resp_score_gut = pd.to_numeric(resposta_valor, errors='coerce')
            is_min_met = pd.notna(resp_score_gut) and pd.notna(min_score) and resp_score_gut >= min_score
            is_max_met_or_na = pd.isna(max_score) or (pd.notna(resp_score_gut) and resp_score_gut <= max_score)
            if is_min_met and is_max_met_or_na:
                 return analise_txt
    return default_analise # Retorna default se nenhuma específica foi encontrada

def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    # ... (Implementação anterior mantida, mas agora `analises_df` é usado por `obter_analise_para_resposta`)
    # A inclusão da análise no PDF já está na função `obter_analise_para_resposta` e na lógica de iteração das perguntas no PDF.
    try:
        pdf = FPDF()
        pdf.add_page()
        empresa_nome = user_data.get("Empresa", "N/D")
        cnpj_pdf = user_data.get("CNPJ", "N/D")
        # ... (header do PDF com logo, dados da empresa, etc.)
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
        categorias = perguntas_df["Categoria"].unique() if not perguntas_df.empty else []
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

        # Kanban (Plano de Ação GUT)
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
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v6")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v6"):
        u = st.text_input("Usuário", key="admin_u_v6"); p = st.text_input("Senha", type="password", key="admin_p_v6")
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
    with st.form("form_cliente_login_v6"):
        c = st.text_input("CNPJ", key="cli_c_v6", value=st.session_state.get("last_cnpj_input",""))
        s = st.text_input("Senha", type="password", key="cli_s_v6")
        if st.form_submit_button("Entrar"):
            st.session_state.last_cnpj_input = c
            try:
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                if c in blocked_df["CNPJ"].values: st.error("CNPJ bloqueado."); st.stop()
                match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                if match.empty: st.error("CNPJ/senha inválidos."); st.stop()
                
                st.session_state.cliente_logado = True; st.session_state.cnpj = c
                st.session_state.user = match.iloc[0].to_dict()
                st.session_state.inicio_sessao_cliente = time.time()
                registrar_acao(c, "Login", "Usuário logou.")
                
                st.session_state.cliente_page = "Instruções" if not st.session_state.user.get("JaVisualizouInstrucoes", False) \
                                               else ("Novo Diagnóstico" if st.session_state.user.get("PodeFazerNovoDiagnostico", True) \
                                               else "Painel Principal")
                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                st.session_state.respostas_atuais_diagnostico = {}
                st.session_state.progresso_diagnostico_percentual = 0
                st.session_state.progresso_diagnostico_contagem = (0,0)
                st.session_state.feedbacks_respostas = {}
                st.session_state.diagnostico_enviado_sucesso = False # Reseta para novo login

                st.success("Login cliente OK!"); st.rerun()
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    # ... (expander Meu Perfil) ...

    menu_options_cli = ["Instruções", "Novo Diagnóstico", "Painel Principal"]
    try: current_idx_cli = menu_options_cli.index(st.session_state.cliente_page)
    except ValueError: current_idx_cli = 0; st.session_state.cliente_page = menu_options_cli[0]
    
    selected_page_cli = st.sidebar.radio("Menu Cliente", menu_options_cli, index=current_idx_cli, key="cli_menu_v6")
    if selected_page_cli != st.session_state.cliente_page:
        st.session_state.cliente_page = selected_page_cli; st.rerun()

    if st.sidebar.button("⬅️ Sair do Portal Cliente"): # Logout melhorado
        keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input']]
        for key in keys_to_clear: del st.session_state[key]
        for key, value in default_session_state.items(): # Re-set defaults
             if key not in ['admin_logado', 'last_cnpj_input']: st.session_state[key] = value
        st.session_state.cliente_logado = False; st.rerun()

    if st.session_state.cliente_page == "Instruções":
        st.subheader("📖 Instruções do Sistema de Diagnóstico")
        # ... (Texto das instruções mantido) ...
        st.markdown("""Bem-vindo(a) ao Portal de Diagnóstico! ... (texto completo) ...""")
        if st.button("Entendi, prosseguir"):
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", True)
            st.session_state.cliente_page = "Novo Diagnóstico" if st.session_state.user.get("PodeFazerNovoDiagnostico", True) else "Painel Principal"
            st.rerun()

    elif st.session_state.cliente_page == "Painel Principal":
        st.subheader("📌 Meu Painel de Diagnósticos")
        if st.session_state.diagnostico_enviado_sucesso: # Feedback do último envio
            st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf:
                    st.download_button(label="📄 Baixar PDF do Diagnóstico Recém-Enviado", data=f_pdf,
                                       file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                       key="dl_novo_diag_painel")
                # Limpar para não mostrar novamente no refresh da página
                st.session_state.pdf_gerado_path = None 
                st.session_state.pdf_gerado_filename = None
            st.session_state.diagnostico_enviado_sucesso = False # Limpa o flag

        # ... (Lógica para listar diagnósticos anteriores, com botão de download para cada um)
        # O download de PDF para diagnósticos anteriores deve chamar gerar_pdf_diagnostico_completo
        # passando analises_df=carregar_analises_perguntas()
        try:
            df_antigos = pd.read_csv(arquivo_csv, dtype={'CNPJ': str}, encoding='utf-8')
            df_cliente_diags = df_antigos[df_antigos["CNPJ"] == st.session_state.cnpj]
            if df_cliente_diags.empty: st.info("Nenhum diagnóstico anterior.")
            else:
                df_cliente_diags = df_cliente_diags.sort_values(by="Data", ascending=False)
                perguntas_df_pdf = pd.read_csv(perguntas_csv, encoding='utf-8')
                analises_df_pdf = carregar_analises_perguntas()

                for idx, row in df_cliente_diags.iterrows():
                    with st.expander(f"📅 {row['Data']} - {row['Empresa']}"):
                        # ... (exibir métricas e outras infos do 'row') ...
                        if st.button("📄 Baixar PDF", key=f"dl_pdf_antigo_{idx}"):
                            # Recalcular medias_cat para o PDF se não estiverem como dict no CSV
                            medias_cat_pdf = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in row.items() if "Media_Cat_" in k and pd.notna(v)}
                            pdf_path = gerar_pdf_diagnostico_completo(row.to_dict(), st.session_state.user, perguntas_df_pdf, row.to_dict(), medias_cat_pdf, analises_df_pdf)
                            if pdf_path:
                                with open(pdf_path, "rb") as f:
                                    st.download_button("Download Confirmado", f, file_name=f"diag_{row['Empresa']}_{row['Data']}.pdf", mime="application/pdf", key=f"dl_confirm_antigo_{idx}")
                                registrar_acao(st.session_state.cnpj, "Download PDF (Painel)", f"Baixou PDF de {row['Data']}")
                            else: st.error("Erro ao gerar PDF.")
                        st.markdown("---")
            # ... (Kanban, Comparativos, etc. do Painel Principal)
        except Exception as e: st.error(f"Erro no painel principal: {e}")


    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader("📋 Formulário de Novo Diagnóstico")

        if not st.session_state.user.get("PodeFazerNovoDiagnostico", False): # Recheca a permissão
            st.warning("Você já enviou seu diagnóstico ou não tem permissão para um novo. Para realizar um novo, por favor, entre em contato com o administrador para liberação.")
            if st.button("Voltar ao Painel Principal", key="voltar_painel_novo_diag_bloq"): st.session_state.cliente_page = "Painel Principal"; st.rerun()
            st.stop()
        
        if st.session_state.diagnostico_enviado_sucesso: # Se acabou de enviar e voltou aqui por engano
            st.success("🎯 Seu último diagnóstico foi enviado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf:
                    st.download_button(label="📄 Baixar PDF do Diagnóstico Enviado", data=f_pdf,
                                       file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                       key="dl_novo_diag_aqui_mesmo")
            if st.button("Ir para o Painel Principal", key="ir_painel_apos_envio_sucesso"): st.session_state.cliente_page = "Painel Principal"; st.rerun()
            st.stop()


        try: perguntas_df_formulario = pd.read_csv(perguntas_csv, encoding='utf-8')
        except Exception as e: st.error(f"Erro ao carregar perguntas: {e}"); st.stop()
        if perguntas_df_formulario.empty: st.warning("Nenhuma pergunta cadastrada."); st.stop()

        total_perguntas_form = len(perguntas_df_formulario)
        st.session_state.progresso_diagnostico_contagem = (st.session_state.progresso_diagnostico_contagem[0], total_perguntas_form) # Atualiza total

        progresso_ph = st.empty() # Placeholder para barra de progresso

        def calcular_e_mostrar_progresso():
            respondidas = 0
            total_q = st.session_state.progresso_diagnostico_contagem[1]
            for _, p_row_prog in perguntas_df_formulario.iterrows():
                p_texto_prog = p_row_prog["Pergunta"]
                resp_prog = st.session_state.respostas_atuais_diagnostico.get(p_texto_prog)
                if resp_prog is not None:
                    if "[Matriz GUT]" in p_texto_prog:
                        if isinstance(resp_prog, dict) and (int(resp_prog.get("G",0)) > 0 or int(resp_prog.get("U",0)) > 0 or int(resp_prog.get("T",0)) > 0): respondidas +=1
                    elif "Escala" in p_texto_prog:
                        if resp_prog != "Selecione": respondidas +=1
                    elif isinstance(resp_prog, str) and resp_prog.strip(): respondidas +=1
                    elif isinstance(resp_prog, (int,float)) and resp_prog != 0 : respondidas +=1
            
            st.session_state.progresso_diagnostico_contagem = (respondidas, total_q)
            st.session_state.progresso_diagnostico_percentual = round((respondidas / total_q) * 100) if total_q > 0 else 0
            progresso_ph.info(f"📊 Progresso: {respondidas} de {total_q} respondidas ({st.session_state.progresso_diagnostico_percentual}%)")

        def on_change_resposta(pergunta_txt_key, widget_st_key, tipo_pergunta_onchange):
            valor_widget = st.session_state.get(widget_st_key)
            if tipo_pergunta_onchange == "GUT_G":
                current_gut = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key, {})
                current_gut["G"] = valor_widget
                st.session_state.respostas_atuais_diagnostico[pergunta_txt_key] = current_gut
            elif tipo_pergunta_onchange == "GUT_U":
                current_gut = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key, {})
                current_gut["U"] = valor_widget
                st.session_state.respostas_atuais_diagnostico[pergunta_txt_key] = current_gut
            elif tipo_pergunta_onchange == "GUT_T":
                current_gut = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key, {})
                current_gut["T"] = valor_widget
                st.session_state.respostas_atuais_diagnostico[pergunta_txt_key] = current_gut
            else: # Para outros tipos
                st.session_state.respostas_atuais_diagnostico[pergunta_txt_key] = valor_widget
            
            st.session_state.feedbacks_respostas[pergunta_txt_key] = "Resposta registrada ✓"
            calcular_e_mostrar_progresso()
            # O st.rerun() implícito do on_change vai redesenhar o feedback.
            # Para limpar o feedback, pode-se usar um timer ou limpar na próxima interação.

        calcular_e_mostrar_progresso() # Mostrar progresso inicial

        for categoria in perguntas_df_formulario["Categoria"].unique():
            st.markdown(f"#### Categoria: {categoria}")
            perg_cat_df = perguntas_df_formulario[perguntas_df_formulario["Categoria"] == categoria]
            for idx, row_q in perg_cat_df.iterrows():
                p_texto = str(row_q["Pergunta"])
                # Chave única para widget baseada no ID do formulário atual e índice da pergunta
                w_key = f"q_{st.session_state.id_formulario_atual}_{idx}" 
                
                feedback_ph = st.empty() # Placeholder para feedback ao lado da pergunta

                if "[Matriz GUT]" in p_texto:
                    st.markdown(f"**{p_texto.replace(' [Matriz GUT]', '')}**")
                    cols_gut_w = st.columns(3)
                    gut_vals = st.session_state.respostas_atuais_diagnostico.get(p_texto, {"G":0,"U":0,"T":0})
                    key_g = f"{w_key}_G"; key_u = f"{w_key}_U"; key_t = f"{w_key}_T"
                    
                    cols_gut_w[0].slider("Gravidade (0-5)",0,5,value=int(gut_vals.get("G",0)), key=key_g, on_change=on_change_resposta, args=(p_texto, key_g, "GUT_G"))
                    cols_gut_w[1].slider("Urgência (0-5)",0,5,value=int(gut_vals.get("U",0)), key=key_u, on_change=on_change_resposta, args=(p_texto, key_u, "GUT_U"))
                    cols_gut_w[2].slider("Tendência (0-5)",0,5,value=int(gut_vals.get("T",0)), key=key_t, on_change=on_change_resposta, args=(p_texto, key_t, "GUT_T"))
                elif "Pontuação (0-5)" in p_texto:
                    st.slider(p_texto,0,5,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto,0)), key=w_key, on_change=on_change_resposta, args=(p_texto, w_key, "Slider05"))
                elif "Pontuação (0-10)" in p_texto:
                    st.slider(p_texto,0,10,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto,0)), key=w_key, on_change=on_change_resposta, args=(p_texto, w_key, "Slider010"))
                elif "Texto Aberto" in p_texto:
                    st.text_area(p_texto,value=str(st.session_state.respostas_atuais_diagnostico.get(p_texto,"")), key=w_key, on_change=on_change_resposta, args=(p_texto, w_key, "Texto"))
                elif "Escala" in p_texto:
                    opts = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]
                    curr_val = st.session_state.respostas_atuais_diagnostico.get(p_texto, "Selecione")
                    st.selectbox(p_texto, opts, index=opts.index(curr_val) if curr_val in opts else 0, key=w_key, on_change=on_change_resposta, args=(p_texto, w_key, "Escala"))
                else: # Default
                    st.slider(p_texto,0,10,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto,0)), key=w_key, on_change=on_change_resposta, args=(p_texto, w_key, "SliderDefault"))

                if st.session_state.feedbacks_respostas.get(p_texto):
                    feedback_ph.caption(f'<p class="feedback-saved">{st.session_state.feedbacks_respostas[p_texto]}</p>', unsafe_allow_html=True)
                    # Limpar feedback (opcional, pode ser com um timer ou na próxima ação)
                    # del st.session_state.feedbacks_respostas[p_texto] # Se quiser que suma após 1 redraw
                st.divider()
        
        # Campos de observação e resumo
        key_obs_cli = f"obs_cli_diag_{st.session_state.id_formulario_atual}"
        st.text_area("Sua Análise/Observações (opcional):", value=st.session_state.respostas_atuais_diagnostico.get("__obs_cliente__", ""), 
                     key=key_obs_cli, on_change=on_change_resposta, args=("__obs_cliente__", key_obs_cli, "ObsCliente"))
        
        key_res_cli = f"diag_resumo_diag_{st.session_state.id_formulario_atual}"
        st.text_area("✍️ Resumo/principais insights (para PDF):", value=st.session_state.respostas_atuais_diagnostico.get("__resumo_cliente__", ""), 
                     key=key_res_cli, on_change=on_change_resposta, args=("__resumo_cliente__", key_res_cli, "ResumoCliente"))

        if st.button("✔️ Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v2"):
            respostas_finais_envio = st.session_state.respostas_atuais_diagnostico
            cont_resp, total_para_resp = st.session_state.progresso_diagnostico_contagem
            
            if cont_resp < total_para_resp:
                st.warning("Por favor, responda todas as perguntas para um diagnóstico completo.")
            elif not respostas_finais_envio.get("__resumo_cliente__","").strip():
                st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
            else:
                # ... (Lógica de processamento e salvamento do diagnóstico - similar à anterior, mas usando respostas_finais_envio)
                # Certifique-se que `nova_linha_diag` é criada corretamente.
                # ... (Cálculo de médias, GUT Média, Médias por Categoria) ...
                soma_gut, count_gut = 0,0
                respostas_csv = {}
                for p,r in respostas_finais_envio.items():
                    if p.startswith("__"): continue
                    if "[Matriz GUT]" in p and isinstance(r, dict):
                        respostas_csv[p] = json.dumps(r)
                        g,u,t = int(r.get("G",0)), int(r.get("U",0)), int(r.get("T",0))
                        soma_gut += (g*u*t); count_gut +=1
                    else: respostas_csv[p] = r
                gut_media = round(soma_gut/count_gut,2) if count_gut > 0 else 0.0
                
                num_resp = [v for k,v in respostas_finais_envio.items() if not k.startswith("__") and isinstance(v,(int,float)) and ("[Matriz GUT]" not in k) and ("Pontuação" in k)]
                media_geral = round(sum(num_resp)/len(num_resp),2) if num_resp else 0.0
                
                emp_nome = st.session_state.user.get("Empresa","N/D")
                nova_linha_diag_final = {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": st.session_state.cnpj,
                    "Nome": st.session_state.user.get("NomeContato", st.session_state.user.get("CNPJ", "")), "Email": "", 
                    "Empresa": emp_nome, "Média Geral": media_geral, "GUT Média": gut_media,
                    "Observações": "", "Análise do Cliente": respostas_finais_envio.get("__obs_cliente__",""),
                    "Diagnóstico": respostas_finais_envio.get("__resumo_cliente__",""), "Comentarios_Admin": ""
                }
                nova_linha_diag_final.update(respostas_csv)
                
                medias_cat_final = {} # Recalcular
                for cat_iter in perguntas_df_formulario["Categoria"].unique():
                    soma_c, cont_c = 0,0
                    for _,pr in perguntas_df_formulario[perguntas_df_formulario["Categoria"]==cat_iter].iterrows():
                        pt = pr["Pergunta"]; rv = respostas_finais_envio.get(pt)
                        if isinstance(rv,(int,float)) and ("[Matriz GUT]" not in pt) and ("Pontuação" in pt): soma_c+=rv; cont_c+=1
                    mc = round(soma_c/cont_c,2) if cont_c>0 else 0.0
                    nova_linha_diag_final[f"Media_Cat_{sanitize_column_name(cat_iter)}"] = mc
                    medias_cat_final[cat_iter] = mc
                
                # Salvar no CSV
                try: df_todos_diags = pd.read_csv(arquivo_csv, encoding='utf-8')
                except (FileNotFoundError, pd.errors.EmptyDataError): df_todos_diags = pd.DataFrame()
                for col_n in nova_linha_diag_final.keys():
                    if col_n not in df_todos_diags.columns: df_todos_diags[col_n] = pd.NA
                df_todos_diags = pd.concat([df_todos_diags, pd.DataFrame([nova_linha_diag_final])], ignore_index=True)
                df_todos_diags.to_csv(arquivo_csv, index=False, encoding='utf-8')

                update_user_data(st.session_state.cnpj, "PodeFazerNovoDiagnostico", False) # Bloqueia novo
                registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", "Cliente enviou novo diagnóstico.")

                analises_df_para_pdf = carregar_analises_perguntas()
                pdf_path_gerado = gerar_pdf_diagnostico_completo(
                    nova_linha_diag_final, st.session_state.user, perguntas_df_formulario, 
                    respostas_finais_envio, medias_cat_final, analises_df_para_pdf
                )

                st.session_state.diagnostico_enviado_sucesso = True
                if pdf_path_gerado:
                    st.session_state.pdf_gerado_path = pdf_path_gerado
                    st.session_state.pdf_gerado_filename = f"diagnostico_{sanitize_column_name(emp_nome)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    
                    st.success("Diagnóstico enviado com sucesso!")
                    with open(pdf_path_gerado, "rb") as f_pdf_dl:
                        st.download_button(label="📄 Baixar PDF do Diagnóstico Enviado", data=f_pdf_dl,
                                           file_name=st.session_state.pdf_gerado_filename,
                                           mime="application/pdf", key="dl_pdf_apos_envio_final")
                    registrar_acao(st.session_state.cnpj, "Download PDF", "Baixou PDF (após envio).")
                else:
                    st.error("Diagnóstico salvo, mas houve um erro ao gerar o PDF.")
                
                # Limpa estado para próxima vez que a página for acessada (se for liberado novo)
                st.session_state.respostas_atuais_diagnostico = {}
                st.session_state.progresso_diagnostico_percentual = 0
                st.session_state.progresso_diagnostico_contagem = (0,0)
                st.session_state.feedbacks_respostas = {}
                
                if st.button("Ir para o Painel Principal", key="ir_painel_final"):
                    st.session_state.cliente_page = "Painel Principal"; st.rerun()


# --- ÁREA DO ADMINISTRADOR LOGADO --- (A lógica do admin para as outras seções é extensa e foi omitida por brevidade,
# mas a nova seção "Gerenciar Análises de Perguntas" e a chamada correta de `gerar_pdf_diagnostico_completo`
# com o parâmetro `analises_df_pdf_param` devem ser consideradas.)

if aba == "Administrador" and st.session_state.admin_logado:
    st.sidebar.image("https_url_da_sua_logo_admin.png", width=100) # Substitua pela URL da sua logo
    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("🚪 Sair do Painel Admin", key="logout_admin_v6"):
        st.session_state.admin_logado = False; st.rerun()

    menu_admin_options = ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Perguntas", 
                          "Gerenciar Análises de Perguntas", "Gerenciar Clientes", "Gerenciar Administradores"]
    menu_admin = st.sidebar.selectbox("Funcionalidades Admin:", menu_admin_options, key="admin_menu_selectbox_v6")
    st.header(f"🔑 Painel Admin: {menu_admin}")

    if menu_admin == "Gerenciar Análises de Perguntas":
        st.subheader("💡 Gerenciar Análises Vinculadas às Perguntas")
        df_analises_existentes = carregar_analises_perguntas()
        try: df_perguntas_formulario = pd.read_csv(perguntas_csv, encoding='utf-8')
        except: df_perguntas_formulario = pd.DataFrame(columns=colunas_base_perguntas)


        st.markdown("#### Adicionar Nova Análise")
        if df_perguntas_formulario.empty:
            st.warning("Nenhuma pergunta cadastrada no formulário. Adicione perguntas primeiro em 'Gerenciar Perguntas'.")
        else:
            lista_perguntas_txt = [""] + df_perguntas_formulario["Pergunta"].unique().tolist()
            pergunta_selecionada_analise = st.selectbox("Selecione a Pergunta para adicionar análise:", lista_perguntas_txt, key="sel_perg_analise_v2")

            if pergunta_selecionada_analise:
                st.caption(f"Pergunta selecionada: {pergunta_selecionada_analise}")
                
                tipo_condicao_analise_display = st.selectbox("Tipo de Condição para a Análise:", 
                                                     ["Faixa Numérica (p/ Pontuação 0-X)", 
                                                      "Valor Exato (p/ Escala)", 
                                                      "Faixa de Score (p/ Matriz GUT)", 
                                                      "Análise Padrão (default para a pergunta)"], 
                                                     key="tipo_cond_analise_v2")
                
                map_tipo_cond_to_csv = {
                    "Faixa Numérica (p/ Pontuação 0-X)": "FaixaNumerica", 
                    "Valor Exato (p/ Escala)": "ValorExatoEscala", 
                    "Faixa de Score (p/ Matriz GUT)": "ScoreGUT", 
                    "Análise Padrão (default para a pergunta)": "Default"
                }
                tipo_condicao_csv_val = map_tipo_cond_to_csv[tipo_condicao_analise_display]

                cond_val_min_ui, cond_val_max_ui, cond_val_exato_ui = None, None, None
                if tipo_condicao_csv_val == "FaixaNumerica":
                    cols_faixa_ui = st.columns(2)
                    cond_val_min_ui = cols_faixa_ui[0].number_input("Valor Mínimo da Faixa", step=1.0, format="%.2f", key="cond_min_analise_v2")
                    cond_val_max_ui = cols_faixa_ui[1].number_input("Valor Máximo da Faixa", step=1.0, format="%.2f", key="cond_max_analise_v2")
                elif tipo_condicao_csv_val == "ValorExatoEscala":
                    cond_val_exato_ui = st.text_input("Valor Exato da Escala (ex: Baixo, Médio, Alto)", key="cond_exato_analise_v2")
                elif tipo_condicao_csv_val == "ScoreGUT":
                    cols_faixa_gut_ui = st.columns(2)
                    cond_val_min_ui = cols_faixa_gut_ui[0].number_input("Score GUT Mínimo", step=1, key="cond_min_gut_analise_v2")
                    cond_val_max_ui = cols_faixa_gut_ui[1].number_input("Score GUT Máximo (opcional, deixe 0 se for 'acima de Mínimo')", step=1, key="cond_max_gut_analise_v2", value=0)

                texto_analise_nova_ui = st.text_area("Texto da Análise:", height=150, key="txt_analise_nova_v2")

                if st.button("💾 Salvar Nova Análise", key="salvar_analise_pergunta_v2"):
                    if texto_analise_nova_ui.strip():
                        nova_id_analise = str(uuid.uuid4())
                        nova_entrada_analise = {
                            "ID_Analise": nova_id_analise, 
                            "TextoPerguntaOriginal": pergunta_selecionada_analise,
                            "TipoCondicao": tipo_condicao_csv_val,
                            "CondicaoValorMin": cond_val_min_ui if cond_val_min_ui is not None else pd.NA,
                            "CondicaoValorMax": cond_val_max_ui if cond_val_max_ui is not None and cond_val_max_ui !=0 else pd.NA,
                            "CondicaoValorExato": cond_val_exato_ui if cond_val_exato_ui else pd.NA,
                            "TextoAnalise": texto_analise_nova_ui
                        }
                        df_analises_existentes = pd.concat([df_analises_existentes, pd.DataFrame([nova_entrada_analise])], ignore_index=True)
                        df_analises_existentes.to_csv(analises_perguntas_csv, index=False, encoding='utf-8')
                        st.success("Nova análise salva!"); st.rerun()
                    else: st.error("O texto da análise não pode estar vazio.")
        
        st.markdown("---"); st.subheader("📜 Análises Cadastradas")
        if df_analises_existentes.empty: st.info("Nenhuma análise cadastrada.")
        else:
            st.dataframe(df_analises_existentes)
            analise_del_id = st.selectbox("Deletar Análise por ID:", [""] + df_analises_existentes["ID_Analise"].tolist(), key="del_analise_id_v2")
            if st.button("🗑️ Deletar Análise", key="btn_del_analise_v2") and analise_del_id:
                df_analises_existentes = df_analises_existentes[df_analises_existentes["ID_Analise"] != analise_del_id]
                df_analises_existentes.to_csv(analises_perguntas_csv, index=False, encoding='utf-8')
                st.warning("Análise deletada."); st.rerun()

    # Inclua aqui as outras seções do Admin (Visão Geral, Histórico, Gerenciar Perguntas, Clientes, Administradores)
    # Adaptando a chamada de `gerar_pdf_diagnostico_completo` na "Visão Geral" para incluir
    # `analises_df_pdf_param=carregar_analises_perguntas()` quando o admin baixar um PDF.
    # Exemplo dentro da lógica de download de PDF na Visão Geral do Admin:
    # if menu_admin == "Visão Geral e Diagnósticos":
    #     ...
    #     if st.button("📄 Baixar PDF deste Diagnóstico", key=f"download_pdf_admin_vX_{index_diag}"):
    #         df_analises_para_pdf_admin = carregar_analises_perguntas()
    #         pdf_path_admin = gerar_pdf_diagnostico_completo(
    #             diagnostico_selecionado_admin_row_vg.to_dict(),
    #             usuario_data_pdf_adm_vg,
    #             perguntas_df_pdf_adm_vg,
    #             diagnostico_selecionado_admin_row_vg.to_dict(), # Respostas já estão no row
    #             medias_cat_pdf_adm_vg,
    #             analises_df_pdf_param=df_analises_para_pdf_admin # << IMPORTANTE
    #         )
    #         ... (restante da lógica de download)

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()