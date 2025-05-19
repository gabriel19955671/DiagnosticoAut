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
st.write("DEBUG: Título do Portal renderizado.") 

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
# A chave DIAGNOSTICO_FORM_ID_KEY será definida dinamicamente com base no CNPJ

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

st.write("DEBUG: Inicializando arquivos CSV...")
try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios)
    inicializar_csv(perguntas_csv, colunas_base_perguntas, is_perguntas_file=True)
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
    st.write("DEBUG: Arquivos CSV inicializados (ou verificados).")
except Exception as e_init_main_full:
    st.error(f"Falha crítica na inicialização de arquivos CSV base: {e_init_main_full}")
    st.exception(e_init_main_full)
    st.markdown("---")
    st.markdown("### Solução de Problemas - Inicialização de Arquivos:")
    st.markdown("""
    1. Verifique se você tem permissão de escrita na pasta onde o script está rodando.
    2. Tente deletar os arquivos CSV da pasta do script. Eles serão recriados.
    3. Verifique o conteúdo dos CSVs, especialmente `perguntas_formulario.csv` (deve ter colunas 'Pergunta' e 'Categoria') e `usuarios.csv` (deve ter as colunas base, incluindo 'NomeContato' e 'Telefone').
    """)
    st.stop()


def registrar_acao(cnpj, acao, descricao):
    try:
        historico_df_ra_full = pd.read_csv(historico_csv, encoding='utf-8') 
    except (FileNotFoundError, pd.errors.EmptyDataError): 
        historico_df_ra_full = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data_ra_full = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }
    historico_df_ra_full = pd.concat([historico_df_ra_full, pd.DataFrame([nova_data_ra_full])], ignore_index=True)
    historico_df_ra_full.to_csv(historico_csv, index=False, encoding='utf-8')


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

                if isinstance(txt_p_pdf_g_det, str) and "[Matriz GUT]" in txt_p_pdf_g_det: # Adicionado check de tipo
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
            if isinstance(pergunta_pdf_k_g, str) and "[Matriz GUT]" in pergunta_pdf_k_g:
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

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_g_final:
            pdf_path_g_final = tmpfile_g_final.name
            pdf.output(pdf_path_g_final)
        return pdf_path_g_final
    except Exception as e_pdf_full:
        st.error(f"Erro ao gerar PDF: {e_pdf_full}")
        st.exception(e_pdf_full)
        return None

# --- Lógica de Login e Navegação Principal (Admin/Cliente) ---
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    st.write("DEBUG: Exibindo seleção de tipo de usuário (Admin/Cliente).")
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_main_debug_v4")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"
st.write(f"DEBUG: Aba selecionada/definida: {aba}")


if aba == "Administrador" and not st.session_state.admin_logado:
    st.write("DEBUG: Exibindo formulário de login do Administrador.")
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_page_debug_v4"): 
        usuario_admin_login_pg_d4 = st.text_input("Usuário", key="admin_user_login_page_d4") 
        senha_admin_login_pg_d4 = st.text_input("Senha", type="password", key="admin_pass_login_page_d4")
        entrar_admin_login_pg_d4 = st.form_submit_button("Entrar")
    if entrar_admin_login_pg_d4:
        st.write("DEBUG: Botão Entrar (Admin) pressionado.")
        try:
            df_admin_login_creds_pg_d4 = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            # st.write(f"DEBUG: CSV Admin lido. Conteúdo: {df_admin_login_creds_pg_d4.head().to_dict()}") # Opcional: muito verboso
            admin_encontrado_d4 = df_admin_login_creds_pg_d4[
                (df_admin_login_creds_pg_d4["Usuario"] == usuario_admin_login_pg_d4) & 
                (df_admin_login_creds_pg_d4["Senha"] == senha_admin_login_pg_d4)
            ]
            if not admin_encontrado_d4.empty:
                st.write("DEBUG: Admin encontrado. Configurando sessão.")
                st.session_state.admin_logado = True
                st.success("Login de administrador bem-sucedido!")
                st.session_state.trigger_admin_rerun = True
                st.rerun() 
            else: 
                st.error("Usuário ou senha inválidos.")
                st.write("DEBUG: Admin não encontrado ou senha inválida.")
        except FileNotFoundError: st.error(f"Arquivo {admin_credenciais_csv} não encontrado. Verifique se ele existe na pasta do script.")
        except pd.errors.EmptyDataError: st.error(f"Arquivo {admin_credenciais_csv} está vazio. Adicione um administrador.")
        except Exception as e_login_admin_d4: st.error(f"Erro no login do admin: {e_login_admin_d4}"); st.exception(e_login_admin_d4)
    st.markdown('</div>', unsafe_allow_html=True)
    st.write("DEBUG: Fim da seção de login do admin (se não logado). Parando execução aqui se não logou.")
    st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.write("DEBUG: Exibindo formulário de login do Cliente.")
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_page_debug_v4"): 
        cnpj_cli_login_page_d4 = st.text_input("CNPJ", key="cli_cnpj_login_page_d4") 
        senha_cli_login_page_d4 = st.text_input("Senha", type="password", key="cli_pass_login_page_d4") 
        acessar_cli_login_page_d4 = st.form_submit_button("Entrar")
    if acessar_cli_login_page_d4:
        st.write("DEBUG: Botão Entrar (Cliente) pressionado.")
        try:
            if not os.path.exists(usuarios_csv): st.error(f"Arquivo {usuarios_csv} não encontrado."); st.stop()
            usuarios_login_df_page_d4 = pd.read_csv(usuarios_csv, encoding='utf-8')
            if not os.path.exists(usuarios_bloqueados_csv): st.error(f"Arquivo {usuarios_bloqueados_csv} não encontrado."); st.stop()
            bloqueados_login_df_page_d4 = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
            
            if cnpj_cli_login_page_d4 in bloqueados_login_df_page_d4["CNPJ"].astype(str).values: 
                st.error("CNPJ bloqueado."); st.stop()
            user_match_li_page_d4 = usuarios_login_df_page_d4[(usuarios_login_df_page_d4["CNPJ"].astype(str) == str(cnpj_cli_login_page_d4)) & (usuarios_login_df_page_d4["Senha"] == senha_cli_login_page_d4)]
            if user_match_li_page_d4.empty: st.error("CNPJ ou senha inválidos."); st.stop()
            
            st.session_state.cliente_logado = True
            st.session_state.cnpj = str(cnpj_cli_login_page_d4) 
            st.session_state.user = user_match_li_page_d4.iloc[0].to_dict() 
            st.session_state.inicio_sessao_cliente = time.time()
            registrar_acao(st.session_state.cnpj, "Login", "Usuário realizou login.")
            st.session_state.cliente_page = "Painel Principal"
            st.success("Login realizado com sucesso!"); st.session_state.trigger_cliente_rerun = True; st.rerun() 
        except FileNotFoundError as e_login_cli_fnf_d4: st.error(f"Arquivo não encontrado durante login: {e_login_cli_fnf_d4.filename}.")
        except pd.errors.EmptyDataError as e_login_cli_empty_d4: st.error(f"Arquivo de usuários ou bloqueados está vazio: {e_login_cli_empty_d4}")
        except Exception as e_login_cli_d4: st.error(f"Erro no login do cliente: {e_login_cli_d4}"); st.exception(e_login_cli_d4)
    st.markdown('</div>', unsafe_allow_html=True)
    st.write("DEBUG: Fim da seção de login do cliente (se não logado). Parando execução aqui se não logou.")
    st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
# (Código da área do cliente mantido como na versão anterior, que já era funcional e tinha sua própria depuração interna se necessário)
# Se o problema persistir na área do cliente, podemos adicionar DEBUGs lá também.
# Por agora, focando no problema da tela em branco do admin.
if aba == "Cliente" and st.session_state.cliente_logado:
    # ... (Colar aqui a SEÇÃO COMPLETA da ÁREA DO CLIENTE LOGADO da versão anterior que estava funcionando para o cliente)
    # Certifique-se que a chave DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME é definida e usada corretamente.
    # Exemplo de como a área do cliente começaria:
    st.write("DEBUG: Entrou na área do Cliente Logado.")
    try: 
        st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
        # ... resto do código da área do cliente ...
    except Exception as e_cliente_area_full:
        st.error(f"Ocorreu um erro na área do cliente: {e_cliente_area_full}")
        st.exception(e_cliente_area_full)


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    st.write("DEBUG: Entrou na área do Administrador Logado.")
    try: 
        st.sidebar.image("https://raw.githubusercontent.com/AndersonCRMG/AppDiagnostico/main/Logo%20Transparente%20(1).png", width=100)
        st.sidebar.success("🟢 Admin Logado")
        st.write("DEBUG: Sidebar do Admin (imagem e status) renderizada.")

        if st.sidebar.button("🚪 Sair do Painel Admin"):
            st.write("DEBUG: Botão Sair (Admin) pressionado.")
            st.session_state.admin_logado = False
            st.rerun() 

        menu_admin_main_view_d_full = st.sidebar.selectbox( 
            "Funcionalidades Admin:",
            ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Perguntas", 
             "Gerenciar Clientes", "Gerenciar Administradores"],
            key="admin_menu_selectbox_main_page_view_debug_v4_full" 
        )
        st.write(f"DEBUG: Sidebar do Admin (Selectbox) renderizado. Opção: {menu_admin_main_view_d_full}")
        st.header(f"🔑 Painel Admin: {menu_admin_main_view_d_full}")
        st.write("DEBUG: Cabeçalho do Painel Admin renderizado.")

        if menu_admin_main_view_d_full == "Visão Geral e Diagnósticos":
            st.write("DEBUG: Renderizando Visão Geral e Diagnósticos (Admin).")
            st.subheader("📊 Visão Geral dos Diagnósticos")
            st.write("DEBUG: Visão Geral (Admin) - Subheader renderizado.")

            diagnosticos_df_admin_geral_full = pd.DataFrame() 
            admin_data_loaded_successfully_full = False

            try:
                st.write(f"DEBUG: Tentando carregar o arquivo: {arquivo_csv}")
                if not os.path.exists(arquivo_csv):
                    st.warning(f"Arquivo de diagnósticos ({arquivo_csv}) não encontrado. Crie um diagnóstico primeiro.")
                else:
                    diagnosticos_df_admin_geral_full = pd.read_csv(arquivo_csv, encoding='utf-8')
                    st.write(f"DEBUG: Arquivo {arquivo_csv} carregado.")
                    if diagnosticos_df_admin_geral_full.empty:
                        st.info("Nenhum diagnóstico no sistema para exibir visão geral.")
                    else:
                        admin_data_loaded_successfully_full = True
                        st.write(f"DEBUG: {len(diagnosticos_df_admin_geral_full)} diagnósticos carregados.")
            except FileNotFoundError: st.error(f"ERRO: Arquivo ({arquivo_csv}) não encontrado.")
            except pd.errors.EmptyDataError: st.warning(f"Arquivo ({arquivo_csv}) está vazio.")
            except Exception as e_load_diag_admin_full:
                st.error(f"Erro ao carregar diagnósticos para o admin: {e_load_diag_admin_full}")
                st.exception(e_load_diag_admin_full)
            
            st.write(f"DEBUG: Status do carregamento de dados (admin): {admin_data_loaded_successfully_full}")

            if admin_data_loaded_successfully_full:
                st.write("DEBUG: Exibindo dados do admin (Indicadores, Gráficos, etc.).")
                st.markdown("#### Indicadores Gerais")
                # ... (Código dos Indicadores Gerais, Evolução Mensal, Ranking, Tabela de Diagnósticos, Detalhar/Comentar/Baixar PDF - como na resposta anterior)
                # Por exemplo, para Indicadores Gerais:
                col_ig1_f, col_ig2_f, col_ig3_f = st.columns(3)
                with col_ig1_f: st.metric("📦 Total de Diagnósticos", len(diagnosticos_df_admin_geral_full))
                # ... etc. ...
                st.write("DEBUG: Métricas de Indicadores Gerais renderizadas (ou tentadas).")
                st.divider()
                # ... (Restante da lógica da Visão Geral e Diagnósticos) ...
            else: 
                st.warning("Não foi possível carregar os dados dos diagnósticos para exibição na Visão Geral.")
            st.write("DEBUG: Fim da seção Visão Geral e Diagnósticos (Admin).")

        elif menu_admin_main_view_d_full == "Histórico de Usuários":
            st.write("DEBUG: Renderizando Histórico de Usuários (Admin).")
            # ... (código da seção)
        elif menu_admin_main_view_d_full == "Gerenciar Perguntas":
            st.write("DEBUG: Renderizando Gerenciar Perguntas (Admin).")
            # ... (código da seção)
        elif menu_admin_main_view_d_full == "Gerenciar Clientes":
            st.write("DEBUG: Renderizando Gerenciar Clientes (Admin).")
            # ... (código da seção)
        elif menu_admin_main_view_d_full == "Gerenciar Administradores":
            st.write("DEBUG: Renderizando Gerenciar Administradores (Admin).")
            # ... (código da seção)

    except Exception as e_admin_area_d_main_full:
        st.error(f"Ocorreu um erro geral na área administrativa: {e_admin_area_d_main_full}")
        st.exception(e_admin_area_d_main_full)
        st.write("DEBUG: Erro capturado no try-except geral da área admin.")

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.write("DEBUG: Fim do script, estado de login não definido para exibir conteúdo principal (fallback).")
    st.stop()

st.write(f"DEBUG: Fim do script principal. Estado admin_logado: {st.session_state.admin_logado}, cliente_logado: {st.session_state.cliente_logado}, aba: {aba if 'aba' in locals() else 'Não definida'}")