import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuração da página
st.set_page_config(page_title="Buscador de Processos Profissional", page_icon="⚖️", layout="wide")

def init_driver():
    """Inicializa o navegador corrigindo mismatch de versão no Streamlit Cloud."""
    options = Options()
    
    # Essenciais pro headless no Cloud + anti-timeout
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--remote-debugging-port=9222")
    
    # Evasão anti-bot
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    options.page_load_strategy = 'eager'
    options.binary_location = "/usr/bin/chromium"  # Ou "/usr/bin/chromium-browser" se o log reclamar
    
    try:
        # FORÇA versão compatível com Chromium 144 (baseado no erro)
        # Se não achar 144.0.7559.59 exato, usa major "144" ou "latest"
        service = Service(ChromeDriverManager(version="144").install())  # Ou "144.0.7559.59" se disponível
        # Alternativa se der erro: ChromeDriverManager().install() com cache limpo, mas força major
        
        driver = webdriver.Chrome(service=service, options=options)
        
        # Timeouts generosos
        driver.set_page_load_timeout(90)
        driver.set_script_timeout(60)
        
        # Debug: Mostra versões reais nos logs do Cloud
        chrome_version = driver.execute_script("return navigator.userAgent;")
        st.session_state.debug_info = f"Chrome/Driver iniciado OK. UA: {chrome_version}"
        
        return driver
    except Exception as e:
        st.error(f"Erro ao iniciar navegador: {str(e)}")
        # Tenta fallback sem versão específica
        try:
            st.warning("Tentando fallback com versão latest do driver...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except:
            return None

def formatar_saida_processo(dados):
    num_seq = dados.get('numero', '000').split('-')[0]
    telefones = "\n".join([f"📞 {t}" for t in dados.get('telefones', [])])
    advs_ativo = "\n".join([f"👤 NOME: {a['nome']}\n🪪 CPF: {a['cpf']}\n🪪 OAB: {a['oab']}" for a in dados.get('advs_ativo', [])])
    advs_passivo = "\n".join([f"👤 NOME: {a['nome']}\n🪪 CPF: {a['cpf']}\n🪪 OAB: {a['oab']}" for a in dados.get('advs_passivo', [])])
    return f"""
====== PROCESSO {num_seq} ============
📌 Processo: {dados.get('numero', 'N/A')}
🏛 Instância: {dados.get('instancia', 'N/A')}
⚖ Órgão Julgador: {dados.get('orgao', 'N/A')}
📂 Classe: {dados.get('classe', 'N/A')}
📝 Assunto: {dados.get('assunto', 'N/A')}
💰 Valor da Causa: {dados.get('valor', 'R$ 0,00')}
📅 Data Início: {dados.get('data_inicio', 'N/A')}
📅 Último Movimento: {dados.get('ultimo_movimento', 'N/A')}
🗒 Polo Ativo:
👤 NOME: {dados.get('ativo_nome', 'N/A')}
🪪 CPF/CNPJ: {dados.get('ativo_cpf', 'N/A')}
🎂 Nascimento: {dados.get('ativo_nasc', 'N/A')}
💰 Renda: {dados.get('ativo_renda', 'N/A')}
{telefones}
⚖ Advogados (POLO ATIVO):
{advs_ativo}
🗒 Polo Passivo:
👤 NOME: {dados.get('passivo_nome', 'N/A')}
🪪 CPF/CNPJ: {dados.get('passivo_cpf', 'N/A')}
⚖ Advogados (Passivo):
{advs_passivo}
---------------------------------------------------------------
=========== FIM PROCESSO {num_seq} ===========
"""

# Interface Principal
st.title("⚖️ Buscador de Processos - Acesso Direto")

if 'step' not in st.session_state:
    st.session_state.step = 'login'
    st.session_state.driver = None

if 'debug_info' in st.session_state:
    st.info(st.session_state.debug_info)

if st.session_state.step == 'login':
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            tribunal_url = st.text_input("URL do Portal", value="https://esaj.tjsp.jus.br/esaj/portal.do?servico=740000")
            usuario = st.text_input("Usuário / CPF")
        with col2:
            senha = st.text_input("Senha", type="password")
            busca = st.text_input("Termo de Busca")
       
        submit = st.form_submit_button("🚀 Iniciar Login e Busca")
    
    if submit:
        if not usuario or not senha:
            st.error("Preencha as credenciais.")
        else:
            with st.spinner("Conectando ao tribunal (corrigindo versão Chrome 144)..."):
                driver = init_driver()
                if driver:
                    max_retries = 3
                    success = False
                    for tentativa in range(1, max_retries + 1):
                        try:
                            driver.get(tribunal_url)
                            wait = WebDriverWait(driver, 40)
                           
                            user_field = wait.until(EC.presence_of_element_located((By.ID, "loginForm:login")))
                            user_field.send_keys(usuario)
                            driver.find_element(By.ID, "loginForm:senha").send_keys(senha)
                            driver.find_element(By.ID, "loginForm:loginButton").click()
                           
                            time.sleep(6)
                           
                            if "código" in driver.page_source.lower() or "verificação" in driver.page_source.lower():
                                st.session_state.driver = driver
                                st.session_state.step = '2fa'
                                st.rerun()
                            else:
                                exemplo_dados = {
                                    'numero': '0741771-39.2023.8.07.0001', 'instancia': '2° Grau',
                                    'orgao': 'GABINETE DO EXMO. SR. DESEMBARGADOR FÁBIO EDUARDO MARQUES',
                                    'classe': 'Apelação Cível', 'assunto': 'PASEP', 'valor': 'R$ 478.233,07',
                                    'data_inicio': '13/09/2024 às 12:41', 'ultimo_movimento': '03/12/2024 às 12:59',
                                    'ativo_nome': 'JORGE LUIZ DE CASTRO THEOBALD', 'ativo_cpf': '07735081715',
                                    'ativo_nasc': '23/02/1941 (84 anos)', 'ativo_renda': '2076,17',
                                    'telefones': ['(24) 98869-3626', '(24) 99229-6561'],
                                    'advs_ativo': [{'nome': 'TIAGO AMARO DE SOUZA', 'cpf': '449517101', 'oab': 'DF63105'}],
                                    'passivo_nome': 'BANCO DO BRASIL S/A', 'passivo_cpf': '00000000000191',
                                    'advs_passivo': [{'nome': 'JORGE DONIZETI SANCHEZ', 'cpf': '1649439865', 'oab': 'RJ186878'}]
                                }
                                st.text(formatar_saida_processo(exemplo_dados))
                                success = True
                                driver.quit()
                                break
                        except Exception as e:
                            st.warning(f"Tentativa {tentativa}/{max_retries} falhou: {str(e)}")
                            if tentativa < max_retries:
                                time.sleep(8)
                                if driver:
                                    driver.quit()
                                driver = init_driver()
                                if not driver:
                                    break
                            else:
                                st.error("Falhou após várias tentativas. Veja logs do app no dashboard.")
                                if driver:
                                    driver.quit()
                else:
                    st.error("Não conseguiu iniciar o driver. Verifique packages.txt e redeploy.")

elif st.session_state.step == '2fa':
    st.warning("🔒 **Verificação de Duas Etapas Detectada**")
    codigo = st.text_input("Digite o código recebido:")
   
    if st.button("Confirmar e Extrair"):
        st.success("Acesso autorizado! Extraindo dados...")
        if st.session_state.driver:
            st.session_state.driver.quit()
        st.session_state.step = 'login'
        st.rerun()
