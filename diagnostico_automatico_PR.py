import streamlit as st
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF

st.set_page_config(page_title="Diagnóstico Automático", layout="wide")

menu = st.sidebar.selectbox("Selecione a visão", ["Cliente - Preencher Diagnóstico", "Admin - Visualizar Diagnósticos"])

arquivo_csv = "diagnosticos_clientes.csv"

if menu == "Cliente - Preencher Diagnóstico":
    st.title("📋 Portal de Diagnóstico Empresarial")
    st.markdown("Preencha as informações abaixo para gerar automaticamente seu diagnóstico.")

    with st.form("form_diagnostico"):
        nome = st.text_input("Nome completo")
        email = st.text_input("E-mail")
        empresa = st.text_input("Nome da empresa")
        financeiro = st.slider("Controle financeiro da empresa", 0, 10)
        processos = st.slider("Eficiência dos processos internos", 0, 10)
        marketing = st.slider("Presença e estratégia de marketing", 0, 10)
        vendas = st.slider("Resultado comercial (vendas/negociação)", 0, 10)
        equipe = st.slider("Desempenho da equipe/colaboradores", 0, 10)
        observacoes = st.text_area("Observações adicionais (opcional)")
        enviado = st.form_submit_button("🚀 Gerar Diagnóstico")

    if enviado:
        media_geral = round((financeiro + processos + marketing + vendas + equipe) / 5, 2)

        insights = []
        if financeiro < 6:
            insights.append("🔴 Controle financeiro necessita de atenção.")
        if processos < 6:
            insights.append("🟠 Processos internos abaixo do ideal.")
        if marketing < 6:
            insights.append("🟡 Estratégia de marketing pode ser melhorada.")
        if vendas < 6:
            insights.append("🔵 Resultados comerciais abaixo da média.")
        if equipe < 6:
            insights.append("🟣 Desempenho da equipe pode estar comprometido.")

        diagnostico_texto = "\n".join(insights) if insights else "✅ Nenhuma área crítica identificada. Excelente desempenho geral."

        resposta = pd.DataFrame([{
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Nome": nome,
            "Email": email,
            "Empresa": empresa,
            "Financeiro": financeiro,
            "Processos": processos,
            "Marketing": marketing,
            "Vendas": vendas,
            "Equipe": equipe,
            "Média Geral": media_geral,
            "Observações": observacoes,
            "Diagnóstico": diagnostico_texto.replace("\n", " ")
        }])

        if os.path.exists(arquivo_csv):
            antigo = pd.read_csv(arquivo_csv)
            resultado = pd.concat([antigo, resposta], ignore_index=True)
        else:
            resultado = resposta

        resultado.to_csv(arquivo_csv, index=False)

        # Gera PDF
        class PDF(FPDF):
            def header(self):
                self.set_font("Arial", 'B', 16)
                self.cell(0, 10, "Diagnóstico Empresarial", ln=True, align='C')
                self.ln(5)

            def footer(self):
                self.set_y(-15)
                self.set_font("Arial", "I", 8)
                self.set_text_color(128)
                self.cell(0, 10, f"Página {self.page_no()}", align='C')

        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(0, 10, f"Nome: {nome}", ln=True)
        pdf.cell(0, 10, f"E-mail: {email}", ln=True)
        pdf.cell(0, 10, f"Empresa: {empresa}", ln=True)
        pdf.ln(5)
        pdf.multi_cell(0, 10, f"Financeiro: {financeiro}\nProcessos: {processos}\nMarketing: {marketing}\nVendas: {vendas}\nEquipe: {equipe}\n\nMédia Geral: {media_geral}\n\nObservações:\n{observacoes}\n\n📊 Diagnóstico Automático:\n{diagnostico_texto}")

        pdf_output = "diagnostico_gerado.pdf"
        pdf.output(pdf_output)

        with open(pdf_output, "rb") as f:
            st.download_button("📄 Baixar PDF do Diagnóstico", f, file_name="diagnostico.pdf", mime="application/pdf")

        st.success("✅ Diagnóstico enviado, analisado e PDF gerado com sucesso!")

elif menu == "Admin - Visualizar Diagnósticos":
    st.title("🧠 Painel Administrativo de Diagnósticos")
    if os.path.exists(arquivo_csv):
        df = pd.read_csv(arquivo_csv)
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Baixar todos os diagnósticos (CSV)", data=df.to_csv(index=False), file_name="diagnosticos.csv", mime="text/csv")
    else:
        st.warning("Nenhum diagnóstico enviado ainda.")