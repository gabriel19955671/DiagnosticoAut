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

    st.success("Painel Administrativo Ativo")

    if menu_admin == "Visualizar Diagnósticos":
        if os.path.exists(arquivo_csv):
            st.subheader("📊 Diagnósticos Enviados")
            diagnosticos = pd.read_csv(arquivo_csv)
            st.dataframe(diagnosticos.sort_values(by="Data", ascending=False))
        else:
            st.info("Nenhum diagnóstico encontrado.")

    elif menu_admin == "Histórico de Usuários":
        st.subheader("📜 Histórico de Ações dos Clientes")
        historico = pd.read_csv(historico_csv)
        st.dataframe(historico.sort_values(by="Data", ascending=False))

    elif menu_admin == "Gerenciar Perguntas do Formulário":
        tabs_perguntas = st.tabs(["📋 Perguntas Atuais", "➕ Adicionar Nova Pergunta"])

        with tabs_perguntas[0]:
            st.subheader("📋 Perguntas Atuais")
            perguntas = pd.read_csv(perguntas_csv)
            if perguntas.empty:
                st.info("Nenhuma pergunta cadastrada ainda.")
            else:
                st.dataframe(perguntas)

        with tabs_perguntas[1]:
            st.subheader("➕ Adicionar Nova Pergunta")
            nova_pergunta = st.text_input("Texto da Pergunta", key="nova_pergunta")
            tipo_pergunta = st.selectbox("Tipo de Pergunta", ["Pontuação (0-10)", "Texto Aberto", "Escala", "Matriz GUT"], key="tipo_pergunta")

            if tipo_pergunta == "Matriz GUT":
                st.markdown("Você poderá configurar a Matriz GUT baseada em outras perguntas do formulário após cadastro.")

            if st.button("Adicionar Pergunta", key="adicionar_pergunta"):
                if nova_pergunta.strip():
                df = pd.read_csv(perguntas_csv)
                nova = pd.DataFrame([[nova_pergunta + f" [{tipo_pergunta}]"]], columns=["Pergunta"])
                df = pd.concat([df, nova], ignore_index=True)
                df.to_csv(perguntas_csv, index=False)
                st.success("Pergunta adicionada com sucesso!")
                st.experimental_rerun()
            else:
                st.warning("Digite uma pergunta antes de adicionar.")

    elif menu_admin == "Gerenciar Usuários":
        st.subheader("👥 Gerenciar Usuários Clientes")
        usuarios_df = pd.read_csv(usuarios_csv)
        st.dataframe(usuarios_df)

        st.markdown("### Adicionar novo usuário")
        with st.form("form_novo_usuario"):
            novo_cnpj = st.text_input("CNPJ do cliente")
            nova_senha = st.text_input("Senha do cliente", type="password")
            nova_empresa = st.text_input("Nome da empresa")
            adicionar = st.form_submit_button("Adicionar Cliente")
        if adicionar:
            if novo_cnpj and nova_senha and nova_empresa:
                novo_usuario = pd.DataFrame([[novo_cnpj, nova_senha, nova_empresa]], columns=["CNPJ", "Senha", "Empresa"])
                usuarios_df = pd.concat([usuarios_df, novo_usuario], ignore_index=True)
                usuarios_df.to_csv(usuarios_csv, index=False)
                st.success("Cliente adicionado com sucesso!")
                st.experimental_rerun()
            else:
                st.warning("Preencha todos os campos para adicionar um novo cliente.")

# Painel Cliente - diagnóstico
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
                    duracao = round(time.time() - st.session_state.inicio_sessao_cliente, 2)
                    registrar_acao(cnpj, "Logout", f"Sessão finalizada. Tempo total: {duracao} segundos.")
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

    perguntas = pd.read_csv(perguntas_csv)
    respostas = {}

    with st.form("form_diagnostico"):
        logo_cliente = st.file_uploader("📎 Envie a logo da sua empresa (opcional)", type=["png", "jpg", "jpeg"])
        nome_empresa = st.text_input("📝 Nome da sua empresa", value=user.iloc[0].get("Empresa", "Nome da Empresa"))
        nome = st.text_input("Nome completo")
        email = st.text_input("E-mail")

        for i, row in perguntas.iterrows():
            respostas[row["Pergunta"]] = st.slider(row["Pergunta"], 0, 10, key=f"q_{i}")

        observacoes = st.text_area("Observações adicionais (opcional)")
        enviar = st.form_submit_button("🚀 Enviar Diagnóstico")

    if enviar:
        registrar_acao(cnpj, "Envio de Diagnóstico", "Formulário respondido com sucesso.")
        st.session_state.diagnostico_enviado = True

        media_geral = round(sum(respostas.values()) / len(respostas), 2)
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
