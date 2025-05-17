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

st.title("\U0001F512 Portal de Acesso")

# Variáveis de arquivos
admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv"
historico_csv = "historico_clientes.csv"

# Inicialização de estados
for key, default in [
    ("admin_logado", False),
    ("cliente_logado", False),
    ("diagnostico_enviado", False),
    ("inicio_sessao_cliente", None),
    ("trigger_cliente_rerun", False),
    ("trigger_admin_rerun", False)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Garantir que os arquivos existam
for arquivo, colunas in [
    (usuarios_bloqueados_csv, ["CNPJ"]),
    (admin_credenciais_csv, ["Usuario", "Senha"]),
    (usuarios_csv, ["CNPJ", "Senha", "Empresa"]),
    (arquivo_csv, ["Data", "CNPJ", "Nome", "Email", "Empresa", "Financeiro", "Processos", "Marketing", "Vendas", "Equipe", "Média Geral", "Observações", "Diagnóstico"]),
    (perguntas_csv, ["Pergunta"]),
    (historico_csv, ["Data", "CNPJ", "Ação", "Descrição"]),
]:
    if not os.path.exists(arquivo):
        pd.DataFrame(columns=colunas).to_csv(arquivo, index=False)

# Função para registrar ações dos usuários

def registrar_acao(cnpj, acao, descricao):
    historico = pd.read_csv(historico_csv)
    nova = pd.DataFrame([{ "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }])
    historico = pd.concat([historico, nova], ignore_index=True)
    historico.to_csv(historico_csv, index=False)

# Redirecionamento seguro após login
if st.session_state.get("trigger_cliente_rerun"):
    st.session_state.trigger_cliente_rerun = False
    st.experimental_rerun()
    st.stop()
if st.session_state.get("trigger_admin_rerun"):
    st.session_state.trigger_admin_rerun = False
    st.experimental_rerun()
    st.stop()

# Login de Acesso
if not st.session_state.admin_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True)
else:
    aba = "Administrador"

# Login Administrador
if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")
    if entrar:
        df_admin = pd.read_csv(admin_credenciais_csv)
        if not df_admin[(df_admin["Usuario"] == usuario) & (df_admin["Senha"] == senha)].empty:
            st.session_state.admin_logado = True
            st.success("Login de administrador realizado com sucesso!")
            st.session_state.trigger_admin_rerun = True
            st.stop()
        else:
            st.error("Usuário ou senha inválidos.")
    st.markdown('</div>', unsafe_allow_html=True)

# Login Cliente
if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente"):
        cnpj = st.text_input("CNPJ")
        senha = st.text_input("Senha", type="password")
        acessar = st.form_submit_button("Entrar")
    if acessar:
        if not os.path.exists(usuarios_csv):
            st.error("Base de usuários não encontrada.")
            st.stop()
        usuarios = pd.read_csv(usuarios_csv)
        bloqueados = pd.read_csv(usuarios_bloqueados_csv)
        if cnpj in bloqueados["CNPJ"].values:
            st.error("Este CNPJ está bloqueado. Solicite liberação ao administrador.")
            st.stop()
        user = usuarios[(usuarios["CNPJ"] == cnpj) & (usuarios["Senha"] == senha)]
        if user.empty:
            st.error("CNPJ ou senha inválidos.")
            st.stop()
        st.session_state.cliente_logado = True
        st.session_state.cnpj = cnpj
        st.session_state.user = user
        st.session_state.inicio_sessao_cliente = time.time()
        registrar_acao(cnpj, "Login", "Usuário realizou login no sistema.")
        st.success("Login realizado com sucesso!")
        st.session_state.trigger_cliente_rerun = True
        st.stop()
    st.markdown('</div>', unsafe_allow_html=True)

# Instruções e acesso ao diagnóstico
if aba == "Cliente" and st.session_state.cliente_logado:
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
        if st.button("Ir para Diagnóstico"):
            st.session_state.pular_para_diagnostico = True
    else:
        st.warning("Você precisa confirmar ciência das instruções para acessar o diagnóstico.")

# Formulário de diagnóstico
if aba == "Cliente" and st.session_state.cliente_logado and st.session_state.get("pular_para_diagnostico"):
    st.subheader("📋 Formulário de Diagnóstico")
    perguntas = pd.read_csv(perguntas_csv)
    respostas = {}
    total_perguntas = len(perguntas)
    respondidas = 0
    for i, row in perguntas.iterrows():
        texto = row["Pergunta"]
        if "Pontuação (0-5) + Matriz GUT" in texto:
            respostas[texto] = st.slider(texto, 0, 5, key=f"q_{i}")
            respondidas += 1 if respostas[texto] != 0 else 0
        elif "Pontuação (0-10)" in texto:
            respostas[texto] = st.slider(texto, 0, 10, key=f"q_{i}")
            respondidas += 1 if respostas[texto] != 0 else 0
        elif "Texto Aberto" in texto:
            respostas[texto] = st.text_area(texto, key=f"q_{i}")
            respondidas += 1 if respostas[texto].strip() != "" else 0
        elif "Escala" in texto:
            respostas[texto] = st.selectbox(texto, ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"], key=f"q_{i}")
            respondidas += 1 if respostas[texto] != "" else 0
        else:
            respostas[texto] = st.slider(texto, 0, 10, key=f"q_{i}")
            respondidas += 1 if respostas[texto] != 0 else 0

    st.info(f"📊 Progresso: {respondidas} de {total_perguntas} perguntas respondidas ({round((respondidas / total_perguntas) * 100)}%)")
    observacoes = st.text_area("Observações Gerais")
    diagnostico_texto = st.text_area("Resumo do Diagnóstico (para PDF)")

    if st.button("Enviar Diagnóstico"):
        gut_perguntas = {k: v for k, v in respostas.items() if "Pontuação (0-5) + Matriz GUT" in k and isinstance(v, int)}
        gut_total = sum(gut_perguntas.values())
        gut_media = round(gut_total / len(gut_perguntas), 2) if gut_perguntas else 0
        dados = pd.read_csv(usuarios_csv)
        empresa = dados.loc[dados["CNPJ"] == st.session_state.cnpj, "Empresa"].values[0]
        media = round(sum([v for v in respostas.values() if isinstance(v, (int, float))]) / len(respostas), 2)
        nova_linha = {
            "GUT Média": gut_media,
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "CNPJ": st.session_state.cnpj,
            "Nome": st.session_state.user["CNPJ"].values[0],
            "Email": "",
            "Empresa": empresa,
            "Média Geral": media,
            "Observações": observacoes,
            "Diagnóstico": diagnostico_texto
        }
        nova_linha.update(respostas)
        df = pd.read_csv(arquivo_csv)
        df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        df.to_csv(arquivo_csv, index=False)
        st.success("Diagnóstico enviado com sucesso!")

        # Gerar PDF com FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Diagnóstico - {empresa}", ln=True)
        pdf.cell(200, 10, txt=f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.cell(200, 10, txt=f"CNPJ: {st.session_state.cnpj}", ln=True)
        pdf.cell(200, 10, txt=f"Média Geral: {media}", ln=True)
        pdf.cell(200, 10, txt=f"GUT Média: {gut_media}", ln=True)
        pdf.multi_cell(0, 10, txt=f"Resumo do Diagnóstico:\n{diagnostico_texto}")

        for k, v in respostas.items():
            if isinstance(v, (int, float, str)):
                pdf.multi_cell(0, 10, txt=f"{k}: {v}")

        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_pdf.name)

        with open(temp_pdf.name, "rb") as f:
            st.download_button("📄 Baixar PDF do Diagnóstico", f, file_name=f"diagnostico_{empresa}.pdf")

        registrar_acao(st.session_state.cnpj, "Envio", "Cliente enviou diagnóstico.")
        registrar_acao(st.session_state.cnpj, "Download", "Cliente baixou o PDF do diagnóstico.")
        st.session_state.diagnostico_enviado = True
        st.stop()

# Função de logout
if st.session_state.admin_logado:
    if st.sidebar.button("🚪 Sair (Admin)"):
        st.session_state.admin_logado = False
        st.experimental_rerun()
if st.session_state.cliente_logado:
    if st.sidebar.button("🚪 Sair (Cliente)"):
        st.session_state.cliente_logado = False
        st.experimental_rerun()

# Painel Administrativo
if st.session_state.admin_logado:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Menu Administrativo")
    menu_admin = st.sidebar.selectbox("Escolha uma opção:", [
        "Visualizar Diagnósticos",
        "Gerenciar Perguntas",
        "Gerenciar Usuários",
        "Histórico de Ações"
    ])

    st.success("Painel Administrativo Ativo")

    if menu_admin == "Visualizar Diagnósticos":
        import matplotlib.pyplot as plt
        import seaborn as sns
        st.subheader("📊 Diagnósticos Recebidos")
        if os.path.exists(arquivo_csv):
            df = pd.read_csv(arquivo_csv)
            if df.empty:
                st.info("Nenhum diagnóstico registrado.")
            else:
                st.dataframe(df.sort_values(by="Data", ascending=False))
                st.download_button("⬇️ Baixar Diagnósticos", df.to_csv(index=False).encode("utf-8"), file_name="diagnosticos.csv", mime="text/csv")
                st.subheader("🏆 Ranking de Empresas")
                ranking = df.groupby("Empresa")["Média Geral"].mean().sort_values(ascending=False).reset_index()
                ranking.index = ranking.index + 1
                st.dataframe(ranking.rename(columns={"Média Geral": "Média Geral (Ranking)"}))

                st.subheader("📈 Evolução Temporal de Diagnósticos")
                df["Data"] = pd.to_datetime(df["Data"], errors='coerce')
                df = df.dropna(subset=["Data"])
                df_mes = df.copy()
                df_mes["Mês"] = df_mes["Data"].dt.to_period("M").astype(str)
                resumo = df_mes.groupby("Mês").agg({"CNPJ": "count", "Média Geral": "mean", "GUT Média": "mean"}).reset_index()

                col1, col2 = st.columns(2)
                with col1:
                    st.bar_chart(resumo.set_index("Mês")["CNPJ"], height=300, use_container_width=True)
                with col2:
                    st.line_chart(resumo.set_index("Mês")[["Média Geral", "GUT Média"]], height=300, use_container_width=True)

                st.subheader("🔍 Filtrar por Empresa")
                empresas = df["Empresa"].dropna().unique().tolist()
                empresa_selecionada = st.selectbox("Selecione a empresa para análise comparativa:", ["Todas"] + empresas)
                if empresa_selecionada != "Todas":
                    df_empresa = df[df["Empresa"] == empresa_selecionada].sort_values(by="Data")
                    st.line_chart(df_empresa.set_index("Data")[["Média Geral", "GUT Média"]], height=300)
                    st.subheader(f"💬 Diagnósticos e Observações - {empresa_selecionada}")
                    for _, row in df_empresa.iterrows():
                        st.markdown(f"**{row['Data']}** — Média Geral: {row['Média Geral']}, GUT: {row['GUT Média']}")
                        st.markdown(f"> {row['Diagnóstico']}")
                        st.markdown(f"*Obs:* {row['Observações']}")
                        st.markdown("---")(resumo.set_index("Mês")[["Média Geral", "GUT Média"]], height=300, use_container_width=True)

    elif menu_admin == "Gerenciar Perguntas":
        st.subheader("📝 Perguntas do Diagnóstico")
        tabs = st.tabs(["📄 Perguntas Atuais", "➕ Nova Pergunta"])

        with tabs[0]:
            perguntas = pd.read_csv(perguntas_csv)
            for i, row in perguntas.iterrows():
                col1, col2, col3 = st.columns([6, 1, 1])
                with col1:
                    nova = st.text_input(f"Pergunta {i+1}", value=row["Pergunta"], key=f"edit_{i}")
                    perguntas.at[i, "Pergunta"] = nova
                with col2:
                    if st.button("💾", key=f"save_{i}"):
                        perguntas.to_csv(perguntas_csv, index=False)
                        st.success("Pergunta atualizada.")
                with col3:
                    if st.button("🗑️", key=f"del_{i}"):
                        perguntas = perguntas.drop(i).reset_index(drop=True)
                        perguntas.to_csv(perguntas_csv, index=False)
                        st.warning("Pergunta removida.")

        with tabs[1]:
            with st.form("form_add_pergunta"):
                nova = st.text_input("Digite a nova pergunta")
                tipo = st.selectbox("Tipo da pergunta", ["Pontuação (0-10)", "Texto Aberto", "Escala", "Pontuação (0-5) + Matriz GUT"])
                submit = st.form_submit_button("Adicionar")
                if submit and nova.strip():
                    df = pd.read_csv(perguntas_csv)
                    df = pd.concat([df, pd.DataFrame([[f"{nova} [{tipo}]"]], columns=["Pergunta"])], ignore_index=True)
                    df.to_csv(perguntas_csv, index=False)
                    st.success("Pergunta adicionada com sucesso!")

    elif menu_admin == "Gerenciar Usuários":
        st.subheader("👥 Usuários Clientes")
        usuarios_df = pd.read_csv(usuarios_csv)
        st.dataframe(usuarios_df)

        with st.form("form_novo_user"):
            novo_cnpj = st.text_input("CNPJ")
            nova_senha = st.text_input("Senha", type="password")
            nova_empresa = st.text_input("Empresa")
            if st.form_submit_button("Adicionar Cliente"):
                if novo_cnpj and nova_senha and nova_empresa:
                    novo = pd.DataFrame([[novo_cnpj, nova_senha, nova_empresa]], columns=["CNPJ", "Senha", "Empresa"])
                    usuarios_df = pd.concat([usuarios_df, novo], ignore_index=True)
                    usuarios_df.to_csv(usuarios_csv, index=False)
                    st.success("Cliente adicionado com sucesso!")
                else:
                    st.warning("Preencha todos os campos.")

    elif menu_admin == "Histórico de Ações":
        st.subheader("📜 Histórico de Ações dos Clientes")
        historico = pd.read_csv(historico_csv)
        st.dataframe(historico.sort_values(by="Data", ascending=False))
