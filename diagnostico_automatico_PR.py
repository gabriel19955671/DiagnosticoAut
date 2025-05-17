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

st.title("🔐 Portal de Acesso")

# Arquivos e dados necessários
USERS_FILE = "usuarios.csv"
ADMINS_FILE = "admins.csv"
PERGUNTAS_FILE = "perguntas_formulario.csv"
DIAGNOSTICOS_FILE = "diagnosticos_clientes.csv"

# Garante que os arquivos existam
for file, cols in [
    (USERS_FILE, ["CNPJ", "Senha", "Empresa"]),
    (ADMINS_FILE, ["Usuario", "Senha"]),
    (PERGUNTAS_FILE, ["Pergunta"]),
    (DIAGNOSTICOS_FILE, ["Data", "CNPJ", "Empresa", "Diagnóstico", "Média", "Observações"])
]:
    if not os.path.exists(file):
        pd.DataFrame(columns=cols).to_csv(file, index=False)

# Estado de sessão
if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state:
    st.session_state.cliente_logado = False

# LOGIN
aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True)

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            df_admin = pd.read_csv(ADMINS_FILE)
            if not df_admin[(df_admin.Usuario == usuario) & (df_admin.Senha == senha)].empty:
                st.session_state.admin_logado = True
                st.success("Administrador logado com sucesso.")
            else:
                st.error("Usuário ou senha incorretos.")
    st.markdown('</div>', unsafe_allow_html=True)

elif aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente"):
        cnpj = st.text_input("CNPJ")
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            df = pd.read_csv(USERS_FILE)
            user = df[(df.CNPJ == cnpj) & (df.Senha == senha)]
            if not user.empty:
                st.session_state.cliente_logado = True
                st.session_state.cnpj = cnpj
                st.session_state.empresa = user.iloc[0]["Empresa"]
                st.success("Cliente logado com sucesso.")
            else:
                st.error("CNPJ ou senha inválidos.")
    st.markdown('</div>', unsafe_allow_html=True)

# FORMULÁRIO DO CLIENTE
if st.session_state.cliente_logado:
    st.header("📋 Formulário de Diagnóstico")
    perguntas = pd.read_csv(PERGUNTAS_FILE)
    respostas = {}
    for i, row in perguntas.iterrows():
        respostas[row["Pergunta"]] = st.slider(row["Pergunta"], 0, 10, 5)

    observacoes = st.text_area("Observações")
    if st.button("Enviar Diagnóstico"):
        media = sum(respostas.values()) / len(respostas)
        novo = pd.DataFrame([{
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "CNPJ": st.session_state.cnpj,
            "Empresa": st.session_state.empresa,
            "Diagnóstico": str(respostas),
            "Média": round(media, 2),
            "Observações": observacoes
        }])
        df_antigo = pd.read_csv(DIAGNOSTICOS_FILE)
        df = pd.concat([df_antigo, novo], ignore_index=True)
        df.to_csv(DIAGNOSTICOS_FILE, index=False)
        st.success("Diagnóstico enviado com sucesso!")

        # Gerar PDF com FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Diagnóstico - {st.session_state.empresa}", ln=True)
        pdf.cell(200, 10, txt=f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.cell(200, 10, txt=f"CNPJ: {st.session_state.cnpj}", ln=True)
        pdf.cell(200, 10, txt=f"Média Geral: {round(media, 2)}", ln=True)
        pdf.multi_cell(0, 10, txt=f"Resumo:\n{observacoes}")
        for k, v in respostas.items():
            pdf.multi_cell(0, 10, txt=f"{k}: {v}")

        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_pdf.name)
        with open(temp_pdf.name, "rb") as f:
            st.download_button("📄 Baixar PDF do Diagnóstico", f, file_name=f"diagnostico_{st.session_state.empresa}.pdf")

# PAINEL ADMINISTRATIVO
if st.session_state.admin_logado:
    st.header("📊 Painel Administrativo")
    op = st.selectbox("Escolha uma funcionalidade:", ["Visualizar Diagnósticos", "Cadastrar Pergunta"])

    if op == "Visualizar Diagnósticos":
        df = pd.read_csv(DIAGNOSTICOS_FILE)
        st.dataframe(df)

    elif op == "Cadastrar Pergunta":
        with st.form("form_nova"):
            nova = st.text_input("Digite a nova pergunta")
            if st.form_submit_button("Salvar"):
                if nova.strip():
                    df = pd.read_csv(PERGUNTAS_FILE)
                    df.loc[len(df)] = [nova.strip()]
                    df.to_csv(PERGUNTAS_FILE, index=False)
                    st.success("Pergunta adicionada com sucesso!")
