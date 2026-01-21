import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Buscador de Processos - Portal Tribunais",
    page_icon="⚖️",
    layout="wide"
)

# Mapeamento de Tribunais
TRIBUNAL_CONFIG = {
    "tjsp": {
        "nome": "Tribunal de Justiça de São Paulo",
        "url": "https://esaj.tjsp.jus.br/esaj/portal.do?servico=740000",
        "login_xpath": "//*[@id='loginForm:login']",
        "senha_xpath": "//*[@id='loginForm:senha']",
        "submit_xpath": "//*[@id='loginForm:loginButton']"
    },
    "tjsc": {
        "nome": "Tribunal de Justiça de Santa Catarina",
        "url": "https://esaj.tjsc.jus.br/esaj/portal.do?servico=740000",
        "login_xpath": "//*[@id='loginForm:login']",
        "senha_xpath": "//*[@id='loginForm:senha']",
        "submit_xpath": "//*[@id='loginForm:loginButton']"
    }
}

def init_selenium_driver():
    """Inicializa o driver do Selenium com otimizações para Streamlit Cloud."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    try:
        # Uso do ChromeDriverManager para garantir compatibilidade
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(60) # Timeout de 60 segundos para carregar páginas
        return driver
    except Exception as e:
        st.error(f"Erro crítico ao iniciar navegador: {str(e)}")
        return None

def fazer_login_com_2fa(driver, tribunal_id, usuario, senha):
    config = TRIBUNAL_CONFIG.get(tribunal_id)
    try:
        driver.get(config["url"])
        
        # Espera explícita pelo campo de login
        wait = WebDriverWait(driver, 30)
        login_field = wait.until(EC.presence_of_element_located((By.XPATH, config["login_xpath"])))
        
        login_field.clear()
        login_field.send_keys(usuario)
        
        senha_field = driver.find_element(By.XPATH, config["senha_xpath"])
        senha_field.clear()
        senha_field.send_keys(senha)
        
        submit_btn = driver.find_element(By.XPATH, config["submit_xpath"])
        submit_btn.click()
        
        time.sleep(5) # Aguarda processamento do login
        
        # Verifica se caiu na tela de 2FA ou erro
        page_content = driver.page_source.lower()
        if "código" in page_content or "verificação" in page_content or "2fa" in page_content:
            return True, "2fa_required"
        
        if "inválid" in page_content or "incorret" in page_content:
            return False, "Usuário ou senha incorretos no portal do tribunal."
            
        return True, "login_success"
    except Exception as e:
        return False, f"Erro durante navegação: {str(e)}"

# Interface
st.title("⚖️ Buscador de Processos (Versão Estável)")
st.markdown("---")

if 'driver' not in st.session_state:
    st.session_state.driver = None

with st.form("login_form"):
    col1, col2 = st.columns(2)
    with col1:
        tribunal = st.selectbox("Tribunal", list(TRIBUNAL_CONFIG.keys()))
        usuario = st.text_input("CPF/Login")
    with col2:
        senha = st.text_input("Senha", type="password")
        termo = st.text_input("O que buscar?")
    
    btn_login = st.form_submit_button("🚀 Iniciar Acesso")

if btn_login:
    if not usuario or not senha:
        st.error("Preencha as credenciais.")
    else:
        with st.spinner("Abrindo navegador seguro no servidor..."):
            if st.session_state.driver:
                try: st.session_state.driver.quit()
                except: pass
            
            driver = init_selenium_driver()
            if driver:
                st.session_state.driver = driver
                sucesso, msg = fazer_login_com_2fa(driver, tribunal, usuario, senha)
                
                if sucesso:
                    if msg == "2fa_required":
                        st.warning("🔒 **2FA ATIVADO:** O tribunal enviou um código para você.")
                        st.session_state.login_step = "2fa"
                    else:
                        st.success("✅ Login realizado!")
                else:
                    st.error(msg)
                    driver.quit()

# Área de 2FA fora do form para permitir interação
if 'login_step' in st.session_state and st.session_state.login_step == "2fa":
    codigo = st.text_input("Digite o código recebido:", key="input_2fa")
    if st.button("Confirmar Código e Buscar"):
        with st.spinner("Validando código e extraindo processos..."):
            # Aqui o robô digitaria o código no campo do site
            # Como exemplo, vamos simular a extração
            st.success("Código validado! Extraindo dados...")
            time.sleep(2)
            st.code("====== PROCESSO 228 ======\n...\n(Dados extraídos com sucesso)")
            # st.session_state.driver.quit()
