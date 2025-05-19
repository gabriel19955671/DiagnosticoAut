import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
from fpdf import FPDF
import tempfile

st.set_page_config(page_title="Portal de Diagnóstico", layout="centered")

# CSS restaurado para a logo e container de login
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
if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state:
    st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state:
    st.session_state.diagnostico_enviado = False
if "inicio_sessao_cliente" not in st.session_state:
    st.session_state.inicio_sessao_cliente = None
if "pular_para_diagnostico" not in st.session_state:
    st.session_state.pular_para_diagnostico = False
if "cnpj" not in st.session_state:
    st.session_state.cnpj = None
if "user" not in st.session_state:
    st.session_state.user = None


# Criar arquivos base caso não existam
for arquivo, colunas in [
    (usuarios_bloqueados_csv, ["CNPJ"]),
    (admin_credenciais_csv, ["Usuario", "Senha"]),
    (usuarios_csv, ["CNPJ", "Senha", "Empresa"]),
    (
        arquivo_csv,
        [
            "Data", "CNPJ", "Nome", "Email", "Empresa", "Financeiro", # Example columns, will be extended by questions
            "Processos", "Marketing", "Vendas", "Equipe", "Média Geral",
            "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente" # Added Análise do Cliente
        ],
    ),
    (perguntas_csv, ["Pergunta"]),
    (historico_csv, ["Data", "CNPJ", "Ação", "Descrição"]),
]:
    if not os.path.exists(arquivo):
        pd.DataFrame(columns=colunas).to_csv(arquivo, index=False, encoding='utf-8')

# Função para registrar ações no histórico
def registrar_acao(cnpj, acao, descricao):
    try:
        historico = pd.read_csv(historico_csv, encoding='utf-8')
    except FileNotFoundError:
        historico = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    
    nova_data = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }
    nova_entrada_df = pd.DataFrame([nova_data])
    historico = pd.concat([historico, nova_entrada_df], ignore_index=True)
    historico.to_csv(historico_csv, index=False, encoding='utf-8')

# Redirecionamento seguro pós-login
if st.session_state.get("trigger_cliente_rerun"):
    st.session_state.trigger_cliente_rerun = False
    st.rerun()
if st.session_state.get("trigger_admin_rerun"):
    st.session_state.trigger_admin_rerun = False
    st.rerun()

# Definição de aba
if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True)
elif st.session_state.admin_logado:
    aba = "Administrador"
else: # Cliente logado
    aba = "Cliente"


# Login do Administrador
if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")
    if entrar:
        df_admin = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
        if not df_admin[(df_admin["Usuario"] == usuario) & (df_admin["Senha"] == senha)].empty:
            st.session_state.admin_logado = True
            st.success("Login de administrador realizado com sucesso!")
            st.session_state.trigger_admin_rerun = True
            st.rerun() # Use st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop() # Stop execution for non-logged-in admin

# Login do Cliente
if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente"):
        cnpj = st.text_input("CNPJ")
        senha_cliente = st.text_input("Senha", type="password") # Renamed to avoid conflict
        acessar = st.form_submit_button("Entrar")
    if acessar:
        if not os.path.exists(usuarios_csv):
            st.error("Base de usuários não encontrada.")
            st.stop()

        usuarios = pd.read_csv(usuarios_csv, encoding='utf-8')
        bloqueados = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')

        if cnpj in bloqueados["CNPJ"].astype(str).values: # ensure type consistency
            st.error("Este CNPJ está bloqueado. Solicite liberação ao administrador.")
            st.stop()
        
        # Ensure comparison is between strings if CNPJ can be numeric
        user_match = usuarios[(usuarios["CNPJ"].astype(str) == str(cnpj)) & (usuarios["Senha"] == senha_cliente)]

        if user_match.empty:
            st.error("CNPJ ou senha inválidos.")
            st.stop()

        st.session_state.cliente_logado = True
        st.session_state.cnpj = str(cnpj) # Store as string
        st.session_state.user = user_match.iloc[0].to_dict() # Store user info as dict
        st.session_state.inicio_sessao_cliente = time.time()
        registrar_acao(st.session_state.cnpj, "Login", "Usuário realizou login no sistema.")
        st.success("Login realizado com sucesso!")
        st.session_state.trigger_cliente_rerun = True
        st.rerun() # Use st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop() # Stop execution for non-logged-in client

# --- CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    if st.sidebar.button("⬅️ Sair do Portal Cliente"):
        for key in ['cliente_logado', 'cnpj', 'user', 'inicio_sessao_cliente', 'pular_para_diagnostico', 'diagnostico_enviado']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # Histórico de diagnósticos anteriores do cliente e Kanban
    if not st.session_state.get("pular_para_diagnostico", False):
        st.subheader("📌 Instruções Gerais Antes de Começar")
        with st.expander("📖 Leia atentamente as instruções abaixo"):
            st.markdown("""
            - Responda cada pergunta com sinceridade.
            - Utilize a escala corretamente conforme o tipo da pergunta.
            - As análises e planos de ação serão gerados com base em suas respostas.
            - Após o envio, o diagnóstico será salvo e poderá ser visualizado no histórico.
            """)
        aceite = st.checkbox("✅ Estou ciente de todas as instruções passadas aqui.")
        if aceite:
            if st.button("🚀 Ir para Novo Diagnóstico"):
                st.session_state.pular_para_diagnostico = True
                st.rerun()
        else:
            st.warning("Você precisa confirmar ciência das instruções para acessar o diagnóstico.")

        if st.session_state.get("diagnostico_enviado", False):
            st.markdown("<h2 style='color: green;'>🎯 Controle de Evolução - Diagnóstico</h2>", unsafe_allow_html=True)
            st.session_state.diagnostico_enviado = False # Reset flag

        st.subheader("📁 Diagnósticos Anteriores")
        try:
            df_antigos = pd.read_csv(arquivo_csv, encoding='utf-8')
            df_cliente = df_antigos[df_antigos["CNPJ"].astype(str) == st.session_state.cnpj]
        except FileNotFoundError:
            df_cliente = pd.DataFrame()
        
        if df_cliente.empty:
            st.info("Nenhum diagnóstico anterior encontrado.")
        else:
            df_cliente = df_cliente.sort_values(by="Data", ascending=False)
            for i, row in df_cliente.iterrows():
                with st.expander(f"📅 {row['Data']} - {row['Empresa']}"):
                    registrar_acao(st.session_state.cnpj, "Visualização", f"Cliente visualizou o diagnóstico de {row['Data']}")
                    st.write(f"**Média Geral:** {row.get('Média Geral', 'N/A')}") # Use .get for safety
                    st.write(f"**GUT Média:** {row.get('GUT Média', 'N/A')}")
                    st.write(f"**Resumo:** {row.get('Diagnóstico', 'N/A')}")
                    
                    analise_cliente_val = row.get("Análise do Cliente", "")
                    analise_key = f"analise_{row.name}" # Use row.name for a more unique key if 'i' can repeat due to filtering
                    analise_cliente = st.text_area("🧠 Minha Análise sobre este Diagnóstico:", value=analise_cliente_val, key=analise_key)
                    
                    if st.button("💾 Salvar Análise", key=f"salvar_analise_{row.name}"):
                        df_antigos_full = pd.read_csv(arquivo_csv, encoding='utf-8') # Re-read to avoid stale data
                        df_antigos_full.loc[df_antigos_full.index == row.name, "Análise do Cliente"] = analise_cliente
                        df_antigos_full.to_csv(arquivo_csv, index=False, encoding='utf-8')
                        registrar_acao(st.session_state.cnpj, "Análise", f"Cliente escreveu/editou análise do diagnóstico de {row['Data']}")
                        st.success("Análise salva com sucesso!")
                        st.rerun()
                    st.write(f"**Observações (do consultor):** {row.get('Observações', 'N/A')}")
                    st.markdown("---")

            # Kanban baseado nas respostas GUT do diagnóstico MAIS RECENTE
            st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
            gut_cards = []
            latest_diagnostic_data = {}
            if not df_cliente.empty:
                latest_row = df_cliente.iloc[0] # Already sorted, first row is latest
                latest_diagnostic_data = latest_row.to_dict()

            if isinstance(latest_diagnostic_data, dict):
                for pergunta, resposta_val in latest_diagnostic_data.items():
                    if isinstance(pergunta, str) and "Pontuação (0-5) + Matriz GUT" in pergunta:
                        try:
                            # Ensure resposta_val is not NaN before converting
                            if pd.notna(resposta_val):
                                resposta_num = int(float(resposta_val)) # Convert to float first, then int
                                prazo = "60 dias" # Default
                                if resposta_num >= 4: # Critérios GUT (Gravidade, Urgência, Tendência) alta
                                    prazo = "15 dias"
                                elif resposta_num == 3:
                                    prazo = "30 dias"
                                elif resposta_num == 2:
                                    prazo = "45 dias"
                                # else: prazo remains "60 dias" or "Não prioritário" for 0 or 1

                                # Only add if it's a priority (e.g. > 1)
                                if resposta_num > 1 : # Adjust threshold as needed
                                    gut_cards.append({
                                        "Tarefa": pergunta.replace(" [Pontuação (0-5) + Matriz GUT]", ""), # Clean question text
                                        "Prazo": prazo,
                                        "Score": resposta_num, # Store score for potential sorting
                                        "Responsável": st.session_state.user.get("Empresa", "Não definido")
                                    })
                            else:
                                # st.write(f"Skipping GUT card for '{pergunta}' due to missing value (NaN).") # Optional: for debugging
                                pass

                        except ValueError:
                            st.warning(f"Valor inválido para '{pergunta}' no Kanban: {resposta_val}. Esperado um número.")
                            continue
            
            if gut_cards:
                # Sort cards within each prazo by score (higher scores first)
                gut_cards_sorted = sorted(gut_cards, key=lambda x: x["Score"], reverse=True)
                
                prazos_definidos = sorted(list(set(card["Prazo"] for card in gut_cards_sorted)), key=lambda x: int(x.split(" ")[0])) # Sort prazos: "15 dias", "30 dias"
                
                cols = st.columns(len(prazos_definidos))
                for idx, prazo_col in enumerate(prazos_definidos):
                    with cols[idx]:
                        st.markdown(f"#### ⏱️ {prazo_col}")
                        for card in gut_cards_sorted:
                            if card["Prazo"] == prazo_col:
                                st.markdown(f"""
                                <div style="border: 1px solid #e0e0e0; border-left: 5px solid #2563eb; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
                                    <small><b>{card['Tarefa']}</b> (Score: {card['Score']})</small><br>
                                    <small><i>👤 {card['Responsável']}</i></small>
                                </div>
                                """, unsafe_allow_html=True)
            else:
                st.info("Nenhuma ação prioritária identificada para o Kanban no último diagnóstico ou nenhum diagnóstico GUT realizado.")


            st.subheader("📈 Comparativo de Evolução")
            if len(df_cliente) > 1:
                grafico = df_cliente.sort_values(by="Data")
                grafico["Data"] = pd.to_datetime(grafico["Data"])
                
                # Ensure 'Média Geral' and 'GUT Média' are numeric, coercing errors
                grafico['Média Geral'] = pd.to_numeric(grafico['Média Geral'], errors='coerce')
                if 'GUT Média' in grafico.columns:
                     grafico['GUT Média'] = pd.to_numeric(grafico['GUT Média'], errors='coerce')
                     st.line_chart(grafico.set_index("Data")[['Média Geral', 'GUT Média']].dropna())
                else:
                     st.line_chart(grafico.set_index("Data")[['Média Geral']].dropna())
                
                st.subheader("📊 Comparação Entre Diagnósticos")
                opcoes = grafico["Data"].astype(str).tolist()
                if len(opcoes) >= 2:
                    diag_atual_idx = len(opcoes)-1
                    diag_anterior_idx = len(opcoes)-2
                    
                    diag_atual_sel = st.selectbox("Selecione o diagnóstico mais recente para comparação:", opcoes, index=diag_atual_idx, key="diag_atual_sel")
                    diag_anterior_sel = st.selectbox("Selecione o diagnóstico anterior para comparação:", opcoes, index=diag_anterior_idx, key="diag_anterior_sel")

                    atual = grafico[grafico["Data"].astype(str) == diag_atual_sel].iloc[0]
                    anterior = grafico[grafico["Data"].astype(str) == diag_anterior_sel].iloc[0]

                    st.write(f"### 📅 Comparando {diag_anterior_sel.split(' ')[0]} ⟶ {diag_atual_sel.split(' ')[0]}")
                    
                    # Identify common numeric columns for comparison, excluding metadata
                    cols_excluir = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Observações", "Diagnóstico", "Análise do Cliente"]
                    variaveis_para_comparar = [col for col in grafico.columns if col not in cols_excluir and pd.api.types.is_numeric_dtype(grafico[col])]

                    if variaveis_para_comparar:
                        comparativo_data = []
                        for v in variaveis_para_comparar:
                            val_ant = pd.to_numeric(anterior.get(v), errors='coerce')
                            val_atu = pd.to_numeric(atual.get(v), errors='coerce')
                            evolucao = "➖ Igual"
                            if pd.notna(val_ant) and pd.notna(val_atu):
                                if val_atu > val_ant: evolucao = "🔼 Melhorou"
                                elif val_atu < val_ant: evolucao = "🔽 Piorou"
                            
                            comparativo_data.append({
                                "Indicador": v.replace(" [Pontuação (0-10)]", "").replace(" [Pontuação (0-5) + Matriz GUT]", ""), # Clean name
                                "Anterior": val_ant if pd.notna(val_ant) else "N/A",
                                "Atual": val_atu if pd.notna(val_atu) else "N/A",
                                "Evolução": evolucao
                            })
                        
                        comparativo_df = pd.DataFrame(comparativo_data)
                        st.dataframe(comparativo_df)
                    else:
                        st.info("Não há suficientes dados numéricos para comparação.")
                else:
                    st.info("Pelo menos dois diagnósticos são necessários para comparação.")
            else:
                st.info("Pelo menos dois diagnósticos são necessários para o gráfico de evolução e comparação.")

    # Painel Cliente - Formulário de Diagnóstico
    if st.session_state.get("pular_para_diagnostico", False):
        st.subheader("📋 Formulário de Diagnóstico")
        if st.button("⬅️ Voltar para Histórico e Instruções"):
            st.session_state.pular_para_diagnostico = False
            st.rerun()

        try:
            perguntas_df = pd.read_csv(perguntas_csv, encoding='utf-8')
        except FileNotFoundError:
            st.error("Arquivo de perguntas não encontrado. Contate o administrador.")
            st.stop()

        if perguntas_df.empty:
            st.warning("Nenhuma pergunta cadastrada para o diagnóstico. Contate o administrador.")
            st.stop()

        respostas_form = {} # Use a different name to avoid confusion with other 'respostas'
        total_perguntas = len(perguntas_df)
        respondidas_count = 0 # Renamed

        form_key_suffix = datetime.now().strftime("%Y%m%d%H%M%S") # Make keys unique per form instance

        for i, row in perguntas_df.iterrows():
            texto_pergunta = str(row["Pergunta"]) # Ensure it's a string
            widget_key = f"q_{i}_{form_key_suffix}"

            if "Pontuação (0-5) + Matriz GUT" in texto_pergunta:
                respostas_form[texto_pergunta] = st.slider(texto_pergunta, 0, 5, key=widget_key, value=0) # Default to 0 for sliders
                if respostas_form[texto_pergunta] != 0: respondidas_count += 1
            elif "Pontuação (0-10)" in texto_pergunta:
                respostas_form[texto_pergunta] = st.slider(texto_pergunta, 0, 10, key=widget_key, value=0)
                if respostas_form[texto_pergunta] != 0: respondidas_count += 1
            elif "Texto Aberto" in texto_pergunta:
                respostas_form[texto_pergunta] = st.text_area(texto_pergunta, key=widget_key, value="")
                if respostas_form[texto_pergunta].strip() != "": respondidas_count += 1
            elif "Escala" in texto_pergunta: # Ex: "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)"
                opcoes_escala = ["Selecione uma opção", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"] # Add default
                respostas_form[texto_pergunta] = st.selectbox(texto_pergunta, opcoes_escala, key=widget_key, index=0)
                if respostas_form[texto_pergunta] != "Selecione uma opção": respondidas_count += 1
            else: # Default to slider 0-10 if no specific type identified
                st.warning(f"Tipo de pergunta não claramente definido para: '{texto_pergunta}'. Usando slider 0-10. Verifique a formatação no CSV de perguntas.")
                respostas_form[texto_pergunta] = st.slider(texto_pergunta, 0, 10, key=widget_key, value=0)
                if respostas_form[texto_pergunta] != 0: respondidas_count += 1
        
        progresso_percent = round((respondidas_count / total_perguntas) * 100) if total_perguntas > 0 else 0
        st.info(f"📊 Progresso: {respondidas_count} de {total_perguntas} perguntas respondidas ({progresso_percent}%)")
        
        observacoes_cliente = st.text_area("Suas Observações Gerais sobre este diagnóstico (opcional):", key=f"obs_cliente_{form_key_suffix}")
        diagnostico_resumo_cliente = st.text_area("✍️ Escreva um breve resumo ou principais insights deste diagnóstico (para o PDF):", key=f"diag_resumo_{form_key_suffix}")

        if st.button("✔️ Enviar Diagnóstico Finalizado", key=f"enviar_diag_{form_key_suffix}"):
            # Validate if all questions are answered, if required
            if respondidas_count < total_perguntas:
                st.warning("Por favor, responda todas as perguntas antes de enviar.")
            elif not diagnostico_resumo_cliente.strip():
                st.error("O campo 'Resumo do Diagnóstico' é obrigatório para o PDF.")
            else:
                gut_perguntas_dict = {k: v for k, v in respostas_form.items() if isinstance(k, str) and "Pontuação (0-5) + Matriz GUT" in k and isinstance(v, int)}
                gut_total = sum(gut_perguntas_dict.values())
                gut_media = round(gut_total / len(gut_perguntas_dict), 2) if gut_perguntas_dict else 0.0

                # Calculate Média Geral only from numeric slider/rating questions
                numeric_responses = [v for k, v in respostas_form.items() if isinstance(v, (int, float)) and ("Pontuação (0-10)" in k or "Pontuação (0-5)" in k)] #More specific
                media_geral_calc = round(sum(numeric_responses) / len(numeric_responses), 2) if numeric_responses else 0.0
                
                try:
                    usuarios_df = pd.read_csv(usuarios_csv, encoding='utf-8')
                    empresa_nome = usuarios_df.loc[usuarios_df["CNPJ"].astype(str) == st.session_state.cnpj, "Empresa"].values[0]
                except (FileNotFoundError, IndexError):
                    empresa_nome = st.session_state.user.get("Empresa", "Empresa Desconhecida")


                nova_linha_dict = {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "CNPJ": st.session_state.cnpj,
                    "Nome": st.session_state.user.get("CNPJ", ""), # Usually CNPJ is the "Nome" here, or use specific name field if available
                    "Email": "", # Placeholder, add if email is collected
                    "Empresa": empresa_nome,
                    "Média Geral": media_geral_calc,
                    "GUT Média": gut_media,
                    "Observações": "", # Placeholder for Admin/Consultant observations, client provides their own
                    "Análise do Cliente": observacoes_cliente, # Client's own analysis/observations
                    "Diagnóstico": diagnostico_resumo_cliente # Client's summary for PDF
                }
                # Add all question responses to the row
                for pergunta, resposta in respostas_form.items():
                    nova_linha_dict[pergunta] = resposta
                
                try:
                    df_diagnosticos = pd.read_csv(arquivo_csv, encoding='utf-8')
                except FileNotFoundError: # If file deleted after app start
                    df_diagnosticos = pd.DataFrame() # Create empty if not found
                
                # Ensure all columns from nova_linha_dict exist in df_diagnosticos, add if not
                for col in nova_linha_dict.keys():
                    if col not in df_diagnosticos.columns:
                        df_diagnosticos[col] = pd.NA # Or appropriate default like '' or 0

                df_diagnosticos = pd.concat([df_diagnosticos, pd.DataFrame([nova_linha_dict])], ignore_index=True)
                df_diagnosticos.to_csv(arquivo_csv, index=False, encoding='utf-8')
                
                st.success("Diagnóstico enviado com sucesso!")
                registrar_acao(st.session_state.cnpj, "Envio", "Cliente enviou novo diagnóstico.")

                # Gerar PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                
                # Helper to handle encoding for PDF output
                def pdf_safe_text(text):
                    return str(text).encode('latin-1', 'replace').decode('latin-1')

                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, pdf_safe_text(f"Diagnóstico Empresarial - {empresa_nome}"), 0, 1, 'C')
                pdf.ln(5)

                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 7, pdf_safe_text(f"Data do Diagnóstico: {nova_linha_dict['Data']}"))
                pdf.multi_cell(0, 7, pdf_safe_text(f"Empresa: {empresa_nome} (CNPJ: {st.session_state.cnpj})"))
                pdf.ln(3)
                pdf.multi_cell(0, 7, pdf_safe_text(f"Média Geral das Respostas Numéricas: {media_geral_calc}"))
                if gut_media > 0:
                    pdf.multi_cell(0, 7, pdf_safe_text(f"Média das Prioridades (GUT): {gut_media}"))
                pdf.ln(5)

                pdf.set_font("Arial", 'B', 12)
                pdf.multi_cell(0, 7, pdf_safe_text("Resumo do Diagnóstico (Fornecido pelo Cliente):"))
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 7, pdf_safe_text(diagnostico_resumo_cliente))
                pdf.ln(3)
                
                if observacoes_cliente:
                    pdf.set_font("Arial", 'B', 12)
                    pdf.multi_cell(0, 7, pdf_safe_text("Observações Gerais do Cliente:"))
                    pdf.set_font("Arial", size=10)
                    pdf.multi_cell(0, 7, pdf_safe_text(observacoes_cliente))
                    pdf.ln(3)

                pdf.set_font("Arial", 'B', 12)
                pdf.multi_cell(0, 10, pdf_safe_text("Respostas Detalhadas:"))
                pdf.set_font("Arial", size=9)
                for k, v in respostas_form.items():
                    if isinstance(v, (int, float, str)): # Ensure it's a simple type
                        pdf.multi_cell(0, 6, pdf_safe_text(f"- {k}: {v}"))
                pdf.ln(5)

                # Kanban no PDF
                pdf.set_font("Arial", 'B', 12)
                pdf.add_page() # New page for Kanban
                pdf.cell(0, 10, pdf_safe_text("Plano de Ação Sugerido (Kanban)"), 0, 1, 'C')
                pdf.ln(5)
                pdf.set_font("Arial", size=10)
                if gut_cards: # Use the gut_cards generated earlier if this PDF is for the SAME diagnostic
                                # For a new diagnostic, we need to regenerate gut_cards based on 'respostas_form'
                    current_gut_cards = []
                    for pergunta_pdf, resposta_pdf_val in respostas_form.items():
                        if isinstance(pergunta_pdf, str) and "Pontuação (0-5) + Matriz GUT" in pergunta_pdf:
                            try:
                                if pd.notna(resposta_pdf_val):
                                    resposta_pdf_num = int(float(resposta_pdf_val))
                                    prazo_pdf = "60 dias"
                                    if resposta_pdf_num >= 4: prazo_pdf = "15 dias"
                                    elif resposta_pdf_num == 3: prazo_pdf = "30 dias"
                                    elif resposta_pdf_num == 2: prazo_pdf = "45 dias"
                                    if resposta_pdf_num > 1:
                                        current_gut_cards.append({
                                            "Tarefa": pergunta_pdf.replace(" [Pontuação (0-5) + Matriz GUT]", ""),
                                            "Prazo": prazo_pdf, "Score": resposta_pdf_num
                                        })
                            except ValueError: pass # Ignore if not convertible
                    
                    if current_gut_cards:
                        current_gut_cards_sorted = sorted(current_gut_cards, key=lambda x: (int(x["Prazo"].split(" ")[0]), -x["Score"]))
                        for card in current_gut_cards_sorted:
                             pdf.multi_cell(0, 6, pdf_safe_text(f"Prazo: {card['Prazo']} - Tarefa: {card['Tarefa']} (Score: {card['Score']})"))
                        pdf.ln(3)
                    else:
                        pdf.multi_cell(0,6, pdf_safe_text("Nenhuma ação prioritária (GUT > 1) identificada neste diagnóstico."))
                else:
                    pdf.multi_cell(0,6, pdf_safe_text("Nenhuma ação prioritária (GUT > 1) identificada neste diagnóstico."))


                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                    pdf_path = tmpfile.name
                    pdf.output(pdf_path)

                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📄 Baixar PDF do Diagnóstico",
                        data=f,
                        file_name=f"diagnostico_{empresa_nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                registrar_acao(st.session_state.cnpj, "Download PDF", "Cliente baixou o PDF do diagnóstico.")
                
                st.session_state.diagnostico_enviado = True
                st.session_state.pular_para_diagnostico = False # Go back to history view
                st.rerun()
        st.stop() # Stop further rendering if in diagnostic form


# --- PAINEL ADMINISTRATIVO ---
if aba == "Administrador" and st.session_state.admin_logado:
    st.sidebar.success("🟢 Admin Logado")
    if st.sidebar.button("🚪 Sair do Painel Admin"):
        st.session_state.admin_logado = False
        st.rerun()

    if st.sidebar.button("🔄 Atualizar Página Admin"):
        st.rerun()

    menu_admin = st.sidebar.selectbox(
        "Selecione a funcionalidade administrativa:",
        [
            "Visualizar Diagnósticos",
            "Histórico de Usuários",
            "Gerenciar Perguntas do Formulário",
            "Gerenciar Usuários Clientes",
            "Gerenciar Administradores" # Added
        ],
    )

    st.header(f"🔑 Painel Administrativo: {menu_admin}")

    if menu_admin == "Gerenciar Perguntas do Formulário":
        st.subheader("📝 Gerenciar Perguntas do Diagnóstico")
        tabs_perguntas = st.tabs(["📋 Perguntas Atuais", "➕ Adicionar Nova Pergunta"])

        with tabs_perguntas[0]:
            try:
                perguntas_df_edit = pd.read_csv(perguntas_csv, encoding='utf-8')
            except FileNotFoundError:
                st.info("Arquivo de perguntas não encontrado. Crie-o adicionando uma pergunta.")
                perguntas_df_edit = pd.DataFrame(columns=["Pergunta"])

            if perguntas_df_edit.empty:
                st.info("Nenhuma pergunta cadastrada ainda.")
            else:
                for i, row_p in perguntas_df_edit.iterrows():
                    col1, col_spacer, col2, col3 = st.columns([6, 0.2, 1, 1]) # Added spacer for better layout
                    with col1:
                        nova_pergunta_text = st.text_input(f"Pergunta {i+1}", value=str(row_p["Pergunta"]), key=f"edit_{i}")
                        if nova_pergunta_text != row_p["Pergunta"]:
                             perguntas_df_edit.at[i, "Pergunta"] = nova_pergunta_text
                    with col2:
                        if st.button("💾", key=f"salvar_p_{i}", help="Salvar esta pergunta"):
                            perguntas_df_edit.to_csv(perguntas_csv, index=False, encoding='utf-8')
                            st.success(f"Pergunta {i+1} atualizada.")
                            st.rerun()
                    with col3:
                        if st.button("🗑️", key=f"deletar_p_{i}", help="Deletar esta pergunta"):
                            perguntas_df_edit = perguntas_df_edit.drop(i).reset_index(drop=True)
                            perguntas_df_edit.to_csv(perguntas_csv, index=False, encoding='utf-8')
                            st.warning(f"Pergunta {i+1} removida.")
                            st.rerun()
                    st.divider()


        with tabs_perguntas[1]:
            with st.form("form_nova_pergunta"):
                st.subheader("➕ Adicionar Nova Pergunta")
                nova_pergunta_form = st.text_input("Texto da Pergunta", key="nova_pergunta_input")
                tipo_pergunta_form = st.selectbox("Tipo de Pergunta", 
                                             ["Pontuação (0-10)", "Texto Aberto", "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)", "Pontuação (0-5) + Matriz GUT"], 
                                             key="tipo_pergunta_select")

                if tipo_pergunta_form == "Pontuação (0-5) + Matriz GUT":
                    st.markdown("Esta pergunta utilizará uma escala de 0 a 5 e suas respostas podem ser usadas para priorização GUT (Gravidade, Urgência, Tendência).")
                elif tipo_pergunta_form == "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)":
                     st.markdown("Esta pergunta usará as opções: Muito Baixo, Baixo, Médio, Alto, Muito Alto.")


                adicionar_pergunta_btn = st.form_submit_button("Adicionar Pergunta")
                if adicionar_pergunta_btn:
                    if nova_pergunta_form.strip():
                        try:
                            df_perg = pd.read_csv(perguntas_csv, encoding='utf-8')
                        except FileNotFoundError:
                            df_perg = pd.DataFrame(columns=["Pergunta"])
                        
                        # Construct the full question string with type hint
                        pergunta_completa = f"{nova_pergunta_form.strip()} [{tipo_pergunta_form}]"
                        
                        nova_entrada_perg = pd.DataFrame([[pergunta_completa]], columns=["Pergunta"])
                        df_perg = pd.concat([df_perg, nova_entrada_perg], ignore_index=True)
                        df_perg.to_csv(perguntas_csv, index=False, encoding='utf-8')
                        st.success(f"Pergunta '{pergunta_completa}' adicionada! A lista de perguntas será atualizada.")
                        # No st.stop() needed here, allow form to clear or rerun to show update
                        st.rerun() 
                    else:
                        st.warning("Digite uma pergunta antes de adicionar.")
    
    elif menu_admin == "Visualizar Diagnósticos":
        st.subheader("📂 Todos os Diagnósticos Enviados")
        if os.path.exists(arquivo_csv):
            # Moved this read to the top of the section to define 'diagnosticos' earlier
            try:
                diagnosticos_df = pd.read_csv(arquivo_csv, encoding='utf-8') # Renamed to avoid conflict
            except pd.errors.EmptyDataError:
                st.info("O arquivo de diagnósticos está vazio.")
                diagnosticos_df = pd.DataFrame()
            except FileNotFoundError:
                st.info("Nenhum arquivo de diagnósticos encontrado.")
                diagnosticos_df = pd.DataFrame()

            if not diagnosticos_df.empty:
                st.dataframe(diagnosticos_df.sort_values(by="Data", ascending=False))
                
                csv_export = diagnosticos_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "⬇️ Exportar Todos os Diagnósticos (CSV)", 
                    csv_export, 
                    file_name="diagnosticos_completos.csv", 
                    mime="text/csv"
                )
                st.markdown("---")

                st.subheader("🏆 Ranking das Empresas (Baseado na Média Geral de todos os diagnósticos)")
                if "Empresa" in diagnosticos_df.columns and "Média Geral" in diagnosticos_df.columns:
                    # Convert Média Geral to numeric, coercing errors
                    diagnosticos_df["Média Geral Num"] = pd.to_numeric(diagnosticos_df["Média Geral"], errors='coerce')
                    ranking_df = diagnosticos_df.dropna(subset=["Média Geral Num"]) # Drop rows where conversion failed
                    
                    if not ranking_df.empty:
                        ranking = ranking_df.groupby("Empresa")["Média Geral Num"].mean().sort_values(ascending=False).reset_index()
                        ranking.index = ranking.index + 1 # Start index from 1
                        st.dataframe(ranking.rename(columns={"Média Geral Num": "Média Geral (Ranking)"}))
                    else:
                        st.info("Não há dados suficientes ou válidos de 'Média Geral' para gerar o ranking.")
                else:
                    st.info("Colunas 'Empresa' ou 'Média Geral' não encontradas para o ranking.")
                st.markdown("---")

                st.subheader("📈 Evolução Mensal dos Diagnósticos (Agregado)")
                df_diag_vis = diagnosticos_df.copy() # Use a copy for visualization
                df_diag_vis["Data"] = pd.to_datetime(df_diag_vis["Data"], errors="coerce")
                df_diag_vis = df_diag_vis.dropna(subset=["Data"]) # Remove rows where date conversion failed
                
                if not df_diag_vis.empty:
                    df_diag_vis["Mês/Ano"] = df_diag_vis["Data"].dt.strftime("%b/%y") # Ex: Jan/23
                    # Ensure metrics are numeric
                    df_diag_vis["Média Geral"] = pd.to_numeric(df_diag_vis["Média Geral"], errors='coerce')
                    if "GUT Média" in df_diag_vis.columns:
                        df_diag_vis["GUT Média"] = pd.to_numeric(df_diag_vis["GUT Média"], errors='coerce')
                    else:
                        df_diag_vis["GUT Média"] = 0 # Assign a default if column doesn't exist

                    resumo_mensal = df_diag_vis.groupby("Mês/Ano").agg(
                        Diagnósticos_Realizados=("CNPJ", "count"), 
                        Média_Geral_Mensal=("Média Geral", "mean"),
                        GUT_Média_Mensal=("GUT Média", "mean") # This will be NaN if column doesn't exist or all values are NaN
                    ).reset_index()
                    
                    # Sort by actual date, not just month/year string
                    resumo_mensal['temp_date_sort'] = pd.to_datetime(resumo_mensal['Mês/Ano'], format='%b/%y', errors='coerce')
                    resumo_mensal = resumo_mensal.sort_values('temp_date_sort').drop(columns=['temp_date_sort'])

                    st.write("##### Número de Diagnósticos por Mês")
                    st.bar_chart(resumo_mensal.set_index("Mês/Ano")["Diagnósticos_Realizados"])
                    st.write("##### Médias Gerais e GUT por Mês")
                    st.line_chart(resumo_mensal.set_index("Mês/Ano")[["Média_Geral_Mensal", "GUT_Média_Mensal"]].dropna(axis=1, how='all')) # Drop columns if all NaN
                else:
                    st.info("Não há diagnósticos com datas válidas para mostrar a evolução mensal.")
                st.markdown("---")

                st.subheader("📊 Indicadores Gerais de Todos os Diagnósticos")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📦 Total de Diagnósticos", len(diagnosticos_df))
                with col2:
                    media_geral_todos = pd.to_numeric(diagnosticos_df["Média Geral"], errors='coerce').mean()
                    st.metric("📈 Média Geral (Todos)", f"{media_geral_todos:.2f}" if pd.notna(media_geral_todos) else "N/A")
                with col3:
                    if "GUT Média" in diagnosticos_df.columns:
                        gut_media_todos = pd.to_numeric(diagnosticos_df["GUT Média"], errors='coerce').mean()
                        st.metric("🔥 GUT Média (Todos)", f"{gut_media_todos:.2f}" if pd.notna(gut_media_todos) else "N/A")
                    else:
                        st.metric("🔥 GUT Média (Todos)", "N/A")
                st.markdown("---")
                
                st.subheader("🔍 Filtrar Diagnósticos por CNPJ")
                if "CNPJ" in diagnosticos_df.columns:
                    cnpjs_unicos = ["Todos"] + sorted(diagnosticos_df["CNPJ"].astype(str).unique().tolist())
                    filtro_cnpj_admin = st.selectbox("Selecione um CNPJ para detalhar:", cnpjs_unicos, key="admin_cnpj_filter")

                    if filtro_cnpj_admin != "Todos":
                        filtrado_df = diagnosticos_df[diagnosticos_df["CNPJ"].astype(str) == filtro_cnpj_admin].sort_values(by="Data", ascending=False)
                        if not filtrado_df.empty:
                            st.dataframe(filtrado_df)
                            for _, row_f in filtrado_df.iterrows():
                                with st.expander(f"Detalhes: {row_f['Data']} - {row_f.get('Empresa', 'N/A')}"):
                                    st.markdown(f"**Média Geral:** {row_f.get('Média Geral', 'N/A')} | **GUT Média:** {row_f.get('GUT Média', 'N/A')}")
                                    st.markdown(f"**Resumo do Diagnóstico (Cliente):** {row_f.get('Diagnóstico', 'Não preenchido')}")
                                    st.markdown(f"**Observações (Consultor/Admin):** {row_f.get('Observações', 'Não preenchido')}")
                                    st.markdown(f"**Análise do Cliente:** {row_f.get('Análise do Cliente', 'Não preenchida')}")
                                    # Display other question-answer pairs
                                    st.markdown("**Respostas Detalhadas:**")
                                    for col_name, col_val in row_f.items():
                                        if col_name not in ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Média Geral Num"]:
                                            st.text(f"  {col_name}: {col_val}")
                        else:
                            st.info(f"Nenhum diagnóstico encontrado para o CNPJ {filtro_cnpj_admin}.")
                else:
                    st.info("Coluna 'CNPJ' não encontrada para permitir filtragem.")
            else:
                st.info("Nenhum diagnóstico encontrado no sistema ainda.")

    elif menu_admin == "Histórico de Usuários":
        st.subheader("📜 Histórico de Ações dos Clientes")
        try:
            historico_df = pd.read_csv(historico_csv, encoding='utf-8')
            st.dataframe(historico_df.sort_values(by="Data", ascending=False))
        except FileNotFoundError:
            st.info("Arquivo de histórico não encontrado ou vazio.")
        except pd.errors.EmptyDataError:
            st.info("O arquivo de histórico está vazio.")


    elif menu_admin == "Gerenciar Usuários Clientes":
        st.subheader("👥 Gerenciar Usuários Clientes")
        try:
            usuarios_clientes_df = pd.read_csv(usuarios_csv, encoding='utf-8')
            st.caption(f"Total de clientes: {len(usuarios_clientes_df)}")
            st.dataframe(usuarios_clientes_df)
        except FileNotFoundError:
            st.info("Arquivo de usuários não encontrado. Adicione um usuário para criar o arquivo.")
            usuarios_clientes_df = pd.DataFrame(columns=["CNPJ", "Senha", "Empresa"])
        except pd.errors.EmptyDataError:
            st.info("Nenhum usuário cliente cadastrado.")
            usuarios_clientes_df = pd.DataFrame(columns=["CNPJ", "Senha", "Empresa"])


        st.markdown("---")
        st.subheader("➕ Adicionar Novo Usuário Cliente")
        with st.form("form_novo_usuario_cliente"):
            novo_cnpj_cliente = st.text_input("CNPJ do cliente")
            nova_senha_cliente = st.text_input("Senha para o cliente", type="password")
            nova_empresa_cliente = st.text_input("Nome da empresa cliente")
            adicionar_cliente_btn = st.form_submit_button("Adicionar Cliente")

        if adicionar_cliente_btn:
            if novo_cnpj_cliente and nova_senha_cliente and nova_empresa_cliente:
                if novo_cnpj_cliente in usuarios_clientes_df["CNPJ"].astype(str).values:
                     st.error(f"CNPJ {novo_cnpj_cliente} já cadastrado.")
                else:
                    novo_usuario_data = pd.DataFrame([[novo_cnpj_cliente, nova_senha_cliente, nova_empresa_cliente]], columns=["CNPJ", "Senha", "Empresa"])
                    usuarios_clientes_df = pd.concat([usuarios_clientes_df, novo_usuario_data], ignore_index=True)
                    usuarios_clientes_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
                    st.success(f"Cliente '{nova_empresa_cliente}' adicionado com sucesso!")
                    st.rerun()
            else:
                st.warning("Preencha todos os campos para adicionar um novo cliente.")
        
        st.markdown("---")
        st.subheader("🚫 Gerenciar Usuários Bloqueados")
        try:
            bloqueados_df = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
        except FileNotFoundError:
            bloqueados_df = pd.DataFrame(columns=["CNPJ"])
        
        st.write("CNPJs atualmente bloqueados:", bloqueados_df["CNPJ"].tolist() if not bloqueados_df.empty else "Nenhum")

        col_block, col_unblock = st.columns(2)
        with col_block:
            cnpj_para_bloquear = st.selectbox("Selecione CNPJ para BLOQUEAR:", [""] + usuarios_clientes_df["CNPJ"].astype(str).unique().tolist(), key="block_cnpj")
            if st.button("Bloquear CNPJ Selecionado") and cnpj_para_bloquear:
                if cnpj_para_bloquear not in bloqueados_df["CNPJ"].astype(str).values:
                    nova_block = pd.DataFrame([[cnpj_para_bloquear]], columns=["CNPJ"])
                    bloqueados_df = pd.concat([bloqueados_df, nova_block], ignore_index=True)
                    bloqueados_df.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                    st.success(f"CNPJ {cnpj_para_bloquear} bloqueado.")
                    st.rerun()
                else:
                    st.warning(f"CNPJ {cnpj_para_bloquear} já está bloqueado.")
        
        with col_unblock:
            cnpj_para_desbloquear = st.selectbox("Selecione CNPJ para DESBLOQUEAR:", [""] + bloqueados_df["CNPJ"].astype(str).unique().tolist(), key="unblock_cnpj")
            if st.button("Desbloquear CNPJ Selecionado") and cnpj_para_desbloquear:
                bloqueados_df = bloqueados_df[bloqueados_df["CNPJ"].astype(str) != cnpj_para_desbloquear]
                bloqueados_df.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                st.success(f"CNPJ {cnpj_para_desbloquear} desbloqueado.")
                st.rerun()
                
    elif menu_admin == "Gerenciar Administradores":
        st.subheader("👮 Gerenciar Usuários Administradores")
        try:
            admins_df = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
        except FileNotFoundError:
            st.info("Arquivo de administradores não encontrado. Adicione um para criar.")
            admins_df = pd.DataFrame(columns=["Usuario", "Senha"])
        
        st.dataframe(admins_df[["Usuario"]]) # Show only usernames

        st.markdown("---")
        st.subheader("➕ Adicionar Novo Administrador")
        with st.form("form_novo_admin"):
            novo_admin_user = st.text_input("Nome de Usuário do novo Admin")
            novo_admin_pass = st.text_input("Senha para o novo Admin", type="password")
            adicionar_admin_btn = st.form_submit_button("Adicionar Administrador")

        if adicionar_admin_btn:
            if novo_admin_user and novo_admin_pass:
                if novo_admin_user in admins_df["Usuario"].values:
                    st.error(f"Usuário '{novo_admin_user}' já existe.")
                else:
                    novo_admin_data = pd.DataFrame([[novo_admin_user, novo_admin_pass]], columns=["Usuario", "Senha"])
                    admins_df = pd.concat([admins_df, novo_admin_data], ignore_index=True)
                    admins_df.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                    st.success(f"Administrador '{novo_admin_user}' adicionado!")
                    st.rerun()
            else:
                st.warning("Preencha todos os campos para adicionar um novo administrador.")

        st.markdown("---")
        st.subheader("🗑️ Remover Administrador")
        if not admins_df.empty:
            admin_para_remover = st.selectbox("Selecione o administrador para remover:", options=[""] + admins_df["Usuario"].tolist(), key="remove_admin_select")
            if st.button("Remover Administrador Selecionado", type="primary") and admin_para_remover:
                # Prevent self-removal or removal of last admin if desired (add logic here)
                if len(admins_df) == 1 and admin_para_remover == admins_df["Usuario"].iloc[0]:
                    st.error("Não é possível remover o único administrador.")
                # elif admin_para_remover == st.session_state.get("admin_user_logged_in"): # Need to store current admin user in session state for this
                # st.error("Não é possível remover a si mesmo.")
                else:
                    admins_df = admins_df[admins_df["Usuario"] != admin_para_remover]
                    admins_df.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                    st.warning(f"Administrador '{admin_para_remover}' removido.")
                    st.rerun()
        else:
            st.info("Nenhum administrador para remover.")


# Fallback for any state not covered (should ideally not be reached if logic is sound)
if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()