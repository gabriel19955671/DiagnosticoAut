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

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
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
LOGOS_DIR = "client_logos"

# --- Inicialização do Session State ---
if "admin_logado" not in st.session_state: st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state: st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state: st.session_state.diagnostico_enviado = False
if "inicio_sessao_cliente" not in st.session_state: st.session_state.inicio_sessao_cliente = None
if "cliente_page" not in st.session_state: st.session_state.cliente_page = "Instruções" # Página inicial padrão para cliente
if "cnpj" not in st.session_state: st.session_state.cnpj = None
if "user" not in st.session_state: st.session_state.user = None

# --- Funções Utilitárias ---
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s)
    return s

def pdf_safe_text_output(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def find_client_logo_path(cnpj_find_logo_arg):
    if not cnpj_find_logo_arg: return None
    base_name = str(cnpj_find_logo_arg).replace('/', '').replace('.', '').replace('-', '')
    for ext_logo_arg in ["png", "jpg", "jpeg"]:
        path_logo_arg = os.path.join(LOGOS_DIR, f"{base_name}_logo.{ext_logo_arg}")
        if os.path.exists(path_logo_arg):
            return path_logo_arg
    return None

# --- Criação e Verificação de Arquivos e Pastas ---
if not os.path.exists(LOGOS_DIR):
    try:
        os.makedirs(LOGOS_DIR)
    except OSError as e_logo_dir_final_v3:
        st.error(f"Não foi possível criar o diretório de logos '{LOGOS_DIR}': {e_logo_dir_final_v3}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone", "PodeFazerNovoDiagnostico", "JaVisualizouInstrucoes"] # Novas colunas
colunas_base_perguntas = ["Pergunta", "Categoria"]

def inicializar_csv(filepath, columns, is_perguntas_file=False, is_usuarios_file=False):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if is_usuarios_file:
                if "PodeFazerNovoDiagnostico" in columns: df_init["PodeFazerNovoDiagnostico"] = True # Default
                if "JaVisualizouInstrucoes" in columns: df_init["JaVisualizouInstrucoes"] = False # Default
            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else:
            df_init = pd.read_csv(filepath, encoding='utf-8')
            missing_cols = [col for col in columns if col not in df_init.columns]
            made_changes = False
            if missing_cols:
                for col_m in missing_cols:
                    if is_perguntas_file and col_m == "Categoria": df_init[col_m] = "Geral"
                    elif is_usuarios_file and col_m == "PodeFazerNovoDiagnostico": df_init[col_m] = True
                    elif is_usuarios_file and col_m == "JaVisualizouInstrucoes": df_init[col_m] = False
                    else: df_init[col_m] = pd.NA
                made_changes = True
            
            # Explicitly check and add if still missing for usuarios.csv (after first creation)
            if is_usuarios_file:
                if "PodeFazerNovoDiagnostico" not in df_init.columns:
                    df_init["PodeFazerNovoDiagnostico"] = True
                    made_changes = True
                if "JaVisualizouInstrucoes" not in df_init.columns:
                    df_init["JaVisualizouInstrucoes"] = False
                    made_changes = True
            
            if is_perguntas_file and "Categoria" not in df_init.columns:
                df_init["Categoria"] = "Geral"; made_changes = True

            if made_changes:
                df_init.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError:
        df_empty_init = pd.DataFrame(columns=columns)
        if is_usuarios_file:
            if "PodeFazerNovoDiagnostico" in columns: df_empty_init["PodeFazerNovoDiagnostico"] = True
            if "JaVisualizouInstrucoes" in columns: df_empty_init["JaVisualizouInstrucoes"] = False
        df_empty_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e_init_csv:
        st.error(f"Erro ao inicializar/verificar {filepath}: {e_init_csv}. O app pode não funcionar corretamente.")
        st.exception(e_init_csv)
        raise

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios, is_usuarios_file=True) # Indicar que é o arquivo de usuários
    inicializar_csv(perguntas_csv, colunas_base_perguntas, is_perguntas_file=True)
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
except Exception as e_init_all:
    st.error(f"Falha crítica na inicialização de arquivos CSV base: {e_init_all}")
    st.exception(e_init_all)
    st.markdown("Verifique permissões de arquivo e a integridade dos CSVs. Delete-os para recriação se necessário.")
    st.stop()


def registrar_acao(cnpj_reg, acao_reg, descricao_reg):
    try:
        historico_df_reg = pd.read_csv(historico_csv, encoding='utf-8')
    except (FileNotFoundError, pd.errors.EmptyDataError):
        historico_df_reg = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data_reg = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj_reg, "Ação": acao_reg, "Descrição": descricao_reg }
    historico_df_reg = pd.concat([historico_df_reg, pd.DataFrame([nova_data_reg])], ignore_index=True)
    historico_df_reg.to_csv(historico_csv, index=False, encoding='utf-8')

def update_user_data(cnpj_update, field_update, value_update):
    try:
        users_df_update = pd.read_csv(usuarios_csv, encoding='utf-8')
        user_idx_update = users_df_update[users_df_update['CNPJ'].astype(str) == str(cnpj_update)].index
        if not user_idx_update.empty:
            users_df_update.loc[user_idx_update, field_update] = value_update
            users_df_update.to_csv(usuarios_csv, index=False, encoding='utf-8')
            # Recarregar dados do usuário na session_state se for o usuário logado
            if 'user' in st.session_state and st.session_state.user and str(st.session_state.user.get('CNPJ')) == str(cnpj_update):
                st.session_state.user[field_update] = value_update
            return True
    except Exception as e_update_user:
        st.error(f"Erro ao atualizar dados do usuário ({field_update}): {e_update_user}")
    return False

def gerar_pdf_diagnostico_completo(diagnostico_data_pdf_param, usuario_data_pdf_param,
                                   perguntas_df_pdf_param, respostas_coletadas_pdf_param,
                                   medias_categorias_pdf_param):
    try:
        pdf_gen_param = FPDF()
        pdf_gen_param.add_page()
        empresa_nome_pdf_g_param = usuario_data_pdf_param.get("Empresa", "N/D")
        cnpj_pdf_g_param = usuario_data_pdf_param.get("CNPJ", "N/D")
        nome_contato_pdf_g_param = usuario_data_pdf_param.get("NomeContato", "")
        telefone_pdf_g_param = usuario_data_pdf_param.get("Telefone", "")

        logo_path_pdf_g_param = find_client_logo_path(cnpj_pdf_g_param)
        if logo_path_pdf_g_param:
            try:
                current_y_pdf_g_param = pdf_gen_param.get_y()
                max_logo_height_g_param = 20
                pdf_gen_param.image(logo_path_pdf_g_param, x=10, y=current_y_pdf_g_param, h=max_logo_height_g_param)
                pdf_gen_param.set_y(current_y_pdf_g_param + max_logo_height_g_param + 5)
            except RuntimeError: pass # FPDF error if image not found or format issue
            except Exception: pass

        pdf_gen_param.set_font("Arial", 'B', 16)
        pdf_gen_param.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome_pdf_g_param}"), 0, 1, 'C')
        pdf_gen_param.ln(5)

        pdf_gen_param.set_font("Arial", size=10)
        pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Data do Diagnóstico: {diagnostico_data_pdf_param.get('Data','N/D')}"))
        pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Empresa: {empresa_nome_pdf_g_param} (CNPJ: {cnpj_pdf_g_param})"))
        if nome_contato_pdf_g_param: pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {nome_contato_pdf_g_param}"))
        if telefone_pdf_g_param: pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {telefone_pdf_g_param}"))
        pdf_gen_param.ln(3)

        pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral (Numérica): {diagnostico_data_pdf_param.get('Média Geral','N/A')}"))
        pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Média Scores GUT (G*U*T): {diagnostico_data_pdf_param.get('GUT Média','N/A')}"))
        pdf_gen_param.ln(3)

        if medias_categorias_pdf_param:
            pdf_gen_param.set_font("Arial", 'B', 11); pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria (Perguntas de Pontuação):"))
            pdf_gen_param.set_font("Arial", size=10)
            for cat_pdf_g_mc_param, media_cat_pdf_g_mc_param in medias_categorias_pdf_param.items():
                pdf_gen_param.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat_pdf_g_mc_param}: {media_cat_pdf_g_mc_param}"))
            pdf_gen_param.ln(5)

        for titulo_pdf_g_param, campo_dado_pdf_g_param in [("Resumo do Diagnóstico (Cliente):", "Diagnóstico"),
                                                           ("Análise/Observações do Cliente:", "Análise do Cliente"),
                                                           ("Comentários do Consultor:", "Comentarios_Admin")]:
            valor_campo_pdf_g_param = diagnostico_data_pdf_param.get(campo_dado_pdf_g_param, "")
            if valor_campo_pdf_g_param and not pd.isna(valor_campo_pdf_g_param):
                pdf_gen_param.set_font("Arial", 'B', 12); pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(titulo_pdf_g_param))
                pdf_gen_param.set_font("Arial", size=10); pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(str(valor_campo_pdf_g_param))); pdf_gen_param.ln(3)

        pdf_gen_param.set_font("Arial", 'B', 12); pdf_gen_param.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas por Categoria:"))
        categorias_unicas_pdf_g_param = []
        if perguntas_df_pdf_param is not None and "Categoria" in perguntas_df_pdf_param.columns:
            categorias_unicas_pdf_g_param = perguntas_df_pdf_param["Categoria"].unique()

        for categoria_pdf_det_g_param in categorias_unicas_pdf_g_param:
            pdf_gen_param.set_font("Arial", 'B', 10); pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria_pdf_det_g_param}"))
            pdf_gen_param.set_font("Arial", size=9)
            perguntas_cat_pdf_det_g_param = perguntas_df_pdf_param[perguntas_df_pdf_param["Categoria"] == categoria_pdf_det_g_param]
            for _, p_row_pdf_det_g_param in perguntas_cat_pdf_det_g_param.iterrows():
                txt_p_pdf_det_g_param = p_row_pdf_det_g_param["Pergunta"]
                # Prioritize respostas_coletadas if available (form context), else from diagnostico_data (saved context)
                resp_p_pdf_det_g_param = respostas_coletadas_pdf_param.get(txt_p_pdf_det_g_param)
                if resp_p_pdf_det_g_param is None:
                    resp_p_pdf_det_g_param = diagnostico_data_pdf_param.get(txt_p_pdf_det_g_param, "N/R")


                if isinstance(txt_p_pdf_det_g_param, str) and "[Matriz GUT]" in txt_p_pdf_det_g_param:
                    g_pdf_v_param, u_pdf_v_param, t_pdf_v_param = 0,0,0
                    score_gut_item_pdf_v_param = 0
                    if isinstance(resp_p_pdf_det_g_param, dict):
                        g_pdf_v_param,u_pdf_v_param,t_pdf_v_param = resp_p_pdf_det_g_param.get("G",0), resp_p_pdf_det_g_param.get("U",0), resp_p_pdf_det_g_param.get("T",0)
                    elif isinstance(resp_p_pdf_det_g_param, str): # Handle stringified JSON from CSV
                        try:
                            gut_data_pdf_v_param = json.loads(resp_p_pdf_det_g_param.replace("'", "\""))
                            g_pdf_v_param,u_pdf_v_param,t_pdf_v_param = gut_data_pdf_v_param.get("G",0), gut_data_pdf_v_param.get("U",0), gut_data_pdf_v_param.get("T",0)
                        except: pass
                    score_gut_item_pdf_v_param = g_pdf_v_param*u_pdf_v_param*t_pdf_v_param
                    pdf_gen_param.multi_cell(0,6,pdf_safe_text_output(f"  - {txt_p_pdf_det_g_param.replace(' [Matriz GUT]','')}: G={g_pdf_v_param}, U={u_pdf_v_param}, T={t_pdf_v_param} (Score: {score_gut_item_pdf_v_param})"))
                elif isinstance(resp_p_pdf_det_g_param, (int, float, str)):
                    pdf_gen_param.multi_cell(0, 6, pdf_safe_text_output(f"  - {txt_p_pdf_det_g_param}: {resp_p_pdf_det_g_param}"))
            pdf_gen_param.ln(2)
        pdf_gen_param.ln(3)

        pdf_gen_param.add_page(); pdf_gen_param.set_font("Arial", 'B', 12)
        pdf_gen_param.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf_gen_param.ln(5)
        pdf_gen_param.set_font("Arial", size=10)
        gut_cards_pdf_g_list_param = []
        
        # Iterate through perguntas_df to ensure all GUT questions are considered
        if perguntas_df_pdf_param is not None:
            for _, p_row_kanban in perguntas_df_pdf_param.iterrows():
                pergunta_pdf_k_g_item_param = p_row_kanban["Pergunta"]
                if isinstance(pergunta_pdf_k_g_item_param, str) and "[Matriz GUT]" in pergunta_pdf_k_g_item_param:
                    resp_pdf_k_val_g_item_param = respostas_coletadas_pdf_param.get(pergunta_pdf_k_g_item_param)
                    if resp_pdf_k_val_g_item_param is None: # Fallback to diagnostico_data if not in collected
                        resp_pdf_k_val_g_item_param = diagnostico_data_pdf_param.get(pergunta_pdf_k_g_item_param)

                    g_k_g_item_param, u_k_g_item_param, t_k_g_item_param = 0,0,0
                    if isinstance(resp_pdf_k_val_g_item_param, dict):
                        g_k_g_item_param, u_k_g_item_param, t_k_g_item_param = resp_pdf_k_val_g_item_param.get("G",0), resp_pdf_k_val_g_item_param.get("U",0), resp_pdf_k_val_g_item_param.get("T",0)
                    elif isinstance(resp_pdf_k_val_g_item_param, str): # Handle stringified JSON
                        try:
                            gut_data_k_g_item_param = json.loads(resp_pdf_k_val_g_item_param.replace("'", "\""))
                            g_k_g_item_param,u_k_g_item_param,t_k_g_item_param = gut_data_k_g_item_param.get("G",0), gut_data_k_g_item_param.get("U",0), gut_data_k_g_item_param.get("T",0)
                        except: pass

                    score_gut_total_k_pdf_g_item_param = g_k_g_item_param * u_k_g_item_param * t_k_g_item_param
                    prazo_k_pdf_g_item_param = "N/A"
                    if score_gut_total_k_pdf_g_item_param >= 75: prazo_k_pdf_g_item_param = "15 dias"
                    elif score_gut_total_k_pdf_g_item_param >= 40: prazo_k_pdf_g_item_param = "30 dias"
                    elif score_gut_total_k_pdf_g_item_param >= 20: prazo_k_pdf_g_item_param = "45 dias"
                    elif score_gut_total_k_pdf_g_item_param > 0: prazo_k_pdf_g_item_param = "60 dias"
                    else: continue
                    if prazo_k_pdf_g_item_param != "N/A":
                        gut_cards_pdf_g_list_param.append({"Tarefa": pergunta_pdf_k_g_item_param.replace(" [Matriz GUT]", ""),"Prazo": prazo_k_pdf_g_item_param, "Score": score_gut_total_k_pdf_g_item_param})
        
        if gut_cards_pdf_g_list_param:
            gut_cards_pdf_g_sorted_param = sorted(gut_cards_pdf_g_list_param, key=lambda x_g_pdf_param: (int(x_g_pdf_param["Prazo"].split(" ")[0]), -x_g_pdf_param["Score"]))
            for card_item_pdf_g_final_param in gut_cards_pdf_g_sorted_param:
                 pdf_gen_param.multi_cell(0, 6, pdf_safe_text_output(f"Prazo: {card_item_pdf_g_final_param['Prazo']} - Tarefa: {card_item_pdf_g_final_param['Tarefa']} (Score GUT: {card_item_pdf_g_final_param['Score']})"))
        else: pdf_gen_param.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_pdf_gerado_final_param:
            pdf_path_gerado_final_param = tmpfile_pdf_gerado_final_param.name
            pdf_gen_param.output(pdf_path_gerado_final_param)
        return pdf_path_gerado_final_param
    except Exception as e_pdf_main_gerar_final_param:
        st.error(f"Erro crítico ao gerar PDF: {e_pdf_main_gerar_final_param}")
        st.exception(e_pdf_main_gerar_final_param); return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v3")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v3"):
        usuario_admin_login = st.text_input("Usuário", key="admin_user_login_v3")
        senha_admin_login = st.text_input("Senha", type="password", key="admin_pass_login_v3")
        entrar_admin_login = st.form_submit_button("Entrar")
    if entrar_admin_login:
        try:
            df_admin_login_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            admin_encontrado = df_admin_login_creds[(df_admin_login_creds["Usuario"] == usuario_admin_login) & (df_admin_login_creds["Senha"] == senha_admin_login)]
            if not admin_encontrado.empty:
                st.session_state.admin_logado = True; st.success("Login de administrador bem-sucedido!")
                st.session_state.trigger_admin_rerun = True; st.rerun()
            else: st.error("Usuário ou senha inválidos.")
        except FileNotFoundError: st.error(f"Arquivo {admin_credenciais_csv} não encontrado.")
        except pd.errors.EmptyDataError: st.error(f"Arquivo {admin_credenciais_csv} está vazio.")
        except Exception as e_login_admin_v3: st.error(f"Erro no login: {e_login_admin_v3}"); st.exception(e_login_admin_v3)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_v3"):
        cnpj_cli_login = st.text_input("CNPJ", key="cli_cnpj_login_v3")
        senha_cli_login = st.text_input("Senha", type="password", key="cli_pass_login_v3")
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

            st.session_state.cliente_logado = True; st.session_state.cnpj = str(cnpj_cli_login)
            st.session_state.user = user_match_li.iloc[0].to_dict()
            st.session_state.inicio_sessao_cliente = time.time()
            registrar_acao(st.session_state.cnpj, "Login", "Usuário realizou login.")
            
            # Determinar página inicial do cliente
            ja_visualizou_instrucoes = st.session_state.user.get("JaVisualizouInstrucoes", False)
            pode_fazer_novo = st.session_state.user.get("PodeFazerNovoDiagnostico", True) # Default to True if column doesn't exist yet

            if not ja_visualizou_instrucoes:
                st.session_state.cliente_page = "Instruções"
            elif pode_fazer_novo:
                st.session_state.cliente_page = "Novo Diagnóstico"
            else:
                st.session_state.cliente_page = "Painel Principal"

            st.success("Login realizado com sucesso!"); st.session_state.trigger_cliente_rerun = True; st.rerun()
        except FileNotFoundError as e_login_cli_fnf_v3: st.error(f"Arquivo não encontrado: {e_login_cli_fnf_v3.filename}.")
        except pd.errors.EmptyDataError as e_login_cli_empty_v3: st.error(f"Arquivo de usuários ou bloqueados está vazio: {e_login_cli_empty_v3}")
        except Exception as e_login_cli_v3: st.error(f"Erro no login do cliente: {e_login_cli_v3}"); st.exception(e_login_cli_v3)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    try:
        st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")

        with st.sidebar.expander("Meu Perfil", expanded=False):
            logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
            if logo_cliente_path:
                try: st.image(logo_cliente_path, width=100)
                except Exception as e_logo_display_cli: st.caption(f"Erro ao exibir logo: {e_logo_display_cli}")
            st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
            st.write(f"**CNPJ:** {st.session_state.cnpj}")
            st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
            st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")

        DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}"
        
        # Menu de navegação do cliente
        # A lógica de qual página mostrar é definida no login e após ações
        menu_options_cliente = ["Instruções", "Novo Diagnóstico", "Painel Principal"]
        try:
            current_page_index = menu_options_cliente.index(st.session_state.cliente_page)
        except ValueError:
            current_page_index = 0 # Default to first if something is wrong
            st.session_state.cliente_page = menu_options_cliente[0]

        selected_page_from_menu = st.sidebar.radio(
            "Menu Cliente", menu_options_cliente,
            index=current_page_index,
            key="cliente_menu_radio_v4"
        )
        if selected_page_from_menu != st.session_state.cliente_page:
            st.session_state.cliente_page = selected_page_from_menu
            st.rerun()


        if st.sidebar.button("⬅️ Sair do Portal Cliente"):
            keys_to_del_cli_logout = ['cliente_logado', 'cnpj', 'user', 'inicio_sessao_cliente',
                                      'diagnostico_enviado', 'cliente_page', DIAGNOSTICO_FORM_ID_KEY_USER]
            temp_resp_key_logout = f"temp_respostas_{st.session_state.get(DIAGNOSTICO_FORM_ID_KEY_USER,'')}"
            if temp_resp_key_logout in st.session_state:
                keys_to_del_cli_logout.append(temp_resp_key_logout)
            for key_cd_lo in keys_to_del_cli_logout:
                if key_cd_lo in st.session_state: del st.session_state[key_cd_lo]
            st.rerun()

        if st.session_state.cliente_page == "Instruções":
            st.subheader("📖 Instruções do Sistema de Diagnóstico")
            st.markdown("""
            Bem-vindo(a) ao Portal de Diagnóstico!

            Este sistema foi projetado para ajudar a sua empresa a identificar pontos fortes e áreas de melhoria através de um formulário de autoavaliação.

            **Como funciona:**

            1.  **Novo Diagnóstico:**
                * Você preencherá um formulário com perguntas sobre diversas áreas da sua empresa.
                * Algumas perguntas serão de pontuação (escalas numéricas), outras usarão a Matriz GUT (Gravidade, Urgência, Tendência) para priorização, e algumas podem ser textuais.
                * Seja honesto(a) em suas respostas para que o diagnóstico reflita a realidade da sua empresa.
                * Ao final, você deverá fornecer um resumo dos seus principais insights.

            2.  **Envio e Resultados:**
                * Após enviar o formulário, seus dados serão processados.
                * Você poderá baixar um PDF com o resumo do seu diagnóstico, incluindo suas respostas, médias e um plano de ação inicial baseado na Matriz GUT.

            3.  **Painel Principal:**
                * Nesta seção, você poderá visualizar todos os diagnósticos que já realizou.
                * Acompanhe sua evolução ao longo do tempo através de gráficos comparativos.
                * Revise os planos de ação (Kanban) gerados a partir dos seus diagnósticos.
                * Adicione suas próprias análises e observações aos diagnósticos passados.
                * Baixe novamente os PDFs dos seus diagnósticos anteriores.

            **Importante:**
            * Inicialmente, você tem direito a realizar **um diagnóstico**.
            * Caso necessite realizar novos diagnósticos, entre em contato com o administrador do sistema para verificar as condições de liberação.

            Estamos à disposição para qualquer dúvida!
            """)
            if st.button("Entendi, prosseguir"):
                update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", True)
                st.session_state.user["JaVisualizouInstrucoes"] = True # Atualiza localmente também

                pode_fazer_novo = st.session_state.user.get("PodeFazerNovoDiagnostico", True)
                if pode_fazer_novo:
                    st.session_state.cliente_page = "Novo Diagnóstico"
                else:
                    st.session_state.cliente_page = "Painel Principal"
                st.rerun()


        elif st.session_state.cliente_page == "Painel Principal":
            st.subheader("📌 Meu Painel de Diagnósticos")
            with st.expander("📖 Instruções e Informações", expanded=True):
                st.markdown("- Visualize seus diagnósticos anteriores e sua evolução.")
                st.markdown("- Acompanhe seu plano de ação no Kanban.")
                st.markdown("- Para um novo diagnóstico (se liberado), selecione 'Novo Diagnóstico' no menu ao lado.")

            if st.session_state.get("diagnostico_enviado", False):
                st.success("🎯 Último diagnóstico enviado com sucesso!"); st.session_state.diagnostico_enviado = False

            st.subheader("📁 Diagnósticos Anteriores")
            df_cliente_view_pp = pd.DataFrame()
            try:
                df_antigos_cli_pp = pd.read_csv(arquivo_csv, encoding='utf-8')
                if not df_antigos_cli_pp.empty:
                    df_cliente_view_pp = df_antigos_cli_pp[df_antigos_cli_pp["CNPJ"].astype(str) == st.session_state.cnpj]
            except (FileNotFoundError, pd.errors.EmptyDataError): pass
            except Exception as e_read_diag_cli_pp: st.error(f"Erro ao ler diagnósticos do cliente: {e_read_diag_cli_pp}")

            if df_cliente_view_pp.empty:
                st.info("Nenhum diagnóstico anterior. Selecione 'Novo Diagnóstico' no menu (se disponível).")
            else:
                df_cliente_view_pp = df_cliente_view_pp.sort_values(by="Data", ascending=False)
                for idx_cv_pp, row_cv_pp in df_cliente_view_pp.iterrows():
                    with st.expander(f"📅 {row_cv_pp['Data']} - {row_cv_pp['Empresa']}"):
                        cols_diag_cli_metrics = st.columns(2)
                        with cols_diag_cli_metrics[0]: st.metric("Média Geral", f"{row_cv_pp.get('Média Geral', 0.0):.2f}")
                        with cols_diag_cli_metrics[1]: st.metric("GUT Média (G*U*T)", f"{row_cv_pp.get('GUT Média', 0.0):.2f}")
                        st.write(f"**Resumo (Cliente):** {row_cv_pp.get('Diagnóstico', 'N/P')}")
                        st.markdown("**Médias por Categoria:**")
                        found_cat_media_cv = False
                        cat_cols_display = [col for col in row_cv_pp.index if str(col).startswith("Media_Cat_")]
                        if cat_cols_display:
                            num_cat_cols_display = len(cat_cols_display); max_cols_per_row = 4
                            display_cols_metrics = st.columns(min(num_cat_cols_display, max_cols_per_row))
                            col_idx_display = 0
                            for col_name_cv_display in cat_cols_display:
                                cat_name_display_cv = col_name_cv_display.replace("Media_Cat_", "").replace("_", " ")
                                current_col_obj = display_cols_metrics[col_idx_display % min(num_cat_cols_display, max_cols_per_row)]
                                current_col_obj.metric(f"Média {cat_name_display_cv}", f"{row_cv_pp.get(col_name_cv_display, 0.0):.2f}")
                                col_idx_display += 1; found_cat_media_cv = True
                        if not found_cat_media_cv: st.caption("  Nenhuma média por categoria.")
                        
                        analise_cli_val_cv = row_cv_pp.get("Análise do Cliente", "")
                        analise_cli_cv = st.text_area("🧠 Minha Análise sobre este Diagnóstico:", value=analise_cli_val_cv, key=f"analise_cv_final_{row_cv_pp.name}")
                        if st.button("💾 Salvar Minha Análise", key=f"salvar_analise_cv_final_{row_cv_pp.name}"):
                            try:
                                df_antigos_upd_cv = pd.read_csv(arquivo_csv, encoding='utf-8')
                                df_antigos_upd_cv.loc[idx_cv_pp, "Análise do Cliente"] = analise_cli_cv # Usar idx_cv_pp que é o índice original
                                df_antigos_upd_cv.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                registrar_acao(st.session_state.cnpj, "Análise Cliente", f"Editou análise de {row_cv_pp['Data']}")
                                st.success("Análise salva!"); st.rerun()
                            except Exception as e_save_analise_final: st.error(f"Erro ao salvar análise: {e_save_analise_final}")
                        
                        com_admin_val_cv = row_cv_pp.get("Comentarios_Admin", "")
                        if com_admin_val_cv and not pd.isna(com_admin_val_cv):
                            st.markdown("**Comentários do Consultor:**"); st.info(f"{com_admin_val_cv}")
                        else: st.caption("Nenhum comentário do consultor.")

                        # Botão para baixar PDF do diagnóstico específico
                        if st.button("📄 Baixar PDF deste Diagnóstico", key=f"download_pdf_cliente_painel_{idx_cv_pp}"):
                            try:
                                perguntas_df_pdf_cli = pd.read_csv(perguntas_csv, encoding='utf-8')
                                if "Categoria" not in perguntas_df_pdf_cli.columns: perguntas_df_pdf_cli["Categoria"] = "Geral"
                            except: perguntas_df_pdf_cli = pd.DataFrame(columns=colunas_base_perguntas)

                            respostas_coletadas_pdf_cli = row_cv_pp.to_dict() # Todas as colunas do CSV são as "respostas"
                            medias_categorias_pdf_cli = {}
                            if not perguntas_df_pdf_cli.empty and "Categoria" in perguntas_df_pdf_cli.columns:
                                cats_unicas_pdf_cli = perguntas_df_pdf_cli["Categoria"].unique()
                                for cat_pdf_cli_calc in cats_unicas_pdf_cli:
                                    nome_col_media_cat_pdf = f"Media_Cat_{sanitize_column_name(cat_pdf_cli_calc)}"
                                    medias_categorias_pdf_cli[cat_pdf_cli_calc] = row_cv_pp.get(nome_col_media_cat_pdf, 0.0)
                            
                            pdf_path_cliente = gerar_pdf_diagnostico_completo(
                                diagnostico_data_pdf_param=row_cv_pp.to_dict(),
                                usuario_data_pdf_param=st.session_state.user,
                                perguntas_df_pdf_param=perguntas_df_pdf_cli,
                                respostas_coletadas_pdf_param=respostas_coletadas_pdf_cli, # Passa o row_cv_pp como respostas
                                medias_categorias_pdf_param=medias_categorias_pdf_cli
                            )
                            if pdf_path_cliente:
                                with open(pdf_path_cliente, "rb") as f_pdf_cli:
                                    st.download_button(
                                        label="Download Confirmado", 
                                        data=f_pdf_cli,
                                        file_name=f"diagnostico_{sanitize_column_name(st.session_state.user.get('Empresa','Cliente'))}_{row_cv_pp['Data'].replace(':','-').replace(' ','_')}.pdf",
                                        mime="application/pdf",
                                        key=f"confirm_dl_pdf_cliente_{idx_cv_pp}"
                                    )
                                registrar_acao(st.session_state.cnpj, "Download PDF (Painel)", f"Baixou PDF do diagnóstico de {row_cv_pp['Data']}")
                            else:
                                st.error("Falha ao gerar o PDF para download.")
                        st.markdown("---")

                st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
                gut_cards_painel = []
                if not df_cliente_view_pp.empty:
                    latest_diag_row_painel = df_cliente_view_pp.iloc[0]
                    for pergunta_p, resposta_p_val_str in latest_diag_row_painel.items():
                        if isinstance(pergunta_p, str) and "[Matriz GUT]" in pergunta_p:
                            try:
                                if pd.notna(resposta_p_val_str) and isinstance(resposta_p_val_str, str):
                                    gut_data = json.loads(resposta_p_val_str.replace("'", "\""))
                                    g = int(gut_data.get("G", 0)); u = int(gut_data.get("U", 0)); t_val = int(gut_data.get("T", 0))
                                    score_gut_total_p = g * u * t_val
                                    prazo_p = "N/A"
                                    if score_gut_total_p >= 75: prazo_p = "15 dias"
                                    elif score_gut_total_p >= 40: prazo_p = "30 dias"
                                    elif score_gut_total_p >= 20: prazo_p = "45 dias"
                                    elif score_gut_total_p > 0: prazo_p = "60 dias"
                                    else: continue
                                    if prazo_p != "N/A":
                                        gut_cards_painel.append({"Tarefa": pergunta_p.replace(" [Matriz GUT]", ""), "Prazo": prazo_p, "Score": score_gut_total_p, "Responsável": st.session_state.user.get("Empresa", "N/D")})
                            except (json.JSONDecodeError, ValueError, TypeError) as e_k_pp: st.warning(f"Erro processar GUT Kanban para '{pergunta_p}': {e_k_pp}")

                if gut_cards_painel:
                    gut_cards_sorted_p = sorted(gut_cards_painel, key=lambda x_pp: x_pp["Score"], reverse=True)
                    prazos_def_p = sorted(list(set(card_pp["Prazo"] for card_pp in gut_cards_sorted_p)), key=lambda x_d_pp: int(x_d_pp.split(" ")[0]))
                    if prazos_def_p:
                        cols_kanban_p = st.columns(len(prazos_def_p))
                        for idx_kp, prazo_col_kp in enumerate(prazos_def_p):
                            with cols_kanban_p[idx_kp]:
                                st.markdown(f"#### ⏱️ {prazo_col_kp}")
                                for card_item_kp in gut_cards_sorted_p:
                                    if card_item_kp["Prazo"] == prazo_col_kp:
                                        st.markdown(f"""<div class="custom-card"><b>{card_item_kp['Tarefa']}</b> (Score GUT: {card_item_kp['Score']})<br><small><i>👤 {card_item_kp['Responsável']}</i></small></div>""", unsafe_allow_html=True)
                else: st.info("Nenhuma ação prioritária para o Kanban (GUT) no último diagnóstico.")

                st.subheader("📈 Comparativo de Evolução")
                if len(df_cliente_view_pp) > 1:
                    grafico_comp_ev = df_cliente_view_pp.sort_values(by="Data")
                    grafico_comp_ev["Data"] = pd.to_datetime(grafico_comp_ev["Data"])
                    colunas_plot_comp = ['Média Geral', 'GUT Média']
                    for col_g_comp in grafico_comp_ev.columns:
                        if str(col_g_comp).startswith("Media_Cat_") and pd.api.types.is_numeric_dtype(grafico_comp_ev[col_g_comp]):
                            colunas_plot_comp.append(col_g_comp)
                    for col_plot_c in colunas_plot_comp:
                        if col_plot_c in grafico_comp_ev.columns: grafico_comp_ev[col_plot_c] = pd.to_numeric(grafico_comp_ev[col_plot_c], errors='coerce')

                    colunas_validas_plot = [c for c in colunas_plot_comp if c in grafico_comp_ev.columns and pd.api.types.is_numeric_dtype(grafico_comp_ev[c]) and not grafico_comp_ev[c].isnull().all()]
                    if colunas_validas_plot:
                        st.line_chart(grafico_comp_ev.set_index("Data")[colunas_validas_plot].dropna(axis=1, how='all'))
                    else:
                        st.info("Não há dados suficientes ou válidos para plotar o gráfico de evolução.")


                    st.subheader("📊 Comparação Entre Diagnósticos")
                    opcoes_cli = grafico_comp_ev["Data"].astype(str).tolist()
                    if len(opcoes_cli) >= 2:
                        diag_atual_idx, diag_anterior_idx = len(opcoes_cli)-1, len(opcoes_cli)-2
                        diag_atual_sel_cli = st.selectbox("Diagnóstico mais recente:", opcoes_cli, index=diag_atual_idx, key="diag_atual_sel_cli_v3")
                        diag_anterior_sel_cli = st.selectbox("Diagnóstico anterior:", opcoes_cli, index=diag_anterior_idx, key="diag_anterior_sel_cli_v3")
                        atual_cli = grafico_comp_ev[grafico_comp_ev["Data"].astype(str) == diag_atual_sel_cli].iloc[0]
                        anterior_cli = grafico_comp_ev[grafico_comp_ev["Data"].astype(str) == diag_anterior_sel_cli].iloc[0]
                        st.write(f"### 📅 Comparando {diag_anterior_sel_cli.split(' ')[0]} ⟶ {diag_atual_sel_cli.split(' ')[0]}")
                        cols_excluir_comp = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
                        variaveis_comp = [col for col in grafico_comp_ev.columns if col not in cols_excluir_comp and pd.api.types.is_numeric_dtype(grafico_comp_ev[col])]
                        if variaveis_comp:
                            comp_data = []
                            for v_comp in variaveis_comp:
                                val_ant_c = pd.to_numeric(anterior_cli.get(v_comp), errors='coerce')
                                val_atu_c = pd.to_numeric(atual_cli.get(v_comp), errors='coerce')
                                evolucao_c = "➖ Igual"
                                if pd.notna(val_ant_c) and pd.notna(val_atu_c):
                                    if val_atu_c > val_ant_c: evolucao_c = "🔼 Melhorou"
                                    elif val_atu_c < val_ant_c: evolucao_c = "🔽 Piorou"
                                display_name_comp = v_comp.replace("Media_Cat_", "Média ").replace("_", " ")
                                if "[Pontuação (0-10)]" in display_name_comp or "[Pontuação (0-5) + Matriz GUT]" in display_name_comp or "[Matriz GUT]" in display_name_comp:
                                    display_name_comp = display_name_comp.split(" [")[0]
                                comp_data.append({"Indicador": display_name_comp, "Anterior": f"{val_ant_c:.2f}" if pd.notna(val_ant_c) else "N/A", "Atual": f"{val_atu_c:.2f}" if pd.notna(val_atu_c) else "N/A", "Evolução": evolucao_c})
                            st.dataframe(pd.DataFrame(comp_data))
                        else: st.info("Sem dados numéricos para comparação.")
                    else: st.info("Pelo menos dois diagnósticos para comparação.")
                else: st.info("Pelo menos dois diagnósticos para comparativos.")

        elif st.session_state.cliente_page == "Novo Diagnóstico":
            st.subheader("📋 Formulário de Novo Diagnóstico")

            pode_fazer_novo_check = st.session_state.user.get("PodeFazerNovoDiagnostico", True)
            try:
                diagnosticos_feitos = pd.read_csv(arquivo_csv, encoding='utf-8')
                diagnosticos_feitos_cliente = diagnosticos_feitos[diagnosticos_feitos["CNPJ"].astype(str) == st.session_state.cnpj]
                if not diagnosticos_feitos_cliente.empty and not pode_fazer_novo_check: # Se já fez algum e não está explicitamente liberado
                     st.warning("Você já enviou um diagnóstico. Para realizar um novo, por favor, entre em contato com o administrador para liberação.")
                     st.stop()
                elif diagnosticos_feitos_cliente.empty: # Se nunca fez, pode_fazer_novo_check é True por default ou da carga inicial
                    pode_fazer_novo_check = True

            except (FileNotFoundError, pd.errors.EmptyDataError): # Arquivo de diagnósticos não existe ou vazio, então pode fazer
                pode_fazer_novo_check = True
            except Exception as e_check_diag:
                st.error(f"Erro ao verificar diagnósticos anteriores: {e_check_diag}")
                pode_fazer_novo_check = False # Trava por segurança
                st.stop()

            if not pode_fazer_novo_check: # Dupla checagem após try-except
                st.warning("Você não tem permissão para realizar um novo diagnóstico no momento. Contate o administrador.")
                st.stop()


            DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}"
            if DIAGNOSTICO_FORM_ID_KEY_USER not in st.session_state:
                st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER] = datetime.now().strftime("%Y%m%d%H%M%S%f")
            form_id_sufixo_nd = st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER]

            temp_respostas_key_nd = f"temp_respostas_{form_id_sufixo_nd}"
            if temp_respostas_key_nd not in st.session_state:
                st.session_state[temp_respostas_key_nd] = {}

            respostas_form_coletadas_nd = st.session_state[temp_respostas_key_nd]

            try:
                perguntas_df_diag = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_diag.columns:
                    perguntas_df_diag["Categoria"] = "Geral"
            except (FileNotFoundError, pd.errors.EmptyDataError):
                st.error(f"Arquivo de perguntas ({perguntas_csv}) não encontrado ou vazio."); st.stop()
            except Exception as e_read_perg_form:
                st.error(f"Erro ao ler arquivo de perguntas: {e_read_perg_form}"); st.stop()

            if perguntas_df_diag.empty:
                st.warning("Nenhuma pergunta cadastrada."); st.stop()

            total_perguntas_diag = len(perguntas_df_diag)
            respondidas_count_diag = 0

            if "Categoria" not in perguntas_df_diag.columns:
                st.error("Coluna 'Categoria' não encontrada no arquivo de perguntas."); st.stop()

            categorias_unicas_diag = perguntas_df_diag["Categoria"].unique()

            with st.form(key=f"diagnostico_form_completo_{form_id_sufixo_nd}"):
                if total_perguntas_diag == 0:
                    st.warning("Nenhuma pergunta disponível.")
                else:
                    for categoria_diag in categorias_unicas_diag:
                        st.markdown(f"#### Categoria: {categoria_diag}")
                        perguntas_cat_diag = perguntas_df_diag[perguntas_df_diag["Categoria"] == categoria_diag]

                        if perguntas_cat_diag.empty: continue

                        for idx_diag_f, row_diag_f in perguntas_cat_diag.iterrows():
                            texto_pergunta_diag = str(row_diag_f["Pergunta"])
                            widget_base_key = f"q_form_{idx_diag_f}_{form_id_sufixo_nd}" # Adicionar form_id_sufixo para unicidade

                            if "[Matriz GUT]" in texto_pergunta_diag:
                                st.markdown(f"**{texto_pergunta_diag.replace(' [Matriz GUT]', '')}**")
                                cols_gut = st.columns(3)
                                gut_current_vals = respostas_form_coletadas_nd.get(texto_pergunta_diag, {"G":0, "U":0, "T":0})
                                with cols_gut[0]: g_val = st.slider("Gravidade (0-5)", 0, 5, value=int(gut_current_vals.get("G",0)), key=f"{widget_base_key}_G")
                                with cols_gut[1]: u_val = st.slider("Urgência (0-5)", 0, 5, value=int(gut_current_vals.get("U",0)), key=f"{widget_base_key}_U")
                                with cols_gut[2]: t_val = st.slider("Tendência (0-5)", 0, 5, value=int(gut_current_vals.get("T",0)), key=f"{widget_base_key}_T")
                                respostas_form_coletadas_nd[texto_pergunta_diag] = {"G": g_val, "U": u_val, "T": t_val}
                                if g_val > 0 or u_val > 0 or t_val > 0 : respondidas_count_diag +=1
                            elif "Pontuação (0-5)" in texto_pergunta_diag:
                                val_slider = respostas_form_coletadas_nd.get(texto_pergunta_diag, 0)
                                respostas_form_coletadas_nd[texto_pergunta_diag] = st.slider(texto_pergunta_diag, 0, 5, value=int(val_slider), key=widget_base_key)
                                if respostas_form_coletadas_nd[texto_pergunta_diag] != 0: respondidas_count_diag += 1
                            elif "Pontuação (0-10)" in texto_pergunta_diag:
                                val_slider = respostas_form_coletadas_nd.get(texto_pergunta_diag, 0)
                                respostas_form_coletadas_nd[texto_pergunta_diag] = st.slider(texto_pergunta_diag, 0, 10, value=int(val_slider), key=widget_base_key)
                                if respostas_form_coletadas_nd[texto_pergunta_diag] != 0: respondidas_count_diag += 1
                            elif "Texto Aberto" in texto_pergunta_diag:
                                val_text = respostas_form_coletadas_nd.get(texto_pergunta_diag, "")
                                respostas_form_coletadas_nd[texto_pergunta_diag] = st.text_area(texto_pergunta_diag, value=str(val_text), key=widget_base_key)
                                if respostas_form_coletadas_nd[texto_pergunta_diag].strip() != "": respondidas_count_diag += 1
                            elif "Escala" in texto_pergunta_diag:
                                opcoes_escala_diag = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]
                                val_escala = respostas_form_coletadas_nd.get(texto_pergunta_diag, "Selecione")
                                idx_sel_escala = opcoes_escala_diag.index(val_escala) if val_escala in opcoes_escala_diag else 0
                                respostas_form_coletadas_nd[texto_pergunta_diag] = st.selectbox(texto_pergunta_diag, opcoes_escala_diag, index=idx_sel_escala, key=widget_base_key)
                                if respostas_form_coletadas_nd[texto_pergunta_diag] != "Selecione": respondidas_count_diag += 1
                            else: # Default to 0-10 slider if no specific type matches
                                val_slider = respostas_form_coletadas_nd.get(texto_pergunta_diag, 0)
                                respostas_form_coletadas_nd[texto_pergunta_diag] = st.slider(texto_pergunta_diag, 0, 10, value=int(val_slider), key=widget_base_key)
                                if respostas_form_coletadas_nd[texto_pergunta_diag] != 0: respondidas_count_diag += 1
                        st.divider()

                progresso_diag = round((respondidas_count_diag / total_perguntas_diag) * 100) if total_perguntas_diag > 0 else 0
                st.info(f"📊 Progresso: {respondidas_count_diag} de {total_perguntas_diag} respondidas ({progresso_diag}%)")

                obs_cli_diag_form = st.text_area("Sua Análise/Observações (opcional):", value=respostas_form_coletadas_nd.get("__obs_cliente__", ""), key=f"obs_cli_diag_{form_id_sufixo_nd}")
                respostas_form_coletadas_nd["__obs_cliente__"] = obs_cli_diag_form

                diag_resumo_cli_diag = st.text_area("✍️ Resumo/principais insights (para PDF):", value=respostas_form_coletadas_nd.get("__resumo_cliente__", ""), key=f"diag_resumo_diag_{form_id_sufixo_nd}")
                respostas_form_coletadas_nd["__resumo_cliente__"] = diag_resumo_cli_diag

                enviar_diagnostico_btn = st.form_submit_button("✔️ Enviar Diagnóstico")

            if enviar_diagnostico_btn:
                if respondidas_count_diag < total_perguntas_diag: st.warning("Responda todas as perguntas para um diagnóstico completo.")
                elif not respostas_form_coletadas_nd["__resumo_cliente__"].strip(): st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
                else:
                    soma_total_gut_scores, count_gut_perguntas = 0, 0
                    respostas_finais_para_salvar = {}

                    for pergunta_env, resposta_env in respostas_form_coletadas_nd.items():
                        if pergunta_env.startswith("__"): continue
                        if isinstance(pergunta_env, str) and "[Matriz GUT]" in pergunta_env and isinstance(resposta_env, dict):
                            respostas_finais_para_salvar[pergunta_env] = json.dumps(resposta_env)
                            g_f, u_f, t_f = resposta_env.get("G",0), resposta_env.get("U",0), resposta_env.get("T",0)
                            soma_total_gut_scores += (g_f * u_f * t_f)
                            count_gut_perguntas +=1
                        else:
                            respostas_finais_para_salvar[pergunta_env] = resposta_env

                    gut_media_calc = round(soma_total_gut_scores / count_gut_perguntas, 2) if count_gut_perguntas > 0 else 0.0
                    numeric_resp_calc = [v_f for k_f, v_f in respostas_finais_para_salvar.items() if isinstance(v_f, (int, float)) and (isinstance(k_f, str) and ("Pontuação (0-10)" in k_f or "Pontuação (0-5)" in k_f))]
                    media_geral_calc_val = round(sum(numeric_resp_calc) / len(numeric_resp_calc), 2) if numeric_resp_calc else 0.0
                    empresa_nome_final_val = st.session_state.user.get("Empresa", "N/D")

                    nova_linha_final_val = {
                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": st.session_state.cnpj,
                        "Nome": st.session_state.user.get("NomeContato", st.session_state.user.get("CNPJ", "")), # Usar NomeContato ou CNPJ
                        "Email": "", # Adicionar se tiver
                        "Empresa": empresa_nome_final_val,
                        "Média Geral": media_geral_calc_val, "GUT Média": gut_media_calc,
                        "Observações": "", # Campo geral, não preenchido pelo cliente no form
                        "Análise do Cliente": respostas_form_coletadas_nd.get("__obs_cliente__",""),
                        "Diagnóstico": respostas_form_coletadas_nd.get("__resumo_cliente__",""),
                        "Comentarios_Admin": ""
                    }
                    nova_linha_final_val.update(respostas_finais_para_salvar)

                    medias_por_categoria_final_val = {}
                    for cat_final_calc_val in categorias_unicas_diag:
                        perguntas_cat_final_df_val = perguntas_df_diag[perguntas_df_diag["Categoria"] == cat_final_calc_val]
                        soma_cat_final_val, cont_num_cat_final_val = 0, 0
                        for _, p_row_final_val in perguntas_cat_final_df_val.iterrows():
                            txt_p_final_val = p_row_final_val["Pergunta"]
                            resp_p_final_val = respostas_form_coletadas_nd.get(txt_p_final_val)
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

                    # Atualizar status do cliente para não poder fazer novo diagnóstico
                    update_user_data(st.session_state.cnpj, "PodeFazerNovoDiagnostico", False)
                    st.session_state.user["PodeFazerNovoDiagnostico"] = False # Atualiza local

                    st.success("Diagnóstico enviado com sucesso!")
                    registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", "Cliente enviou novo diagnóstico.")

                    pdf_path_final_val = gerar_pdf_diagnostico_completo(
                        diagnostico_data_pdf_param=nova_linha_final_val,
                        usuario_data_pdf_param=st.session_state.user,
                        perguntas_df_pdf_param=perguntas_df_diag,
                        respostas_coletadas_pdf_param=respostas_form_coletadas_nd, # Usa as coletadas no form
                        medias_categorias_pdf_param=medias_por_categoria_final_val
                    )
                    if pdf_path_final_val:
                        with open(pdf_path_final_val, "rb") as f_pdf_final_val:
                            st.download_button(label="📄 Baixar PDF do Diagnóstico", data=f_pdf_final_val,
                                               file_name=f"diagnostico_{sanitize_column_name(empresa_nome_final_val)}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                               mime="application/pdf", key="download_pdf_cliente_final_v3")
                        registrar_acao(st.session_state.cnpj, "Download PDF", "Baixou PDF do novo diagnóstico.")

                    if DIAGNOSTICO_FORM_ID_KEY_USER in st.session_state: del st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER]
                    if temp_respostas_key_nd in st.session_state: del st.session_state[temp_respostas_key_nd]

                    st.session_state.diagnostico_enviado = True
                    st.session_state.cliente_page = "Painel Principal"
                    st.rerun()
    except Exception as e_cliente_area_v3:
        st.error(f"Ocorreu um erro na área do cliente: {e_cliente_area_v3}")
        st.exception(e_cliente_area_v3)


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    st.sidebar.image("https://raw.githubusercontent.com/AndersonCRMG/AppDiagnostico/main/Logo%20Transparente%20(1).png", width=100)
    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("🚪 Sair do Painel Admin"):
        st.session_state.admin_logado = False; st.rerun()

    menu_admin = st.sidebar.selectbox(
        "Funcionalidades Admin:",
        ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Perguntas",
         "Gerenciar Clientes", "Gerenciar Administradores"],
        key="admin_menu_selectbox_v3"
    )
    st.header(f"🔑 Painel Admin: {menu_admin}")

    try:
        if menu_admin == "Visão Geral e Diagnósticos":
            st.subheader("📊 Visão Geral dos Diagnósticos")

            diagnosticos_df_admin = pd.DataFrame()
            admin_data_loaded = False
            try:
                if not os.path.exists(arquivo_csv) or os.path.getsize(arquivo_csv) == 0:
                    st.warning(f"Arquivo de diagnósticos ({arquivo_csv}) não encontrado ou está vazio.")
                else:
                    diagnosticos_df_admin = pd.read_csv(arquivo_csv, encoding='utf-8')
                    if 'Data' in diagnosticos_df_admin.columns:
                         diagnosticos_df_admin['Data'] = pd.to_datetime(diagnosticos_df_admin['Data'], errors='coerce')
                    if diagnosticos_df_admin.empty:
                        st.info("Arquivo de diagnósticos lido, mas não contém dados.")
                    else:
                        admin_data_loaded = True
            except Exception as e_load_diag_admin_vg_v3:
                st.error(f"ERRO AO CARREGAR DIAGNÓSTICOS: {e_load_diag_admin_vg_v3}")
                st.exception(e_load_diag_admin_vg_v3)

            if admin_data_loaded and not diagnosticos_df_admin.empty:
                col_filter1, col_filter2, col_filter3 = st.columns(3)
                with col_filter1:
                    empresas_disponiveis_vg = ["Todos os Clientes"] + sorted(diagnosticos_df_admin["Empresa"].astype(str).unique().tolist())
                    empresa_selecionada_vg = st.selectbox(
                        "Filtrar por Empresa:",
                        empresas_disponiveis_vg,
                        key="admin_vg_filtro_empresa_v3"
                    )
                with col_filter2:
                    data_inicio_filtro = st.date_input("Data Início:", value=None, key="admin_vg_data_inicio")
                with col_filter3:
                    data_fim_filtro = st.date_input("Data Fim:", value=None, key="admin_vg_data_fim")


                df_filtrado_vg = diagnosticos_df_admin.copy()
                if empresa_selecionada_vg != "Todos os Clientes":
                    df_filtrado_vg = df_filtrado_vg[df_filtrado_vg["Empresa"] == empresa_selecionada_vg]
                
                if data_inicio_filtro:
                    df_filtrado_vg = df_filtrado_vg[df_filtrado_vg['Data'] >= pd.to_datetime(data_inicio_filtro)]
                if data_fim_filtro:
                    # Adicionar 1 dia ao data_fim_filtro para incluir o dia inteiro
                    df_filtrado_vg = df_filtrado_vg[df_filtrado_vg['Data'] < pd.to_datetime(data_fim_filtro) + pd.Timedelta(days=1)]


                if df_filtrado_vg.empty:
                    st.info(f"Nenhum diagnóstico encontrado para os filtros aplicados.")
                else:
                    st.markdown(f"#### Indicadores Gerais para: {empresa_selecionada_vg} (Período Selecionado)")
                    col_ig1_vg, col_ig2_vg, col_ig3_vg = st.columns(3)
                    with col_ig1_vg: st.metric("📦 Diagnósticos Selecionados", len(df_filtrado_vg))
                    with col_ig2_vg:
                        media_geral_todos_vg = pd.to_numeric(df_filtrado_vg["Média Geral"], errors='coerce').mean()
                        st.metric("📈 Média Geral", f"{media_geral_todos_vg:.2f}" if pd.notna(media_geral_todos_vg) else "N/A")
                    with col_ig3_vg:
                        if "GUT Média" in df_filtrado_vg.columns:
                            gut_media_todos_vg = pd.to_numeric(df_filtrado_vg["GUT Média"], errors='coerce').mean()
                            st.metric("🔥 GUT Média (G*U*T)", f"{gut_media_todos_vg:.2f}" if pd.notna(gut_media_todos_vg) else "N/A")
                        else: st.metric("🔥 GUT Média (G*U*T)", "N/A")
                    st.divider()

                    st.markdown(f"#### Evolução Mensal ({empresa_selecionada_vg})")
                    df_diag_vis_vg = df_filtrado_vg.copy()
                    df_diag_vis_vg = df_diag_vis_vg.dropna(subset=["Data"])
                    if not df_diag_vis_vg.empty:
                        df_diag_vis_vg["Mês/Ano"] = df_diag_vis_vg["Data"].dt.to_period("M").astype(str)
                        df_diag_vis_vg["Média Geral"] = pd.to_numeric(df_diag_vis_vg["Média Geral"], errors='coerce')
                        df_diag_vis_vg["GUT Média"] = pd.to_numeric(df_diag_vis_vg.get("GUT Média"), errors='coerce') if "GUT Média" in df_diag_vis_vg else pd.Series(dtype='float64', index=df_diag_vis_vg.index)

                        resumo_mensal_vg = df_diag_vis_vg.groupby("Mês/Ano").agg(
                            Diagnósticos_Realizados=("CNPJ", "count"),
                            Média_Geral_Mensal=("Média Geral", "mean"),
                            GUT_Média_Mensal=("GUT Média", "mean")
                        ).reset_index().sort_values("Mês/Ano")
                        resumo_mensal_vg["Mês/Ano_Display"] = pd.to_datetime(resumo_mensal_vg["Mês/Ano"], errors='coerce').dt.strftime('%b/%y')

                        if not resumo_mensal_vg.empty:
                            fig_contagem_vg = px.bar(resumo_mensal_vg, x="Mês/Ano_Display", y="Diagnósticos_Realizados", title="Diagnósticos por Mês", height=350, labels={'Diagnósticos_Realizados':'Total', "Mês/Ano_Display": "Mês"})
                            st.plotly_chart(fig_contagem_vg, use_container_width=True)
                            fig_medias_vg = px.line(resumo_mensal_vg, x="Mês/Ano_Display", y=["Média_Geral_Mensal", "GUT_Média_Mensal"], title="Médias Gerais e GUT por Mês", height=350, labels={'value':'Média', 'variable':'Indicador', "Mês/Ano_Display": "Mês"})
                            fig_medias_vg.update_traces(mode='lines+markers')
                            st.plotly_chart(fig_medias_vg, use_container_width=True)
                        else: st.info("Sem dados para gráficos de evolução mensal com os filtros atuais.")
                    else: st.info("Sem diagnósticos com datas válidas para evolução com os filtros atuais.")
                    st.divider()
                    
                    if empresa_selecionada_vg != "Todos os Clientes" and not df_filtrado_vg.empty:
                        st.markdown(f"#### Melhor Diagnóstico para {empresa_selecionada_vg} (Baseado na Maior Média Geral)")
                        df_empresa_sorted = df_filtrado_vg.sort_values(by="Média Geral", ascending=False)
                        if not df_empresa_sorted.empty:
                            melhor_diag_empresa = df_empresa_sorted.iloc[0]
                            st.success(f"🏆 O diagnóstico de **{melhor_diag_empresa['Data'].strftime('%d/%m/%Y %H:%M')}** teve a maior Média Geral: **{melhor_diag_empresa.get('Média Geral', 0.0):.2f}**")
                        else:
                            st.info("Nenhum diagnóstico para determinar o melhor para esta empresa com os filtros atuais.")
                        st.divider()


                    if empresa_selecionada_vg == "Todos os Clientes":
                        st.markdown("#### Ranking das Empresas (Média Geral)")
                        if "Empresa" in df_filtrado_vg.columns and "Média Geral" in df_filtrado_vg.columns:
                            df_filtrado_vg["Média Geral Num"] = pd.to_numeric(df_filtrado_vg["Média Geral"], errors='coerce')
                            ranking_df_vg = df_filtrado_vg.dropna(subset=["Média Geral Num"])
                            if not ranking_df_vg.empty:
                                ranking_vg = ranking_df_vg.groupby("Empresa")["Média Geral Num"].mean().sort_values(ascending=False).reset_index()
                                ranking_vg.index = ranking_vg.index + 1
                                st.dataframe(ranking_vg.rename(columns={"Média Geral Num": "Média Geral (Ranking)"}))
                            else: st.info("Sem dados para ranking de Média Geral.")
                        st.divider()

                        st.markdown("#### Ranking das Empresas (Média GUT G*U*T)")
                        if "Empresa" in df_filtrado_vg.columns and "GUT Média" in df_filtrado_vg.columns:
                            df_filtrado_vg["GUT Média Num"] = pd.to_numeric(df_filtrado_vg["GUT Média"], errors='coerce')
                            ranking_gut_df_vg = df_filtrado_vg.dropna(subset=["GUT Média Num"])
                            if not ranking_gut_df_vg.empty and not ranking_gut_df_vg[ranking_gut_df_vg["GUT Média Num"] > 0].empty :
                                ranking_gut_vg = ranking_gut_df_vg[ranking_gut_df_vg["GUT Média Num"] > 0].groupby("Empresa")["GUT Média Num"].mean().sort_values(ascending=False).reset_index()
                                ranking_gut_vg.index = ranking_gut_vg.index + 1
                                st.dataframe(ranking_gut_vg.rename(columns={"GUT Média Num": "Média Score GUT (Ranking)"}))
                            else: st.info("Sem dados ou scores GUT válidos (>0) para ranking GUT.")
                        st.divider()

                    st.markdown(f"#### Diagnósticos Enviados ({empresa_selecionada_vg} - Filtro Aplicado)")
                    st.dataframe(df_filtrado_vg.sort_values(by="Data", ascending=False).reset_index(drop=True))
                    if empresa_selecionada_vg == "Todos os Clientes": # Ou se quiser exportar o filtrado
                        csv_export_admin_vg = df_filtrado_vg.to_csv(index=False).encode('utf-8')
                        st.download_button("⬇️ Exportar Diagnósticos Filtrados (CSV)", csv_export_admin_vg, file_name=f"diagnosticos_filtrados.csv", mime="text/csv", key="download_filtrados_csv_admin_v3")
                    st.divider()

                    st.markdown("#### Detalhar, Comentar e Baixar PDF de Diagnóstico Específico")
                    # Usar df_filtrado_vg para popular selectbox de empresas para detalhe
                    empresas_detalhe_vg_filtradas = sorted(df_filtrado_vg["Empresa"].astype(str).unique().tolist())
                    if not empresas_detalhe_vg_filtradas:
                        st.info("Nenhuma empresa na seleção atual para detalhar.")
                    else:
                        default_empresa_detalhe_idx_vg = 0
                        if empresa_selecionada_vg != "Todos os Clientes" and empresa_selecionada_vg in empresas_detalhe_vg_filtradas:
                            default_empresa_detalhe_idx_vg = empresas_detalhe_vg_filtradas.index(empresa_selecionada_vg)

                        empresa_selecionada_detalhe_vg = st.selectbox("Selecione uma Empresa para Detalhar (da lista filtrada):", empresas_detalhe_vg_filtradas, index=default_empresa_detalhe_idx_vg, key="admin_empresa_filter_detail_v3")

                        diagnosticos_empresa_detalhe_vg = df_filtrado_vg[df_filtrado_vg["Empresa"] == empresa_selecionada_detalhe_vg].sort_values(by="Data", ascending=False)
                        if not diagnosticos_empresa_detalhe_vg.empty:
                            datas_diagnosticos_detalhe_vg = ["Selecione Data..."] + diagnosticos_empresa_detalhe_vg["Data"].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
                            diagnostico_data_str_selecionada_detalhe_vg = st.selectbox("Selecione a Data do Diagnóstico:", datas_diagnosticos_detalhe_vg, key="admin_data_diagnostico_select_v3")
                            if diagnostico_data_str_selecionada_detalhe_vg != "Selecione Data...":
                                diagnostico_selecionado_adm_row_vg = diagnosticos_empresa_detalhe_vg[diagnosticos_empresa_detalhe_vg["Data"] == pd.to_datetime(diagnostico_data_str_selecionada_detalhe_vg)].iloc[0]
                                diag_original_index = diagnostico_selecionado_adm_row_vg.name # Preserve original index for saving

                                st.markdown(f"**Detalhes do Diagnóstico de {diagnostico_selecionado_adm_row_vg['Data'].strftime('%d/%m/%Y %H:%M')}**")
                                st.write(f"**Média Geral:** {diagnostico_selecionado_adm_row_vg.get('Média Geral', 'N/A')} | **GUT Média (G*U*T):** {diagnostico_selecionado_adm_row_vg.get('GUT Média', 'N/A')}")

                                comentario_adm_atual_val_vg = diagnostico_selecionado_adm_row_vg.get("Comentarios_Admin", "")
                                if pd.isna(comentario_adm_atual_val_vg): comentario_adm_atual_val_vg = ""
                                novo_comentario_adm_val_vg = st.text_area("Comentários do Consultor/Admin:", value=comentario_adm_atual_val_vg, key=f"admin_comment_detail_v3_{diag_original_index}")
                                if st.button("💾 Salvar Comentário", key=f"save_admin_comment_detail_v3_{diag_original_index}"):
                                    df_diag_save_com_adm_det_vg = pd.read_csv(arquivo_csv, encoding='utf-8')
                                    df_diag_save_com_adm_det_vg.loc[diag_original_index, "Comentarios_Admin"] = novo_comentario_adm_val_vg
                                    df_diag_save_com_adm_det_vg.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                    registrar_acao("ADMIN", "Comentário Admin", f"Admin comentou diag. de {diagnostico_selecionado_adm_row_vg['Data']} para {empresa_selecionada_detalhe_vg}")
                                    st.success("Comentário salvo!"); st.rerun()

                                if st.button("📄 Baixar PDF deste Diagnóstico", key=f"download_pdf_admin_v3_{diag_original_index}"):
                                    try:
                                        perguntas_df_pdf_adm_vg = pd.read_csv(perguntas_csv, encoding='utf-8')
                                        if "Categoria" not in perguntas_df_pdf_adm_vg.columns: perguntas_df_pdf_adm_vg["Categoria"] = "Geral"
                                    except: perguntas_df_pdf_adm_vg = pd.DataFrame(columns=colunas_base_perguntas)

                                    respostas_para_pdf_adm_vg = diagnostico_selecionado_adm_row_vg.to_dict()
                                    medias_cat_pdf_adm_vg = {}
                                    if not perguntas_df_pdf_adm_vg.empty and "Categoria" in perguntas_df_pdf_adm_vg.columns:
                                        cats_unicas_pdf_adm_vg = perguntas_df_pdf_adm_vg["Categoria"].unique()
                                        for cat_pdf_adm_calc_vg in cats_unicas_pdf_adm_vg:
                                            nome_col_media_cat_pdf_vg = f"Media_Cat_{sanitize_column_name(cat_pdf_adm_calc_vg)}"
                                            medias_cat_pdf_adm_vg[cat_pdf_adm_calc_vg] = diagnostico_selecionado_adm_row_vg.get(nome_col_media_cat_pdf_vg, 0.0)
                                    try:
                                        usuarios_df_pdf_adm_vg = pd.read_csv(usuarios_csv, encoding='utf-8')
                                        usuario_data_pdf_adm_vg = usuarios_df_pdf_adm_vg[usuarios_df_pdf_adm_vg["CNPJ"].astype(str) == str(diagnostico_selecionado_adm_row_vg["CNPJ"])].iloc[0].to_dict()
                                    except: usuario_data_pdf_adm_vg = {"Empresa": diagnostico_selecionado_adm_row_vg.get("Empresa", "N/D"),
                                                                       "CNPJ": diagnostico_selecionado_adm_row_vg.get("CNPJ", "N/D"),
                                                                       "NomeContato": diagnostico_selecionado_adm_row_vg.get("NomeContato","N/D"),
                                                                       "Telefone": diagnostico_selecionado_adm_row_vg.get("Telefone","N/D")}

                                    pdf_path_admin_dl_vg = gerar_pdf_diagnostico_completo(
                                        diagnostico_data_pdf_param=diagnostico_selecionado_adm_row_vg.to_dict(),
                                        usuario_data_pdf_param=usuario_data_pdf_adm_vg,
                                        perguntas_df_pdf_param=perguntas_df_pdf_adm_vg,
                                        respostas_coletadas_pdf_param=respostas_para_pdf_adm_vg, # Passa o row como respostas
                                        medias_categorias_pdf_param=medias_cat_pdf_adm_vg
                                    )
                                    if pdf_path_admin_dl_vg:
                                        with open(pdf_path_admin_dl_vg, "rb") as f_pdf_adm_dl_vg:
                                            st.download_button(label="Download PDF Confirmado", data=f_pdf_adm_dl_vg,
                                                               file_name=f"diagnostico_{sanitize_column_name(empresa_selecionada_detalhe_vg)}_{diagnostico_selecionado_adm_row_vg['Data'].strftime('%Y%m%d_%H%M%S')}.pdf",
                                                               mime="application/pdf", key=f"confirm_dl_pdf_admin_v3_{diag_original_index}")
                                        registrar_acao("ADMIN", "Download PDF Cliente", f"Admin baixou PDF de {diagnostico_selecionado_adm_row_vg['Data']} para {empresa_selecionada_detalhe_vg}")
                                    else: st.error("Falha ao gerar o PDF para download.")
                        else: st.info(f"Nenhum diagnóstico para a empresa {empresa_selecionada_detalhe_vg} com os filtros atuais.")
            else:
                st.warning("AVISO: Nenhum dado de diagnóstico carregado ou os filtros não retornaram resultados.")


        elif menu_admin == "Histórico de Usuários":
            st.subheader("📜 Histórico de Ações dos Clientes")
            try:
                historico_df = pd.read_csv(historico_csv, encoding='utf-8')
                if not historico_df.empty:
                    st.dataframe(historico_df.sort_values(by="Data", ascending=False))
                else: st.info("Nenhum histórico de ações encontrado.")
            except (FileNotFoundError, pd.errors.EmptyDataError): st.info("Arquivo de histórico não encontrado ou vazio.")
            except Exception as e_hist_v3: st.error(f"Erro ao carregar histórico: {e_hist_v3}")

        elif menu_admin == "Gerenciar Perguntas":
            st.subheader("📝 Gerenciar Perguntas do Diagnóstico")
            tabs_perg_admin = st.tabs(["📋 Perguntas Atuais", "➕ Adicionar Nova Pergunta"])
            with tabs_perg_admin[0]:
                try:
                    perguntas_df_admin_edit = pd.read_csv(perguntas_csv, encoding='utf-8')
                    if "Categoria" not in perguntas_df_admin_edit.columns: perguntas_df_admin_edit["Categoria"] = "Geral"
                except (FileNotFoundError, pd.errors.EmptyDataError):
                    st.info("Arquivo de perguntas não encontrado ou vazio.")
                    perguntas_df_admin_edit = pd.DataFrame(columns=colunas_base_perguntas)

                if perguntas_df_admin_edit.empty: st.info("Nenhuma pergunta cadastrada.")
                else:
                    for i_p_admin, row_p_admin in perguntas_df_admin_edit.iterrows():
                        cols_p_admin = st.columns([4, 2, 0.5, 0.5])
                        with cols_p_admin[0]:
                            nova_p_text_admin = st.text_input("Pergunta", value=str(row_p_admin["Pergunta"]), key=f"edit_p_txt_v3_{i_p_admin}")
                        with cols_p_admin[1]:
                            nova_cat_text_admin = st.text_input("Categoria", value=str(row_p_admin.get("Categoria", "Geral")), key=f"edit_p_cat_v3_{i_p_admin}")
                        with cols_p_admin[2]:
                            st.write("") # Spacer
                            if st.button("💾", key=f"salvar_p_adm_v3_{i_p_admin}", help="Salvar"):
                                perguntas_df_admin_edit.loc[i_p_admin, "Pergunta"] = nova_p_text_admin
                                perguntas_df_admin_edit.loc[i_p_admin, "Categoria"] = nova_cat_text_admin
                                perguntas_df_admin_edit.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.success(f"Pergunta {i_p_admin+1} atualizada."); st.rerun()
                        with cols_p_admin[3]:
                            st.write("") # Spacer
                            if st.button("🗑️", key=f"deletar_p_adm_v3_{i_p_admin}", help="Deletar"):
                                perguntas_df_admin_edit = perguntas_df_admin_edit.drop(i_p_admin).reset_index(drop=True)
                                perguntas_df_admin_edit.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.warning(f"Pergunta {i_p_admin+1} removida."); st.rerun()
                        st.divider()
            with tabs_perg_admin[1]:
                with st.form("form_nova_pergunta_admin_v3"):
                    st.subheader("➕ Adicionar Nova Pergunta")
                    nova_p_form_txt_admin = st.text_input("Texto da Pergunta", key="nova_p_input_admin_txt_v3")
                    try:
                        perg_exist_df = pd.read_csv(perguntas_csv, encoding='utf-8')
                        cat_existentes = sorted(list(perg_exist_df['Categoria'].astype(str).unique())) if not perg_exist_df.empty and "Categoria" in perg_exist_df else []
                    except: cat_existentes = []

                    cat_options = ["Nova Categoria"] + cat_existentes
                    cat_selecionada = st.selectbox("Categoria:", cat_options, key="cat_select_admin_new_q_v3")

                    if cat_selecionada == "Nova Categoria":
                        nova_cat_form_admin = st.text_input("Nome da Nova Categoria:", key="nova_cat_input_admin_new_q_v3")
                    else: nova_cat_form_admin = cat_selecionada

                    tipo_p_form_admin = st.selectbox("Tipo de Pergunta",
                                                     ["Pontuação (0-10)", "Pontuação (0-5)", "Texto Aberto", "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)", "[Matriz GUT]"],
                                                     key="tipo_p_select_admin_new_q_v3")
                    add_p_btn_admin = st.form_submit_button("Adicionar Pergunta")
                    if add_p_btn_admin:
                        if nova_p_form_txt_admin.strip() and nova_cat_form_admin.strip():
                            try: df_perg_add_admin = pd.read_csv(perguntas_csv, encoding='utf-8')
                            except (FileNotFoundError, pd.errors.EmptyDataError): df_perg_add_admin = pd.DataFrame(columns=colunas_base_perguntas)
                            if "Categoria" not in df_perg_add_admin.columns: df_perg_add_admin["Categoria"] = "Geral"

                            p_completa_add_admin = f"{nova_p_form_txt_admin.strip()} [{tipo_p_form_admin.replace('[','').replace(']','')}]" # Adiciona tipo entre colchetes

                            nova_entrada_p_add_admin = pd.DataFrame([[p_completa_add_admin, nova_cat_form_admin.strip()]], columns=["Pergunta", "Categoria"])
                            df_perg_add_admin = pd.concat([df_perg_add_admin, nova_entrada_p_add_admin], ignore_index=True)
                            df_perg_add_admin.to_csv(perguntas_csv, index=False, encoding='utf-8')
                            st.success(f"Pergunta adicionada!"); st.rerun()
                        else: st.warning("Texto da pergunta e categoria são obrigatórios.")

        elif menu_admin == "Gerenciar Clientes":
            st.subheader("👥 Gerenciar Clientes")
            try:
                usuarios_clientes_df = pd.read_csv(usuarios_csv, encoding='utf-8')
                # Garantir que as novas colunas existam
                if "PodeFazerNovoDiagnostico" not in usuarios_clientes_df.columns:
                    usuarios_clientes_df["PodeFazerNovoDiagnostico"] = True 
                    usuarios_clientes_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
                if "JaVisualizouInstrucoes" not in usuarios_clientes_df.columns:
                    usuarios_clientes_df["JaVisualizouInstrucoes"] = False
                    usuarios_clientes_df.to_csv(usuarios_csv, index=False, encoding='utf-8')

                for col_usr_check in colunas_base_usuarios:
                    if col_usr_check not in usuarios_clientes_df.columns: usuarios_clientes_df[col_usr_check] = "" # Ou valor default apropriado
            except (FileNotFoundError, pd.errors.EmptyDataError):
                usuarios_clientes_df = pd.DataFrame(columns=colunas_base_usuarios)

            st.caption(f"Total de clientes: {len(usuarios_clientes_df)}")

            if not usuarios_clientes_df.empty:
                st.markdown("#### Editar Clientes Existentes")
                for idx_gc, row_gc in usuarios_clientes_df.iterrows():
                    with st.expander(f"{row_gc.get('Empresa','N/A')} (CNPJ: {row_gc['CNPJ']})"):
                        cols_edit_cli = st.columns(2)
                        with cols_edit_cli[0]:
                            st.text_input("CNPJ (não editável)", value=row_gc['CNPJ'], disabled=True, key=f"cnpj_gc_v3_{idx_gc}")
                            nova_senha_gc = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password", key=f"senha_gc_v3_{idx_gc}")
                            nome_empresa_gc = st.text_input("Nome Empresa", value=row_gc.get('Empresa',""), key=f"empresa_gc_v3_{idx_gc}")
                            
                            pode_fazer_novo_atual = bool(row_gc.get('PodeFazerNovoDiagnostico', True))
                            if st.button(f"{'Desabilitar' if pode_fazer_novo_atual else 'Liberar'} Novo Diagnóstico", key=f"liberar_diag_gc_{idx_gc}"):
                                if update_user_data(row_gc['CNPJ'], "PodeFazerNovoDiagnostico", not pode_fazer_novo_atual):
                                    st.success(f"Status de novo diagnóstico para {row_gc['Empresa']} atualizado para: {not pode_fazer_novo_atual}")
                                    registrar_acao("ADMIN", "Liberação Diagnóstico", f"Status 'PodeFazerNovoDiagnostico' para {row_gc['CNPJ']} alterado para {not pode_fazer_novo_atual}")
                                    st.rerun()
                                else:
                                    st.error("Falha ao atualizar status de novo diagnóstico.")
                            st.caption(f"Pode fazer novo diagnóstico: {'Sim' if pode_fazer_novo_atual else 'Não'}")


                        with cols_edit_cli[1]:
                            nome_contato_gc = st.text_input("Nome Contato", value=row_gc.get("NomeContato", ""), key=f"nomec_gc_v3_{idx_gc}")
                            telefone_gc = st.text_input("Telefone", value=row_gc.get("Telefone", ""), key=f"tel_gc_v3_{idx_gc}")
                            logo_atual_path = find_client_logo_path(row_gc['CNPJ'])
                            if logo_atual_path: st.image(logo_atual_path, width=100, caption="Logo Atual")
                            uploaded_logo_gc = st.file_uploader("Alterar/Adicionar Logo", type=["png", "jpg", "jpeg"], key=f"logo_gc_v3_{idx_gc}")

                        if st.button("💾 Salvar Alterações do Cliente", key=f"save_gc_v3_{idx_gc}"):
                            changes_made_gc = False
                            if nova_senha_gc: usuarios_clientes_df.loc[idx_gc, "Senha"] = nova_senha_gc; changes_made_gc = True
                            if nome_empresa_gc != row_gc.get('Empresa',""): usuarios_clientes_df.loc[idx_gc, "Empresa"] = nome_empresa_gc; changes_made_gc = True
                            if nome_contato_gc != row_gc.get('NomeContato',""): usuarios_clientes_df.loc[idx_gc, "NomeContato"] = nome_contato_gc; changes_made_gc = True
                            if telefone_gc != row_gc.get('Telefone',""): usuarios_clientes_df.loc[idx_gc, "Telefone"] = telefone_gc; changes_made_gc = True
                            
                            if uploaded_logo_gc is not None:
                                if not os.path.exists(LOGOS_DIR): os.makedirs(LOGOS_DIR)
                                clean_cnpj_gc_save = sanitize_column_name(str(row_gc['CNPJ']))
                                for ext_old in ["png", "jpg", "jpeg"]:
                                    old_path = os.path.join(LOGOS_DIR, f"{clean_cnpj_gc_save}_logo.{ext_old}")
                                    if os.path.exists(old_path):
                                        try: os.remove(old_path)
                                        except Exception as e_remove_logo: st.warning(f"Não foi possível remover logo antiga {old_path}: {e_remove_logo}")
                                file_extension = uploaded_logo_gc.name.split('.')[-1].lower()
                                logo_save_path_gc = os.path.join(LOGOS_DIR, f"{clean_cnpj_gc_save}_logo.{file_extension}")
                                try:
                                    with open(logo_save_path_gc, "wb") as f: f.write(uploaded_logo_gc.getbuffer())
                                    st.success(f"Logo de {row_gc['Empresa']} atualizada!")
                                    changes_made_gc = True # Consider this a change
                                except Exception as e_save_logo_v3: st.error(f"Erro ao salvar logo: {e_save_logo_v3}")
                            
                            if changes_made_gc:
                                usuarios_clientes_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
                                st.success(f"Dados de {row_gc['Empresa']} atualizados!"); st.rerun()
                            else:
                                st.info("Nenhuma alteração detectada para salvar (exceto liberação de diagnóstico que é salva individualmente).")
                        st.divider()


            st.subheader("➕ Adicionar Novo Cliente")
            with st.form("form_novo_cliente_admin_v3"):
                cols_add_cli_1 = st.columns(2)
                with cols_add_cli_1[0]:
                    novo_cnpj_gc_form = st.text_input("CNPJ do cliente *")
                    nova_senha_gc_form = st.text_input("Senha para o cliente *", type="password")
                    nova_empresa_gc_form = st.text_input("Nome da empresa cliente *")
                with cols_add_cli_1[1]:
                    novo_nomecontato_gc_form = st.text_input("Nome do Contato")
                    novo_telefone_gc_form = st.text_input("Telefone")
                    nova_logo_gc_form = st.file_uploader("Logo da Empresa", type=["png", "jpg", "jpeg"], key="new_client_logo_uploader")

                adicionar_cliente_btn_gc = st.form_submit_button("Adicionar Cliente")

            if adicionar_cliente_btn_gc:
                if novo_cnpj_gc_form and nova_senha_gc_form and nova_empresa_gc_form:
                    if novo_cnpj_gc_form in usuarios_clientes_df["CNPJ"].astype(str).values:
                         st.error(f"CNPJ {novo_cnpj_gc_form} já cadastrado.")
                    else:
                        novo_usuario_data_gc = pd.DataFrame([[
                            novo_cnpj_gc_form, nova_senha_gc_form, nova_empresa_gc_form,
                            novo_nomecontato_gc_form, novo_telefone_gc_form,
                            True, False # PodeFazerNovoDiagnostico = True, JaVisualizouInstrucoes = False
                            ]], columns=colunas_base_usuarios)
                        usuarios_clientes_df = pd.concat([usuarios_clientes_df, novo_usuario_data_gc], ignore_index=True)
                        usuarios_clientes_df.to_csv(usuarios_csv, index=False, encoding='utf-8')

                        if nova_logo_gc_form is not None:
                            if not os.path.exists(LOGOS_DIR): os.makedirs(LOGOS_DIR)
                            clean_cnpj_new_gc_save = sanitize_column_name(str(novo_cnpj_gc_form))
                            file_extension_new = nova_logo_gc_form.name.split('.')[-1].lower()
                            logo_save_path_new_gc = os.path.join(LOGOS_DIR, f"{clean_cnpj_new_gc_save}_logo.{file_extension_new}")
                            try:
                                with open(logo_save_path_new_gc, "wb") as f: f.write(nova_logo_gc_form.getbuffer())
                            except Exception as e_save_new_logo_v3: st.error(f"Erro ao salvar nova logo: {e_save_new_logo_v3}")

                        st.success(f"Cliente '{nova_empresa_gc_form}' adicionado!"); st.rerun()
                else: st.warning("CNPJ, Senha e Nome da Empresa são obrigatórios.")

            st.markdown("---"); st.subheader("🚫 Gerenciar Bloqueios de Acesso")
            try: bloqueados_df_adm = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
            except (FileNotFoundError, pd.errors.EmptyDataError): bloqueados_df_adm = pd.DataFrame(columns=["CNPJ"])
            st.write("CNPJs com acesso bloqueado:", bloqueados_df_adm["CNPJ"].tolist() if not bloqueados_df_adm.empty else "Nenhum")
            col_block, col_unblock = st.columns(2)
            with col_block:
                cnpj_para_bloquear = st.selectbox("Bloquear CNPJ:", [""] + usuarios_clientes_df["CNPJ"].astype(str).unique().tolist(), key="block_cnpj_v3")
                if st.button("Bloquear Selecionado", key="btn_block_v3") and cnpj_para_bloquear:
                    if cnpj_para_bloquear not in bloqueados_df_adm["CNPJ"].astype(str).values:
                        nova_block = pd.DataFrame([[cnpj_para_bloquear]], columns=["CNPJ"])
                        bloqueados_df_adm = pd.concat([bloqueados_df_adm, nova_block], ignore_index=True)
                        bloqueados_df_adm.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        st.success(f"CNPJ {cnpj_para_bloquear} bloqueado."); st.rerun()
                    else: st.warning(f"CNPJ {cnpj_para_bloquear} já bloqueado.")
            with col_unblock:
                cnpj_para_desbloquear = st.selectbox("Desbloquear CNPJ:", [""] + bloqueados_df_adm["CNPJ"].astype(str).unique().tolist(), key="unblock_cnpj_v3")
                if st.button("Desbloquear Selecionado", key="btn_unblock_v3") and cnpj_para_desbloquear:
                    bloqueados_df_adm = bloqueados_df_adm[bloqueados_df_adm["CNPJ"].astype(str) != cnpj_para_desbloquear]
                    bloqueados_df_adm.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                    st.success(f"CNPJ {cnpj_para_desbloquear} desbloqueado."); st.rerun()

        elif menu_admin == "Gerenciar Administradores":
            st.subheader("👮 Gerenciar Administradores")
            try:
                admins_df_manage = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            except (FileNotFoundError, pd.errors.EmptyDataError):
                admins_df_manage = pd.DataFrame(columns=["Usuario", "Senha"])

            st.dataframe(admins_df_manage[["Usuario"]])
            st.markdown("---"); st.subheader("➕ Adicionar Novo Admin")
            with st.form("form_novo_admin_manage_v3"):
                novo_admin_user_manage = st.text_input("Usuário do Admin")
                novo_admin_pass_manage = st.text_input("Senha do Admin", type="password")
                adicionar_admin_btn_manage = st.form_submit_button("Adicionar Admin")
            if adicionar_admin_btn_manage:
                if novo_admin_user_manage and novo_admin_pass_manage:
                    if novo_admin_user_manage in admins_df_manage["Usuario"].values:
                        st.error(f"Usuário '{novo_admin_user_manage}' já existe.")
                    else:
                        novo_admin_data_manage = pd.DataFrame([[novo_admin_user_manage, novo_admin_pass_manage]], columns=["Usuario", "Senha"])
                        admins_df_manage = pd.concat([admins_df_manage, novo_admin_data_manage], ignore_index=True)
                        admins_df_manage.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                        st.success(f"Admin '{novo_admin_user_manage}' adicionado!"); st.rerun()
                else: st.warning("Preencha todos os campos.")
            st.markdown("---"); st.subheader("🗑️ Remover Admin")
            if not admins_df_manage.empty:
                admin_para_remover_manage = st.selectbox("Remover Admin:", options=[""] + admins_df_manage["Usuario"].tolist(), key="remove_admin_select_manage_v3")
                if st.button("Remover Admin Selecionado", type="primary", key="btn_remove_admin_v3") and admin_para_remover_manage:
                    if len(admins_df_manage) == 1 and admin_para_remover_manage == admins_df_manage["Usuario"].iloc[0]:
                        st.error("Não é possível remover o único administrador.")
                    else:
                        admins_df_manage = admins_df_manage[admins_df_manage["Usuario"] != admin_para_remover_manage]
                        admins_df_manage.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                        st.warning(f"Admin '{admin_para_remover_manage}' removido."); st.rerun()
            else: st.info("Nenhum administrador para remover.")

    except Exception as e_admin_area_v3:
        st.error(f"Ocorreu um erro crítico na área administrativa: {e_admin_area_v3}")
        st.exception(e_admin_area_v3)

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.") # Should not be reached if radio is used.
    st.stop()