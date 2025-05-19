import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
from fpdf import FPDF
import tempfile
import re # Para sanitizar nomes de colunas
import json # Para armazenar respostas GUT estruturadas

st.set_page_config(page_title="Portal de Diagnóstico", layout="centered")

# CSS (sem alterações)
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
</style>
""", unsafe_allow_html=True)

st.title("🔒 Portal de Acesso")

admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv" 
historico_csv = "historico_clientes.csv"

# Initialize session state variables
if "admin_logado" not in st.session_state: st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state: st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state: st.session_state.diagnostico_enviado = False
if "inicio_sessao_cliente" not in st.session_state: st.session_state.inicio_sessao_cliente = None
if "cliente_page" not in st.session_state: st.session_state.cliente_page = "Painel Principal"
if "cnpj" not in st.session_state: st.session_state.cnpj = None
if "user" not in st.session_state: st.session_state.user = None
# Chave para estabilizar widgets do formulário de diagnóstico
DIAGNOSTICO_FORM_ID_KEY = f"form_id_diagnostico_cliente_{st.session_state.get('cnpj', 'default_user')}"


# Função para sanitizar nomes de categoria para nomes de colunas
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s) 
    return s

# Criar arquivos base caso não existam
colunas_base_diagnosticos = [
    "Data", "CNPJ", "Nome", "Email", "Empresa",
    "Média Geral", "GUT Média", "Observações", "Diagnóstico", 
    "Análise do Cliente", "Comentarios_Admin"
]
for arquivo, colunas_base in [
    (usuarios_bloqueados_csv, ["CNPJ"]),
    (admin_credenciais_csv, ["Usuario", "Senha"]),
    (usuarios_csv, ["CNPJ", "Senha", "Empresa"]),
    (perguntas_csv, ["Pergunta", "Categoria"]), 
    (historico_csv, ["Data", "CNPJ", "Ação", "Descrição"]),
    (arquivo_csv, colunas_base_diagnosticos) 
]:
    if not os.path.exists(arquivo):
        pd.DataFrame(columns=colunas_base).to_csv(arquivo, index=False, encoding='utf-8')
    else: 
        if arquivo == arquivo_csv: 
            try:
                df_temp = pd.read_csv(arquivo, encoding='utf-8')
                missing_cols = False
                for col_base_check in colunas_base_diagnosticos: # Renomeado para evitar conflito
                    if col_base_check not in df_temp.columns:
                        df_temp[col_base_check] = pd.NA 
                        missing_cols = True
                if missing_cols:
                    df_temp.to_csv(arquivo, index=False, encoding='utf-8')
            except pd.errors.EmptyDataError:
                 pd.DataFrame(columns=colunas_base).to_csv(arquivo, index=False, encoding='utf-8') # usa colunas_base_diagnosticos se vazio
            except Exception as e: st.error(f"Erro ao verificar colunas de {arquivo}: {e}")
        elif arquivo == perguntas_csv: 
            try:
                df_temp = pd.read_csv(arquivo, encoding='utf-8')
                if "Categoria" not in df_temp.columns:
                    df_temp["Categoria"] = "Geral" 
                    df_temp.to_csv(arquivo, index=False, encoding='utf-8')
            except pd.errors.EmptyDataError:
                 pd.DataFrame(columns=colunas_base).to_csv(arquivo, index=False, encoding='utf-8') # usa ["Pergunta", "Categoria"] se vazio
            except Exception as e: st.error(f"Erro ao verificar colunas de {arquivo}: {e}")


def registrar_acao(cnpj, acao, descricao):
    # ... (código mantido)
    try:
        historico = pd.read_csv(historico_csv, encoding='utf-8')
    except FileNotFoundError: historico = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }
    historico = pd.concat([historico, pd.DataFrame([nova_data])], ignore_index=True)
    historico.to_csv(historico_csv, index=False, encoding='utf-8')

if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True)
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    # ... (código login admin mantido)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin"):
        usuario_admin_login = st.text_input("Usuário") 
        senha_admin_login_val = st.text_input("Senha", type="password")
        entrar_admin = st.form_submit_button("Entrar")
    if entrar_admin:
        df_admin_login = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
        if not df_admin_login[(df_admin_login["Usuario"] == usuario_admin_login) & (df_admin_login["Senha"] == senha_admin_login_val)].empty:
            st.session_state.admin_logado = True; st.success("Login de administrador bem-sucedido!")
            st.session_state.trigger_admin_rerun = True; st.rerun() 
        else: st.error("Usuário ou senha inválidos.")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    # ... (código login cliente mantido)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente"):
        cnpj_cli_login = st.text_input("CNPJ") 
        senha_cli_login_val = st.text_input("Senha", type="password") 
        acessar_cli = st.form_submit_button("Entrar")
    if acessar_cli:
        if not os.path.exists(usuarios_csv): st.error("Base de usuários não encontrada."); st.stop()
        usuarios_login_df = pd.read_csv(usuarios_csv, encoding='utf-8')
        bloqueados_login_df = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
        if cnpj_cli_login in bloqueados_login_df["CNPJ"].astype(str).values: 
            st.error("CNPJ bloqueado. Contate o administrador."); st.stop()
        user_match_cli = usuarios_login_df[(usuarios_login_df["CNPJ"].astype(str) == str(cnpj_cli_login)) & (usuarios_login_df["Senha"] == senha_cli_login_val)]
        if user_match_cli.empty: st.error("CNPJ ou senha inválidos."); st.stop()
        st.session_state.cliente_logado = True
        st.session_state.cnpj = str(cnpj_cli_login) 
        st.session_state.user = user_match_cli.iloc[0].to_dict() 
        st.session_state.inicio_sessao_cliente = time.time()
        registrar_acao(st.session_state.cnpj, "Login", "Usuário realizou login.")
        st.session_state.cliente_page = "Painel Principal"
        st.success("Login realizado com sucesso!"); st.session_state.trigger_cliente_rerun = True; st.rerun() 
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 

# --- CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    st.session_state.cliente_page = st.sidebar.radio(
        "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
        index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page)
    )
    if st.sidebar.button("⬅️ Sair do Portal Cliente"):
        keys_to_delete_cli = ['cliente_logado', 'cnpj', 'user', 'inicio_sessao_cliente', 
                              'diagnostico_enviado', 'cliente_page', DIAGNOSTICO_FORM_ID_KEY] # Limpar form_id também
        for key_cd in keys_to_delete_cli:
            if key_cd in st.session_state: del st.session_state[key_cd]
        st.rerun()

    if st.session_state.cliente_page == "Painel Principal":
        # ... (código do Painel Principal, Histórico, Kanban, Comparações - com ajustes para nova GUT)
        st.subheader("📌 Instruções Gerais")
        with st.expander("📖 Leia atentamente"): # Título simplificado
            st.markdown("- Responda com sinceridade.\n- Utilize a escala corretamente.\n- Análises e planos de ação são baseados em suas respostas.\n- Para novo diagnóstico, selecione no menu ao lado.")
        if st.session_state.get("diagnostico_enviado", False):
            st.success("🎯 Último diagnóstico enviado com sucesso!"); st.session_state.diagnostico_enviado = False
        st.subheader("📁 Diagnósticos Anteriores")
        try:
            df_antigos_cli_hist = pd.read_csv(arquivo_csv, encoding='utf-8')
            df_cliente_view = df_antigos_cli_hist[df_antigos_cli_hist["CNPJ"].astype(str) == st.session_state.cnpj]
        except FileNotFoundError: df_cliente_view = pd.DataFrame()
        if df_cliente_view.empty: st.info("Nenhum diagnóstico anterior. Comece um novo no menu ao lado.")
        else:
            df_cliente_view = df_cliente_view.sort_values(by="Data", ascending=False)
            for idx_cv, row_cv in df_cliente_view.iterrows():
                with st.expander(f"📅 {row_cv['Data']} - {row_cv['Empresa']}"):
                    st.write(f"**Média Geral:** {row_cv.get('Média Geral', 'N/A')}") 
                    st.write(f"**GUT Média (G*U*T):** {row_cv.get('GUT Média', 'N/A')}") # Agora é média de G*U*T
                    st.write(f"**Resumo (Cliente):** {row_cv.get('Diagnóstico', 'N/P')}")
                    st.markdown("**Médias por Categoria:**") # ... (código para exibir médias de categoria)
                    # ... (restante da visualização do histórico e análise do cliente mantido)
                    # Exibir Médias por Categoria se existirem
                    found_cat_media_cv = False
                    for col_name_cv in row_cv.index:
                        if col_name_cv.startswith("Media_Cat_"):
                            cat_name_display_cv = col_name_cv.replace("Media_Cat_", "").replace("_", " ")
                            st.write(f"  - {cat_name_display_cv}: {row_cv.get(col_name_cv, 'N/A')}")
                            found_cat_media_cv = True
                    if not found_cat_media_cv: st.caption("  Nenhuma média por categoria.")

                    analise_cli_val_cv = row_cv.get("Análise do Cliente", "")
                    analise_cli_cv = st.text_area("🧠 Minha Análise:", value=analise_cli_val_cv, key=f"analise_cv_{row_cv.name}")
                    if st.button("💾 Salvar Análise", key=f"salvar_analise_cv_{row_cv.name}"):
                        df_antigos_upd_cv = pd.read_csv(arquivo_csv, encoding='utf-8') 
                        df_antigos_upd_cv.loc[df_antigos_upd_cv.index == row_cv.name, "Análise do Cliente"] = analise_cli_cv
                        df_antigos_upd_cv.to_csv(arquivo_csv, index=False, encoding='utf-8')
                        registrar_acao(st.session_state.cnpj, "Análise Cliente", f"Editou análise de {row_cv['Data']}")
                        st.success("Análise salva!"); st.rerun()
                    
                    com_admin_val_cv = row_cv.get("Comentarios_Admin", "")
                    if com_admin_val_cv and not pd.isna(com_admin_val_cv):
                        st.markdown("**Comentários do Consultor:**"); st.info(f"{com_admin_val_cv}")
                    else: st.caption("Nenhum comentário do consultor.")
                    st.markdown("---")


            st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
            gut_cards_painel = []
            if not df_cliente_view.empty:
                latest_diag_row_painel = df_cliente_view.iloc[0]
                for pergunta_p, resposta_p_val_str in latest_diag_row_painel.items():
                    if isinstance(pergunta_p, str) and "[Matriz GUT]" in pergunta_p:
                        try:
                            if pd.notna(resposta_p_val_str) and isinstance(resposta_p_val_str, str):
                                gut_data = json.loads(resposta_p_val_str.replace("'", "\"")) # Lida com aspas simples
                                g = int(gut_data.get("G", 0))
                                u = int(gut_data.get("U", 0))
                                t = int(gut_data.get("T", 0))
                                score_gut_total_p = g * u * t
                                
                                prazo_p = "N/A"
                                if score_gut_total_p >= 75: prazo_p = "15 dias" # Ex: 5x5x3
                                elif score_gut_total_p >= 40: prazo_p = "30 dias" # Ex: 4x4x2.5 (arredondar para cima) -> 5x3x3 = 45
                                elif score_gut_total_p >= 20: prazo_p = "45 dias" # Ex: 3x3x2.2 -> 3x3x3 = 27
                                elif score_gut_total_p > 0: prazo_p = "60 dias"
                                else: continue # Não adiciona se score for 0

                                if prazo_p != "N/A":
                                    gut_cards_painel.append({
                                        "Tarefa": pergunta_p.replace(" [Matriz GUT]", ""), 
                                        "Prazo": prazo_p, "Score": score_gut_total_p, 
                                        "Responsável": st.session_state.user.get("Empresa", "N/D")
                                    })
                        except (json.JSONDecodeError, ValueError, TypeError) as e:
                            st.warning(f"Erro ao processar GUT para Kanban: '{pergunta_p}' ({resposta_p_val_str}). Detalhe: {e}")
                            continue
            
            if gut_cards_painel: # ... (código do Kanban como antes, usando gut_cards_painel)
                gut_cards_sorted_p = sorted(gut_cards_painel, key=lambda x_p_k: x_p_k["Score"], reverse=True)
                prazos_def_p = sorted(list(set(card_p["Prazo"] for card_p in gut_cards_sorted_p)), key=lambda x_p_d: int(x_p_d.split(" ")[0])) 
                if prazos_def_p:
                    cols_kanban_p = st.columns(len(prazos_def_p))
                    for idx_kp, prazo_col_kp in enumerate(prazos_def_p):
                        with cols_kanban_p[idx_kp]:
                            st.markdown(f"#### ⏱️ {prazo_col_kp}")
                            for card_item_kp in gut_cards_sorted_p:
                                if card_item_kp["Prazo"] == prazo_col_kp:
                                    st.markdown(f"""<div style="border:1px solid #e0e0e0;border-left:5px solid #2563eb;padding:10px;margin-bottom:10px;border-radius:5px;"><small><b>{card_item_kp['Tarefa']}</b> (Score GUT: {card_item_kp['Score']})</small><br><small><i>👤 {card_item_kp['Responsável']}</i></small></div>""", unsafe_allow_html=True)
            else: st.info("Nenhuma ação prioritária para o Kanban (GUT).")
            
            # Comparativo de Evolução e Comparação entre Diagnósticos (sem alterações na lógica interna, já pegava GUT Média do CSV)
            # ... (código mantido) ...
            st.subheader("📈 Comparativo de Evolução")
            if len(df_cliente_view) > 1:
                grafico_comp_ev = df_cliente_view.sort_values(by="Data")
                grafico_comp_ev["Data"] = pd.to_datetime(grafico_comp_ev["Data"])
                # ... (lógica de plotagem incluindo Media_Cat_ e GUT Média) ...
                colunas_plot_comp = ['Média Geral', 'GUT Média'] # GUT Média agora é média de G*U*T
                for col_g_comp in grafico_comp_ev.columns:
                    if col_g_comp.startswith("Media_Cat_") and pd.api.types.is_numeric_dtype(grafico_comp_ev[col_g_comp]):
                        colunas_plot_comp.append(col_g_comp)
                for col_plot_c in colunas_plot_comp:
                    if col_plot_c in grafico_comp_ev.columns: grafico_comp_ev[col_plot_c] = pd.to_numeric(grafico_comp_ev[col_plot_c], errors='coerce')
                    # else: if col_plot_c in colunas_plot_comp: colunas_plot_comp.remove(col_plot_c) # Não remover, apenas ignorar no plot se não for numérico
                
                colunas_validas_plot = [c for c in colunas_plot_comp if c in grafico_comp_ev.columns and pd.api.types.is_numeric_dtype(grafico_comp_ev[c])]

                if colunas_validas_plot:
                    st.line_chart(grafico_comp_ev.set_index("Data")[colunas_validas_plot].dropna(axis=1, how='all'))
                
                st.subheader("📊 Comparação Entre Diagnósticos") # ... (lógica mantida) ...
            else: st.info("Pelo menos dois diagnósticos para comparativos.")


    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader("📋 Formulário de Novo Diagnóstico")
        
        # Gerar/Recuperar form_id estável para esta sessão de preenchimento
        if DIAGNOSTICO_FORM_ID_KEY not in st.session_state:
            st.session_state[DIAGNOSTICO_FORM_ID_KEY] = datetime.now().strftime("%Y%m%d%H%M%S%f")
        form_id_sufixo = st.session_state[DIAGNOSTICO_FORM_ID_KEY]

        try:
            perguntas_df_diag = pd.read_csv(perguntas_csv, encoding='utf-8')
            if "Categoria" not in perguntas_df_diag.columns: 
                perguntas_df_diag["Categoria"] = "Geral"
        except FileNotFoundError: st.error("Arquivo de perguntas não encontrado."); st.stop()
        if perguntas_df_diag.empty: st.warning("Nenhuma pergunta cadastrada."); st.stop()

        # Usar um dicionário no session_state para armazenar respostas temporariamente
        temp_respostas_key = f"temp_respostas_{form_id_sufixo}"
        if temp_respostas_key not in st.session_state:
            st.session_state[temp_respostas_key] = {}
        
        respostas_form_coletadas = st.session_state[temp_respostas_key] # Referência direta
        total_perguntas_diag = len(perguntas_df_diag)
        respondidas_count_diag = 0 
        
        categorias_unicas_diag = perguntas_df_diag["Categoria"].unique()
        
        with st.form(key=f"diagnostico_form_completo_{form_id_sufixo}"): # Envolver todo o formulário em st.form
            for categoria_diag in categorias_unicas_diag:
                st.markdown(f"#### Categoria: {categoria_diag}")
                perguntas_cat_diag = perguntas_df_diag[perguntas_df_diag["Categoria"] == categoria_diag]
                for idx_diag_f, row_diag_f in perguntas_cat_diag.iterrows():
                    texto_pergunta_diag = str(row_diag_f["Pergunta"]) 
                    # Chave do widget deve ser estável e única para a pergunta, não para a categoria ou data
                    widget_base_key = f"q_form_{idx_diag_f}" # Usa índice original da pergunta

                    if "[Matriz GUT]" in texto_pergunta_diag:
                        st.markdown(f"**{texto_pergunta_diag.replace(' [Matriz GUT]', '')}**")
                        cols_gut = st.columns(3)
                        gut_vals = respostas_form_coletadas.get(texto_pergunta_diag, {"G":0, "U":0, "T":0}) # Pega valor anterior ou default
                        with cols_gut[0]:
                            g_val = st.slider("Gravidade (0-5)", 0, 5, value=gut_vals.get("G",0), key=f"{widget_base_key}_G")
                        with cols_gut[1]:
                            u_val = st.slider("Urgência (0-5)", 0, 5, value=gut_vals.get("U",0), key=f"{widget_base_key}_U")
                        with cols_gut[2]:
                            t_val = st.slider("Tendência (0-5)", 0, 5, value=gut_vals.get("T",0), key=f"{widget_base_key}_T")
                        respostas_form_coletadas[texto_pergunta_diag] = {"G": g_val, "U": u_val, "T": t_val}
                        if g_val > 0 or u_val > 0 or t_val > 0 : respondidas_count_diag +=1 # Considera respondida se algum GUT for > 0

                    elif "Pontuação (0-5)" in texto_pergunta_diag: # Antes de Pontuação (0-10) para especificidade
                        val = respostas_form_coletadas.get(texto_pergunta_diag, 0)
                        respostas_form_coletadas[texto_pergunta_diag] = st.slider(texto_pergunta_diag, 0, 5, value=val, key=widget_base_key) 
                        if respostas_form_coletadas[texto_pergunta_diag] != 0: respondidas_count_diag += 1
                    elif "Pontuação (0-10)" in texto_pergunta_diag:
                        val = respostas_form_coletadas.get(texto_pergunta_diag, 0)
                        respostas_form_coletadas[texto_pergunta_diag] = st.slider(texto_pergunta_diag, 0, 10, value=val, key=widget_base_key)
                        if respostas_form_coletadas[texto_pergunta_diag] != 0: respondidas_count_diag += 1
                    elif "Texto Aberto" in texto_pergunta_diag:
                        val = respostas_form_coletadas.get(texto_pergunta_diag, "")
                        respostas_form_coletadas[texto_pergunta_diag] = st.text_area(texto_pergunta_diag, value=val, key=widget_base_key)
                        if respostas_form_coletadas[texto_pergunta_diag].strip() != "": respondidas_count_diag += 1
                    elif "Escala" in texto_pergunta_diag: 
                        opcoes_escala_diag = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"] 
                        val = respostas_form_coletadas.get(texto_pergunta_diag, "Selecione")
                        idx_sel = opcoes_escala_diag.index(val) if val in opcoes_escala_diag else 0
                        respostas_form_coletadas[texto_pergunta_diag] = st.selectbox(texto_pergunta_diag, opcoes_escala_diag, index=idx_sel, key=widget_base_key)
                        if respostas_form_coletadas[texto_pergunta_diag] != "Selecione": respondidas_count_diag += 1
                    else: 
                        val = respostas_form_coletadas.get(texto_pergunta_diag, 0)
                        respostas_form_coletadas[texto_pergunta_diag] = st.slider(texto_pergunta_diag, 0, 10, value=val, key=widget_base_key)
                        if respostas_form_coletadas[texto_pergunta_diag] != 0: respondidas_count_diag += 1
                st.divider()
            
            progresso_diag = round((respondidas_count_diag / total_perguntas_diag) * 100) if total_perguntas_diag > 0 else 0
            st.info(f"📊 Progresso: {respondidas_count_diag} de {total_perguntas_diag} respondidas ({progresso_diag}%)")
            
            observacoes_cli_diag_form = st.text_area("Sua Análise/Observações (opcional):", value=respostas_form_coletadas.get("__obs_cliente__", ""), key=f"obs_cli_diag_{form_id_sufixo}")
            respostas_form_coletadas["__obs_cliente__"] = observacoes_cli_diag_form # Salva no dict temporário
            
            diagnostico_resumo_cli_diag = st.text_area("✍️ Resumo/principais insights (para PDF):", value=respostas_form_coletadas.get("__resumo_cliente__", ""), key=f"diag_resumo_diag_{form_id_sufixo}")
            respostas_form_coletadas["__resumo_cliente__"] = diagnostico_resumo_cli_diag # Salva no dict temporário

            enviar_diagnostico_btn = st.form_submit_button("✔️ Enviar Diagnóstico")

        if enviar_diagnostico_btn:
            if respondidas_count_diag < total_perguntas_diag: st.warning("Responda todas as perguntas.")
            elif not respostas_form_coletadas["__resumo_cliente__"].strip(): st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
            else:
                # Processar e salvar
                soma_total_gut_scores = 0
                count_gut_perguntas = 0
                
                # Processar respostas finais (ex: converter GUT para string JSON)
                respostas_finais_para_salvar = {}
                for pergunta_env, resposta_env in respostas_form_coletadas.items():
                    if pergunta_env.startswith("__"): continue # Ignora chaves internas
                    if "[Matriz GUT]" in pergunta_env and isinstance(resposta_env, dict):
                        respostas_finais_para_salvar[pergunta_env] = json.dumps(resposta_env) # Salva como string JSON
                        g, u, t = resposta_env.get("G",0), resposta_env.get("U",0), resposta_env.get("T",0)
                        soma_total_gut_scores += (g * u * t)
                        count_gut_perguntas +=1
                    else:
                        respostas_finais_para_salvar[pergunta_env] = resposta_env

                gut_media_final = round(soma_total_gut_scores / count_gut_perguntas, 2) if count_gut_perguntas > 0 else 0.0
                
                numeric_resp_final = [v for k, v in respostas_finais_para_salvar.items() if isinstance(v, (int, float)) and ("Pontuação (0-10)" in k or "Pontuação (0-5)" in k)] 
                media_geral_calc_final = round(sum(numeric_resp_final) / len(numeric_resp_final), 2) if numeric_resp_final else 0.0
                empresa_nome_final = st.session_state.user.get("Empresa", "N/D")
                
                nova_linha_final = {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": st.session_state.cnpj,
                    "Nome": st.session_state.user.get("CNPJ", ""), "Email": "", "Empresa": empresa_nome_final,
                    "Média Geral": media_geral_calc_final, "GUT Média": gut_media_final, # GUT Média agora é média de G*U*T
                    "Observações": "", 
                    "Análise do Cliente": respostas_form_coletadas.get("__obs_cliente__",""), 
                    "Diagnóstico": respostas_form_coletadas.get("__resumo_cliente__",""), 
                    "Comentarios_Admin": ""
                }
                nova_linha_final.update(respostas_finais_para_salvar) # Adiciona todas as respostas (GUT como JSON str)

                # Calcular e adicionar médias por categoria
                medias_por_categoria_final = {}
                for cat_final_calc in categorias_unicas_diag:
                    perguntas_cat_final_df = perguntas_df_diag[perguntas_df_diag["Categoria"] == cat_final_calc]
                    soma_cat_final, cont_num_cat_final = 0, 0
                    for _, p_row_final in perguntas_cat_final_df.iterrows():
                        txt_p_final = p_row_final["Pergunta"]
                        resp_p_final = respostas_form_coletadas.get(txt_p_final) # Pega do dict temporário
                        
                        # Não incluir GUT aqui, pois já tem sua própria média. Focar em sliders de pontuação simples.
                        if isinstance(resp_p_final, (int, float)) and \
                           ("[Matriz GUT]" not in txt_p_final) and \
                           ("Pontuação (0-10)" in txt_p_final or "Pontuação (0-5)" in txt_p_final):
                            soma_cat_final += resp_p_final
                            cont_num_cat_final += 1
                    media_c_final = round(soma_cat_final / cont_num_cat_final, 2) if cont_num_cat_final > 0 else 0.0
                    nome_col_media_cat_final = f"Media_Cat_{sanitize_column_name(cat_final_calc)}"
                    nova_linha_final[nome_col_media_cat_final] = media_c_final
                    medias_por_categoria_final[cat_final_calc] = media_c_final

                # Salvar no CSV
                try: df_diag_todos_final = pd.read_csv(arquivo_csv, encoding='utf-8')
                except FileNotFoundError: df_diag_todos_final = pd.DataFrame() 
                for col_f_save_final in nova_linha_final.keys(): 
                    if col_f_save_final not in df_diag_todos_final.columns: df_diag_todos_final[col_f_save_final] = pd.NA 
                df_diag_todos_final = pd.concat([df_diag_todos_final, pd.DataFrame([nova_linha_final])], ignore_index=True)
                df_diag_todos_final.to_csv(arquivo_csv, index=False, encoding='utf-8')
                
                st.success("Diagnóstico enviado com sucesso!")
                registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", "Cliente enviou novo diagnóstico.")
                
                # Limpar form_id e respostas temporárias
                if DIAGNOSTICO_FORM_ID_KEY in st.session_state: del st.session_state[DIAGNOSTICO_FORM_ID_KEY]
                if temp_respostas_key in st.session_state: del st.session_state[temp_respostas_key]


                # Gerar PDF (com nova estrutura GUT e categorias)
                pdf = FPDF()
                pdf.add_page()
                def pdf_safe_out(text): return str(text).encode('latin-1', 'replace').decode('latin-1')
                pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, pdf_safe_out(f"Diagnóstico - {empresa_nome_final}"), 0, 1, 'C'); pdf.ln(5)
                # ... (Cabeçalho do PDF: Data, Empresa, Média Geral, GUT Média - que agora é média de G*U*T)
                pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_out(f"Data: {nova_linha_final['Data']}"))
                pdf.multi_cell(0, 7, pdf_safe_out(f"Empresa: {empresa_nome_final} (CNPJ: {st.session_state.cnpj})")); pdf.ln(3)
                pdf.multi_cell(0, 7, pdf_safe_out(f"Média Geral (Numérica): {media_geral_calc_final}"))
                pdf.multi_cell(0, 7, pdf_safe_out(f"Média Scores GUT (G*U*T): {gut_media_final}")); pdf.ln(3)


                pdf.set_font("Arial", 'B', 11); pdf.multi_cell(0, 7, pdf_safe_out("Médias por Categoria (Perguntas de Pontuação):"))
                pdf.set_font("Arial", size=10)
                for cat_pdf_f, media_cat_pdf_f in medias_por_categoria_final.items():
                    pdf.multi_cell(0, 6, pdf_safe_out(f"  - {cat_pdf_f}: {media_cat_pdf_f}"))
                pdf.ln(5)

                pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_out("Resumo (Cliente):"))
                pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_out(respostas_form_coletadas.get("__resumo_cliente__",""))); pdf.ln(3)
                if respostas_form_coletadas.get("__obs_cliente__",""):
                    pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_out("Análise/Obs. Cliente:"))
                    pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_out(respostas_form_coletadas.get("__obs_cliente__",""))); pdf.ln(3)
                
                pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 10, pdf_safe_out("Respostas Detalhadas por Categoria:"))
                for categoria_pdf_final in categorias_unicas_diag:
                    pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_out(f"Categoria: {categoria_pdf_final}"))
                    pdf.set_font("Arial", size=9)
                    perguntas_cat_pdf_final = perguntas_df_diag[perguntas_df_diag["Categoria"] == categoria_pdf_final]
                    for _, p_row_pdf_final in perguntas_cat_pdf_final.iterrows():
                        txt_p_pdf_final = p_row_pdf_final["Pergunta"]
                        resp_p_pdf_final = respostas_form_coletadas.get(txt_p_pdf_final, "N/R")
                        if "[Matriz GUT]" in txt_p_pdf_final and isinstance(resp_p_pdf_final, dict):
                            g,u,t = resp_p_pdf_final.get("G",0), resp_p_pdf_final.get("U",0), resp_p_pdf_final.get("T",0)
                            score_gut_item = g*u*t
                            pdf.multi_cell(0,6,pdf_safe_out(f"  - {txt_p_pdf_final.replace(' [Matriz GUT]','')}: G={g}, U={u}, T={t} (Score: {score_gut_item})"))
                        elif isinstance(resp_p_pdf_final, (int, float, str)): 
                            pdf.multi_cell(0, 6, pdf_safe_out(f"  - {txt_p_pdf_final}: {resp_p_pdf_final}"))
                    pdf.ln(2)
                pdf.ln(3)
                
                # Kanban no PDF (com nova lógica GUT)
                pdf.add_page(); pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, pdf_safe_out("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf.ln(5)
                pdf.set_font("Arial", size=10)
                gut_cards_pdf_final = []
                for pergunta_pdf_k, resposta_pdf_k_val in respostas_form_coletadas.items(): # Usa respostas_form_coletadas
                    if "[Matriz GUT]" in pergunta_pdf_k and isinstance(resposta_pdf_k_val, dict):
                        g_k, u_k, t_k = resposta_pdf_k_val.get("G",0), resposta_pdf_k_val.get("U",0), resposta_pdf_k_val.get("T",0)
                        score_gut_total_k_pdf = g_k * u_k * t_k
                        prazo_k_pdf = "N/A"
                        if score_gut_total_k_pdf >= 75: prazo_k_pdf = "15 dias"
                        elif score_gut_total_k_pdf >= 40: prazo_k_pdf = "30 dias"
                        elif score_gut_total_k_pdf >= 20: prazo_k_pdf = "45 dias"
                        elif score_gut_total_k_pdf > 0: prazo_k_pdf = "60 dias"
                        else: continue
                        if prazo_k_pdf != "N/A":
                            gut_cards_pdf_final.append({"Tarefa": pergunta_pdf_k.replace(" [Matriz GUT]", ""),"Prazo": prazo_k_pdf, "Score": score_gut_total_k_pdf})
                if gut_cards_pdf_final:
                    gut_cards_pdf_final_sorted = sorted(gut_cards_pdf_final, key=lambda x_f_k_pdf: (int(x_f_k_pdf["Prazo"].split(" ")[0]), -x_f_k_pdf["Score"]))
                    for card_item_f_k_pdf in gut_cards_pdf_final_sorted:
                         pdf.multi_cell(0, 6, pdf_safe_out(f"Prazo: {card_item_f_k_pdf['Prazo']} - Tarefa: {card_item_f_k_pdf['Tarefa']} (Score GUT: {card_item_f_k_pdf['Score']})"))
                else: pdf.multi_cell(0,6, pdf_safe_out("Nenhuma ação prioritária (GUT > 0) identificada."))

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_final:
                    pdf_path_final = tmpfile_final.name
                    pdf.output(pdf_path_final)
                with open(pdf_path_final, "rb") as f_pdf_final:
                    st.download_button(label="📄 Baixar PDF do Diagnóstico", data=f_pdf_final, 
                                       file_name=f"diagnostico_{sanitize_column_name(empresa_nome_final)}_{datetime.now().strftime('%Y%m%d')}.pdf", 
                                       mime="application/pdf")
                registrar_acao(st.session_state.cnpj, "Download PDF", "Baixou PDF do novo diagnóstico.")
                
                st.session_state.diagnostico_enviado = True
                st.session_state.cliente_page = "Painel Principal" 
                st.rerun()

# --- PAINEL ADMINISTRATIVO ---
if aba == "Administrador" and st.session_state.admin_logado:
    # ... (Código do painel admin como antes, com a lógica de Categoria já integrada no Gerenciar Perguntas)
    # A visualização de diagnósticos pelo admin já deve mostrar as colunas Media_Cat_*
    # A funcionalidade de Comentários do Admin já está presente.
    st.sidebar.success("🟢 Admin Logado")
    if st.sidebar.button("🚪 Sair do Painel Admin"):
        st.session_state.admin_logado = False; st.rerun()

    menu_admin_sel_view = st.sidebar.selectbox( # Renomeado para evitar conflito de chave
        "Funcionalidades Admin:",
        ["Visualizar Diagnósticos", "Histórico de Usuários", "Gerenciar Perguntas", 
         "Gerenciar Clientes", "Gerenciar Administradores"],
        key="admin_menu_selectbox_main" # Chave única
    )
    st.header(f"🔑 Painel Admin: {menu_admin_sel_view}")

    if menu_admin_sel_view == "Gerenciar Perguntas":
        st.subheader("📝 Gerenciar Perguntas do Diagnóstico")
        # ... (Lógica de Gerenciar Perguntas como na versão anterior, já inclui Categoria)
        tabs_perg_admin_view = st.tabs(["📋 Perguntas Atuais", "➕ Adicionar Nova Pergunta"])
        with tabs_perg_admin_view[0]: 
            try:
                perguntas_df_admin_edit_view = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_admin_edit_view.columns: perguntas_df_admin_edit_view["Categoria"] = "Geral"
            except FileNotFoundError: st.info("Arquivo de perguntas não encontrado."); perguntas_df_admin_edit_view = pd.DataFrame(columns=["Pergunta", "Categoria"])
            if perguntas_df_admin_edit_view.empty: st.info("Nenhuma pergunta cadastrada.")
            else:
                for i_p_adm_v, row_p_adm_v in perguntas_df_admin_edit_view.iterrows():
                    cols_p_adm_v = st.columns([4, 2, 0.5, 0.5]) 
                    with cols_p_adm_v[0]:
                        nova_p_text_adm_v = st.text_input("Pergunta", value=str(row_p_adm_v["Pergunta"]), key=f"edit_p_txt_v_{i_p_adm_v}")
                        if nova_p_text_adm_v != row_p_adm_v["Pergunta"]: perguntas_df_admin_edit_view.at[i_p_adm_v, "Pergunta"] = nova_p_text_adm_v
                    with cols_p_adm_v[1]:
                        nova_cat_text_adm_v = st.text_input("Categoria", value=str(row_p_adm_v.get("Categoria", "Geral")), key=f"edit_p_cat_v_{i_p_adm_v}")
                        if nova_cat_text_adm_v != row_p_adm_v.get("Categoria", "Geral"): perguntas_df_admin_edit_view.at[i_p_adm_v, "Categoria"] = nova_cat_text_adm_v
                    with cols_p_adm_v[2]:
                        if st.button("💾", key=f"salvar_p_adm_v_{i_p_adm_v}", help="Salvar"):
                            perguntas_df_admin_edit_view.to_csv(perguntas_csv, index=False, encoding='utf-8')
                            st.success(f"Pergunta {i_p_adm_v+1} atualizada."); st.rerun()
                    with cols_p_adm_v[3]:
                        if st.button("🗑️", key=f"deletar_p_adm_v_{i_p_adm_v}", help="Deletar"):
                            perguntas_df_admin_edit_view = perguntas_df_admin_edit_view.drop(i_p_adm_v).reset_index(drop=True)
                            perguntas_df_admin_edit_view.to_csv(perguntas_csv, index=False, encoding='utf-8')
                            st.warning(f"Pergunta {i_p_adm_v+1} removida."); st.rerun()
                    st.divider()
        with tabs_perg_admin_view[1]: 
            with st.form("form_nova_pergunta_admin_view"):
                st.subheader("➕ Adicionar Nova Pergunta")
                # ... (Restante do form de adicionar pergunta como na versão anterior, já inclui Categoria)
                nova_p_form_txt_adm_v = st.text_input("Texto da Pergunta", key="nova_p_input_admin_txt_v")
                try:
                    perg_exist_df_v = pd.read_csv(perguntas_csv, encoding='utf-8')
                    cat_existentes_v = sorted(list(perg_exist_df_v['Categoria'].astype(str).unique())) if not perg_exist_df_v.empty and "Categoria" in perg_exist_df_v else []
                except: cat_existentes_v = []
                cat_options_v = ["Nova Categoria"] + cat_existentes_v
                cat_selecionada_v = st.selectbox("Selecionar/Criar Categoria:", cat_options_v, key="cat_select_admin_new_q_v")
                if cat_selecionada_v == "Nova Categoria": nova_cat_form_admin_v = st.text_input("Nome da Nova Categoria:", key="nova_cat_input_admin_new_q_v")
                else: nova_cat_form_admin_v = cat_selecionada_v
                tipo_p_form_admin_v = st.selectbox("Tipo de Pergunta", ["Pontuação (0-10)", "Texto Aberto", "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)", "[Matriz GUT]"], key="tipo_p_select_admin_new_q_v") # Simplificado para Matriz GUT
                
                add_p_btn_admin_v = st.form_submit_button("Adicionar Pergunta")
                if add_p_btn_admin_v:
                    if nova_p_form_txt_adm_v.strip() and nova_cat_form_admin_v.strip():
                        try: df_perg_add_admin_v = pd.read_csv(perguntas_csv, encoding='utf-8')
                        except FileNotFoundError: df_perg_add_admin_v = pd.DataFrame(columns=["Pergunta", "Categoria"])
                        if "Categoria" not in df_perg_add_admin_v.columns: df_perg_add_admin_v["Categoria"] = "Geral"
                        
                        # Adiciona o marcador de tipo diretamente ao texto da pergunta
                        p_completa_add_admin_v = f"{nova_p_form_txt_adm_v.strip()} {tipo_p_form_admin_v if tipo_p_form_admin_v == '[Matriz GUT]' else f'[{tipo_p_form_admin_v}]'}"
                        
                        nova_entrada_p_add_admin_v = pd.DataFrame([[p_completa_add_admin_v, nova_cat_form_admin_v.strip()]], columns=["Pergunta", "Categoria"])
                        df_perg_add_admin_v = pd.concat([df_perg_add_admin_v, nova_entrada_p_add_admin_v], ignore_index=True)
                        df_perg_add_admin_v.to_csv(perguntas_csv, index=False, encoding='utf-8')
                        st.success(f"Pergunta adicionada!"); st.rerun() 
                    else: st.warning("Texto da pergunta e categoria são obrigatórios.")


    elif menu_admin_sel_view == "Visualizar Diagnósticos":
        # ... (código como na versão anterior, já mostra Media_Cat_* e Comentarios_Admin)
        st.subheader("📂 Todos os Diagnósticos")
        if os.path.exists(arquivo_csv):
            try:
                diag_df_adm_v = pd.read_csv(arquivo_csv, encoding='utf-8') 
            except: diag_df_adm_v = pd.DataFrame()
            if not diag_df_adm_v.empty:
                st.dataframe(diag_df_adm_v.sort_values(by="Data", ascending=False).reset_index(drop=True))
                # ... (Ranking, Evolução, Indicadores, Exportar como antes) ...
                st.subheader("🔍 Filtrar e Comentar") # Simplificado
                if "CNPJ" in diag_df_adm_v.columns:
                    cnpjs_uniq_adm_v = ["Todos"] + sorted(diag_df_adm_v["CNPJ"].astype(str).unique().tolist())
                    f_cnpj_adm_v = st.selectbox("Selecionar CNPJ:", cnpjs_uniq_adm_v, key="admin_cnpj_filter_v_comment")
                    if f_cnpj_adm_v != "Todos":
                        # ... (Lógica de exibir detalhes do diagnóstico filtrado e adicionar/salvar comentários do admin, como antes)
                        filt_df_adm_v = diag_df_adm_v[diag_df_adm_v["CNPJ"].astype(str) == f_cnpj_adm_v].sort_values(by="Data", ascending=False)
                        if not filt_df_adm_v.empty:
                            for idx_d_adm, row_d_adm in filt_df_adm_v.iterrows():
                                with st.expander(f"Detalhes: {row_d_adm['Data']} (ID: {idx_d_adm})"):
                                    # ... (Exibição de médias, resumos, e médias de categoria como antes)
                                    st.markdown(f"**Média Geral:** {row_d_adm.get('Média Geral', 'N/A')} | **GUT Média (G*U*T):** {row_d_adm.get('GUT Média', 'N/A')}")
                                    st.markdown("**Médias por Categoria:**")
                                    # ... (código para exibir Media_Cat_* do row_d_adm)
                                    com_adm_val_v = row_d_adm.get("Comentarios_Admin", "")
                                    if pd.isna(com_adm_val_v): com_adm_val_v = ""
                                    novo_com_adm_v = st.text_area("Comentários Admin:", value=com_adm_val_v, key=f"adm_com_v_{idx_d_adm}")
                                    if st.button("💾 Salvar Comentário", key=f"save_adm_com_v_{idx_d_adm}"):
                                        df_diag_save_com_v = pd.read_csv(arquivo_csv, encoding='utf-8')
                                        df_diag_save_com_v.loc[idx_d_adm, "Comentarios_Admin"] = novo_com_adm_v
                                        df_diag_save_com_v.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                        st.success(f"Comentário salvo!"); st.rerun()
                        else: st.info(f"Nenhum diagnóstico para {f_cnpj_adm_v}.")
            else: st.info("Nenhum diagnóstico no sistema.")
        else: st.info("Arquivo de diagnósticos não encontrado.")


    # Histórico de Usuários, Gerenciar Clientes, Gerenciar Administradores (lógica interna mantida)
    # ... (código mantido para essas seções)
    elif menu_admin_sel_view == "Histórico de Usuários":
        st.subheader("📜 Histórico de Ações dos Clientes")
        try: hist_df_adm_v = pd.read_csv(historico_csv, encoding='utf-8'); st.dataframe(hist_df_adm_v.sort_values(by="Data", ascending=False))
        except: st.info("Histórico não encontrado ou vazio.")
    elif menu_admin_sel_view == "Gerenciar Clientes":
        st.subheader("👥 Gerenciar Clientes"); # ... (código mantido)
    elif menu_admin_sel_view == "Gerenciar Administradores":
        st.subheader("👮 Gerenciar Administradores"); # ... (código mantido)

# Fallback (sem alterações)
if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()