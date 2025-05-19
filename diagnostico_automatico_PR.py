import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
from fpdf import FPDF
import tempfile
import re 
import json
import plotly.express as px

st.set_page_config(page_title="Portal de Diagnóstico", layout="wide") 

# CSS (mantido)
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
.custom-card {
    border: 1px solid #e0e0e0;
    border-left: 5px solid #2563eb; 
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
usuarios_csv = "usuarios.csv" 
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv" 
historico_csv = "historico_clientes.csv"

# --- Inicialização do Session State ---
if "admin_logado" not in st.session_state: st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state: st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state: st.session_state.diagnostico_enviado = False
if "inicio_sessao_cliente" not in st.session_state: st.session_state.inicio_sessao_cliente = None
if "cliente_page" not in st.session_state: st.session_state.cliente_page = "Painel Principal"
if "cnpj" not in st.session_state: st.session_state.cnpj = None
if "user" not in st.session_state: st.session_state.user = None
# A chave DIAGNOSTICO_FORM_ID_KEY será definida dinamicamente quando o formulário for acessado

# --- Funções Utilitárias ---
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s) 
    return s

def pdf_safe_text_output(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# --- Criação e Verificação de Arquivos ---
colunas_base_diagnosticos = [
    "Data", "CNPJ", "Nome", "Email", "Empresa",
    "Média Geral", "GUT Média", "Observações", "Diagnóstico", 
    "Análise do Cliente", "Comentarios_Admin"
]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone"]
colunas_base_perguntas = ["Pergunta", "Categoria"]

def inicializar_csv(filepath, columns):
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        pd.DataFrame(columns=columns).to_csv(filepath, index=False, encoding='utf-8')
        st.info(f"Arquivo {filepath} criado/inicializado com colunas: {', '.join(columns)}")
    else:
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
            missing_cols = [col for col in columns if col not in df.columns]
            if missing_cols:
                for col in missing_cols:
                    df[col] = "Geral" if col == "Categoria" and filepath == perguntas_csv else pd.NA # Default para Categoria
                df.to_csv(filepath, index=False, encoding='utf-8')
                st.info(f"Colunas {', '.join(missing_cols)} adicionadas ao arquivo {filepath}.")
        except pd.errors.EmptyDataError: # Se o arquivo existe mas está totalmente vazio (sem nem cabeçalhos)
            pd.DataFrame(columns=columns).to_csv(filepath, index=False, encoding='utf-8')
            st.info(f"Arquivo {filepath} estava vazio e foi reinicializado com colunas: {', '.join(columns)}")
        except Exception as e:
            st.error(f"Erro ao verificar/atualizar {filepath}: {e}. Delete o arquivo e tente novamente ou verifique o conteúdo.")

inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
inicializar_csv(usuarios_csv, colunas_base_usuarios)
inicializar_csv(perguntas_csv, colunas_base_perguntas)
inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
inicializar_csv(arquivo_csv, colunas_base_diagnosticos)


def registrar_acao(cnpj, acao, descricao):
    try:
        historico_df_ra = pd.read_csv(historico_csv, encoding='utf-8') 
    except (FileNotFoundError, pd.errors.EmptyDataError): 
        historico_df_ra = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data_ra = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }
    historico_df_ra = pd.concat([historico_df_ra, pd.DataFrame([nova_data_ra])], ignore_index=True)
    historico_df_ra.to_csv(historico_csv, index=False, encoding='utf-8')

# --- Função Refatorada de Geração de PDF (mantida como antes) ---
def gerar_pdf_diagnostico_completo(diagnostico_data, usuario_data, perguntas_df_geracao, respostas_coletadas_geracao, medias_categorias_geracao):
    # ... (Código da função gerar_pdf_diagnostico_completo mantido da versão anterior) ...
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

    resumo_cliente_pdf = diagnostico_data.get("Diagnóstico", "") 
    analise_cliente_pdf = diagnostico_data.get("Análise do Cliente", "") 
    
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
    categorias_unicas_pdf_ger = []
    if "Categoria" in perguntas_df_geracao.columns: # Checagem importante
        categorias_unicas_pdf_ger = perguntas_df_geracao["Categoria"].unique()
    
    for categoria_pdf_g_det in categorias_unicas_pdf_ger:
        pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria_pdf_g_det}"))
        pdf.set_font("Arial", size=9)
        perguntas_cat_pdf_g_det = perguntas_df_geracao[perguntas_df_geracao["Categoria"] == categoria_pdf_g_det]
        for _, p_row_pdf_g_det in perguntas_cat_pdf_g_det.iterrows():
            txt_p_pdf_g_det = p_row_pdf_g_det["Pergunta"]
            resp_p_pdf_g_det = respostas_coletadas_geracao.get(txt_p_pdf_g_det)
            if resp_p_pdf_g_det is None: 
                resp_p_pdf_g_det = diagnostico_data.get(txt_p_pdf_g_det, "N/R")

            if "[Matriz GUT]" in txt_p_pdf_g_det:
                g_pdf, u_pdf, t_pdf = 0,0,0
                score_gut_item_pdf = 0
                if isinstance(resp_p_pdf_g_det, dict): 
                    g_pdf,u_pdf,t_pdf = resp_p_pdf_g_det.get("G",0), resp_p_pdf_g_det.get("U",0), resp_p_pdf_g_det.get("T",0)
                elif isinstance(resp_p_pdf_g_det, str): 
                    try: 
                        gut_data_pdf = json.loads(resp_p_pdf_g_det.replace("'", "\""))
                        g_pdf,u_pdf,t_pdf = gut_data_pdf.get("G",0), gut_data_pdf.get("U",0), gut_data_pdf.get("T",0)
                    except: pass 
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
    for pergunta_pdf_k_g, resp_pdf_k_g_val in respostas_coletadas_geracao.items(): 
        if isinstance(pergunta_pdf_k_g, str) and "[Matriz GUT]" in pergunta_pdf_k_g: # Adicionado check de tipo para pergunta
            g_k_g, u_k_g, t_k_g = 0,0,0
            if isinstance(resp_pdf_k_g_val, dict):
                g_k_g, u_k_g, t_k_g = resp_pdf_k_g_val.get("G",0), resp_pdf_k_g_val.get("U",0), resp_pdf_k_g_val.get("T",0)
            elif isinstance(resp_pdf_k_g_val, str): 
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
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_main")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    # ... (código login admin mantido, com chaves únicas para widgets)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_page"): 
        usuario_admin_login_page = st.text_input("Usuário", key="admin_user_login_page") 
        senha_admin_login_page = st.text_input("Senha", type="password", key="admin_pass_login_page")
        entrar_admin_login_page = st.form_submit_button("Entrar")
    if entrar_admin_login_page:
        try:
            df_admin_login_creds_page = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            if not df_admin_login_creds_page[(df_admin_login_creds_page["Usuario"] == usuario_admin_login_page) & (df_admin_login_creds_page["Senha"] == senha_admin_login_page)].empty:
                st.session_state.admin_logado = True; st.success("Login de administrador bem-sucedido!")
                st.session_state.trigger_admin_rerun = True; st.rerun() 
            else: st.error("Usuário ou senha inválidos.")
        except FileNotFoundError: st.error(f"Arquivo {admin_credenciais_csv} não encontrado. Contate o suporte.")
        except Exception as e_login_admin: st.error(f"Erro no login: {e_login_admin}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    # ... (código login cliente mantido, com chaves únicas para widgets)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_page"): 
        cnpj_cli_login_page = st.text_input("CNPJ", key="cli_cnpj_login_page") 
        senha_cli_login_page = st.text_input("Senha", type="password", key="cli_pass_login_page") 
        acessar_cli_login_page = st.form_submit_button("Entrar")
    if acessar_cli_login_page:
        try:
            if not os.path.exists(usuarios_csv): st.error("Base de usuários não encontrada."); st.stop()
            usuarios_login_df_page = pd.read_csv(usuarios_csv, encoding='utf-8')
            bloqueados_login_df_page = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
            if cnpj_cli_login_page in bloqueados_login_df_page["CNPJ"].astype(str).values: 
                st.error("CNPJ bloqueado. Contate o administrador."); st.stop()
            user_match_li_page = usuarios_login_df_page[(usuarios_login_df_page["CNPJ"].astype(str) == str(cnpj_cli_login_page)) & (usuarios_login_df_page["Senha"] == senha_cli_login_page)]
            if user_match_li_page.empty: st.error("CNPJ ou senha inválidos."); st.stop()
            st.session_state.cliente_logado = True
            st.session_state.cnpj = str(cnpj_cli_login_page) 
            st.session_state.user = user_match_li_page.iloc[0].to_dict() 
            st.session_state.inicio_sessao_cliente = time.time()
            registrar_acao(st.session_state.cnpj, "Login", "Usuário realizou login.")
            st.session_state.cliente_page = "Painel Principal"
            st.success("Login realizado com sucesso!"); st.session_state.trigger_cliente_rerun = True; st.rerun() 
        except FileNotFoundError as e_login_cli_fnf: st.error(f"Arquivo não encontrado durante o login: {e_login_cli_fnf.filename}. Contate o suporte.")
        except Exception as e_login_cli: st.error(f"Erro no login do cliente: {e_login_cli}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    
    # Definir DIAGNOSTICO_FORM_ID_KEY com base no CNPJ do usuário logado para isolamento
    DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}"

    st.session_state.cliente_page = st.sidebar.radio(
        "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
        index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page),
        key="cliente_menu_radio_main"
    )
    if st.sidebar.button("⬅️ Sair do Portal Cliente"):
        keys_to_del_cli_logout_page = ['cliente_logado', 'cnpj', 'user', 'inicio_sessao_cliente', 
                                       'diagnostico_enviado', 'cliente_page', DIAGNOSTICO_FORM_ID_KEY_USER]
        temp_resp_key_logout_page = f"temp_respostas_{st.session_state.get(DIAGNOSTICO_FORM_ID_KEY_USER,'')}"
        if temp_resp_key_logout_page in st.session_state:
            keys_to_del_cli_logout_page.append(temp_resp_key_logout_page)
        for key_cd_lo_page in keys_to_del_cli_logout_page:
            if key_cd_lo_page in st.session_state: del st.session_state[key_cd_lo_page]
        st.rerun()

    if st.session_state.cliente_page == "Painel Principal":
        st.subheader("📌 Instruções Gerais")
        with st.expander("📖 Leia atentamente"): 
            st.markdown("- Responda com sinceridade.\n- Utilize a escala corretamente.\n- Análises e planos de ação são baseados em suas respostas.\n- Para novo diagnóstico, selecione no menu ao lado.")
        if st.session_state.get("diagnostico_enviado", False):
            st.success("🎯 Último diagnóstico enviado!"); st.session_state.diagnostico_enviado = False
        
        st.subheader("📁 Diagnósticos Anteriores")
        try:
            df_antigos_cli_pp_page = pd.read_csv(arquivo_csv, encoding='utf-8')
            df_cliente_view_pp_page = df_antigos_cli_pp_page[df_antigos_cli_pp_page["CNPJ"].astype(str) == st.session_state.cnpj]
        except (FileNotFoundError, pd.errors.EmptyDataError): 
            df_cliente_view_pp_page = pd.DataFrame() # Se o arquivo não existe ou está vazio, df vazio
        
        if df_cliente_view_pp_page.empty: 
            st.info("Nenhum diagnóstico anterior. Comece um novo no menu ao lado.")
        else:
            # ... (Restante do código para exibir históricos, Kanban, gráficos como na versão anterior) ...
            # Assegure-se que toda a lógica de exibição aqui seja robusta a dados faltantes
            # (Exemplo de como você pode continuar daqui)
            df_cliente_view_pp_page = df_cliente_view_pp_page.sort_values(by="Data", ascending=False)
            for idx_cv_pp_page, row_cv_pp_page in df_cliente_view_pp_page.iterrows():
                with st.expander(f"📅 {row_cv_pp_page['Data']} - {row_cv_pp_page['Empresa']}"):
                    st.write(f"**Média Geral:** {row_cv_pp_page.get('Média Geral', 'N/A')}") 
                    st.write(f"**GUT Média (G*U*T):** {row_cv_pp_page.get('GUT Média', 'N/A')}") 
                    st.write(f"**Resumo (Cliente):** {row_cv_pp_page.get('Diagnóstico', 'N/P')}")
                    
                    st.markdown("**Médias por Categoria:**")
                    found_cat_media_cv_page = False
                    for col_name_cv_page in row_cv_pp_page.index:
                        if col_name_cv_page.startswith("Media_Cat_"):
                            cat_name_display_cv_page = col_name_cv_page.replace("Media_Cat_", "").replace("_", " ")
                            st.write(f"  - {cat_name_display_cv_page}: {row_cv_pp_page.get(col_name_cv_page, 'N/A')}")
                            found_cat_media_cv_page = True
                    if not found_cat_media_cv_page: st.caption("  Nenhuma média por categoria.")

                    analise_cli_val_cv_page = row_cv_pp_page.get("Análise do Cliente", "")
                    analise_cli_cv_page = st.text_area("🧠 Minha Análise:", value=analise_cli_val_cv_page, key=f"analise_cv_page_{row_cv_pp_page.name}") # row_cv_pp_page.name é o índice original
                    if st.button("💾 Salvar Análise", key=f"salvar_analise_cv_page_{row_cv_pp_page.name}"):
                        try:
                            df_antigos_upd_cv_page = pd.read_csv(arquivo_csv, encoding='utf-8') 
                            df_antigos_upd_cv_page.loc[row_cv_pp_page.name, "Análise do Cliente"] = analise_cli_cv_page # Usar .name se for o índice original
                            df_antigos_upd_cv_page.to_csv(arquivo_csv, index=False, encoding='utf-8')
                            registrar_acao(st.session_state.cnpj, "Análise Cliente", f"Editou análise de {row_cv_pp_page['Data']}")
                            st.success("Análise salva!"); st.rerun()
                        except Exception as e_save_analise: st.error(f"Erro ao salvar análise: {e_save_analise}")
                    
                    com_admin_val_cv_page = row_cv_pp_page.get("Comentarios_Admin", "")
                    if com_admin_val_cv_page and not pd.isna(com_admin_val_cv_page):
                        st.markdown("**Comentários do Consultor:**"); st.info(f"{com_admin_val_cv_page}")
                    else: st.caption("Nenhum comentário do consultor.")
                    st.markdown("---")
            
            # KANBAN - PAINEL PRINCIPAL DO CLIENTE (como antes)
            # GRÁFICOS DE EVOLUÇÃO E COMPARAÇÃO (como antes)


    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader("📋 Formulário de Novo Diagnóstico")
        
        # Gerar/Recuperar form_id estável para esta sessão de preenchimento
        if DIAGNOSTICO_FORM_ID_KEY_USER not in st.session_state:
            st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER] = datetime.now().strftime("%Y%m%d%H%M%S%f")
        form_id_sufixo_nd_page = st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER]

        temp_respostas_key_nd_page = f"temp_respostas_{form_id_sufixo_nd_page}"
        if temp_respostas_key_nd_page not in st.session_state:
            st.session_state[temp_respostas_key_nd_page] = {}
        
        respostas_form_coletadas_nd_page = st.session_state[temp_respostas_key_nd_page]
        
        try:
            perguntas_df_diag_page = pd.read_csv(perguntas_csv, encoding='utf-8')
            if "Categoria" not in perguntas_df_diag_page.columns: 
                perguntas_df_diag_page["Categoria"] = "Geral"
                st.warning("Atenção: Arquivo de perguntas parece desatualizado (sem coluna 'Categoria'). Usando 'Geral' como padrão.")
        except (FileNotFoundError, pd.errors.EmptyDataError): 
            st.error(f"Arquivo de perguntas ({perguntas_csv}) não encontrado ou vazio. Não é possível carregar o formulário."); st.stop()
        
        if perguntas_df_diag_page.empty: 
            st.warning("Nenhuma pergunta cadastrada no sistema. Contate o administrador."); st.stop()

        total_perguntas_diag_page = len(perguntas_df_diag_page)
        respondidas_count_diag_page = 0 
        
        # Fallback se 'Categoria' não estiver no DataFrame após tentativa de leitura/correção
        if "Categoria" not in perguntas_df_diag_page.columns:
            st.error("Falha crítica: Coluna 'Categoria' não pode ser lida ou criada no arquivo de perguntas.")
            st.stop()

        categorias_unicas_diag_page = perguntas_df_diag_page["Categoria"].unique()
        
        with st.form(key=f"diagnostico_form_completo_{form_id_sufixo_nd_page}"):
            # ... (Loop do formulário como na versão anterior, com widgets usando respostas_form_coletadas_nd_page)
            for categoria_diag_page in categorias_unicas_diag_page:
                st.markdown(f"#### Categoria: {categoria_diag_page}")
                perguntas_cat_diag_page = perguntas_df_diag_page[perguntas_df_diag_page["Categoria"] == categoria_diag_page]
                for idx_diag_f_page, row_diag_f_page in perguntas_cat_diag_page.iterrows():
                    texto_pergunta_diag_page = str(row_diag_f_page["Pergunta"]) 
                    widget_base_key_page = f"q_form_page_{idx_diag_f_page}" 

                    # Lógica de renderização dos widgets (GUT, sliders, text_area, selectbox)
                    # Usando respostas_form_coletadas_nd_page para value= e para salvar a resposta
                    # Exemplo para GUT:
                    if "[Matriz GUT]" in texto_pergunta_diag_page:
                        st.markdown(f"**{texto_pergunta_diag_page.replace(' [Matriz GUT]', '')}**")
                        cols_gut_page = st.columns(3)
                        gut_current_vals_page = respostas_form_coletadas_nd_page.get(texto_pergunta_diag_page, {"G":0, "U":0, "T":0})
                        with cols_gut_page[0]: g_val_page = st.slider("Gravidade (0-5)", 0, 5, value=int(gut_current_vals_page.get("G",0)), key=f"{widget_base_key_page}_G")
                        with cols_gut_page[1]: u_val_page = st.slider("Urgência (0-5)", 0, 5, value=int(gut_current_vals_page.get("U",0)), key=f"{widget_base_key_page}_U")
                        with cols_gut_page[2]: t_val_page = st.slider("Tendência (0-5)", 0, 5, value=int(gut_current_vals_page.get("T",0)), key=f"{widget_base_key_page}_T")
                        respostas_form_coletadas_nd_page[texto_pergunta_diag_page] = {"G": g_val_page, "U": u_val_page, "T": t_val_page}
                        if g_val_page > 0 or u_val_page > 0 or t_val_page > 0 : respondidas_count_diag_page +=1
                    # ... (outros tipos de pergunta como antes)
                st.divider()
            
            progresso_diag_page = round((respondidas_count_diag_page / total_perguntas_diag_page) * 100) if total_perguntas_diag_page > 0 else 0
            st.info(f"📊 Progresso: {respondidas_count_diag_page} de {total_perguntas_diag_page} respondidas ({progresso_diag_page}%)")
            
            obs_cli_diag_form_page = st.text_area("Sua Análise/Observações (opcional):", value=respostas_form_coletadas_nd_page.get("__obs_cliente__", ""), key=f"obs_cli_diag_page_{form_id_sufixo_nd_page}")
            respostas_form_coletadas_nd_page["__obs_cliente__"] = obs_cli_diag_form_page 
            
            diag_resumo_cli_diag_page = st.text_area("✍️ Resumo/principais insights (para PDF):", value=respostas_form_coletadas_nd_page.get("__resumo_cliente__", ""), key=f"diag_resumo_diag_page_{form_id_sufixo_nd_page}")
            respostas_form_coletadas_nd_page["__resumo_cliente__"] = diag_resumo_cli_diag_page

            enviar_diagnostico_btn_page = st.form_submit_button("✔️ Enviar Diagnóstico")

        if enviar_diagnostico_btn_page:
            # ... (Lógica de processamento e salvamento do formulário como na versão anterior)
            # Certifique-se que a função gerar_pdf_diagnostico_completo é chamada corretamente
            # E que as chaves de session_state são limpas
            pass # Código completo já fornecido anteriormente. Se precisar, posso colar só essa parte.


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    # ... (código do admin como na versão anterior, com as melhorias de PDF e Plotly)
    pass # Código completo já fornecido anteriormente.

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()