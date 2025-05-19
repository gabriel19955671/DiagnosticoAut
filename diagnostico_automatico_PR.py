import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
from fpdf import FPDF
import tempfile
import re 
import json
import plotly.express as px # Importar Plotly Express

st.set_page_config(page_title="Portal de Diagnóstico", layout="wide") # Mudei para layout="wide" para melhor visualização

# CSS (sem alterações)
st.markdown("""
<style>
/* ... Seu CSS anterior aqui ... */
.login-container {
    max-width: 400px;
    margin: 60px auto 0 auto;
    padding: 40px;
    border-radius: 8px;
    background-color: #ffffff;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    font-family: 'Segoe UI', sans-serif;
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
    padding: 0.5rem 1.2rem;
    margin-top: 0.5rem;
}
.stDownloadButton>button {
    background-color: #10b981;
    color: white;
    font-weight: 600;
    border-radius: 6px;
    margin-top: 10px;
    padding: 0.5rem 1.2rem;
}
.stTextInput>div>input, .stTextArea>div>textarea {
    border-radius: 6px;
    padding: 0.4rem;
    border: 1px solid #d1d5db;
    background-color: #f9fafb;
}
.stTabs [data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 600;
    padding: 10px 20px;
}
/* Adicionar um pouco de estilo para cards (opcional) */
.custom-card {
    border: 1px solid #e0e0e0;
    border-left: 5px solid #2563eb; /* Cor da borda esquerda */
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 5px;
    background-color: #f9f9f9;
}
.custom-card h4 {
    margin-top: 0;
    color: #2563eb;
}
</style>
""", unsafe_allow_html=True)

st.title("🔒 Portal de Diagnóstico")

# --- Configuração de Arquivos e Variáveis Globais ---
admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv" # Adicionar NomeContato, Telefone
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv" 
historico_csv = "historico_clientes.csv"

# --- Inicialização do Session State ---
if "admin_logado" not in st.session_state: st.session_state.admin_logado = False
# ... (outras inicializações do session_state como antes) ...
if "cliente_logado" not in st.session_state: st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state: st.session_state.diagnostico_enviado = False
if "inicio_sessao_cliente" not in st.session_state: st.session_state.inicio_sessao_cliente = None
if "cliente_page" not in st.session_state: st.session_state.cliente_page = "Painel Principal"
if "cnpj" not in st.session_state: st.session_state.cnpj = None
if "user" not in st.session_state: st.session_state.user = None
DIAGNOSTICO_FORM_ID_KEY = f"form_id_diagnostico_cliente_{st.session_state.get('cnpj', 'default_user')}"


# --- Funções Utilitárias ---
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s) 
    return s

def pdf_safe_text_output(text): # Renomeada para clareza
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# --- Criação e Verificação de Arquivos ---
colunas_base_diagnosticos = [
    "Data", "CNPJ", "Nome", "Email", "Empresa",
    "Média Geral", "GUT Média", "Observações", "Diagnóstico", 
    "Análise do Cliente", "Comentarios_Admin"
]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone"] # Novas colunas

for arquivo, colunas_base_f in [ # Renomeado colunas_base
    (usuarios_bloqueados_csv, ["CNPJ"]),
    (admin_credenciais_csv, ["Usuario", "Senha"]),
    (usuarios_csv, colunas_base_usuarios), # Usando novas colunas
    (perguntas_csv, ["Pergunta", "Categoria"]), 
    (historico_csv, ["Data", "CNPJ", "Ação", "Descrição"]),
    (arquivo_csv, colunas_base_diagnosticos) 
]:
    if not os.path.exists(arquivo):
        pd.DataFrame(columns=colunas_base_f).to_csv(arquivo, index=False, encoding='utf-8')
    else: 
        try:
            df_temp_check = pd.read_csv(arquivo, encoding='utf-8')
            missing_cols_check = False
            for col_check in colunas_base_f:
                if col_check not in df_temp_check.columns:
                    df_temp_check[col_check] = pd.NA 
                    missing_cols_check = True
            if missing_cols_check:
                df_temp_check.to_csv(arquivo, index=False, encoding='utf-8')
        except pd.errors.EmptyDataError:
             pd.DataFrame(columns=colunas_base_f).to_csv(arquivo, index=False, encoding='utf-8')
        except Exception as e: st.error(f"Erro ao verificar/criar {arquivo}: {e}")

def registrar_acao(cnpj, acao, descricao):
    # ... (código mantido)
    try:
        historico_df_ra = pd.read_csv(historico_csv, encoding='utf-8') # Renomeado para evitar conflito
    except FileNotFoundError: historico_df_ra = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data_ra = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }
    historico_df_ra = pd.concat([historico_df_ra, pd.DataFrame([nova_data_ra])], ignore_index=True)
    historico_df_ra.to_csv(historico_csv, index=False, encoding='utf-8')

# --- Função Refatorada de Geração de PDF ---
def gerar_pdf_diagnostico_completo(diagnostico_data, usuario_data, perguntas_df_geracao, respostas_coletadas_geracao, medias_categorias_geracao):
    pdf = FPDF()
    pdf.add_page()
    empresa_nome_pdf = usuario_data.get("Empresa", "N/D")
    cnpj_pdf = usuario_data.get("CNPJ", "N/D")
    nome_contato_pdf = usuario_data.get("NomeContato", "")
    telefone_pdf = usuario_data.get("Telefone", "")

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome_pdf}"), 0, 1, 'C')
    pdf.ln(5)

    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 7, pdf_safe_text_output(f"Data do Diagnóstico: {diagnostico_data.get('Data','N/D')}"))
    pdf.multi_cell(0, 7, pdf_safe_text_output(f"Empresa: {empresa_nome_pdf} (CNPJ: {cnpj_pdf})"))
    if nome_contato_pdf: pdf.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {nome_contato_pdf}"))
    if telefone_pdf: pdf.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {telefone_pdf}"))
    pdf.ln(3)

    pdf.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral (Numérica): {diagnostico_data.get('Média Geral','N/A')}"))
    pdf.multi_cell(0, 7, pdf_safe_text_output(f"Média Scores GUT (G*U*T): {diagnostico_data.get('GUT Média','N/A')}"))
    pdf.ln(3)

    if medias_categorias_geracao:
        pdf.set_font("Arial", 'B', 11); pdf.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria (Perguntas de Pontuação):"))
        pdf.set_font("Arial", size=10)
        for cat_pdf_g, media_cat_pdf_g in medias_categorias_geracao.items():
            pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat_pdf_g}: {media_cat_pdf_g}"))
        pdf.ln(5)

    resumo_cliente_pdf = diagnostico_data.get("Diagnóstico", "") # Campo "Diagnóstico" é o resumo do cliente
    analise_cliente_pdf = diagnostico_data.get("Análise do Cliente", "") # Campo separado para análise
    
    if resumo_cliente_pdf:
        pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output("Resumo do Diagnóstico (Cliente):"))
        pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(resumo_cliente_pdf)); pdf.ln(3)
    if analise_cliente_pdf:
        pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output("Análise/Observações do Cliente:"))
        pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(analise_cliente_pdf)); pdf.ln(3)

    comentarios_admin_pdf = diagnostico_data.get("Comentarios_Admin", "")
    if comentarios_admin_pdf:
        pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output("Comentários do Consultor:"))
        pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(comentarios_admin_pdf)); pdf.ln(3)
        
    pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas por Categoria:"))
    categorias_unicas_pdf_ger = perguntas_df_geracao["Categoria"].unique()
    for categoria_pdf_g_det in categorias_unicas_pdf_ger:
        pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria_pdf_g_det}"))
        pdf.set_font("Arial", size=9)
        perguntas_cat_pdf_g_det = perguntas_df_geracao[perguntas_df_geracao["Categoria"] == categoria_pdf_g_det]
        for _, p_row_pdf_g_det in perguntas_cat_pdf_g_det.iterrows():
            txt_p_pdf_g_det = p_row_pdf_g_det["Pergunta"]
            # Acessar a resposta correta: pode estar em respostas_coletadas_geracao (se for do form atual)
            # ou diretamente em diagnostico_data (se for um diagnóstico antigo)
            resp_p_pdf_g_det = respostas_coletadas_geracao.get(txt_p_pdf_g_det)
            if resp_p_pdf_g_det is None: # Se não estiver nas respostas coletadas (ex: admin baixando PDF antigo)
                resp_p_pdf_g_det = diagnostico_data.get(txt_p_pdf_g_det, "N/R")


            if "[Matriz GUT]" in txt_p_pdf_g_det:
                g_pdf, u_pdf, t_pdf = 0,0,0
                score_gut_item_pdf = 0
                if isinstance(resp_p_pdf_g_det, dict): # Se já for dict (do formulário atual)
                    g_pdf,u_pdf,t_pdf = resp_p_pdf_g_det.get("G",0), resp_p_pdf_g_det.get("U",0), resp_p_pdf_g_det.get("T",0)
                elif isinstance(resp_p_pdf_g_det, str): # Se for string JSON (de um diagnóstico salvo)
                    try: 
                        gut_data_pdf = json.loads(resp_p_pdf_g_det.replace("'", "\""))
                        g_pdf,u_pdf,t_pdf = gut_data_pdf.get("G",0), gut_data_pdf.get("U",0), gut_data_pdf.get("T",0)
                    except: pass # Deixa g,u,t como 0 se não conseguir parsear
                score_gut_item_pdf = g_pdf*u_pdf*t_pdf
                pdf.multi_cell(0,6,pdf_safe_text_output(f"  - {txt_p_pdf_g_det.replace(' [Matriz GUT]','')}: G={g_pdf}, U={u_pdf}, T={t_pdf} (Score: {score_gut_item_pdf})"))
            elif isinstance(resp_p_pdf_g_det, (int, float, str)): 
                pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {txt_p_pdf_g_det}: {resp_p_pdf_g_det}"))
        pdf.ln(2)
    pdf.ln(3)
    
    pdf.add_page(); pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf.ln(5)
    pdf.set_font("Arial", size=10)
    gut_cards_pdf_ger = []
    for pergunta_pdf_k_g, resp_pdf_k_g_val in respostas_coletadas_geracao.items(): # Usa respostas_coletadas (ou adaptado para dados salvos)
        if "[Matriz GUT]" in pergunta_pdf_k_g:
            g_k_g, u_k_g, t_k_g = 0,0,0
            if isinstance(resp_pdf_k_g_val, dict):
                g_k_g, u_k_g, t_k_g = resp_pdf_k_g_val.get("G",0), resp_pdf_k_g_val.get("U",0), resp_pdf_k_g_val.get("T",0)
            elif isinstance(resp_pdf_k_g_val, str): # Se for string JSON
                try: 
                    gut_data_k_g = json.loads(resp_pdf_k_g_val.replace("'", "\""))
                    g_k_g,u_k_g,t_k_g = gut_data_k_g.get("G",0), gut_data_k_g.get("U",0), gut_data_k_g.get("T",0)
                except: pass
            
            score_gut_total_k_g_pdf = g_k_g * u_k_g * t_k_g
            prazo_k_g_pdf = "N/A"
            if score_gut_total_k_g_pdf >= 75: prazo_k_g_pdf = "15 dias"
            elif score_gut_total_k_g_pdf >= 40: prazo_k_g_pdf = "30 dias"
            elif score_gut_total_k_g_pdf >= 20: prazo_k_g_pdf = "45 dias"
            elif score_gut_total_k_g_pdf > 0: prazo_k_g_pdf = "60 dias"
            else: continue
            if prazo_k_g_pdf != "N/A":
                gut_cards_pdf_ger.append({"Tarefa": pergunta_pdf_k_g.replace(" [Matriz GUT]", ""),"Prazo": prazo_k_g_pdf, "Score": score_gut_total_k_g_pdf})
    if gut_cards_pdf_ger:
        gut_cards_pdf_ger_sorted = sorted(gut_cards_pdf_ger, key=lambda x_f_k_g_pdf: (int(x_f_k_g_pdf["Prazo"].split(" ")[0]), -x_f_k_g_pdf["Score"]))
        for card_item_f_k_g_pdf in gut_cards_pdf_ger_sorted:
             pdf.multi_cell(0, 6, pdf_safe_text_output(f"Prazo: {card_item_f_k_g_pdf['Prazo']} - Tarefa: {card_item_f_k_g_pdf['Tarefa']} (Score GUT: {card_item_f_k_g_pdf['Score']})"))
    else: pdf.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_g:
        pdf_path_g = tmpfile_g.name
        pdf.output(pdf_path_g)
    return pdf_path_g


# --- Lógica de Login e Navegação Principal (Admin/Cliente) ---
# ... (código de login admin e cliente mantido como antes) ...
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True)
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login"): # Chave única
        usuario_admin_li = st.text_input("Usuário", key="admin_user_li") 
        senha_admin_li = st.text_input("Senha", type="password", key="admin_pass_li")
        entrar_admin_li = st.form_submit_button("Entrar")
    if entrar_admin_li:
        df_admin_li_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
        if not df_admin_li_creds[(df_admin_li_creds["Usuario"] == usuario_admin_li) & (df_admin_li_creds["Senha"] == senha_admin_li)].empty:
            st.session_state.admin_logado = True; st.success("Login de administrador bem-sucedido!")
            st.session_state.trigger_admin_rerun = True; st.rerun() 
        else: st.error("Usuário ou senha inválidos.")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login"): # Chave única
        cnpj_cli_li = st.text_input("CNPJ", key="cli_cnpj_li") 
        senha_cli_li = st.text_input("Senha", type="password", key="cli_pass_li") 
        acessar_cli_li = st.form_submit_button("Entrar")
    if acessar_cli_li:
        # ... (lógica de login cliente como antes)
        if not os.path.exists(usuarios_csv): st.error("Base de usuários não encontrada."); st.stop()
        usuarios_li_df = pd.read_csv(usuarios_csv, encoding='utf-8')
        bloqueados_li_df = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
        if cnpj_cli_li in bloqueados_li_df["CNPJ"].astype(str).values: 
            st.error("CNPJ bloqueado."); st.stop()
        user_match_li = usuarios_li_df[(usuarios_li_df["CNPJ"].astype(str) == str(cnpj_cli_li)) & (usuarios_li_df["Senha"] == senha_cli_li)]
        if user_match_li.empty: st.error("CNPJ ou senha inválidos."); st.stop()
        st.session_state.cliente_logado = True
        st.session_state.cnpj = str(cnpj_cli_li) 
        st.session_state.user = user_match_li.iloc[0].to_dict() 
        st.session_state.inicio_sessao_cliente = time.time()
        registrar_acao(st.session_state.cnpj, "Login", "Usuário realizou login.")
        st.session_state.cliente_page = "Painel Principal"
        st.success("Login realizado com sucesso!"); st.session_state.trigger_cliente_rerun = True; st.rerun() 
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    # ... (código da área do cliente como na versão anterior, incluindo a nova lógica GUT no Kanban e no PDF gerado ao final do formulário)
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    st.session_state.cliente_page = st.sidebar.radio(
        "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
        index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page)
    )
    if st.sidebar.button("⬅️ Sair do Portal Cliente"):
        keys_to_del_cli_logout = ['cliente_logado', 'cnpj', 'user', 'inicio_sessao_cliente', 
                              'diagnostico_enviado', 'cliente_page', DIAGNOSTICO_FORM_ID_KEY, f"temp_respostas_{st.session_state.get(DIAGNOSTICO_FORM_ID_KEY,'')}"]
        for key_cd_lo in keys_to_del_cli_logout:
            if key_cd_lo in st.session_state: del st.session_state[key_cd_lo]
        st.rerun()

    if st.session_state.cliente_page == "Painel Principal":
        # ... (código como antes, mas o Kanban usará a nova lógica GUT)
        st.subheader("📌 Instruções Gerais")
        with st.expander("📖 Leia atentamente"): 
            st.markdown("- Responda com sinceridade.\n- Para novo diagnóstico, selecione no menu ao lado.")
        if st.session_state.get("diagnostico_enviado", False):
            st.success("🎯 Último diagnóstico enviado!"); st.session_state.diagnostico_enviado = False
        
        st.subheader("📁 Diagnósticos Anteriores")
        # ... (código como antes, mas a exibição do GUT Média agora reflete G*U*T)
        try:
            df_antigos_cli_pp = pd.read_csv(arquivo_csv, encoding='utf-8')
            df_cliente_view_pp = df_antigos_cli_pp[df_antigos_cli_pp["CNPJ"].astype(str) == st.session_state.cnpj]
        except FileNotFoundError: df_cliente_view_pp = pd.DataFrame()
        if df_cliente_view_pp.empty: st.info("Nenhum diagnóstico anterior.")
        else:
            # ... (loop e expander para cada diagnóstico como antes)
            # ... (Kanban e gráficos como antes, mas a lógica de GUT Média e GUT Score foi atualizada)
             df_cliente_view_pp = df_cliente_view_pp.sort_values(by="Data", ascending=False)
             for idx_cv_pp, row_cv_pp in df_cliente_view_pp.iterrows():
                with st.expander(f"📅 {row_cv_pp['Data']} - {row_cv_pp['Empresa']}"):
                    # ... (código de exibição do diagnóstico anterior)
                    pass # Código completo já fornecido anteriormente

            st.subheader("📌 Plano de Ação - Kanban (Último Diagnóstico)")
            # ... (código do Kanban do cliente, que agora usa G*U*T score)
            pass # Código completo já fornecido anteriormente
            st.subheader("📈 Comparativo de Evolução")
            # ... (código de gráficos de evolução)
            pass # Código completo já fornecido anteriormente

    elif st.session_state.cliente_page == "Novo Diagnóstico":
        # ... (código do formulário de Novo Diagnóstico como na versão anterior, com GUT G-U-T e chaves estáveis)
        st.subheader("📋 Formulário de Novo Diagnóstico")
        if DIAGNOSTICO_FORM_ID_KEY not in st.session_state:
            st.session_state[DIAGNOSTICO_FORM_ID_KEY] = datetime.now().strftime("%Y%m%d%H%M%S%f")
        form_id_sufixo_nd = st.session_state[DIAGNOSTICO_FORM_ID_KEY]
        temp_respostas_key_nd = f"temp_respostas_{form_id_sufixo_nd}"
        if temp_respostas_key_nd not in st.session_state: st.session_state[temp_respostas_key_nd] = {}
        
        respostas_form_coletadas_nd = st.session_state[temp_respostas_key_nd]
        # ... (Restante do código do formulário, incluindo o st.form e o botão de submit)
        # O código para gerar PDF já foi atualizado para usar a função `gerar_pdf_diagnostico_completo`
        # Ao final do envio:
        # del st.session_state[DIAGNOSTICO_FORM_ID_KEY]
        # del st.session_state[temp_respostas_key_nd]
        pass # Código completo já fornecido anteriormente

# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    st.sidebar.success("🟢 Admin Logado")
    if st.sidebar.button("🚪 Sair do Painel Admin"):
        st.session_state.admin_logado = False; st.rerun()

    menu_admin_main = st.sidebar.selectbox( # Chave única
        "Funcionalidades Admin:",
        ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Perguntas", 
         "Gerenciar Clientes", "Gerenciar Administradores"],
        key="admin_menu_selectbox_main_page" 
    )
    st.header(f"🔑 Painel Admin: {menu_admin_main}")

    if menu_admin_main == "Visão Geral e Diagnósticos": # Renomeado para mais clareza
        st.subheader("📊 Visão Geral dos Diagnósticos")
        
        try:
            diagnosticos_df_admin_geral = pd.read_csv(arquivo_csv, encoding='utf-8')
            if diagnosticos_df_admin_geral.empty:
                st.info("Nenhum diagnóstico no sistema para exibir visão geral."); st.stop()
        except FileNotFoundError:
            st.info("Arquivo de diagnósticos não encontrado."); st.stop()
        except pd.errors.EmptyDataError:
            st.info("Arquivo de diagnósticos está vazio."); st.stop()

        # Indicadores Gerais
        col_ig1, col_ig2, col_ig3 = st.columns(3)
        with col_ig1:
            st.metric("📦 Total de Diagnósticos", len(diagnosticos_df_admin_geral))
        with col_ig2:
            media_geral_todos_adm = pd.to_numeric(diagnosticos_df_admin_geral["Média Geral"], errors='coerce').mean()
            st.metric("📈 Média Geral (Todos)", f"{media_geral_todos_adm:.2f}" if pd.notna(media_geral_todos_adm) else "N/A")
        with col_ig3:
            if "GUT Média" in diagnosticos_df_admin_geral.columns: # GUT Média agora é média de G*U*T
                gut_media_todos_adm = pd.to_numeric(diagnosticos_df_admin_geral["GUT Média"], errors='coerce').mean()
                st.metric("🔥 GUT Média (Todos)", f"{gut_media_todos_adm:.2f}" if pd.notna(gut_media_todos_adm) else "N/A")
            else: st.metric("🔥 GUT Média (Todos)", "N/A")
        st.divider()

        # Evolução Mensal com Plotly
        st.subheader("📈 Evolução Mensal dos Diagnósticos (Agregado)")
        df_diag_vis_adm = diagnosticos_df_admin_geral.copy()
        df_diag_vis_adm["Data"] = pd.to_datetime(df_diag_vis_adm["Data"], errors="coerce")
        df_diag_vis_adm = df_diag_vis_adm.dropna(subset=["Data"])
        
        if not df_diag_vis_adm.empty:
            df_diag_vis_adm["Mês/Ano"] = df_diag_vis_adm["Data"].dt.to_period("M").astype(str) # Formato YYYY-MM para ordenação
            df_diag_vis_adm["Média Geral"] = pd.to_numeric(df_diag_vis_adm["Média Geral"], errors='coerce')
            df_diag_vis_adm["GUT Média"] = pd.to_numeric(df_diag_vis_adm.get("GUT Média"), errors='coerce') if "GUT Média" in df_diag_vis_adm else pd.Series(0, index=df_diag_vis_adm.index)

            resumo_mensal_adm = df_diag_vis_adm.groupby("Mês/Ano").agg(
                Diagnósticos_Realizados=("CNPJ", "count"), 
                Média_Geral_Mensal=("Média Geral", "mean"),
                GUT_Média_Mensal=("GUT Média", "mean")
            ).reset_index().sort_values("Mês/Ano")
            resumo_mensal_adm["Mês/Ano"] = pd.to_datetime(resumo_mensal_adm["Mês/Ano"]).dt.strftime('%b/%y')


            if not resumo_mensal_adm.empty:
                fig_contagem = px.bar(resumo_mensal_adm, x="Mês/Ano", y="Diagnósticos_Realizados", 
                                      title="Número de Diagnósticos por Mês", labels={'Diagnósticos_Realizados':'Total Diagnósticos'})
                st.plotly_chart(fig_contagem, use_container_width=True)

                fig_medias = px.line(resumo_mensal_adm, x="Mês/Ano", y=["Média_Geral_Mensal", "GUT_Média_Mensal"],
                                     title="Médias Gerais e GUT por Mês", labels={'value':'Média', 'variable':'Indicador'})
                fig_medias.update_traces(mode='lines+markers')
                st.plotly_chart(fig_medias, use_container_width=True)
            else: st.info("Sem dados suficientes para gráficos de evolução mensal.")
        else: st.info("Não há diagnósticos com datas válidas para mostrar a evolução mensal.")
        st.divider()
        
        # Ranking das Empresas (como antes)
        st.subheader("🏆 Ranking das Empresas (Baseado na Média Geral)")
        # ... (código do ranking como antes) ...

        st.divider()
        st.subheader("📂 Todos os Diagnósticos Enviados")
        st.dataframe(diagnosticos_df_admin_geral.sort_values(by="Data", ascending=False).reset_index(drop=True))
        csv_export_admin_geral = diagnosticos_df_admin_geral.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Exportar Todos (CSV)", csv_export_admin_geral, file_name="diagnosticos_completos.csv", mime="text/csv")
        
        st.divider()
        st.subheader("🔍 Detalhar, Comentar e Baixar PDF de Diagnóstico Específico")
        if "CNPJ" in diagnosticos_df_admin_geral.columns:
            empresas_unicas_adm = sorted(diagnosticos_df_admin_geral["Empresa"].astype(str).unique().tolist())
            empresa_selecionada_adm = st.selectbox("Selecione uma Empresa para detalhar:", ["Selecione..."] + empresas_unicas_adm, key="admin_empresa_filter_detail")

            if empresa_selecionada_adm != "Selecione...":
                diagnosticos_empresa_adm = diagnosticos_df_admin_geral[diagnosticos_df_admin_geral["Empresa"] == empresa_selecionada_adm].sort_values(by="Data", ascending=False)
                
                if not diagnosticos_empresa_adm.empty:
                    diagnostico_data_selecionada_adm = st.selectbox(
                        "Selecione a Data do Diagnóstico:", 
                        diagnosticos_empresa_adm["Data"].tolist(), 
                        key="admin_data_diagnostico_select"
                    )
                    diagnostico_selecionado_adm_row = diagnosticos_empresa_adm[diagnosticos_empresa_adm["Data"] == diagnostico_data_selecionada_adm].iloc[0]
                    
                    st.markdown(f"**Detalhes do Diagnóstico de {diagnostico_selecionado_adm_row['Data']} para {empresa_selecionada_adm}**")
                    # Exibir algumas informações chave
                    st.write(f"**Média Geral:** {diagnostico_selecionado_adm_row.get('Média Geral', 'N/A')} | **GUT Média (G*U*T):** {diagnostico_selecionado_adm_row.get('GUT Média', 'N/A')}")
                    st.write(f"**Resumo (Cliente):** {diagnostico_selecionado_adm_row.get('Diagnóstico', 'N/P')}")
                    st.write(f"**Análise do Cliente:** {diagnostico_selecionado_adm_row.get('Análise do Cliente', 'N/P')}")
                    
                    # Comentários do Admin
                    comentario_adm_atual_val = diagnostico_selecionado_adm_row.get("Comentarios_Admin", "")
                    if pd.isna(comentario_adm_atual_val): comentario_adm_atual_val = ""
                    
                    novo_comentario_adm_val = st.text_area(
                        "Comentários do Consultor/Admin:", 
                        value=comentario_adm_atual_val, 
                        key=f"admin_comment_detail_{diagnostico_selecionado_adm_row.name}" # Usa índice da linha original
                    )
                    if st.button("💾 Salvar Comentário do Admin", key=f"save_admin_comment_detail_{diagnostico_selecionado_adm_row.name}"):
                        df_diag_save_com_adm_det = pd.read_csv(arquivo_csv, encoding='utf-8')
                        df_diag_save_com_adm_det.loc[diagnostico_selecionado_adm_row.name, "Comentarios_Admin"] = novo_comentario_adm_val
                        df_diag_save_com_adm_det.to_csv(arquivo_csv, index=False, encoding='utf-8')
                        registrar_acao("ADMIN", "Comentário Admin", f"Admin comentou diag. de {diagnostico_selecionado_adm_row['Data']} para {empresa_selecionada_adm}")
                        st.success("Comentário salvo!"); st.rerun()

                    # Botão para baixar PDF
                    if st.button("📄 Baixar PDF deste Diagnóstico", key=f"download_pdf_admin_{diagnostico_selecionado_adm_row.name}"):
                        try:
                            perguntas_df_pdf_adm = pd.read_csv(perguntas_csv, encoding='utf-8')
                            if "Categoria" not in perguntas_df_pdf_adm.columns: perguntas_df_pdf_adm["Categoria"] = "Geral"
                        except: perguntas_df_pdf_adm = pd.DataFrame(columns=["Pergunta", "Categoria"])

                        # Preparar dados para a função de PDF
                        # respostas_coletadas para PDF: pegar da linha do diagnóstico (row_diagnostico_selecionado_adm)
                        respostas_para_pdf_adm = diagnostico_selecionado_adm_row.to_dict()
                        
                        # Calcular médias de categoria para este diagnóstico específico
                        medias_cat_pdf_adm = {}
                        if not perguntas_df_pdf_adm.empty:
                            cats_unicas_pdf_adm = perguntas_df_pdf_adm["Categoria"].unique()
                            for cat_pdf_adm_calc in cats_unicas_pdf_adm:
                                perguntas_cat_pdf_adm_df = perguntas_df_pdf_adm[perguntas_df_pdf_adm["Categoria"] == cat_pdf_adm_calc]
                                soma_cat_pdf_adm, cont_num_cat_pdf_adm = 0,0
                                for _, p_row_pdf_adm in perguntas_cat_pdf_adm_df.iterrows():
                                    txt_p_pdf_adm = p_row_pdf_adm["Pergunta"]
                                    resp_p_pdf_adm = diagnostico_selecionado_adm_row.get(txt_p_pdf_adm)
                                    if isinstance(resp_p_pdf_adm, (int, float)) and \
                                       ("[Matriz GUT]" not in txt_p_pdf_adm) and \
                                       ("Pontuação (0-10)" in txt_p_pdf_adm or "Pontuação (0-5)" in txt_p_pdf_adm):
                                        soma_cat_pdf_adm += resp_p_pdf_adm
                                        cont_num_cat_pdf_adm += 1
                                media_c_pdf_adm = round(soma_cat_pdf_adm / cont_num_cat_pdf_adm, 2) if cont_num_cat_pdf_adm > 0 else 0.0
                                medias_cat_pdf_adm[cat_pdf_adm_calc] = media_c_pdf_adm
                        
                        # Pegar dados do usuário (empresa)
                        try:
                            usuarios_df_pdf_adm = pd.read_csv(usuarios_csv, encoding='utf-8')
                            usuario_data_pdf_adm = usuarios_df_pdf_adm[usuarios_df_pdf_adm["CNPJ"] == diagnostico_selecionado_adm_row["CNPJ"]].iloc[0].to_dict()
                        except: usuario_data_pdf_adm = {"Empresa": diagnostico_selecionado_adm_row.get("Empresa", "N/D"), "CNPJ": diagnostico_selecionado_adm_row.get("CNPJ", "N/D")}


                        pdf_path_admin_download = gerar_pdf_diagnostico_completo(
                            diagnostico_data=diagnostico_selecionado_adm_row.to_dict(), 
                            usuario_data=usuario_data_pdf_adm,
                            perguntas_df_geracao=perguntas_df_pdf_adm, 
                            respostas_coletadas_geracao=respostas_para_pdf_adm, # Passar todas as colunas da linha do diagnóstico
                            medias_categorias_geracao=medias_cat_pdf_adm
                        )
                        with open(pdf_path_admin_download, "rb") as f_pdf_adm_dl:
                            st.download_button(
                                label="Clique aqui para confirmar o download do PDF", 
                                data=f_pdf_adm_dl, 
                                file_name=f"diagnostico_{sanitize_column_name(empresa_selecionada_adm)}_{diagnostico_selecionado_adm_row['Data'].replace(':','-')}.pdf",
                                mime="application/pdf",
                                key=f"confirm_download_pdf_admin_{diagnostico_selecionado_adm_row.name}"
                            )
                        registrar_acao("ADMIN", "Download PDF Cliente", f"Admin baixou PDF de {diagnostico_selecionado_adm_row['Data']} para {empresa_selecionada_adm}")
                        st.success("PDF pronto para download!")
                else:
                    st.info(f"Nenhum diagnóstico encontrado para a empresa {empresa_selecionada_adm}.")
        else:
            st.info("Coluna 'CNPJ' não encontrada para permitir filtragem detalhada.")

    elif menu_admin_main == "Gerenciar Clientes":
        st.subheader("👥 Gerenciar Clientes")
        try:
            usuarios_clientes_df_adm_gc = pd.read_csv(usuarios_csv, encoding='utf-8')
        except: usuarios_clientes_df_adm_gc = pd.DataFrame(columns=colunas_base_usuarios) # Usa colunas base com NomeContato e Telefone
        
        # Garantir que as novas colunas existam
        for col_gc_check in ["NomeContato", "Telefone"]:
            if col_gc_check not in usuarios_clientes_df_adm_gc.columns:
                usuarios_clientes_df_adm_gc[col_gc_check] = ""
        
        st.caption(f"Total de clientes: {len(usuarios_clientes_df_adm_gc)}")
        
        # Edição dos clientes existentes
        if not usuarios_clientes_df_adm_gc.empty:
            st.markdown("#### Editar Clientes Existentes")
            for idx_gc, row_gc in usuarios_clientes_df_adm_gc.iterrows():
                with st.expander(f"{row_gc['Empresa']} (CNPJ: {row_gc['CNPJ']})"):
                    cols_edit_cli = st.columns([2,2,2,1]) # Senha, Nome Contato, Telefone, Salvar
                    with cols_edit_cli[0]:
                        nova_senha_gc = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password", key=f"senha_gc_{idx_gc}")
                    with cols_edit_cli[1]:
                        nome_contato_gc = st.text_input("Nome Contato", value=row_gc.get("NomeContato", ""), key=f"nomec_gc_{idx_gc}")
                    with cols_edit_cli[2]:
                        telefone_gc = st.text_input("Telefone", value=row_gc.get("Telefone", ""), key=f"tel_gc_{idx_gc}")
                    with cols_edit_cli[3]:
                        st.write("") # Espaçador
                        if st.button("💾 Salvar", key=f"save_gc_{idx_gc}"):
                            if nova_senha_gc: usuarios_clientes_df_adm_gc.loc[idx_gc, "Senha"] = nova_senha_gc
                            usuarios_clientes_df_adm_gc.loc[idx_gc, "NomeContato"] = nome_contato_gc
                            usuarios_clientes_df_adm_gc.loc[idx_gc, "Telefone"] = telefone_gc
                            usuarios_clientes_df_adm_gc.to_csv(usuarios_csv, index=False, encoding='utf-8')
                            st.success(f"Dados de {row_gc['Empresa']} atualizados!"); st.rerun()
            st.divider()

        st.subheader("➕ Adicionar Novo Cliente")
        with st.form("form_novo_cliente_admin_gc"):
            novo_cnpj_gc_form = st.text_input("CNPJ do cliente")
            nova_senha_gc_form = st.text_input("Senha para o cliente", type="password")
            nova_empresa_gc_form = st.text_input("Nome da empresa cliente")
            novo_nomecontato_gc_form = st.text_input("Nome do Contato (opcional)")
            novo_telefone_gc_form = st.text_input("Telefone (opcional)")
            adicionar_cliente_btn_gc = st.form_submit_button("Adicionar Cliente")

        if adicionar_cliente_btn_gc:
            if novo_cnpj_gc_form and nova_senha_gc_form and nova_empresa_gc_form:
                if novo_cnpj_gc_form in usuarios_clientes_df_adm_gc["CNPJ"].astype(str).values:
                     st.error(f"CNPJ {novo_cnpj_gc_form} já cadastrado.")
                else:
                    novo_usuario_data_gc = pd.DataFrame([[
                        novo_cnpj_gc_form, nova_senha_gc_form, nova_empresa_gc_form, 
                        novo_nomecontato_gc_form, novo_telefone_gc_form
                        ]], columns=colunas_base_usuarios) # Usa colunas base
                    usuarios_clientes_df_adm_gc = pd.concat([usuarios_clientes_df_adm_gc, novo_usuario_data_gc], ignore_index=True)
                    usuarios_clientes_df_adm_gc.to_csv(usuarios_csv, index=False, encoding='utf-8')
                    st.success(f"Cliente '{nova_empresa_gc_form}' adicionado!"); st.rerun()
            else: st.warning("CNPJ, Senha e Nome da Empresa são obrigatórios.")
        
        # ... (Gerenciar Bloqueios como antes)
        st.markdown("---"); st.subheader("🚫 Gerenciar Bloqueios")
        # ... (código de bloqueio/desbloqueio mantido)

    # Outras seções do Admin (Histórico, Gerenciar Perguntas, Gerenciar Admins)
    # ... (código mantido como na versão anterior)
    elif menu_admin_main == "Histórico de Usuários":
        st.subheader("📜 Histórico de Ações dos Clientes") # ... (código mantido)
    elif menu_admin_main == "Gerenciar Perguntas":
        st.subheader("📝 Gerenciar Perguntas do Diagnóstico") # ... (código mantido)
    elif menu_admin_main == "Gerenciar Administradores":
        st.subheader("👮 Gerenciar Administradores"); # ... (código mantido)


# Fallback (sem alterações)
if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()