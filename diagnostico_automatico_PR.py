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

# Função para registrar ações no histórico
def registrar_acao(cnpj, acao, descricao):
    historico = pd.read_csv(historico_csv)
    nova = pd.DataFrame([{ "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }])
    historico = pd.concat([historico, nova], ignore_index=True)
    historico.to_csv(historico_csv, index=False)

# Definição de aba
if not st.session_state.admin_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True)
else:
    aba = "Administrador"

# Login do Administrador
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
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.markdown('</div>', unsafe_allow_html=True)

# Login do Cliente
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
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Painel Cliente - Diagnóstico
if aba == "Cliente" and st.session_state.cliente_logado:
    st.subheader("📋 Formulário de Diagnóstico")
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
        # Calcular GUT se aplicável
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
        registrar_acao(st.session_state.cnpj, "Envio", "Cliente enviou diagnóstico.")
        st.session_state.diagnostico_enviado = True

# Painel Administrativo
if aba == "Administrador" and st.session_state.admin_logado:
    if st.sidebar.button("🔄 Atualizar Página"):
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
    if menu_admin == "Gerenciar Perguntas do Formulário":
        st.subheader("📝 Gerenciar Perguntas do Diagnóstico")
        tabs_perguntas = st.tabs(["📋 Perguntas Atuais", "➕ Adicionar Nova Pergunta"])

        with tabs_perguntas[0]:
            perguntas = pd.read_csv(perguntas_csv)
            if perguntas.empty:
                st.info("Nenhuma pergunta cadastrada ainda.")
            else:
                for i, row in perguntas.iterrows():
                    col1, col2, col3 = st.columns([6, 1, 1])
                    with col1:
                        nova = st.text_input(f"Pergunta {i+1}", value=row["Pergunta"], key=f"edit_{i}")
                        perguntas.at[i, "Pergunta"] = nova
                    with col2:
                        if st.button("💾", key=f"salvar_{i}"):
                            perguntas.to_csv(perguntas_csv, index=False)
                            st.success("Pergunta atualizada.")
                            st.experimental_rerun()
                    with col3:
                        if st.button("🗑️", key=f"deletar_{i}"):
                            perguntas = perguntas.drop(i).reset_index(drop=True)
                            perguntas.to_csv(perguntas_csv, index=False)
                            st.warning("Pergunta removida.")
                            st.experimental_rerun()

        with tabs_perguntas[1]:
            with st.form("form_nova_pergunta"):
                st.subheader("➕ Adicionar Nova Pergunta")
                nova_pergunta = st.text_input("Texto da Pergunta", key="nova_pergunta")
                tipo_pergunta = st.selectbox("Tipo de Pergunta", ["Pontuação (0-10)", "Texto Aberto", "Escala", "Pontuação (0-5) + Matriz GUT"], key="tipo_pergunta")

                if tipo_pergunta == "Pontuação (0-5) + Matriz GUT":
                    st.markdown("Essa pergunta utilizará uma escala de 0 a 5 e será analisada com base em Gravidade, Urgência e Tendência da Matriz GUT.")

                adicionar = st.form_submit_button("Adicionar Pergunta")
                if adicionar:
                    if nova_pergunta.strip():
                        df = pd.read_csv(perguntas_csv)
                        nova = pd.DataFrame([[nova_pergunta + f" [{tipo_pergunta}]"]], columns=["Pergunta"])
                        df = pd.concat([df, nova], ignore_index=True)
                        df.to_csv(perguntas_csv, index=False)
                        st.success("Pergunta adicionada com sucesso! Para visualizar a pergunta adicionada, recarregue a página.")
                        st.stop()
                    else:
                        st.warning("Digite uma pergunta antes de adicionar.")

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
