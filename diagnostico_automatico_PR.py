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

admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv"
historico_csv = "historico_clientes.csv"

if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state:
    st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state:
    st.session_state.diagnostico_enviado = False
if "inicio_sessao_cliente" not in st.session_state:
    st.session_state.inicio_sessao_cliente = None

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
    (historico_csv, ["Data", "CNPJ", "Ação", "Descrição"]),
]:
    if not os.path.exists(arquivo):
        pd.DataFrame(columns=colunas).to_csv(arquivo, index=False)

# Função de log de ações

def registrar_acao(cnpj, acao, descricao):
    historico = pd.read_csv(historico_csv)
    nova = pd.DataFrame([{"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao}])
    historico = pd.concat([historico, nova], ignore_index=True)
    historico.to_csv(historico_csv, index=False)

# Determina a aba com base na sessão ou na seleção do usuário
if not st.session_state.admin_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True)
else:
    aba = "Administrador"

# LOGIN ADMINISTRADOR
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

# LOGIN CLIENTE
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
        st.stop()
    st.markdown('</div>', unsafe_allow_html=True)

# Painel Administrativo
if aba == "Administrador" and st.session_state.admin_logado:
    if st.sidebar.button("Sair do Painel Admin"):
        st.session_state.admin_logado = False
        st.experimental_rerun()

    menu_admin = st.sidebar.selectbox(
        "Selecione a funcionalidade administrativa:",
        [
            "Visualizar Diagnósticos",
            "Histórico de Usuários",
            "Gerenciar Perguntas do Formulário",
            "Gerenciar Usuários"
        ],
    )
    if st.sidebar.button("🔄 Atualizar Página"):
        st.experimental_rerun(), 2)
        insights = [f"{k} abaixo da média." for k, v in respostas.items() if v < 6]
        diagnostico_texto = "\n".join(insights) if insights else "Nenhuma área crítica identificada. Excelente desempenho geral."

        resposta = pd.DataFrame([{
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "CNPJ": cnpj,
            "Nome": nome,
            "Email": email,
            "Empresa": nome_empresa,
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
                self.cell(0, 10, f"Potencialize Resultados - Página {self.page_no()}", align="C")

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
        pdf.cell(0, 10, f"Empresa: {nome_empresa}", ln=True)
        pdf.ln(5)
        for pergunta, nota in respostas.items():
            pdf.cell(0, 10, f"{pergunta}: {nota}", ln=True)
        pdf.ln(5)
        pdf.multi_cell(0, 10, f"Média Geral: {media_geral}\n\nObservações:\n{observacoes}\n\nDiagnóstico Automático:\n{diagnostico_texto}")
        pdf.output(f"diagnostico_{cnpj}.pdf")

        st.experimental_rerun()
