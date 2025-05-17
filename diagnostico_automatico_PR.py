import streamlit as st
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF
import tempfile

st.set_page_config(page_title="Portal de Diagnóstico", layout="centered")

admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv"

if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state:
    st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state:
    st.session_state.diagnostico_enviado = False

# Criar arquivos base caso não existam
for arquivo, colunas in [
    (usuarios_bloqueados_csv, ["CNPJ"]),
    (admin_credenciais_csv, ["Usuario", "Senha"]),
    (usuarios_csv, ["CNPJ", "Senha", "Empresa"]),
    (
        arquivo_csv,
        [
            "Data", "CNPJ", "Nome", "Email", "Empresa", "Financeiro",
            "Processos", "Marketing", "Vendas", "Equipe", "Média Geral",
            "Observações", "Diagnóstico",
        ],
    ),
    (perguntas_csv, ["Pergunta"]),
]:
    if not os.path.exists(arquivo):
        pd.DataFrame(columns=colunas).to_csv(arquivo, index=False)

# CSS
st.markdown("""
<style>
.login-container {
    max-width: 400px;
    margin: 60px auto 0 auto;
    padding: 40px;
    border-radius: 8px;
    background-color: #f0f2f6;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
h2.login-title {
    text-align: center;
    margin-bottom: 30px;
    font-weight: 700;
    font-size: 28px;
}
</style>
""", unsafe_allow_html=True)

st.title("🔒 Portal de Acesso")

# Aba
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
        st.success("Login realizado com sucesso!")
        st.stop()
    st.markdown('</div>', unsafe_allow_html=True)

# Painel Admin
if aba == "Administrador" and st.session_state.admin_logado:
    st.success("Painel Administrativo Ativo")
    menu_admin = st.selectbox(
        "Selecione a funcionalidade administrativa:",
        [
            "Visualizar Diagnósticos",
            "Reautorizar Cliente",
            "Gerenciar Usuários",
            "Gerenciar Bloqueios",
            "Gerenciar Administradores",
            "Gerenciar Perguntas do Formulário"
        ],
    )
    if st.sidebar.button("Sair do Painel Admin"):
        st.session_state.admin_logado = False
        st.experimental_rerun()

    if menu_admin == "Gerenciar Perguntas do Formulário":
        st.subheader("📝 Gerenciar Perguntas do Diagnóstico")
        perguntas = pd.read_csv(perguntas_csv)
        for i, row in perguntas.iterrows():
            nova = st.text_input(f"Pergunta {i+1}", value=row["Pergunta"], key=f"pergunta_{i}")
            perguntas.at[i, "Pergunta"] = nova
        if st.button("Salvar Perguntas"):
            perguntas.to_csv(perguntas_csv, index=False)
            st.success("Perguntas atualizadas com sucesso!")

# Painel Cliente
if aba == "Cliente" and st.session_state.cliente_logado:
    cnpj = st.session_state.cnpj
    user = st.session_state.user

    if st.session_state.diagnostico_enviado:
        st.success("✅ Diagnóstico já enviado. Obrigado!")
        with open(f"diagnostico_{cnpj}.pdf", "rb") as f:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📄 Baixar PDF do Diagnóstico",
                    f,
                    file_name="diagnostico.pdf",
                    mime="application/pdf",
                    key="download_pdf",
                )
            with col2:
                if st.button("Finalização do processo"):
                    st.session_state.cliente_logado = False
                    st.session_state.diagnostico_enviado = False
                    st.session_state.cnpj = None
                    st.session_state.user = None
                    st.experimental_rerun()
        st.stop()

    st.subheader("📌 Instruções do Diagnóstico")
    st.markdown("""
    - Avalie cada item com uma nota de 0 a 10.
    - Seja honesto em suas respostas para que o diagnóstico seja o mais fiel possível.
    - Após o preenchimento, você poderá baixar um PDF com o resultado.
    """)

    perguntas_form = pd.read_csv(perguntas_csv)
    respostas = {}

    with st.form("form_diagnostico"):
        logo_cliente = st.file_uploader("📎 Envie a logo da sua empresa (opcional)", type=["png", "jpg", "jpeg"])
        nome_empresa_custom = st.text_input("📝 Nome da sua empresa", value=user.iloc[0].get("Empresa", "Nome da Empresa"))
        nome = st.text_input("Nome completo")
        email = st.text_input("E-mail")

        for idx, row in perguntas_form.iterrows():
            respostas[row["Pergunta"]] = st.slider(row["Pergunta"], 0, 10, key=f"resposta_{idx}")

        observacoes = st.text_area("Observações adicionais (opcional)")
        enviado = st.form_submit_button("🚀 Enviar Diagnóstico")

    if enviado:
        st.session_state.diagnostico_enviado = True

        class PDF(FPDF):
            def header(self):
                if hasattr(self, "logo_path") and self.logo_path:
                    self.image(self.logo_path, x=10, y=8, w=30)
                self.set_font("Arial", "B", 16)
                self.cell(0, 10, "Diagnóstico Empresarial - Potencialize Resultados", ln=True, align="C")
                self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font("Arial", "I", 8)
                self.set_text_color(128)
                self.cell(0, 10, f"Potencialize Resultados - Diagnóstico Automático | Página {self.page_no()}", align="C")

        media_geral = round(sum(respostas.values()) / len(respostas), 2)
        insights = [f"{k} abaixo da média." for k, v in respostas.items() if v < 6]

        diagnostico_texto = "\n".join(insights) if insights else "Nenhuma área crítica identificada. Excelente desempenho geral."

        resposta = pd.DataFrame([{
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "CNPJ": cnpj,
            "Nome": nome,
            "Email": email,
            "Empresa": nome_empresa_custom,
            "Financeiro": respostas.get("Controle financeiro da empresa", 0),
            "Processos": respostas.get("Eficiência dos processos internos", 0),
            "Marketing": respostas.get("Presença e estratégia de marketing", 0),
            "Vendas": respostas.get("Resultado comercial (vendas/negociação)", 0),
            "Equipe": respostas.get("Desempenho da equipe/colaboradores", 0),
            "Média Geral": media_geral,
            "Observações": observacoes,
            "Diagnóstico": diagnostico_texto.replace("\n", " "),
        }])

        if os.path.exists(arquivo_csv):
            antigo = pd.read_csv(arquivo_csv)
            resultado = pd.concat([antigo, resposta], ignore_index=True)
        else:
            resultado = resposta

        resultado.to_csv(arquivo_csv, index=False)

        pdf = PDF()
        if logo_cliente is not None:
            img_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            img_temp.write(logo_cliente.read())
            img_temp.close()
            pdf.logo_path = img_temp.name
        else:
            pdf.logo_path = None

        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(0, 10, f"Nome: {nome}", ln=True)
        pdf.cell(0, 10, f"E-mail: {email}", ln=True)
        pdf.cell(0, 10, f"Empresa: {nome_empresa_custom}", ln=True)
        pdf.ln(5)
        for pergunta, nota in respostas.items():
            pdf.cell(0, 10, f"{pergunta}: {nota}", ln=True)
        pdf.ln(5)
        pdf.multi_cell(0, 10, f"Média Geral: {media_geral}\n\nObservações:\n{observacoes}\n\nDiagnóstico Automático:\n{diagnostico_texto}")
        pdf_output = f"diagnostico_{cnpj}.pdf"
        pdf.output(pdf_output)

        st.experimental_rerun()
