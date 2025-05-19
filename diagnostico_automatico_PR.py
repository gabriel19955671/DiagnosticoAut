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

admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv" 
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv" 
historico_csv = "historico_clientes.csv"

if "admin_logado" not in st.session_state: st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state: st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state: st.session_state.diagnostico_enviado = False
if "inicio_sessao_cliente" not in st.session_state: st.session_state.inicio_sessao_cliente = None
if "cliente_page" not in st.session_state: st.session_state.cliente_page = "Painel Principal"
if "cnpj" not in st.session_state: st.session_state.cnpj = None
if "user" not in st.session_state: st.session_state.user = None
DIAGNOSTICO_FORM_ID_KEY = f"form_id_diagnostico_cliente_{st.session_state.get('cnpj', 'default_user')}"

def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s) 
    return s

def pdf_safe_text_output(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

colunas_base_diagnosticos = [
    "Data", "CNPJ", "Nome", "Email", "Empresa",
    "Média Geral", "GUT Média", "Observações", "Diagnóstico", 
    "Análise do Cliente", "Comentarios_Admin"
]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone"]

for arquivo, colunas_base_f in [ 
    (usuarios_bloqueados_csv, ["CNPJ"]),
    (admin_credenciais_csv, ["Usuario", "Senha"]),
    (usuarios_csv, colunas_base_usuarios), 
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
            # Adiciona colunas base se estiverem faltando
            for col_check in colunas_base_f:
                if col_check not in df_temp_check.columns:
                    df_temp_check[col_check] = pd.NA 
                    missing_cols_check = True
            
            # Especificamente para perguntas.csv, garante 'Categoria'
            if arquivo == perguntas_csv and "Categoria" not in df_temp_check.columns:
                 df_temp_check["Categoria"] = "Geral"
                 missing_cols_check = True
            
            if missing_cols_check:
                df_temp_check.to_csv(arquivo, index=False, encoding='utf-8')
        except pd.errors.EmptyDataError:
             pd.DataFrame(columns=colunas_base_f).to_csv(arquivo, index=False, encoding='utf-8')
        except Exception as e: st.error(f"Erro ao verificar/criar {arquivo}: {e}")


def registrar_acao(cnpj, acao, descricao):
    try:
        historico_df_ra = pd.read_csv(historico_csv, encoding='utf-8') 
    except FileNotFoundError: historico_df_ra = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data_ra = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }
    historico_df_ra = pd.concat([historico_df_ra, pd.DataFrame([nova_data_ra])], ignore_index=True)
    historico_df_ra.to_csv(historico_csv, index=False, encoding='utf-8')

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
    if "Categoria" in perguntas_df_geracao.columns:
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
        if "[Matriz GUT]" in pergunta_pdf_k_g:
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

if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_main"): 
        usuario_admin_li_main = st.text_input("Usuário", key="admin_user_li_main") 
        senha_admin_li_main = st.text_input("Senha", type="password", key="admin_pass_li_main")
        entrar_admin_li_main = st.form_submit_button("Entrar")
    if entrar_admin_li_main:
        df_admin_li_creds_main = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
        if not df_admin_li_creds_main[(df_admin_li_creds_main["Usuario"] == usuario_admin_li_main) & (df_admin_li_creds_main["Senha"] == senha_admin_li_main)].empty:
            st.session_state.admin_logado = True; st.success("Login de administrador bem-sucedido!")
            st.session_state.trigger_admin_rerun = True; st.rerun() 
        else: st.error("Usuário ou senha inválidos.")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_main"): 
        cnpj_cli_li_main = st.text_input("CNPJ", key="cli_cnpj_li_main") 
        senha_cli_li_main = st.text_input("Senha", type="password", key="cli_pass_li_main") 
        acessar_cli_li_main = st.form_submit_button("Entrar")
    if acessar_cli_li_main:
        if not os.path.exists(usuarios_csv): st.error("Base de usuários não encontrada."); st.stop()
        usuarios_li_df_main = pd.read_csv(usuarios_csv, encoding='utf-8')
        bloqueados_li_df_main = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
        if cnpj_cli_li_main in bloqueados_li_df_main["CNPJ"].astype(str).values: 
            st.error("CNPJ bloqueado. Contate o administrador."); st.stop()
        user_match_li_main = usuarios_li_df_main[(usuarios_li_df_main["CNPJ"].astype(str) == str(cnpj_cli_li_main)) & (usuarios_li_df_main["Senha"] == senha_cli_li_main)]
        if user_match_li_main.empty: st.error("CNPJ ou senha inválidos."); st.stop()
        st.session_state.cliente_logado = True
        st.session_state.cnpj = str(cnpj_cli_li_main) 
        st.session_state.user = user_match_li_main.iloc[0].to_dict() 
        st.session_state.inicio_sessao_cliente = time.time()
        registrar_acao(st.session_state.cnpj, "Login", "Usuário realizou login.")
        st.session_state.cliente_page = "Painel Principal"
        st.success("Login realizado com sucesso!"); st.session_state.trigger_cliente_rerun = True; st.rerun() 
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    st.session_state.cliente_page = st.sidebar.radio(
        "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
        index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page),
        key="cliente_menu_radio"
    )
    if st.sidebar.button("⬅️ Sair do Portal Cliente"):
        keys_to_del_cli_logout_main = ['cliente_logado', 'cnpj', 'user', 'inicio_sessao_cliente', 
                                       'diagnostico_enviado', 'cliente_page', DIAGNOSTICO_FORM_ID_KEY]
        # Adiciona a chave de respostas temporárias para limpeza, se existir
        temp_resp_key_logout = f"temp_respostas_{st.session_state.get(DIAGNOSTICO_FORM_ID_KEY,'')}"
        if temp_resp_key_logout in st.session_state:
            keys_to_del_cli_logout_main.append(temp_resp_key_logout)

        for key_cd_lo_main in keys_to_del_cli_logout_main:
            if key_cd_lo_main in st.session_state: del st.session_state[key_cd_lo_main]
        st.rerun()

    if st.session_state.cliente_page == "Painel Principal":
        st.subheader("📌 Instruções Gerais")
        with st.expander("📖 Leia atentamente"): 
            st.markdown("- Responda com sinceridade.\n- Utilize a escala corretamente.\n- Análises e planos de ação são baseados em suas respostas.\n- Para novo diagnóstico, selecione no menu ao lado.")
        if st.session_state.get("diagnostico_enviado", False):
            st.success("🎯 Último diagnóstico enviado!"); st.session_state.diagnostico_enviado = False
        
        st.subheader("📁 Diagnósticos Anteriores")
        try:
            df_antigos_cli_pp_main = pd.read_csv(arquivo_csv, encoding='utf-8')
            df_cliente_view_pp_main = df_antigos_cli_pp_main[df_antigos_cli_pp_main["CNPJ"].astype(str) == st.session_state.cnpj]
        except FileNotFoundError: df_cliente_view_pp_main = pd.DataFrame()
        
        if df_cliente_view_pp_main.empty: 
            st.info("Nenhum diagnóstico anterior. Comece um novo no menu ao lado.")
        else:
            df_cliente_view_pp_main = df_cliente_view_pp_main.sort_values(by="Data", ascending=False)
            for idx_cv_pp_main, row_cv_pp_main in df_cliente_view_pp_main.iterrows():
                with st.expander(f"📅 {row_cv_pp_main['Data']} - {row_cv_pp_main['Empresa']}"):
                    st.write(f"**Média Geral:** {row_cv_pp_main.get('Média Geral', 'N/A')}") 
                    st.write(f"**GUT Média (G*U*T):** {row_cv_pp_main.get('GUT Média', 'N/A')}") 
                    st.write(f"**Resumo (Cliente):** {row_cv_pp_main.get('Diagnóstico', 'N/P')}")
                    
                    st.markdown("**Médias por Categoria:**")
                    found_cat_media_cv_main = False
                    for col_name_cv_main in row_cv_pp_main.index:
                        if col_name_cv_main.startswith("Media_Cat_"):
                            cat_name_display_cv_main = col_name_cv_main.replace("Media_Cat_", "").replace("_", " ")
                            st.write(f"  - {cat_name_display_cv_main}: {row_cv_pp_main.get(col_name_cv_main, 'N/A')}")
                            found_cat_media_cv_main = True
                    if not found_cat_media_cv_main: st.caption("  Nenhuma média por categoria.")

                    analise_cli_val_cv_main = row_cv_pp_main.get("Análise do Cliente", "")
                    analise_cli_cv_main = st.text_area("🧠 Minha Análise:", value=analise_cli_val_cv_main, key=f"analise_cv_main_{row_cv_pp_main.name}")
                    if st.button("💾 Salvar Análise", key=f"salvar_analise_cv_main_{row_cv_pp_main.name}"):
                        df_antigos_upd_cv_main = pd.read_csv(arquivo_csv, encoding='utf-8') 
                        df_antigos_upd_cv_main.loc[df_antigos_upd_cv_main.index == row_cv_pp_main.name, "Análise do Cliente"] = analise_cli_cv_main
                        df_antigos_upd_cv_main.to_csv(arquivo_csv, index=False, encoding='utf-8')
                        registrar_acao(st.session_state.cnpj, "Análise Cliente", f"Editou análise de {row_cv_pp_main['Data']}")
                        st.success("Análise salva!"); st.rerun()
                    
                    com_admin_val_cv_main = row_cv_pp_main.get("Comentarios_Admin", "")
                    if com_admin_val_cv_main and not pd.isna(com_admin_val_cv_main):
                        st.markdown("**Comentários do Consultor:**"); st.info(f"{com_admin_val_cv_main}")
                    else: st.caption("Nenhum comentário do consultor.")
                    st.markdown("---")
            
            # KANBAN - PAINEL PRINCIPAL DO CLIENTE
            st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
            gut_cards_painel_main = []
            if not df_cliente_view_pp_main.empty:
                latest_diag_row_painel_main = df_cliente_view_pp_main.iloc[0]
                for pergunta_p_main, resposta_p_val_str_main in latest_diag_row_painel_main.items():
                    if isinstance(pergunta_p_main, str) and "[Matriz GUT]" in pergunta_p_main:
                        try:
                            if pd.notna(resposta_p_val_str_main) and isinstance(resposta_p_val_str_main, str):
                                gut_data_main = json.loads(resposta_p_val_str_main.replace("'", "\"")) 
                                g_main = int(gut_data_main.get("G", 0))
                                u_main = int(gut_data_main.get("U", 0))
                                t_main = int(gut_data_main.get("T", 0))
                                score_gut_total_p_main = g_main * u_main * t_main
                                
                                prazo_p_main = "N/A"
                                if score_gut_total_p_main >= 75: prazo_p_main = "15 dias"
                                elif score_gut_total_p_main >= 40: prazo_p_main = "30 dias"
                                elif score_gut_total_p_main >= 20: prazo_p_main = "45 dias"
                                elif score_gut_total_p_main > 0: prazo_p_main = "60 dias"
                                else: continue 

                                if prazo_p_main != "N/A":
                                    gut_cards_painel_main.append({
                                        "Tarefa": pergunta_p_main.replace(" [Matriz GUT]", ""), 
                                        "Prazo": prazo_p_main, "Score": score_gut_total_p_main, 
                                        "Responsável": st.session_state.user.get("Empresa", "N/D")
                                    })
                        except (json.JSONDecodeError, ValueError, TypeError) as e_k_main:
                            st.warning(f"Erro ao processar GUT p/ Kanban: '{pergunta_p_main}' ({resposta_p_val_str_main}). Erro: {e_k_main}")
                            continue
            
            if gut_cards_painel_main:
                gut_cards_sorted_p_main = sorted(gut_cards_painel_main, key=lambda x_p_k_main: x_p_k_main["Score"], reverse=True)
                prazos_def_p_main = sorted(list(set(card_p_main["Prazo"] for card_p_main in gut_cards_sorted_p_main)), key=lambda x_p_d_main: int(x_p_d_main.split(" ")[0])) 
                if prazos_def_p_main:
                    cols_kanban_p_main = st.columns(len(prazos_def_p_main))
                    for idx_kp_main, prazo_col_kp_main in enumerate(prazos_def_p_main):
                        with cols_kanban_p_main[idx_kp_main]:
                            st.markdown(f"#### ⏱️ {prazo_col_kp_main}")
                            for card_item_kp_main in gut_cards_sorted_p_main:
                                if card_item_kp_main["Prazo"] == prazo_col_kp_main:
                                    st.markdown(f"""<div style="border:1px solid #e0e0e0;border-left:5px solid #2563eb;padding:10px;margin-bottom:10px;border-radius:5px;"><small><b>{card_item_kp_main['Tarefa']}</b> (Score GUT: {card_item_kp_main['Score']})</small><br><small><i>👤 {card_item_kp_main['Responsável']}</i></small></div>""", unsafe_allow_html=True)
            else: st.info("Nenhuma ação prioritária para o Kanban (GUT).")
            
            st.subheader("📈 Comparativo de Evolução")
            if len(df_cliente_view_pp_main) > 1:
                grafico_comp_ev_main = df_cliente_view_pp_main.sort_values(by="Data")
                grafico_comp_ev_main["Data"] = pd.to_datetime(grafico_comp_ev_main["Data"])
                colunas_plot_comp_main = ['Média Geral', 'GUT Média'] 
                for col_g_comp_main in grafico_comp_ev_main.columns:
                    if col_g_comp_main.startswith("Media_Cat_") and pd.api.types.is_numeric_dtype(grafico_comp_ev_main[col_g_comp_main]):
                        colunas_plot_comp_main.append(col_g_comp_main)
                for col_plot_c_main in colunas_plot_comp_main:
                    if col_plot_c_main in grafico_comp_ev_main.columns: grafico_comp_ev_main[col_plot_c_main] = pd.to_numeric(grafico_comp_ev_main[col_plot_c_main], errors='coerce')
                
                colunas_validas_plot_main = [c_main for c_main in colunas_plot_comp_main if c_main in grafico_comp_ev_main.columns and pd.api.types.is_numeric_dtype(grafico_comp_ev_main[c_main])]
                if colunas_validas_plot_main:
                    st.line_chart(grafico_comp_ev_main.set_index("Data")[colunas_validas_plot_main].dropna(axis=1, how='all'))
                
                st.subheader("📊 Comparação Entre Diagnósticos") 
                opcoes_cli_main = grafico_comp_ev_main["Data"].astype(str).tolist()
                if len(opcoes_cli_main) >= 2:
                    diag_atual_idx_main, diag_anterior_idx_main = len(opcoes_cli_main)-1, len(opcoes_cli_main)-2
                    diag_atual_sel_cli_main = st.selectbox("Diagnóstico mais recente:", opcoes_cli_main, index=diag_atual_idx_main, key="diag_atual_sel_cli_main")
                    diag_anterior_sel_cli_main = st.selectbox("Diagnóstico anterior:", opcoes_cli_main, index=diag_anterior_idx_main, key="diag_anterior_sel_cli_main")
                    atual_cli_main = grafico_comp_ev_main[grafico_comp_ev_main["Data"].astype(str) == diag_atual_sel_cli_main].iloc[0]
                    anterior_cli_main = grafico_comp_ev_main[grafico_comp_ev_main["Data"].astype(str) == diag_anterior_sel_cli_main].iloc[0]
                    st.write(f"### 📅 Comparando {diag_anterior_sel_cli_main.split(' ')[0]} ⟶ {diag_atual_sel_cli_main.split(' ')[0]}")
                    cols_excluir_comp_main = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
                    variaveis_comp_main = [col_main for col_main in grafico_comp_ev_main.columns if col_main not in cols_excluir_comp_main and pd.api.types.is_numeric_dtype(grafico_comp_ev_main[col_main])]
                    if variaveis_comp_main:
                        comp_data_main = []
                        for v_comp_main in variaveis_comp_main:
                            val_ant_c_main = pd.to_numeric(anterior_cli_main.get(v_comp_main), errors='coerce')
                            val_atu_c_main = pd.to_numeric(atual_cli_main.get(v_comp_main), errors='coerce')
                            evolucao_c_main = "➖ Igual"
                            if pd.notna(val_ant_c_main) and pd.notna(val_atu_c_main):
                                if val_atu_c_main > val_ant_c_main: evolucao_c_main = "🔼 Melhorou"
                                elif val_atu_c_main < val_ant_c_main: evolucao_c_main = "🔽 Piorou"
                            display_name_comp_main = v_comp_main.replace("Media_Cat_", "Média ").replace("_", " ")
                            if "[Pontuação (0-10)]" in display_name_comp_main or "[Pontuação (0-5) + Matriz GUT]" in display_name_comp_main or "[Matriz GUT]" in display_name_comp_main:
                                display_name_comp_main = display_name_comp_main.split(" [")[0] 
                            comp_data_main.append({"Indicador": display_name_comp_main, "Anterior": val_ant_c_main if pd.notna(val_ant_c_main) else "N/A", "Atual": val_atu_c_main if pd.notna(val_atu_c_main) else "N/A", "Evolução": evolucao_c_main})
                        st.dataframe(pd.DataFrame(comp_data_main))
                    else: st.info("Sem dados numéricos para comparação.")
                else: st.info("Pelo menos dois diagnósticos para comparação.")
            else: st.info("Pelo menos dois diagnósticos para comparativos.")

    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader("📋 Formulário de Novo Diagnóstico")
        
        if DIAGNOSTICO_FORM_ID_KEY not in st.session_state:
            st.session_state[DIAGNOSTICO_FORM_ID_KEY] = datetime.now().strftime("%Y%m%d%H%M%S%f")
        form_id_sufixo_nd_main = st.session_state[DIAGNOSTICO_FORM_ID_KEY]

        temp_respostas_key_nd_main = f"temp_respostas_{form_id_sufixo_nd_main}"
        if temp_respostas_key_nd_main not in st.session_state:
            st.session_state[temp_respostas_key_nd_main] = {}
        
        respostas_form_coletadas_nd_main = st.session_state[temp_respostas_key_nd_main]
        
        try:
            perguntas_df_diag_main = pd.read_csv(perguntas_csv, encoding='utf-8')
            if "Categoria" not in perguntas_df_diag_main.columns: 
                perguntas_df_diag_main["Categoria"] = "Geral"
        except FileNotFoundError: st.error("Arquivo de perguntas não encontrado."); st.stop()
        if perguntas_df_diag_main.empty: st.warning("Nenhuma pergunta cadastrada."); st.stop()

        total_perguntas_diag_main = len(perguntas_df_diag_main)
        respondidas_count_diag_main = 0 
        
        categorias_unicas_diag_main = perguntas_df_diag_main["Categoria"].unique()
        
        with st.form(key=f"diagnostico_form_completo_{form_id_sufixo_nd_main}"):
            for categoria_diag_main in categorias_unicas_diag_main:
                st.markdown(f"#### Categoria: {categoria_diag_main}")
                perguntas_cat_diag_main = perguntas_df_diag_main[perguntas_df_diag_main["Categoria"] == categoria_diag_main]
                for idx_diag_f_main, row_diag_f_main in perguntas_cat_diag_main.iterrows():
                    texto_pergunta_diag_main = str(row_diag_f_main["Pergunta"]) 
                    widget_base_key_main = f"q_form_main_{idx_diag_f_main}" 

                    if "[Matriz GUT]" in texto_pergunta_diag_main:
                        st.markdown(f"**{texto_pergunta_diag_main.replace(' [Matriz GUT]', '')}**")
                        cols_gut_main = st.columns(3)
                        # Busca valor anterior ou default para os sliders GUT
                        gut_current_vals = respostas_form_coletadas_nd_main.get(texto_pergunta_diag_main, {"G":0, "U":0, "T":0})
                        
                        with cols_gut_main[0]:
                            g_val_main = st.slider("Gravidade (0-5)", 0, 5, value=int(gut_current_vals.get("G",0)), key=f"{widget_base_key_main}_G")
                        with cols_gut_main[1]:
                            u_val_main = st.slider("Urgência (0-5)", 0, 5, value=int(gut_current_vals.get("U",0)), key=f"{widget_base_key_main}_U")
                        with cols_gut_main[2]:
                            t_val_main = st.slider("Tendência (0-5)", 0, 5, value=int(gut_current_vals.get("T",0)), key=f"{widget_base_key_main}_T")
                        respostas_form_coletadas_nd_main[texto_pergunta_diag_main] = {"G": g_val_main, "U": u_val_main, "T": t_val_main}
                        if g_val_main > 0 or u_val_main > 0 or t_val_main > 0 : respondidas_count_diag_main +=1

                    elif "Pontuação (0-5)" in texto_pergunta_diag_main: 
                        val_main = respostas_form_coletadas_nd_main.get(texto_pergunta_diag_main, 0)
                        respostas_form_coletadas_nd_main[texto_pergunta_diag_main] = st.slider(texto_pergunta_diag_main, 0, 5, value=int(val_main), key=widget_base_key_main) 
                        if respostas_form_coletadas_nd_main[texto_pergunta_diag_main] != 0: respondidas_count_diag_main += 1
                    elif "Pontuação (0-10)" in texto_pergunta_diag_main:
                        val_main = respostas_form_coletadas_nd_main.get(texto_pergunta_diag_main, 0)
                        respostas_form_coletadas_nd_main[texto_pergunta_diag_main] = st.slider(texto_pergunta_diag_main, 0, 10, value=int(val_main), key=widget_base_key_main)
                        if respostas_form_coletadas_nd_main[texto_pergunta_diag_main] != 0: respondidas_count_diag_main += 1
                    elif "Texto Aberto" in texto_pergunta_diag_main:
                        val_main = respostas_form_coletadas_nd_main.get(texto_pergunta_diag_main, "")
                        respostas_form_coletadas_nd_main[texto_pergunta_diag_main] = st.text_area(texto_pergunta_diag_main, value=str(val_main), key=widget_base_key_main)
                        if respostas_form_coletadas_nd_main[texto_pergunta_diag_main].strip() != "": respondidas_count_diag_main += 1
                    elif "Escala" in texto_pergunta_diag_main: 
                        opcoes_escala_diag_main = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"] 
                        val_main = respostas_form_coletadas_nd_main.get(texto_pergunta_diag_main, "Selecione")
                        idx_sel_main = opcoes_escala_diag_main.index(val_main) if val_main in opcoes_escala_diag_main else 0
                        respostas_form_coletadas_nd_main[texto_pergunta_diag_main] = st.selectbox(texto_pergunta_diag_main, opcoes_escala_diag_main, index=idx_sel_main, key=widget_base_key_main)
                        if respostas_form_coletadas_nd_main[texto_pergunta_diag_main] != "Selecione": respondidas_count_diag_main += 1
                    else: 
                        val_main = respostas_form_coletadas_nd_main.get(texto_pergunta_diag_main, 0)
                        respostas_form_coletadas_nd_main[texto_pergunta_diag_main] = st.slider(texto_pergunta_diag_main, 0, 10, value=int(val_main), key=widget_base_key_main)
                        if respostas_form_coletadas_nd_main[texto_pergunta_diag_main] != 0: respondidas_count_diag_main += 1
                st.divider()
            
            progresso_diag_main = round((respondidas_count_diag_main / total_perguntas_diag_main) * 100) if total_perguntas_diag_main > 0 else 0
            st.info(f"📊 Progresso: {respondidas_count_diag_main} de {total_perguntas_diag_main} respondidas ({progresso_diag_main}%)")
            
            obs_cli_diag_form_main = st.text_area("Sua Análise/Observações (opcional):", value=respostas_form_coletadas_nd_main.get("__obs_cliente__", ""), key=f"obs_cli_diag_main_{form_id_sufixo_nd_main}")
            respostas_form_coletadas_nd_main["__obs_cliente__"] = obs_cli_diag_form_main 
            
            diag_resumo_cli_diag_main = st.text_area("✍️ Resumo/principais insights (para PDF):", value=respostas_form_coletadas_nd_main.get("__resumo_cliente__", ""), key=f"diag_resumo_diag_main_{form_id_sufixo_nd_main}")
            respostas_form_coletadas_nd_main["__resumo_cliente__"] = diag_resumo_cli_diag_main

            enviar_diagnostico_btn_main = st.form_submit_button("✔️ Enviar Diagnóstico")

        if enviar_diagnostico_btn_main:
            if respondidas_count_diag_main < total_perguntas_diag_main: st.warning("Responda todas as perguntas.")
            elif not respostas_form_coletadas_nd_main["__resumo_cliente__"].strip(): st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
            else:
                soma_total_gut_scores_main, count_gut_perguntas_main = 0, 0
                respostas_finais_para_salvar_main = {}

                for pergunta_env_main, resposta_env_main in respostas_form_coletadas_nd_main.items():
                    if pergunta_env_main.startswith("__"): continue 
                    if "[Matriz GUT]" in pergunta_env_main and isinstance(resposta_env_main, dict):
                        respostas_finais_para_salvar_main[pergunta_env_main] = json.dumps(resposta_env_main) 
                        g_m, u_m, t_m = resposta_env_main.get("G",0), resposta_env_main.get("U",0), resposta_env_main.get("T",0)
                        soma_total_gut_scores_main += (g_m * u_m * t_m)
                        count_gut_perguntas_main +=1
                    else:
                        respostas_finais_para_salvar_main[pergunta_env_main] = resposta_env_main

                gut_media_final_main = round(soma_total_gut_scores_main / count_gut_perguntas_main, 2) if count_gut_perguntas_main > 0 else 0.0
                numeric_resp_final_main = [v_m for k_m, v_m in respostas_finais_para_salvar_main.items() if isinstance(v_m, (int, float)) and ("Pontuação (0-10)" in k_m or "Pontuação (0-5)" in k_m)] 
                media_geral_calc_final_main = round(sum(numeric_resp_final_main) / len(numeric_resp_final_main), 2) if numeric_resp_final_main else 0.0
                empresa_nome_final_main = st.session_state.user.get("Empresa", "N/D")
                
                nova_linha_final_main = {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": st.session_state.cnpj,
                    "Nome": st.session_state.user.get("CNPJ", ""), "Email": "", "Empresa": empresa_nome_final_main,
                    "Média Geral": media_geral_calc_final_main, "GUT Média": gut_media_final_main, 
                    "Observações": "", 
                    "Análise do Cliente": respostas_form_coletadas_nd_main.get("__obs_cliente__",""), 
                    "Diagnóstico": respostas_form_coletadas_nd_main.get("__resumo_cliente__",""), 
                    "Comentarios_Admin": ""
                }
                nova_linha_final_main.update(respostas_finais_para_salvar_main)

                medias_por_categoria_final_main = {}
                for cat_final_calc_main in categorias_unicas_diag_main:
                    perguntas_cat_final_df_main = perguntas_df_diag_main[perguntas_df_diag_main["Categoria"] == cat_final_calc_main]
                    soma_cat_final_main, cont_num_cat_final_main = 0, 0
                    for _, p_row_final_main in perguntas_cat_final_df_main.iterrows():
                        txt_p_final_main = p_row_final_main["Pergunta"]
                        resp_p_final_main = respostas_form_coletadas_nd_main.get(txt_p_final_main)
                        if isinstance(resp_p_final_main, (int, float)) and \
                           ("[Matriz GUT]" not in txt_p_final_main) and \
                           ("Pontuação (0-10)" in txt_p_final_main or "Pontuação (0-5)" in txt_p_final_main):
                            soma_cat_final_main += resp_p_final_main
                            cont_num_cat_final_main += 1
                    media_c_final_main = round(soma_cat_final_main / cont_num_cat_final_main, 2) if cont_num_cat_final_main > 0 else 0.0
                    nome_col_media_cat_final_main = f"Media_Cat_{sanitize_column_name(cat_final_calc_main)}"
                    nova_linha_final_main[nome_col_media_cat_final_main] = media_c_final_main
                    medias_por_categoria_final_main[cat_final_calc_main] = media_c_final_main

                try: df_diag_todos_final_main = pd.read_csv(arquivo_csv, encoding='utf-8')
                except FileNotFoundError: df_diag_todos_final_main = pd.DataFrame() 
                for col_f_save_final_main in nova_linha_final_main.keys(): 
                    if col_f_save_final_main not in df_diag_todos_final_main.columns: df_diag_todos_final_main[col_f_save_final_main] = pd.NA 
                df_diag_todos_final_main = pd.concat([df_diag_todos_final_main, pd.DataFrame([nova_linha_final_main])], ignore_index=True)
                df_diag_todos_final_main.to_csv(arquivo_csv, index=False, encoding='utf-8')
                
                st.success("Diagnóstico enviado com sucesso!")
                registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", "Cliente enviou novo diagnóstico.")
                
                pdf_path_final_main = gerar_pdf_diagnostico_completo(
                    diagnostico_data=nova_linha_final_main, 
                    usuario_data=st.session_state.user, 
                    perguntas_df_geracao=perguntas_df_diag_main, 
                    respostas_coletadas_geracao=respostas_form_coletadas_nd_main, # Passar o dict original com GUT como dict
                    medias_categorias_geracao=medias_por_categoria_final_main
                )
                with open(pdf_path_final_main, "rb") as f_pdf_final_main:
                    st.download_button(label="📄 Baixar PDF do Diagnóstico", data=f_pdf_final_main, 
                                       file_name=f"diagnostico_{sanitize_column_name(empresa_nome_final_main)}_{datetime.now().strftime('%Y%m%d')}.pdf", 
                                       mime="application/pdf", key="download_pdf_cliente_final")
                registrar_acao(st.session_state.cnpj, "Download PDF", "Baixou PDF do novo diagnóstico.")
                
                if DIAGNOSTICO_FORM_ID_KEY in st.session_state: del st.session_state[DIAGNOSTICO_FORM_ID_KEY]
                if temp_respostas_key_nd_main in st.session_state: del st.session_state[temp_respostas_key_nd_main]
                
                st.session_state.diagnostico_enviado = True
                st.session_state.cliente_page = "Painel Principal" 
                st.rerun()

# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    st.sidebar.image("https://raw.githubusercontent.com/AndersonCRMG/AppDiagnostico/main/Logo%20Transparente%20(1).png", width=100) # Exemplo de logo na sidebar
    st.sidebar.success("🟢 Admin Logado")
    # ... (restante do código do admin como na versão anterior)
    if st.sidebar.button("🚪 Sair do Painel Admin"):
        st.session_state.admin_logado = False; st.rerun()

    menu_admin_main_view = st.sidebar.selectbox( 
        "Funcionalidades Admin:",
        ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Perguntas", 
         "Gerenciar Clientes", "Gerenciar Administradores"],
        key="admin_menu_selectbox_main_page_view" 
    )
    st.header(f"🔑 Painel Admin: {menu_admin_main_view}")

    if menu_admin_main_view == "Visão Geral e Diagnósticos":
        # ... (código da Visão Geral e Diagnósticos, incluindo botão de download PDF individual)
        pass # Código completo já fornecido anteriormente
    elif menu_admin_main_view == "Gerenciar Clientes":
        # ... (código de Gerenciar Clientes, agora com NomeContato e Telefone)
        pass # Código completo já fornecido anteriormente
    # ... (outras seções do admin)
    elif menu_admin_main_view == "Histórico de Usuários":
        st.subheader("📜 Histórico de Ações dos Clientes") # ... (código mantido)
    elif menu_admin_main_view == "Gerenciar Perguntas":
        st.subheader("📝 Gerenciar Perguntas do Diagnóstico") # ... (código mantido)
    elif menu_admin_main_view == "Gerenciar Administradores":
        st.subheader("👮 Gerenciar Administradores"); # ... (código mantido)

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()