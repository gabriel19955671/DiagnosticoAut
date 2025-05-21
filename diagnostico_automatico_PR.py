# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    try:
        st.sidebar.image("https://via.placeholder.com/200x80.png?text=Logo+Admin", use_container_width=True)
    except Exception as e_img_admin:
        st.sidebar.caption(f"Logo admin não carregada: {e_img_admin}")

    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("🚪 Sair do Painel Admin", key="logout_admin_v16_final", use_container_width=True): # Chave atualizada
        st.session_state.admin_logado = False
        st.toast("Logout de admin realizado.", icon="👋")
        st.rerun()

    menu_admin_options_map = { # Text key -> Emoji
        "Visão Geral e Diagnósticos": "📊",
        "Histórico de Usuários": "📜",
        "Gerenciar Perguntas": "📝",
        "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar Clientes": "👥",
        "Gerenciar Administradores": "👮"
    }
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key]} {key}" for key in admin_page_text_keys]

    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v16_final" # Chave de sessão para a página atual (texto puro)
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v16_final" # Chave para o widget selectbox

    # 1. Inicializar o estado da página admin se não existir ou for inválido
    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or \
       st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] not in admin_page_text_keys:
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0] # Default para a primeira página

    # 2. Função on_change para o selectbox
    def admin_menu_on_change():
        # O widget selectbox (com key WIDGET_KEY_SB_ADMIN_MENU) armazena o valor "emoji Texto"
        selected_display_value_from_widget = st.session_state[WIDGET_KEY_SB_ADMIN_MENU]
        
        # Converter o valor de display de volta para a chave de texto puro
        new_text_key = None
        for text_key, emoji in menu_admin_options_map.items():
            if f"{emoji} {text_key}" == selected_display_value_from_widget:
                new_text_key = text_key
                break
        
        # Atualizar nossa variável de estado principal (SESSION_KEY_FOR_ADMIN_PAGE)
        # se a seleção realmente mudou
        if new_text_key and new_text_key != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
            st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key
            # O st.rerun() não é estritamente necessário aqui porque a mudança no selectbox já causa um rerun.
            # No entanto, se você quisesse forçar um rerun IMEDIATAMENTE após atualizar o estado
            # (antes do Streamlit completar seu próprio ciclo de rerun do widget), você poderia, mas geralmente não é preciso.

    # 3. Determinar o índice atual para o selectbox
    # Este valor é a chave de texto puro da página que DEVE estar selecionada
    current_admin_page_text_key_for_index = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    
    try:
        # O índice deve ser baseado na lista de opções que o selectbox realmente usa (admin_options_for_display)
        # Então, primeiro construímos o valor de display esperado para a página atual
        expected_display_value_for_current_page = f"{menu_admin_options_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
        current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
    except (ValueError, KeyError): # KeyError se current_admin_page_text_key_for_index não estiver no map (improvável com a inicialização)
        # Fallback: se algo der muito errado, default para o índice 0
        current_admin_menu_index = 0
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0] # Resetar o estado para consistência

    # 4. Renderizar o selectbox
    st.sidebar.selectbox(
        "Funcionalidades Admin:",
        options=admin_options_for_display,
        index=current_admin_menu_index, # Este é o ponto crucial para mostrar a seleção correta
        key=WIDGET_KEY_SB_ADMIN_MENU,   # Chave do widget
        on_change=admin_menu_on_change  # Callback para atualizar nosso estado principal
    )

    # 5. Usar a variável de estado principal para a lógica da página
    menu_admin = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    header_display_name = f"{menu_admin_options_map[menu_admin]} {menu_admin}" # Recria o nome com emoji para o header
    st.header(header_display_name)
    # ... resto do código do admin ...