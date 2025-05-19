import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import time
from fpdf import FPDF
import tempfile

st.set_page_config(page_title="Portal de Diagnóstico", layout="centered")

# CSS e estilo
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
</style>
""", unsafe_allow_html=True)

# Arquivos e variáveis
admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv"
historico_csv = "historico_clientes.csv"

rerun_flag = False
if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state:
    st.session_state.cliente_logado = False

# Criação de arquivos base
for arquivo, colunas in [
    (usuarios_bloqueados_csv, ["CNPJ"]),
    (admin_credenciais_csv, ["Usuario", "Senha"]),
    (usuarios_csv, ["CNPJ", "Senha", "Empresa"]),
    (arquivo_csv, ["Data", "CNPJ", "Nome", "Email", "Empresa", "Financeiro", "Processos", "Marketing", "Vendas", "Equipe", "Média Geral", "GUT Média", "Observações", "Diagnóstico"]),
    (perguntas_csv, ["Pergunta"]),
    (historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
]:
    if not os.path.exists(arquivo):
        pd.DataFrame(columns=colunas).to_csv(arquivo, index=False)

# Função para histórico
def registrar_acao(cnpj, acao, descricao):
    historico = pd.read_csv(historico_csv)
    nova = pd.DataFrame([{ "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }])
    historico = pd.concat([historico, nova], ignore_index=True)
    historico.to_csv(historico_csv, index=False)

# Reexecução segura
if st.session_state.get("trigger_cliente_rerun"):
    st.session_state.trigger_cliente_rerun = False
    rerun_flag = True
if st.session_state.get("trigger_admin_rerun"):
    st.session_state.trigger_admin_rerun = False
    rerun_flag = True

# Título e aba
st.title("🔒 Portal de Diagnóstico")
aba = "Administrador" if st.session_state.admin_logado else st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True)

# LOGIN ADMINISTRADOR
if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    with st.form("form_admin"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            df_admin = pd.read_csv(admin_credenciais_csv)
            if not df_admin[(df_admin.Usuario == usuario) & (df_admin.Senha == senha)].empty:
                st.session_state.admin_logado = True
                st.session_state.trigger_admin_rerun = True
                st.success("Login de administrador realizado com sucesso!")
                st.stop()
            else:
                st.error("Usuário ou senha inválidos.")
    st.markdown('</div>', unsafe_allow_html=True)

# LOGIN CLIENTE
if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    with st.form("form_cliente"):
        cnpj = st.text_input("CNPJ")
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if not os.path.exists(usuarios_csv):
                st.error("Base de usuários não encontrada.")
                st.stop()
            usuarios = pd.read_csv(usuarios_csv)
            bloqueados = pd.read_csv(usuarios_bloqueados_csv)
            if cnpj in bloqueados.CNPJ.values:
                st.error("Este CNPJ está bloqueado. Solicite liberação ao administrador.")
                st.stop()
            user = usuarios[(usuarios.CNPJ == cnpj) & (usuarios.Senha == senha)]
            if user.empty:
                st.error("CNPJ ou senha inválidos.")
                st.stop()
            st.session_state.cliente_logado = True
            st.session_state.cnpj = cnpj
            st.session_state.user = user
            registrar_acao(cnpj, "Login", "Usuário realizou login no sistema.")
            st.session_state.trigger_cliente_rerun = True
            st.success("Login realizado com sucesso!")
            st.stop()
    st.markdown('</div>', unsafe_allow_html=True)

# FORMULÁRIO DE DIAGNÓSTICO
if aba == "Cliente" and st.session_state.cliente_logado:
    st.header("📝 Novo Diagnóstico")
    perguntas = pd.read_csv(perguntas_csv)
    respostas = {}
    for i, row in perguntas.iterrows():
        texto = row["Pergunta"]
        if "Pontuação (0-5) + Matriz GUT" in texto:
            respostas[texto] = st.slider(texto, 0, 5, key=f"q_{i}")
        elif "Pontuação (0-10)" in texto:
            respostas[texto] = st.slider(texto, 0, 10, key=f"q_{i}")
        elif "Texto Aberto" in texto:
            respostas[texto] = st.text_area(texto, key=f"q_{i}")
        elif "Escala" in texto:
            respostas[texto] = st.selectbox(texto, ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"], key=f"q_{i}")
        else:
            respostas[texto] = st.slider(texto, 0, 10, key=f"q_{i}")

    observacoes = st.text_area("Observações Gerais")
    diagnostico_texto = st.text_area("Resumo do Diagnóstico (para PDF)")

    if st.button("Enviar Diagnóstico"):
        gut_perguntas = {k: v for k, v in respostas.items() if "Pontuação (0-5) + Matriz GUT" in k and isinstance(v, int)}
        gut_media = round(sum(gut_perguntas.values()) / len(gut_perguntas), 2) if gut_perguntas else 0
        dados = pd.read_csv(usuarios_csv)
        empresa = dados.loc[dados["CNPJ"] == st.session_state.cnpj, "Empresa"].values[0]
        media = round(sum([v for v in respostas.values() if isinstance(v, (int, float))]) / len(respostas), 2)
        nova_linha = {
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "CNPJ": st.session_state.cnpj,
            "Nome": st.session_state.user["CNPJ"].values[0],
            "Email": "",
            "Empresa": empresa,
            "Média Geral": media,
            "GUT Média": gut_media,
            "Observações": observacoes,
            "Diagnóstico": diagnostico_texto,
        }
        nova_linha.update(respostas)
        df = pd.read_csv(arquivo_csv)
        df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        df.to_csv(arquivo_csv, index=False)
        registrar_acao(st.session_state.cnpj, "Envio", "Cliente enviou diagnóstico")
        st.success("Diagnóstico enviado com sucesso!")

        # PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, f"Diagnóstico - {empresa}
CNPJ: {st.session_state.cnpj}
Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        pdf.multi_cell(0, 10, f"Média Geral: {media}
GUT Média: {gut_media}")
        pdf.multi_cell(0, 10, f"Resumo do Diagnóstico:
{diagnostico_texto}")
        for k, v in respostas.items():
            pdf.multi_cell(0, 10, f"{k}: {v}")
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_pdf.name)
        with open(temp_pdf.name, "rb") as f:
            st.download_button("📄 Baixar PDF do Diagnóstico", f, file_name=f"diagnostico_{empresa}.pdf")

# HISTÓRICO E COMPARATIVO DO CLIENTE
if aba == "Cliente" and st.session_state.cliente_logado:
    st.subheader("📁 Diagnósticos Anteriores")
    df_antigos = pd.read_csv(arquivo_csv)
    df_cliente = df_antigos[df_antigos["CNPJ"] == st.session_state.cnpj]
    if not df_cliente.empty:
        df_cliente["Data"] = pd.to_datetime(df_cliente["Data"])
        col_filtro = st.multiselect("Filtrar Indicadores", options=[col for col in df_cliente.columns if col not in ["Data", "CNPJ", "Nome", "Email", "Empresa", "Observações", "Diagnóstico"]], default=["Média Geral", "GUT Média"])
        if col_filtro:
            fig = px.line(df_cliente, x="Data", y=col_filtro, markers=True, title="Evolução dos Indicadores")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("📊 Comparativo Entre Diagnósticos")
        opcoes = df_cliente["Data"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
        if len(opcoes) >= 2:
            diag_atual = st.selectbox("Diagnóstico Atual", opcoes, index=len(opcoes)-1)
            diag_anterior = st.selectbox("Diagnóstico Anterior", opcoes, index=max(len(opcoes)-2, 0))
            atual = df_cliente[df_cliente["Data"].dt.strftime("%Y-%m-%d %H:%M:%S") == diag_atual].iloc[0]
            anterior = df_cliente[df_cliente["Data"].dt.strftime("%Y-%m-%d %H:%M:%S") == diag_anterior].iloc[0]
            variaveis = [col for col in df_cliente.columns if col not in ["Data", "CNPJ", "Nome", "Email", "Empresa", "Observações", "Diagnóstico"]]
            comparativo = pd.DataFrame({
                "Indicador": variaveis,
                "Anterior": [anterior[v] for v in variaveis],
                "Atual": [atual[v] for v in variaveis],
                "Evolução": ["🔼 Melhorou" if atual[v] > anterior[v] else ("🔽 Piorou" if atual[v] < anterior[v] else "➖ Igual") for v in variaveis]
            })
            st.dataframe(comparativo)
            st.download_button("⬇️ Exportar Comparativo", comparativo.to_csv(index=False).encode("utf-8"), file_name="comparativo_diagnostico.csv")

# PAINEL ADMINISTRATIVO
if aba == "Administrador" and st.session_state.admin_logado:
    st.subheader("📊 Painel Administrativo")
    menu_admin = st.selectbox("Menu", ["Visualizar Diagnósticos", "Ranking por Empresa", "Gerenciar Perguntas", "Gerenciar Usuários", "Histórico de Ações"])

    if menu_admin == "Visualizar Diagnósticos":
        if os.path.exists(arquivo_csv):
            df = pd.read_csv(arquivo_csv)
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
            st.dataframe(df.sort_values(by="Data", ascending=False))

    elif menu_admin == "Ranking por Empresa":
        if os.path.exists(arquivo_csv):
            df = pd.read_csv(arquivo_csv)
            ranking = df.groupby("Empresa")["Média Geral"].mean().sort_values(ascending=False).reset_index()
            ranking.index += 1
            st.dataframe(ranking.rename(columns={"Média Geral": "Média Geral (Ranking)"}))

    elif menu_admin == "Gerenciar Perguntas":
        perguntas = pd.read_csv(perguntas_csv)
        st.subheader("✏️ Perguntas do Diagnóstico")
        for i, row in perguntas.iterrows():
            st.text_input(f"Pergunta {i+1}", value=row["Pergunta"], key=f"pergunta_{i}")
        if st.button("Salvar Perguntas"):
            novas = [st.session_state[f"pergunta_{i}"] for i in range(len(perguntas))]
            pd.DataFrame({"Pergunta": novas}).to_csv(perguntas_csv, index=False)
            st.success("Perguntas atualizadas.")

    elif menu_admin == "Gerenciar Usuários":
        usuarios = pd.read_csv(usuarios_csv)
        st.subheader("👥 Usuários Clientes")
        st.dataframe(usuarios)
        with st.form("novo_usuario"):
            cnpj = st.text_input("CNPJ")
            senha = st.text_input("Senha")
            empresa = st.text_input("Empresa")
            if st.form_submit_button("Adicionar Usuário"):
                novos = pd.DataFrame([[cnpj, senha, empresa]], columns=usuarios.columns)
                usuarios = pd.concat([usuarios, novos], ignore_index=True)
                usuarios.to_csv(usuarios_csv, index=False)
                st.success("Usuário adicionado.")

    elif menu_admin == "Histórico de Ações":
        if os.path.exists(historico_csv):
            historico = pd.read_csv(historico_csv)
            st.subheader("📜 Histórico de Atividades")
            st.dataframe(historico.sort_values(by="Data", ascending=False))

# Rerun final
if rerun_flag:
    st.experimental_rerun()
