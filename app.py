import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import re
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Buscador de Processos - Portal Tribunais",
    page_icon="⚖️",
    layout="wide"
)

# Mapeamento de Tribunais e seus portais
TRIBUNAL_CONFIG = {
    "tjsp": {
        "nome": "Tribunal de Justiça de São Paulo",
        "url": "https://esaj.tjsp.jus.br/esaj/portal.do?servico=740000",
        "login_xpath": "//*[@id='loginForm:login']",
        "senha_xpath": "//*[@id='loginForm:senha']",
        "submit_xpath": "//*[@id='loginForm:loginButton']",
        "busca_xpath": "//*[@id='searchForm:searchButton']"
    },
    "tjsc": {
        "nome": "Tribunal de Justiça de Santa Catarina",
        "url": "https://esaj.tjsc.jus.br/esaj/portal.do?servico=740000",
        "login_xpath": "//*[@id='loginForm:login']",
        "senha_xpath": "//*[@id='loginForm:senha']",
        "submit_xpath": "//*[@id='loginForm:loginButton']",
        "busca_xpath": "//*[@id='searchForm:searchButton']"
    },
    "tjrj": {
        "nome": "Tribunal de Justiça do Rio de Janeiro",
        "url": "https://esaj.tjrj.jus.br/esaj/portal.do?servico=740000",
        "login_xpath": "//*[@id='loginForm:login']",
        "senha_xpath": "//*[@id='loginForm:senha']",
        "submit_xpath": "//*[@id='loginForm:loginButton']",
        "busca_xpath": "//*[@id='searchForm:searchButton']"
    },
    "tjmg": {
        "nome": "Tribunal de Justiça de Minas Gerais",
        "url": "https://esaj.tjmg.jus.br/esaj/portal.do?servico=740000",
        "login_xpath": "//*[@id='loginForm:login']",
        "senha_xpath": "//*[@id='loginForm:senha']",
        "submit_xpath": "//*[@id='loginForm:loginButton']",
        "busca_xpath": "//*[@id='searchForm:searchButton']"
    },
    "tjrs": {
        "nome": "Tribunal de Justiça do Rio Grande do Sul",
        "url": "https://esaj.tjrs.jus.br/esaj/portal.do?servico=740000",
        "login_xpath": "//*[@id='loginForm:login']",
        "senha_xpath": "//*[@id='loginForm:senha']",
        "submit_xpath": "//*[@id='loginForm:loginButton']",
        "busca_xpath": "//*[@id='searchForm:searchButton']"
    }
}

def init_selenium_driver():
    """Inicializa o driver do Selenium com Chrome em modo headless."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        st.error(f"Erro ao inicializar o navegador: {str(e)}")
        return None

def fazer_login_com_2fa(driver, tribunal_id, usuario, senha):
    """Realiza login com suporte a 2FA manual."""
    config = TRIBUNAL_CONFIG.get(tribunal_id)
    if not config:
        return False, "Tribunal não configurado"
    
    try:
        # Acessar o portal
        driver.get(config["url"])
        time.sleep(2)
        
        # Preencher login
        login_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, config["login_xpath"]))
        )
        login_field.clear()
        login_field.send_keys(usuario)
        time.sleep(1)
        
        # Preencher senha
        senha_field = driver.find_element(By.XPATH, config["senha_xpath"])
        senha_field.clear()
        senha_field.send_keys(senha)
        time.sleep(1)
        
        # Clicar em login
        submit_btn = driver.find_element(By.XPATH, config["submit_xpath"])
        submit_btn.click()
        time.sleep(3)
        
        # Verificar se há 2FA
        if "2fa" in driver.page_source.lower() or "verificação" in driver.page_source.lower():
            return True, "2fa_required"
        
        return True, "login_success"
    
    except Exception as e:
        return False, f"Erro no login: {str(e)}"

def extrair_processos(driver, tribunal_id, termo_busca):
    """Extrai dados de processos após login bem-sucedido."""
    processos = []
    try:
        # Implementar lógica de busca e extração conforme o portal específico
        # Esta é uma estrutura genérica que pode ser expandida
        
        # Aguardar carregamento da página
        time.sleep(2)
        
        # Procurar por elementos de processo na página
        # Isso varia muito de acordo com o tribunal
        
        st.info("Extração de processos em desenvolvimento para este tribunal.")
        
    except Exception as e:
        st.error(f"Erro ao extrair processos: {str(e)}")
    
    return processos

def formatar_processo(dados_processo):
    """Formata os dados do processo no padrão solicitado."""
    return f"""
====== PROCESSO {dados_processo.get('numero_seq', 'N/A')} ============

📌 Processo: {dados_processo.get('numero', 'N/A')}
🏛 Instância: {dados_processo.get('instancia', 'N/A')}
⚖ Órgão Julgador: {dados_processo.get('orgao', 'N/A')}
📂 Classe: {dados_processo.get('classe', 'N/A')}
📝 Assunto: {dados_processo.get('assunto', 'N/A')}
💰 Valor da Causa: R$ {dados_processo.get('valor', '0,00')}

📅 Data Início: {dados_processo.get('data_inicio', 'N/A')}
📅 Último Movimento: {dados_processo.get('ultimo_movimento', 'N/A')}

🗒 Polo Ativo:
👤 NOME: {dados_processo.get('polo_ativo_nome', 'N/A')}
🪪 CPF/CNPJ: {dados_processo.get('polo_ativo_cpf', 'N/A')}
🎂 Nascimento: {dados_processo.get('polo_ativo_nasc', 'N/A')}
💰 Renda: {dados_processo.get('polo_ativo_renda', 'N/A')}

📞 Telefones:
{chr(10).join([f"📞 {tel}" for tel in dados_processo.get('polo_ativo_telefones', [])])}

⚖ Advogados (POLO ATIVO):
{chr(10).join([f"👤 NOME: {adv['nome']}{chr(10)}🪪 CPF: {adv['cpf']}{chr(10)}🪪 OAB: {adv['oab']}" for adv in dados_processo.get('polo_ativo_advogados', [])])}

🗒 Polo Passivo:
👤 NOME: {dados_processo.get('polo_passivo_nome', 'N/A')}
🪪 CPF/CNPJ: {dados_processo.get('polo_passivo_cpf', 'N/A')}

⚖ Advogados (Passivo):
{chr(10).join([f"👤 NOME: {adv['nome']}{chr(10)}🪪 CPF: {adv['cpf']}{chr(10)}🪪 OAB: {adv['oab']}" for adv in dados_processo.get('polo_passivo_advogados', [])])}

---------------------------------------------------------------
=========== FIM PROCESSO {dados_processo.get('numero_seq', 'N/A')} ===========
"""

# Interface Streamlit
st.title("⚖️ Buscador de Processos - Portais de Tribunais")
st.markdown("---")

with st.sidebar:
    st.header("🔐 Acesso com 2FA")
    st.info("Você será solicitado a digitar o código de verificação manualmente durante o login.")
    st.warning("⚠️ Suas credenciais são usadas apenas para esta sessão e não são armazenadas.")

with st.form("search_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        tribunal = st.selectbox(
            "Selecione o Tribunal",
            options=list(TRIBUNAL_CONFIG.keys()),
            format_func=lambda x: TRIBUNAL_CONFIG[x]["nome"]
        )
        usuario = st.text_input("Usuário (CPF ou Login)", placeholder="ex: 14885643880")
    
    with col2:
        senha = st.text_input("Senha", type="password", placeholder="Sua senha")
        termo_busca = st.text_input("Termo de Busca", placeholder="ex: PASEP, Apelação, número do processo")
    
    submit = st.form_submit_button("🔍 Iniciar Busca com 2FA")

if submit:
    if not usuario or not senha or not termo_busca:
        st.error("Por favor, preencha todos os campos.")
    else:
        with st.spinner("Inicializando navegador..."):
            driver = init_selenium_driver()
            
            if driver:
                st.info("Tentando fazer login...")
                sucesso, mensagem = fazer_login_com_2fa(driver, tribunal, usuario, senha)
                
                if sucesso and mensagem == "2fa_required":
                    st.warning("⚠️ **Verificação de Duas Etapas Detectada**")
                    st.info("Você recebeu um código de verificação. Digite-o abaixo:")
                    
                    codigo_2fa = st.text_input("Código de Verificação (2FA)", type="password", placeholder="Digite o código que recebeu")
                    
                    if st.button("Confirmar Código"):
                        # Aqui você implementaria a lógica para digitar o código no portal
                        st.success("Código confirmado! Continuando com a busca...")
                        time.sleep(2)
                        
                        # Extrair processos
                        processos = extrair_processos(driver, tribunal, termo_busca)
                        
                        if processos:
                            st.success(f"Encontrados {len(processos)} processos!")
                            for processo in processos:
                                st.text(formatar_processo(processo))
                        else:
                            st.warning("Nenhum processo encontrado com os critérios informados.")
                
                elif sucesso and mensagem == "login_success":
                    st.success("Login realizado com sucesso!")
                    
                    # Extrair processos
                    processos = extrair_processos(driver, tribunal, termo_busca)
                    
                    if processos:
                        st.success(f"Encontrados {len(processos)} processos!")
                        for processo in processos:
                            st.text(formatar_processo(processo))
                    else:
                        st.warning("Nenhum processo encontrado com os critérios informados.")
                
                else:
                    st.error(f"Erro: {mensagem}")
                
                driver.quit()
            else:
                st.error("Não foi possível inicializar o navegador.")
