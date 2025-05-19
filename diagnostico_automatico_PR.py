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

# CSS
st.markdown("""
<style>
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
# A chave DIAGNOSTICO_FORM_ID_KEY será definida dinamicamente com base no CNPJ ao acessar o formulário

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

def inicializar_csv(filepath, columns, is_perguntas_file=False):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df = pd.DataFrame(columns=columns)
            df.to_csv(filepath, index=False, encoding='utf-8')
        else:
            df = pd.read_csv(filepath, encoding='utf-8')
            missing_cols = [col for col in columns if col not in df.columns]
            made_changes = False
            if missing_cols:
                for col in missing_cols:
                    if is_perguntas_file and col == "Categoria": df[col] = "Geral"
                    else: df[col] = pd.NA 
                made_changes = True
            if is_perguntas_file and "Categoria" not in df.columns:
                df["Categoria"] = "Geral"; made_changes = True
            if made_changes:
                df.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError: 
        pd.DataFrame(columns=columns).to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erro ao inicializar/verificar {filepath}: {e}. O app pode não funcionar corretamente.")

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios)
    inicializar_csv(perguntas_csv, colunas_base_perguntas, is_perguntas_file=True)
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
except Exception as e_init_fullcode:
    st.error(f"Falha crítica na inicialização de arquivos CSV base: {e_init_fullcode}")
    st.exception(e_init_fullcode)
    st.markdown("Verifique permissões de arquivo e a integridade dos CSVs existentes.")
    st.stop()


def registrar_acao(cnpj, acao, descricao):
    try:
        historico_df = pd.read_csv(historico_csv, encoding='utf-8') 
    except (FileNotFoundError, pd.errors.EmptyDataError): 
        historico_df = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }
    historico_df = pd.concat([historico_df, pd.DataFrame([nova_data])], ignore_index=True)
    historico_df.to_csv(historico_csv, index=False, encoding='utf-8')


def gerar_pdf_diagnostico_completo(diagnostico_data, usuario_data, perguntas_df_geracao, respostas_coletadas_geracao, medias_categorias_geracao):
    try:
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
            for cat_pdf, media_cat_pdf in medias_categorias_geracao.items():
                pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat_pdf}: {media_cat_pdf}"))
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
        categorias_unicas_pdf = []
        if perguntas_df_geracao is not None and "Categoria" in perguntas_df_geracao.columns: 
            categorias_unicas_pdf = perguntas_df_geracao["Categoria"].unique()
        
        for categoria_pdf_det in categorias_unicas_pdf:
            pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria_pdf_det}"))
            pdf.set_font("Arial", size=9)
            perguntas_cat_pdf_det = perguntas_df_geracao[perguntas_df_geracao["Categoria"] == categoria_pdf_det]
            for _, p_row_pdf_det in perguntas_cat_pdf_det.iterrows():
                txt_p_pdf_det = p_row_pdf_det["Pergunta"]
                resp_p_pdf_det = respostas_coletadas_geracao.get(txt_p_pdf_det) # Do form atual
                if resp_p_pdf_det is None: # Ou de dados salvos (quando admin baixa)
                    resp_p_pdf_det = diagnostico_data.get(txt_p_pdf_det, "N/R")

                if isinstance(txt_p_pdf_det, str) and "[Matriz GUT]" in txt_p_pdf_det: 
                    g_pdf, u_pdf, t_pdf = 0,0,0
                    if isinstance(resp_p_pdf_det, dict): 
                        g_pdf,u_pdf,t_pdf = resp_p_pdf_det.get("G",0), resp_p_pdf_det.get("U",0), resp_p_pdf_det.get("T",0)
                    elif isinstance(resp_p_pdf_det, str): 
                        try: 
                            gut_data_pdf = json.loads(resp_p_pdf_det.replace("'", "\""))
                            g_pdf,u_pdf,t_pdf = gut_data_pdf.get("G",0), gut_data_pdf.get("U",0), gut_data_pdf.get("T",0)
                        except: pass 
                    score_gut_item_pdf = g_pdf*u_pdf*t_pdf
                    pdf.multi_cell(0,6,pdf_safe_text_output(f"  - {txt_p_pdf_det.replace(' [Matriz GUT]','')}: G={g_pdf}, U={u_pdf}, T={t_pdf} (Score: {score_gut_item_pdf})"))
                elif isinstance(resp_p_pdf_det, (int, float, str)): 
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {txt_p_pdf_det}: {resp_p_pdf_det}"))
            pdf.ln(2)
        pdf.ln(3)
        
        pdf.add_page(); pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf.ln(5)
        pdf.set_font("Arial", size=10)
        gut_cards_pdf = [] 
        for pergunta_pdf_k, resp_pdf_k_val in respostas_coletadas_geracao.items(): 
            if isinstance(pergunta_pdf_k, str) and "[Matriz GUT]" in pergunta_pdf_k:
                g_k, u_k, t_k = 0,0,0
                if isinstance(resp_pdf_k_val, dict):
                    g_k, u_k, t_k = resp_pdf_k_val.get("G",0), resp_pdf_k_val.get("U",0), resp_pdf_k_val.get("T",0)
                elif isinstance(resp_pdf_k_val, str): 
                    try: 
                        gut_data_k = json.loads(resp_pdf_k_val.replace("'", "\""))
                        g_k,u_k,t_k = gut_data_k.get("G",0), gut_data_k.get("U",0), gut_data_k.get("T",0)
                    except: pass
                
                score_gut_total_k_pdf = g_k * u_k * t_k
                prazo_k_pdf = "N/A"
                if score_gut_total_k_pdf >= 75: prazo_k_pdf = "15 dias"
                elif score_gut_total_k_pdf >= 40: prazo_k_pdf = "30 dias"
                elif score_gut_total_k_pdf >= 20: prazo_k_pdf = "45 dias"
                elif score_gut_total_k_pdf > 0: prazo_k_pdf = "60 dias"
                else: continue
                if prazo_k_pdf != "N/A":
                    gut_cards_pdf.append({"Tarefa": pergunta_pdf_k.replace(" [Matriz GUT]", ""),"Prazo": prazo_k_pdf, "Score": score_gut_total_k_pdf})
        if gut_cards_pdf:
            gut_cards_pdf_sorted = sorted(gut_cards_pdf, key=lambda x_pdf: (int(x_pdf["Prazo"].split(" ")[0]), -x_pdf["Score"])) 
            for card_item_pdf in gut_cards_pdf_sorted: 
                 pdf.multi_cell(0, 6, pdf_safe_text_output(f"Prazo: {card_item_pdf['Prazo']} - Tarefa: {card_item_pdf['Tarefa']} (Score GUT: {card_item_pdf['Score']})"))
        else: pdf.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_final_pdf:
            pdf_path_final_pdf = tmpfile_final_pdf.name
            pdf.output(pdf_path_final_pdf)
        return pdf_path_final_pdf
    except Exception as e_pdf_main:
        st.error(f"Erro crítico ao gerar PDF: {e_pdf_main}")
        st.exception(e_pdf_main)
        return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_final")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_final"): 
        usuario_admin_login = st.text_input("Usuário", key="admin_user_login_final") 
        senha_admin_login = st.text_input("Senha", type="password", key="admin_pass_login_final")
        entrar_admin_login = st.form_submit_button("Entrar")
    if entrar_admin_login:
        try:
            df_admin_login_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            admin_encontrado = df_admin_login_creds[
                (df_admin_login_creds["Usuario"] == usuario_admin_login) & 
                (df_admin_login_creds["Senha"] == senha_admin_login)
            ]
            if not admin_encontrado.empty:
                st.session_state.admin_logado = True
                st.success("Login de administrador bem-sucedido!")
                st.session_state.trigger_admin_rerun = True; st.rerun() 
            else: st.error("Usuário ou senha inválidos.")
        except FileNotFoundError: st.error(f"Arquivo {admin_credenciais_csv} não encontrado.")
        except pd.errors.EmptyDataError: st.error(f"Arquivo {admin_credenciais_csv} está vazio.")
        except Exception as e_login_admin_final: st.error(f"Erro no login: {e_login_admin_final}"); st.exception(e_login_admin_final)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_final"): 
        cnpj_cli_login = st.text_input("CNPJ", key="cli_cnpj_login_final") 
        senha_cli_login = st.text_input("Senha", type="password", key="cli_pass_login_final") 
        acessar_cli_login = st.form_submit_button("Entrar")
    if acessar_cli_login:
        try:
            if not os.path.exists(usuarios_csv): st.error(f"Arquivo {usuarios_csv} não encontrado."); st.stop()
            usuarios_login_df = pd.read_csv(usuarios_csv, encoding='utf-8')
            if not os.path.exists(usuarios_bloqueados_csv): st.error(f"Arquivo {usuarios_bloqueados_csv} não encontrado."); st.stop()
            bloqueados_login_df = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
            
            if cnpj_cli_login in bloqueados_login_df["CNPJ"].astype(str).values: 
                st.error("CNPJ bloqueado."); st.stop()
            user_match_li = usuarios_login_df[(usuarios_login_df["CNPJ"].astype(str) == str(cnpj_cli_login)) & (usuarios_login_df["Senha"] == senha_cli_login)]
            if user_match_li.empty: st.error("CNPJ ou senha inválidos."); st.stop()
            
            st.session_state.cliente_logado = True
            st.session_state.cnpj = str(cnpj_cli_login) 
            st.session_state.user = user_match_li.iloc[0].to_dict() 
            st.session_state.inicio_sessao_cliente = time.time()
            registrar_acao(st.session_state.cnpj, "Login", "Usuário realizou login.")
            st.session_state.cliente_page = "Painel Principal"
            st.success("Login realizado com sucesso!"); st.session_state.trigger_cliente_rerun = True; st.rerun() 
        except FileNotFoundError as e_login_cli_fnf_final: st.error(f"Arquivo não encontrado: {e_login_cli_fnf_final.filename}.")
        except pd.errors.EmptyDataError as e_login_cli_empty_final: st.error(f"Arquivo de usuários ou bloqueados está vazio: {e_login_cli_empty_final}")
        except Exception as e_login_cli_final: st.error(f"Erro no login do cliente: {e_login_cli_final}"); st.exception(e_login_cli_final)
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    try:
        st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
        
        DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}"

        st.session_state.cliente_page = st.sidebar.radio(
            "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
            index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page),
            key="cliente_menu_radio_final_v2"
        )
        if st.sidebar.button("⬅️ Sair do Portal Cliente"):
            keys_to_del_cli_logout_final = ['cliente_logado', 'cnpj', 'user', 'inicio_sessao_cliente', 
                                           'diagnostico_enviado', 'cliente_page', DIAGNOSTICO_FORM_ID_KEY_USER]
            temp_resp_key_logout_final = f"temp_respostas_{st.session_state.get(DIAGNOSTICO_FORM_ID_KEY_USER,'')}"
            if temp_resp_key_logout_final in st.session_state:
                keys_to_del_cli_logout_final.append(temp_resp_key_logout_final)
            for key_cd_lo_final in keys_to_del_cli_logout_final:
                if key_cd_lo_final in st.session_state: del st.session_state[key_cd_lo_final]
            st.rerun()

        if st.session_state.cliente_page == "Painel Principal":
            st.subheader("📌 Meu Painel de Diagnósticos")
            with st.expander("📖 Instruções e Informações", expanded=True):
                st.markdown("- Visualize seus diagnósticos anteriores e sua evolução.")
                st.markdown("- Acompanhe seu plano de ação no Kanban.")
                st.markdown("- Para um novo diagnóstico, selecione 'Novo Diagnóstico' no menu ao lado.")
            
            if st.session_state.get("diagnostico_enviado", False):
                st.success("🎯 Último diagnóstico enviado com sucesso!"); st.session_state.diagnostico_enviado = False
            
            st.subheader("📁 Diagnósticos Anteriores")
            try:
                df_antigos_cli_pp_final = pd.read_csv(arquivo_csv, encoding='utf-8')
                df_cliente_view_pp_final = df_antigos_cli_pp_final[df_antigos_cli_pp_final["CNPJ"].astype(str) == st.session_state.cnpj]
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                df_cliente_view_pp_final = pd.DataFrame()
            
            if df_cliente_view_pp_final.empty: 
                st.info("Nenhum diagnóstico anterior. Comece um novo no menu ao lado.")
            else:
                df_cliente_view_pp_final = df_cliente_view_pp_final.sort_values(by="Data", ascending=False)
                for idx_cv_pp_final, row_cv_pp_final in df_cliente_view_pp_final.iterrows():
                    with st.expander(f"📅 {row_cv_pp_final['Data']} - {row_cv_pp_final['Empresa']}"):
                        cols_diag_cli = st.columns(2)
                        with cols_diag_cli[0]:
                            st.metric("Média Geral", f"{row_cv_pp_final.get('Média Geral', 0.0):.2f}")
                        with cols_diag_cli[1]:
                            st.metric("GUT Média (G*U*T)", f"{row_cv_pp_final.get('GUT Média', 0.0):.2f}")
                        
                        st.write(f"**Resumo (Cliente):** {row_cv_pp_final.get('Diagnóstico', 'N/P')}")
                        
                        st.markdown("**Médias por Categoria:**")
                        found_cat_media_cv_final = False
                        cat_cols = [col for col in row_cv_pp_final.index if col.startswith("Media_Cat_")]
                        if cat_cols:
                            num_cat_cols = len(cat_cols)
                            display_cols = st.columns(num_cat_cols if num_cat_cols <= 4 else 4) # Max 4 cols de categoria por linha
                            col_idx = 0
                            for col_name_cv_final in cat_cols:
                                cat_name_display_cv_final = col_name_cv_final.replace("Media_Cat_", "").replace("_", " ")
                                with display_cols[col_idx % len(display_cols)]: # Cicla pelas colunas de display
                                     st.metric(f"Média {cat_name_display_cv_final}", f"{row_cv_pp_final.get(col_name_cv_final, 0.0):.2f}")
                                col_idx += 1
                                found_cat_media_cv_final = True
                        if not found_cat_media_cv_final: st.caption("  Nenhuma média por categoria.")

                        analise_cli_val_cv_final = row_cv_pp_final.get("Análise do Cliente", "")
                        analise_cli_cv_final = st.text_area("🧠 Minha Análise sobre este Diagnóstico:", value=analise_cli_val_cv_final, key=f"analise_cv_final_{row_cv_pp_final.name}")
                        if st.button("💾 Salvar Minha Análise", key=f"salvar_analise_cv_final_{row_cv_pp_final.name}"):
                            try:
                                df_antigos_upd_cv_final = pd.read_csv(arquivo_csv, encoding='utf-8') 
                                df_antigos_upd_cv_final.loc[row_cv_pp_final.name, "Análise do Cliente"] = analise_cli_cv_final 
                                df_antigos_upd_cv_final.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                registrar_acao(st.session_state.cnpj, "Análise Cliente", f"Editou análise de {row_cv_pp_final['Data']}")
                                st.success("Análise salva!"); st.rerun()
                            except Exception as e_save_analise_final: st.error(f"Erro ao salvar análise: {e_save_analise_final}")
                        
                        com_admin_val_cv_final = row_cv_pp_final.get("Comentarios_Admin", "")
                        if com_admin_val_cv_final and not pd.isna(com_admin_val_cv_final):
                            st.markdown("**Comentários do Consultor:**"); st.info(f"{com_admin_val_cv_final}")
                        else: st.caption("Nenhum comentário do consultor.")
                        st.markdown("---")
                
                st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
                gut_cards_painel_final = []
                if not df_cliente_view_pp_final.empty:
                    latest_diag_row_painel_final = df_cliente_view_pp_final.iloc[0]
                    for pergunta_p_final, resposta_p_val_str_final in latest_diag_row_painel_final.items():
                        if isinstance(pergunta_p_final, str) and "[Matriz GUT]" in pergunta_p_final:
                            try:
                                if pd.notna(resposta_p_val_str_final) and isinstance(resposta_p_val_str_final, str):
                                    gut_data_final = json.loads(resposta_p_val_str_final.replace("'", "\"")) 
                                    g_final = int(gut_data_final.get("G", 0))
                                    u_final = int(gut_data_final.get("U", 0))
                                    t_final = int(gut_data_final.get("T", 0))
                                    score_gut_total_p_final = g_final * u_final * t_final
                                    
                                    prazo_p_final = "N/A"
                                    if score_gut_total_p_final >= 75: prazo_p_final = "15 dias"
                                    elif score_gut_total_p_final >= 40: prazo_p_final = "30 dias"
                                    elif score_gut_total_p_final >= 20: prazo_p_final = "45 dias"
                                    elif score_gut_total_p_final > 0: prazo_p_final = "60 dias"
                                    else: continue 

                                    if prazo_p_final != "N/A":
                                        gut_cards_painel_final.append({
                                            "Tarefa": pergunta_p_final.replace(" [Matriz GUT]", ""), 
                                            "Prazo": prazo_p_final, "Score": score_gut_total_p_final, 
                                            "Responsável": st.session_state.user.get("Empresa", "N/D")
                                        })
                            except (json.JSONDecodeError, ValueError, TypeError) as e_k_final:
                                st.warning(f"Erro ao processar GUT p/ Kanban: '{pergunta_p_final}' ({resposta_p_val_str_final}). Erro: {e_k_final}")
                
                if gut_cards_painel_final:
                    gut_cards_sorted_p_final = sorted(gut_cards_painel_final, key=lambda x_final: x_final["Score"], reverse=True)
                    prazos_def_p_final = sorted(list(set(card_final["Prazo"] for card_final in gut_cards_sorted_p_final)), key=lambda x_d_final: int(x_d_final.split(" ")[0])) 
                    if prazos_def_p_final:
                        cols_kanban_p_final = st.columns(len(prazos_def_p_final))
                        for idx_kp_final, prazo_col_kp_final in enumerate(prazos_def_p_final):
                            with cols_kanban_p_final[idx_kp_final]:
                                st.markdown(f"#### ⏱️ {prazo_col_kp_final}")
                                for card_item_kp_final in gut_cards_sorted_p_final:
                                    if card_item_kp_final["Prazo"] == prazo_col_kp_final:
                                        st.markdown(f"""<div class="custom-card"><b>{card_item_kp_final['Tarefa']}</b> (Score GUT: {card_item_kp_final['Score']})<br><small><i>👤 {card_item_kp_final['Responsável']}</i></small></div>""", unsafe_allow_html=True)
                else: st.info("Nenhuma ação prioritária para o Kanban (GUT).")
                
                st.subheader("📈 Comparativo de Evolução")
                if len(df_cliente_view_pp_final) > 1:
                    grafico_comp_ev_final = df_cliente_view_pp_final.sort_values(by="Data")
                    grafico_comp_ev_final["Data"] = pd.to_datetime(grafico_comp_ev_final["Data"])
                    colunas_plot_comp_final = ['Média Geral', 'GUT Média'] 
                    for col_g_comp_final in grafico_comp_ev_final.columns:
                        if col_g_comp_final.startswith("Media_Cat_") and pd.api.types.is_numeric_dtype(grafico_comp_ev_final[col_g_comp_final]):
                            colunas_plot_comp_final.append(col_g_comp_final)
                    for col_plot_c_final in colunas_plot_comp_final:
                        if col_plot_c_final in grafico_comp_ev_final.columns: grafico_comp_ev_final[col_plot_c_final] = pd.to_numeric(grafico_comp_ev_final[col_plot_c_final], errors='coerce')
                    
                    colunas_validas_plot_final = [c_final for c_final in colunas_plot_comp_final if c_final in grafico_comp_ev_final.columns and pd.api.types.is_numeric_dtype(grafico_comp_ev_final[c_final])]
                    if colunas_validas_plot_final:
                        st.line_chart(grafico_comp_ev_final.set_index("Data")[colunas_validas_plot_final].dropna(axis=1, how='all'))
                    
                    st.subheader("📊 Comparação Entre Diagnósticos") 
                    opcoes_cli_final = grafico_comp_ev_final["Data"].astype(str).tolist()
                    if len(opcoes_cli_final) >= 2:
                        diag_atual_idx_final, diag_anterior_idx_final = len(opcoes_cli_final)-1, len(opcoes_cli_final)-2
                        diag_atual_sel_cli_final = st.selectbox("Diagnóstico mais recente:", opcoes_cli_final, index=diag_atual_idx_final, key="diag_atual_sel_cli_final")
                        diag_anterior_sel_cli_final = st.selectbox("Diagnóstico anterior:", opcoes_cli_final, index=diag_anterior_idx_final, key="diag_anterior_sel_cli_final")
                        atual_cli_final = grafico_comp_ev_final[grafico_comp_ev_final["Data"].astype(str) == diag_atual_sel_cli_final].iloc[0]
                        anterior_cli_final = grafico_comp_ev_final[grafico_comp_ev_final["Data"].astype(str) == diag_anterior_sel_cli_final].iloc[0]
                        st.write(f"### 📅 Comparando {diag_anterior_sel_cli_final.split(' ')[0]} ⟶ {diag_atual_sel_cli_final.split(' ')[0]}")
                        cols_excluir_comp_final = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
                        variaveis_comp_final = [col_f for col_f in grafico_comp_ev_final.columns if col_f not in cols_excluir_comp_final and pd.api.types.is_numeric_dtype(grafico_comp_ev_final[col_f])]
                        if variaveis_comp_final:
                            comp_data_final = []
                            for v_comp_final in variaveis_comp_final:
                                val_ant_c_final = pd.to_numeric(anterior_cli_final.get(v_comp_final), errors='coerce')
                                val_atu_c_final = pd.to_numeric(atual_cli_final.get(v_comp_final), errors='coerce')
                                evolucao_c_final = "➖ Igual"
                                if pd.notna(val_ant_c_final) and pd.notna(val_atu_c_final):
                                    if val_atu_c_final > val_ant_c_final: evolucao_c_final = "🔼 Melhorou"
                                    elif val_atu_c_final < val_ant_c_final: evolucao_c_final = "🔽 Piorou"
                                display_name_comp_final = v_comp_final.replace("Media_Cat_", "Média ").replace("_", " ")
                                if "[Pontuação (0-10)]" in display_name_comp_final or "[Pontuação (0-5) + Matriz GUT]" in display_name_comp_final or "[Matriz GUT]" in display_name_comp_final:
                                    display_name_comp_final = display_name_comp_final.split(" [")[0] 
                                comp_data_final.append({"Indicador": display_name_comp_final, "Anterior": val_ant_c_final if pd.notna(val_ant_c_final) else "N/A", "Atual": val_atu_c_final if pd.notna(val_atu_c_final) else "N/A", "Evolução": evolucao_c_final})
                            st.dataframe(pd.DataFrame(comp_data_final))
                        else: st.info("Sem dados numéricos para comparação.")
                    else: st.info("Pelo menos dois diagnósticos para comparação.")
                else: st.info("Pelo menos dois diagnósticos para comparativos.")

        elif st.session_state.cliente_page == "Novo Diagnóstico":
            st.subheader("📋 Formulário de Novo Diagnóstico")
            
            DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}" # Definido corretamente aqui
            if DIAGNOSTICO_FORM_ID_KEY_USER not in st.session_state:
                st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER] = datetime.now().strftime("%Y%m%d%H%M%S%f")
            form_id_sufixo_nd_final = st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER]

            temp_respostas_key_nd_final = f"temp_respostas_{form_id_sufixo_nd_final}"
            if temp_respostas_key_nd_final not in st.session_state:
                st.session_state[temp_respostas_key_nd_final] = {}
            
            respostas_form_coletadas_nd_final = st.session_state[temp_respostas_key_nd_final]
            
            try:
                perguntas_df_diag_final = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_diag_final.columns: 
                    perguntas_df_diag_final["Categoria"] = "Geral"
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                st.error(f"Arquivo de perguntas ({perguntas_csv}) não encontrado ou vazio."); st.stop()
            
            if perguntas_df_diag_final.empty: 
                st.warning("Nenhuma pergunta cadastrada."); st.stop()
            
            total_perguntas_diag_final = len(perguntas_df_diag_final)
            respondidas_count_diag_final = 0 
            
            if "Categoria" not in perguntas_df_diag_final.columns: # Checagem final
                st.error("Coluna 'Categoria' não encontrada no arquivo de perguntas."); st.stop()

            categorias_unicas_diag_final = perguntas_df_diag_final["Categoria"].unique()
            
            with st.form(key=f"diagnostico_form_completo_{form_id_sufixo_nd_final}"):
                if total_perguntas_diag_final == 0:
                    st.warning("Nenhuma pergunta disponível.")
                else:
                    for categoria_diag_final in categorias_unicas_diag_final:
                        st.markdown(f"#### Categoria: {categoria_diag_final}")
                        perguntas_cat_diag_final = perguntas_df_diag_final[perguntas_df_diag_final["Categoria"] == categoria_diag_final]
                        
                        if perguntas_cat_diag_final.empty: continue

                        for idx_diag_f_final, row_diag_f_final in perguntas_cat_diag_final.iterrows():
                            texto_pergunta_diag_final = str(row_diag_f_final["Pergunta"]) 
                            widget_base_key_final = f"q_form_final_{idx_diag_f_final}" 

                            if "[Matriz GUT]" in texto_pergunta_diag_final:
                                st.markdown(f"**{texto_pergunta_diag_final.replace(' [Matriz GUT]', '')}**")
                                cols_gut_final = st.columns(3)
                                gut_current_vals_final = respostas_form_coletadas_nd_final.get(texto_pergunta_diag_final, {"G":0, "U":0, "T":0})
                                with cols_gut_final[0]: g_val_final = st.slider("Gravidade (0-5)", 0, 5, value=int(gut_current_vals_final.get("G",0)), key=f"{widget_base_key_final}_G")
                                with cols_gut_final[1]: u_val_final = st.slider("Urgência (0-5)", 0, 5, value=int(gut_current_vals_final.get("U",0)), key=f"{widget_base_key_final}_U")
                                with cols_gut_final[2]: t_val_final = st.slider("Tendência (0-5)", 0, 5, value=int(gut_current_vals_final.get("T",0)), key=f"{widget_base_key_final}_T")
                                respostas_form_coletadas_nd_final[texto_pergunta_diag_final] = {"G": g_val_final, "U": u_val_final, "T": t_val_final}
                                if g_val_final > 0 or u_val_final > 0 or t_val_final > 0 : respondidas_count_diag_final +=1
                            elif "Pontuação (0-5)" in texto_pergunta_diag_final: 
                                val_final = respostas_form_coletadas_nd_final.get(texto_pergunta_diag_final, 0)
                                respostas_form_coletadas_nd_final[texto_pergunta_diag_final] = st.slider(texto_pergunta_diag_final, 0, 5, value=int(val_final), key=widget_base_key_final) 
                                if respostas_form_coletadas_nd_final[texto_pergunta_diag_final] != 0: respondidas_count_diag_final += 1
                            elif "Pontuação (0-10)" in texto_pergunta_diag_final:
                                val_final = respostas_form_coletadas_nd_final.get(texto_pergunta_diag_final, 0)
                                respostas_form_coletadas_nd_final[texto_pergunta_diag_final] = st.slider(texto_pergunta_diag_final, 0, 10, value=int(val_final), key=widget_base_key_final)
                                if respostas_form_coletadas_nd_final[texto_pergunta_diag_final] != 0: respondidas_count_diag_final += 1
                            elif "Texto Aberto" in texto_pergunta_diag_final:
                                val_final = respostas_form_coletadas_nd_final.get(texto_pergunta_diag_final, "")
                                respostas_form_coletadas_nd_final[texto_pergunta_diag_final] = st.text_area(texto_pergunta_diag_final, value=str(val_final), key=widget_base_key_final)
                                if respostas_form_coletadas_nd_final[texto_pergunta_diag_final].strip() != "": respondidas_count_diag_final += 1
                            elif "Escala" in texto_pergunta_diag_final: 
                                opcoes_escala_diag_final = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"] 
                                val_final = respostas_form_coletadas_nd_final.get(texto_pergunta_diag_final, "Selecione")
                                idx_sel_final = opcoes_escala_diag_final.index(val_final) if val_final in opcoes_escala_diag_final else 0
                                respostas_form_coletadas_nd_final[texto_pergunta_diag_final] = st.selectbox(texto_pergunta_diag_final, opcoes_escala_diag_final, index=idx_sel_final, key=widget_base_key_final)
                                if respostas_form_coletadas_nd_final[texto_pergunta_diag_final] != "Selecione": respondidas_count_diag_final += 1
                            else: 
                                val_final = respostas_form_coletadas_nd_final.get(texto_pergunta_diag_final, 0)
                                respostas_form_coletadas_nd_final[texto_pergunta_diag_final] = st.slider(texto_pergunta_diag_final, 0, 10, value=int(val_final), key=widget_base_key_final)
                                if respostas_form_coletadas_nd_final[texto_pergunta_diag_final] != 0: respondidas_count_diag_final += 1
                        st.divider()
                
                progresso_diag_final = round((respondidas_count_diag_final / total_perguntas_diag_final) * 100) if total_perguntas_diag_final > 0 else 0
                st.info(f"📊 Progresso: {respondidas_count_diag_final} de {total_perguntas_diag_final} respondidas ({progresso_diag_final}%)")
                
                obs_cli_diag_form_final = st.text_area("Sua Análise/Observações (opcional):", value=respostas_form_coletadas_nd_final.get("__obs_cliente__", ""), key=f"obs_cli_diag_final_{form_id_sufixo_nd_final}")
                respostas_form_coletadas_nd_final["__obs_cliente__"] = obs_cli_diag_form_final
                
                diag_resumo_cli_diag_final = st.text_area("✍️ Resumo/principais insights (para PDF):", value=respostas_form_coletadas_nd_final.get("__resumo_cliente__", ""), key=f"diag_resumo_diag_final_{form_id_sufixo_nd_final}")
                respostas_form_coletadas_nd_final["__resumo_cliente__"] = diag_resumo_cli_diag_final

                enviar_diagnostico_btn_final = st.form_submit_button("✔️ Enviar Diagnóstico")

            if enviar_diagnostico_btn_final:
                if respondidas_count_diag_final < total_perguntas_diag_final: st.warning("Responda todas as perguntas.")
                elif not respostas_form_coletadas_nd_final["__resumo_cliente__"].strip(): st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
                else:
                    soma_total_gut_scores_final, count_gut_perguntas_final = 0, 0
                    respostas_finais_para_salvar_final = {}

                    for pergunta_env_final, resposta_env_final in respostas_form_coletadas_nd_final.items():
                        if pergunta_env_final.startswith("__"): continue 
                        if isinstance(pergunta_env_final, str) and "[Matriz GUT]" in pergunta_env_final and isinstance(resposta_env_final, dict):
                            respostas_finais_para_salvar_final[pergunta_env_final] = json.dumps(resposta_env_final) 
                            g_f, u_f, t_f = resposta_env_final.get("G",0), resposta_env_final.get("U",0), resposta_env_final.get("T",0)
                            soma_total_gut_scores_final += (g_f * u_f * t_f)
                            count_gut_perguntas_final +=1
                        else:
                            respostas_finais_para_salvar_final[pergunta_env_final] = resposta_env_final

                    gut_media_calc_final = round(soma_total_gut_scores_final / count_gut_perguntas_final, 2) if count_gut_perguntas_final > 0 else 0.0
                    numeric_resp_calc_final = [v_f for k_f, v_f in respostas_finais_para_salvar_final.items() if isinstance(v_f, (int, float)) and ("Pontuação (0-10)" in k_f or "Pontuação (0-5)" in k_f)] 
                    media_geral_calc_final_val = round(sum(numeric_resp_calc_final) / len(numeric_resp_calc_final), 2) if numeric_resp_calc_final else 0.0
                    empresa_nome_final_val = st.session_state.user.get("Empresa", "N/D")
                    
                    nova_linha_final_val = {
                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": st.session_state.cnpj,
                        "Nome": st.session_state.user.get("CNPJ", ""), "Email": "", "Empresa": empresa_nome_final_val,
                        "Média Geral": media_geral_calc_final_val, "GUT Média": gut_media_calc_final, 
                        "Observações": "", 
                        "Análise do Cliente": respostas_form_coletadas_nd_final.get("__obs_cliente__",""), 
                        "Diagnóstico": respostas_form_coletadas_nd_final.get("__resumo_cliente__",""), 
                        "Comentarios_Admin": ""
                    }
                    nova_linha_final_val.update(respostas_finais_para_salvar_final)

                    medias_por_categoria_final_val = {}
                    for cat_final_calc_val in categorias_unicas_diag_final:
                        perguntas_cat_final_df_val = perguntas_df_diag_final[perguntas_df_diag_final["Categoria"] == cat_final_calc_val]
                        soma_cat_final_val, cont_num_cat_final_val = 0, 0
                        for _, p_row_final_val in perguntas_cat_final_df_val.iterrows():
                            txt_p_final_val = p_row_final_val["Pergunta"]
                            resp_p_final_val = respostas_form_coletadas_nd_final.get(txt_p_final_val)
                            if isinstance(resp_p_final_val, (int, float)) and \
                               (isinstance(txt_p_final_val, str) and "[Matriz GUT]" not in txt_p_final_val) and \
                               (isinstance(txt_p_final_val, str) and ("Pontuação (0-10)" in txt_p_final_val or "Pontuação (0-5)" in txt_p_final_val)):
                                soma_cat_final_val += resp_p_final_val
                                cont_num_cat_final_val += 1
                        media_c_final_val = round(soma_cat_final_val / cont_num_cat_final_val, 2) if cont_num_cat_final_val > 0 else 0.0
                        nome_col_media_cat_final_val = f"Media_Cat_{sanitize_column_name(cat_final_calc_val)}"
                        nova_linha_final_val[nome_col_media_cat_final_val] = media_c_final_val
                        medias_por_categoria_final_val[cat_final_calc_val] = media_c_final_val

                    try: df_diag_todos_final_val = pd.read_csv(arquivo_csv, encoding='utf-8')
                    except (FileNotFoundError, pd.errors.EmptyDataError): df_diag_todos_final_val = pd.DataFrame() 
                    
                    for col_f_save_final_val in nova_linha_final_val.keys(): 
                        if col_f_save_final_val not in df_diag_todos_final_val.columns: df_diag_todos_final_val[col_f_save_final_val] = pd.NA 
                    df_diag_todos_final_val = pd.concat([df_diag_todos_final_val, pd.DataFrame([nova_linha_final_val])], ignore_index=True)
                    df_diag_todos_final_val.to_csv(arquivo_csv, index=False, encoding='utf-8')
                    
                    st.success("Diagnóstico enviado com sucesso!")
                    registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", "Cliente enviou novo diagnóstico.")
                    
                    pdf_path_final_val = gerar_pdf_diagnostico_completo(
                        diagnostico_data=nova_linha_final_val, 
                        usuario_data=st.session_state.user, 
                        perguntas_df_geracao=perguntas_df_diag_final, 
                        respostas_coletadas_geracao=respostas_form_coletadas_nd_final,
                        medias_categorias_geracao=medias_por_categoria_final_val
                    )
                    if pdf_path_final_val:
                        with open(pdf_path_final_val, "rb") as f_pdf_final_val:
                            st.download_button(label="📄 Baixar PDF do Diagnóstico", data=f_pdf_final_val, 
                                           file_name=f"diagnostico_{sanitize_column_name(empresa_nome_final_val)}_{datetime.now().strftime('%Y%m%d')}.pdf", 
                                           mime="application/pdf", key="download_pdf_cliente_final_val")
                        registrar_acao(st.session_state.cnpj, "Download PDF", "Baixou PDF do novo diagnóstico.")
                    
                    if DIAGNOSTICO_FORM_ID_KEY_USER in st.session_state: del st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER]
                    if temp_respostas_key_nd_final in st.session_state: del st.session_state[temp_respostas_key_nd_final]
                    
                    st.session_state.diagnostico_enviado = True
                    st.session_state.cliente_page = "Painel Principal" 
                    st.rerun()
    except Exception as e_cliente_area_final:
        st.error(f"Ocorreu um erro na área do cliente: {e_cliente_area_final}")
        st.exception(e_cliente_area_final) 


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    st.sidebar.image("https://raw.githubusercontent.com/AndersonCRMG/AppDiagnostico/main/Logo%20Transparente%20(1).png", width=100)
    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("🚪 Sair do Painel Admin"):
        st.session_state.admin_logado = False; st.rerun() 

    menu_admin_main_view_final = st.sidebar.selectbox( 
        "Funcionalidades Admin:",
        ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Perguntas", 
         "Gerenciar Clientes", "Gerenciar Administradores"],
        key="admin_menu_selectbox_main_page_view_final" 
    )
    st.header(f"🔑 Painel Admin: {menu_admin_main_view_final}")

    try: 
        if menu_admin_main_view_final == "Visão Geral e Diagnósticos":
            st.write("--- DEBUG: Entrando na seção 'Visão Geral e Diagnósticos' ---") 
            st.subheader("📊 Visão Geral dos Diagnósticos")

            diagnosticos_df_admin_geral_final = None 
            admin_data_loaded_successfully_final = False

            try:
                st.write(f"DEBUG: Verificando existência do arquivo: {arquivo_csv}")
                if not os.path.exists(arquivo_csv):
                    st.warning(f"ARQUIVO NÃO ENCONTRADO: ({arquivo_csv}).")
                elif os.path.getsize(arquivo_csv) == 0:
                    st.warning(f"ARQUIVO VAZIO (0 bytes): ({arquivo_csv}).")
                else:
                    st.write(f"DEBUG: Tentando ler o arquivo: {arquivo_csv}")
                    diagnosticos_df_admin_geral_final = pd.read_csv(arquivo_csv, encoding='utf-8')
                    st.write(f"DEBUG: Arquivo {arquivo_csv} lido. Linhas: {len(diagnosticos_df_admin_geral_final)}")
                    if diagnosticos_df_admin_geral_final.empty:
                        st.info("INFO: Arquivo de diagnósticos lido, mas vazio (sem dados).")
                    else:
                        admin_data_loaded_successfully_final = True
            except pd.errors.EmptyDataError: 
                st.warning(f"AVISO (Pandas EmptyDataError): Arquivo ({arquivo_csv}) parece vazio ou mal formatado.")
            except Exception as e_load_diag_admin_final_section:
                st.error(f"ERRO AO CARREGAR DIAGNÓSTICOS: {e_load_diag_admin_final_section}")
                st.exception(e_load_diag_admin_final_section)
            
            st.write(f"DEBUG: Status final do carregamento: admin_data_loaded_successfully_final = {admin_data_loaded_successfully_final}")

            if admin_data_loaded_successfully_final and diagnosticos_df_admin_geral_final is not None and not diagnosticos_df_admin_geral_final.empty:
                st.write("DEBUG: DADOS CARREGADOS. Renderizando conteúdo da Visão Geral...")
                
                st.markdown("#### Indicadores Gerais")
                col_ig1_final, col_ig2_final, col_ig3_final = st.columns(3)
                with col_ig1_final: st.metric("📦 Total de Diagnósticos", len(diagnosticos_df_admin_geral_final))
                with col_ig2_final:
                    media_geral_todos_adm_final = pd.to_numeric(diagnosticos_df_admin_geral_final["Média Geral"], errors='coerce').mean()
                    st.metric("📈 Média Geral (Todos)", f"{media_geral_todos_adm_final:.2f}" if pd.notna(media_geral_todos_adm_final) else "N/A")
                with col_ig3_final:
                    if "GUT Média" in diagnosticos_df_admin_geral_final.columns:
                        gut_media_todos_adm_final = pd.to_numeric(diagnosticos_df_admin_geral_final["GUT Média"], errors='coerce').mean()
                        st.metric("🔥 GUT Média (G*U*T)", f"{gut_media_todos_adm_final:.2f}" if pd.notna(gut_media_todos_adm_final) else "N/A")
                    else: st.metric("🔥 GUT Média (G*U*T)", "N/A")
                st.divider()

                st.markdown("#### Evolução Mensal dos Diagnósticos")
                df_diag_vis_adm_final = diagnosticos_df_admin_geral_final.copy()
                df_diag_vis_adm_final["Data"] = pd.to_datetime(df_diag_vis_adm_final["Data"], errors="coerce")
                df_diag_vis_adm_final = df_diag_vis_adm_final.dropna(subset=["Data"])
                if not df_diag_vis_adm_final.empty:
                    df_diag_vis_adm_final["Mês/Ano"] = df_diag_vis_adm_final["Data"].dt.to_period("M").astype(str) 
                    df_diag_vis_adm_final["Média Geral"] = pd.to_numeric(df_diag_vis_adm_final["Média Geral"], errors='coerce')
                    df_diag_vis_adm_final["GUT Média"] = pd.to_numeric(df_diag_vis_adm_final.get("GUT Média"), errors='coerce') if "GUT Média" in df_diag_vis_adm_final else pd.Series(dtype='float64', index=df_diag_vis_adm_final.index)
                    
                    resumo_mensal_adm_final = df_diag_vis_adm_final.groupby("Mês/Ano").agg(
                        Diagnósticos_Realizados=("CNPJ", "count"), 
                        Média_Geral_Mensal=("Média Geral", "mean"),
                        GUT_Média_Mensal=("GUT Média", "mean")
                    ).reset_index().sort_values("Mês/Ano")
                    resumo_mensal_adm_final["Mês/Ano_Display"] = pd.to_datetime(resumo_mensal_adm_final["Mês/Ano"], errors='coerce').dt.strftime('%b/%y')
                    
                    if not resumo_mensal_adm_final.empty:
                        fig_contagem_final = px.bar(resumo_mensal_adm_final, x="Mês/Ano_Display", y="Diagnósticos_Realizados", title="Número de Diagnósticos por Mês", labels={'Diagnósticos_Realizados':'Total Diagnósticos', "Mês/Ano_Display": "Mês/Ano"})
                        st.plotly_chart(fig_contagem_final, use_container_width=True)
                        fig_medias_final = px.line(resumo_mensal_adm_final, x="Mês/Ano_Display", y=["Média_Geral_Mensal", "GUT_Média_Mensal"], title="Médias Gerais e GUT por Mês", labels={'value':'Média', 'variable':'Indicador', "Mês/Ano_Display": "Mês/Ano"})
                        fig_medias_final.update_traces(mode='lines+markers')
                        st.plotly_chart(fig_medias_final, use_container_width=True)
                    else: st.info("Sem dados para gráficos de evolução mensal.")
                else: st.info("Sem diagnósticos com datas válidas para evolução mensal.")
                st.divider()
                
                st.markdown("#### Ranking das Empresas (Média Geral)")
                if "Empresa" in diagnosticos_df_admin_geral_final.columns and "Média Geral" in diagnosticos_df_admin_geral_final.columns:
                    diagnosticos_df_admin_geral_final["Média Geral Num"] = pd.to_numeric(diagnosticos_df_admin_geral_final["Média Geral"], errors='coerce')
                    ranking_df_final = diagnosticos_df_admin_geral_final.dropna(subset=["Média Geral Num"])
                    if not ranking_df_final.empty:
                        ranking_final = ranking_df_final.groupby("Empresa")["Média Geral Num"].mean().sort_values(ascending=False).reset_index()
                        ranking_final.index = ranking_final.index + 1
                        st.dataframe(ranking_final.rename(columns={"Média Geral Num": "Média Geral (Ranking)"}))
                    else: st.info("Sem dados para ranking.")
                else: st.info("Colunas 'Empresa' ou 'Média Geral' ausentes para ranking.")
                st.divider()

                st.markdown("#### Todos os Diagnósticos Enviados")
                st.dataframe(diagnosticos_df_admin_geral_final.sort_values(by="Data", ascending=False).reset_index(drop=True))
                csv_export_admin_geral_final_val = diagnosticos_df_admin_geral_final.to_csv(index=False).encode('utf-8') 
                st.download_button("⬇️ Exportar Todos (CSV)", csv_export_admin_geral_final_val, file_name="diagnosticos_completos.csv", mime="text/csv", key="download_all_csv_admin_final")
                st.divider()
                
                st.markdown("#### Detalhar, Comentar e Baixar PDF de Diagnóstico Específico")
                if "CNPJ" in diagnosticos_df_admin_geral_final.columns:
                    empresas_unicas_adm_final = sorted(diagnosticos_df_admin_geral_final["Empresa"].astype(str).unique().tolist())
                    empresa_selecionada_adm_final = st.selectbox("Selecione uma Empresa para detalhar:", ["Selecione..."] + empresas_unicas_adm_final, key="admin_empresa_filter_detail_final")

                    if empresa_selecionada_adm_final != "Selecione...":
                        diagnosticos_empresa_adm_final = diagnosticos_df_admin_geral_final[diagnosticos_df_admin_geral_final["Empresa"] == empresa_selecionada_adm_final].sort_values(by="Data", ascending=False)
                        if not diagnosticos_empresa_adm_final.empty:
                            diagnostico_data_selecionada_adm_final = st.selectbox("Selecione a Data do Diagnóstico:", diagnosticos_empresa_adm_final["Data"].tolist(), key="admin_data_diagnostico_select_final")
                            diagnostico_selecionado_adm_row_final = diagnosticos_empresa_adm_final[diagnosticos_empresa_adm_final["Data"] == diagnostico_data_selecionada_adm_final].iloc[0]
                            
                            st.markdown(f"**Detalhes do Diagnóstico de {diagnostico_selecionado_adm_row_final['Data']} para {empresa_selecionada_adm_final}**")
                            st.write(f"**Média Geral:** {diagnostico_selecionado_adm_row_final.get('Média Geral', 'N/A')} | **GUT Média (G*U*T):** {diagnostico_selecionado_adm_row_final.get('GUT Média', 'N/A')}")
                            
                            comentario_adm_atual_val_final = diagnostico_selecionado_adm_row_final.get("Comentarios_Admin", "")
                            if pd.isna(comentario_adm_atual_val_final): comentario_adm_atual_val_final = ""
                            novo_comentario_adm_val_final = st.text_area("Comentários do Consultor/Admin:", value=comentario_adm_atual_val_final, key=f"admin_comment_detail_final_{diagnostico_selecionado_adm_row_final.name}")
                            if st.button("💾 Salvar Comentário do Admin", key=f"save_admin_comment_detail_final_{diagnostico_selecionado_adm_row_final.name}"):
                                df_diag_save_com_adm_det_final = pd.read_csv(arquivo_csv, encoding='utf-8')
                                df_diag_save_com_adm_det_final.loc[diagnostico_selecionado_adm_row_final.name, "Comentarios_Admin"] = novo_comentario_adm_val_final
                                df_diag_save_com_adm_det_final.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                registrar_acao("ADMIN", "Comentário Admin", f"Admin comentou diag. de {diagnostico_selecionado_adm_row_final['Data']} para {empresa_selecionada_adm_final}")
                                st.success("Comentário salvo!"); st.rerun()

                            if st.button("📄 Baixar PDF deste Diagnóstico", key=f"download_pdf_admin_final_{diagnostico_selecionado_adm_row_final.name}"):
                                try:
                                    perguntas_df_pdf_adm_final = pd.read_csv(perguntas_csv, encoding='utf-8')
                                    if "Categoria" not in perguntas_df_pdf_adm_final.columns: perguntas_df_pdf_adm_final["Categoria"] = "Geral"
                                except: perguntas_df_pdf_adm_final = pd.DataFrame(columns=colunas_base_perguntas)

                                respostas_para_pdf_adm_final = diagnostico_selecionado_adm_row_final.to_dict()
                                medias_cat_pdf_adm_final = {}
                                if not perguntas_df_pdf_adm_final.empty and "Categoria" in perguntas_df_pdf_adm_final.columns:
                                    cats_unicas_pdf_adm_final = perguntas_df_pdf_adm_final["Categoria"].unique()
                                    for cat_pdf_adm_calc_final in cats_unicas_pdf_adm_final:
                                        nome_col_media_cat_pdf_final = f"Media_Cat_{sanitize_column_name(cat_pdf_adm_calc_final)}"
                                        medias_cat_pdf_adm_final[cat_pdf_adm_calc_final] = diagnostico_selecionado_adm_row_final.get(nome_col_media_cat_pdf_final, 0.0)
                                
                                try:
                                    usuarios_df_pdf_adm_final = pd.read_csv(usuarios_csv, encoding='utf-8')
                                    usuario_data_pdf_adm_final = usuarios_df_pdf_adm_final[usuarios_df_pdf_adm_final["CNPJ"] == diagnostico_selecionado_adm_row_final["CNPJ"]].iloc[0].to_dict()
                                except: usuario_data_pdf_adm_final = {"Empresa": diagnostico_selecionado_adm_row_final.get("Empresa", "N/D"), "CNPJ": diagnostico_selecionado_adm_row_final.get("CNPJ", "N/D")}

                                pdf_path_admin_download_final = gerar_pdf_diagnostico_completo(
                                    diagnostico_data=diagnostico_selecionado_adm_row_final.to_dict(), 
                                    usuario_data=usuario_data_pdf_adm_final,
                                    perguntas_df_geracao=perguntas_df_pdf_adm_final, 
                                    respostas_coletadas_geracao=respostas_para_pdf_adm_final, 
                                    medias_categorias_geracao=medias_cat_pdf_adm_final
                                )
                                if pdf_path_admin_download_final:
                                    with open(pdf_path_admin_download_final, "rb") as f_pdf_adm_dl_final:
                                        st.download_button(label="Download PDF Confirmado", data=f_pdf_adm_dl_final, 
                                                       file_name=f"diagnostico_{sanitize_column_name(empresa_selecionada_adm_final)}_{diagnostico_selecionado_adm_row_final['Data'].replace(':','-')}.pdf",
                                                       mime="application/pdf", key=f"confirm_download_pdf_admin_final_{diagnostico_selecionado_adm_row_final.name}")
                                    registrar_acao("ADMIN", "Download PDF Cliente", f"Admin baixou PDF de {diagnostico_selecionado_adm_row_final['Data']} para {empresa_selecionada_adm_final}")
                                else: st.error("Falha ao gerar o PDF para download.")
                        else: st.info(f"Nenhum diagnóstico para a empresa {empresa_selecionada_adm_final}.")
                else: st.info("Coluna 'CNPJ' não encontrada para filtro.")
            else: 
                st.warning("AVISO: Nenhum dado de diagnóstico carregado. A 'Visão Geral' está limitada.")
            st.write("--- DEBUG: FIM da seção 'Visão Geral e Diagnósticos' ---")

        elif menu_admin_main_view_final == "Histórico de Usuários":
            st.subheader("📜 Histórico de Ações dos Clientes")
            try:
                hist_df_adm_final = pd.read_csv(historico_csv, encoding='utf-8')
                if not hist_df_adm_final.empty:
                    st.dataframe(hist_df_adm_final.sort_values(by="Data", ascending=False))
                else: st.info("Nenhum histórico de ações encontrado.")
            except (FileNotFoundError, pd.errors.EmptyDataError): st.info("Arquivo de histórico não encontrado ou vazio.")
            except Exception as e_hist: st.error(f"Erro ao carregar histórico: {e_hist}")

        elif menu_admin_main_view_final == "Gerenciar Perguntas":
            st.subheader("📝 Gerenciar Perguntas do Diagnóstico")
            # ... (Código completo da seção Gerenciar Perguntas da versão anterior)
            pass

        elif menu_admin_main_view_final == "Gerenciar Clientes":
            st.subheader("👥 Gerenciar Clientes")
            # ... (Código completo da seção Gerenciar Clientes da versão anterior, com NomeContato e Telefone)
            pass
            
        elif menu_admin_main_view_final == "Gerenciar Administradores":
            st.subheader("👮 Gerenciar Administradores")
            # ... (Código completo da seção Gerenciar Administradores da versão anterior)
            pass

    except Exception as e_admin_area_d_main_final_full:
        st.error(f"Ocorreu um erro crítico na área administrativa: {e_admin_area_d_main_final_full}")
        st.exception(e_admin_area_d_main_final_full)


if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()

# st.write(f"DEBUG FINAL: admin_logado: {st.session_state.admin_logado}, cliente_logado: {st.session_state.cliente_logado}, aba: {aba if 'aba' in locals() else 'Não definida'}")