import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
from fpdf import FPDF
import tempfile

st.set_page_config(page_title="Portal de Diagnóstico", layout="centered")

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

# ... (login e painel admin já existentes)

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
