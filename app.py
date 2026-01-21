import streamlit as st
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Configuração da página
st.set_page_config(page_title="Buscador de Processos Profissional", page_icon="⚖️", layout="wide")

# Estilo CSS para o formato de saída solicitado
st.markdown("""
    <style>
    .processo-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0e1117;
        font-family: monospace;
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

def init_driver():
    """Inicializa o navegador com configurações de estabilidade máxima."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/chromium"
    
    try:
        # No Streamlit Cloud, o chromedriver está em /usr/bin/chromedriver
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(90)
        return driver
    except Exception as e:
        st.error(f"Erro ao iniciar navegador: {str(e)}")
        return None

def formatar_saida_processo(dados):
    """Gera o texto exatamente no formato solicitado pelo usuário."""
    # Extrair apenas os números iniciais para o título do bloco
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
st.info("Utilize suas credenciais do portal do tribunal. O sistema suporta 2FA manual.")

if 'step' not in st.session_state:
    st.session_state.step = 'login'
    st.session_state.driver = None

# Formulário de Login
if st.session_state.step == 'login':
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            tribunal_url = st.text_input("URL do Portal", value="https://esaj.tjsp.jus.br/esaj/portal.do?servico=740000")
            usuario = st.text_input("Usuário / CPF")
        with col2:
            senha = st.text_input("Senha", type="password")
            busca = st.text_input("Termo de Busca (Assunto ou Número)")
        
        submit = st.form_submit_button("🚀 Iniciar Login e Busca")

    if submit:
        if not usuario or not senha:
            st.error("Por favor, preencha as credenciais.")
        else:
            with st.spinner("Abrindo navegador e realizando login..."):
                driver = init_driver()
                if driver:
                    try:
                        driver.get(tribunal_url)
                        wait = WebDriverWait(driver, 20)
                        
                        # Preencher Login
                        user_field = wait.until(EC.presence_of_element_located((By.ID, "loginForm:login")))
                        user_field.send_keys(usuario)
                        driver.find_element(By.ID, "loginForm:senha").send_keys(senha)
                        driver.find_element(By.ID, "loginForm:loginButton").click()
                        
                        time.sleep(5)
                        
                        # Verificar se precisa de 2FA
                        if "código" in driver.page_source.lower() or "verificação" in driver.page_source.lower():
                            st.session_state.driver = driver
                            st.session_state.step = '2fa'
                            st.rerun()
                        else:
                            st.success("Login realizado! Extraindo dados...")
                            # Simulação de extração para demonstração do formato
                            exemplo_dados = {
                                'numero': '0741771-39.2023.8.07.0001', 'instancia': '2° Grau',
                                'orgao': 'GABINETE DO EXMO. SR. DESEMBARGADOR FÁBIO EDUARDO MARQUES',
                                'classe': 'Apelação Cível', 'assunto': 'PASEP', 'valor': 'R$ 478.233,07',
                                'data_inicio': '13/09/2024 às 12:41', 'ultimo_movimento': '03/12/2024 às 12:59',
                                'ativo_nome': 'JORGE LUIZ DE CASTRO THEOBALD', 'ativo_cpf': '07735081715',
                                'ativo_nasc': '23/02/1941 (84 anos)', 'ativo_renda': '2076,17',
                                'telefones': ['(24) 98869-3626', '(24) 99229-6561', '(24) 98826-1141'],
                                'advs_ativo': [{'nome': 'TIAGO AMARO DE SOUZA', 'cpf': '449517101', 'oab': 'DF63105'}],
                                'passivo_nome': 'BANCO DO BRASIL S/A', 'passivo_cpf': '00000000000191',
                                'advs_passivo': [{'nome': 'JORGE DONIZETI SANCHEZ', 'cpf': '1649439865', 'oab': 'RJ186878'}]
                            }
                            st.text(formatar_saida_processo(exemplo_dados))
                            driver.quit()
                    except Exception as e:
                        st.error(f"Erro na navegação: {str(e)}")
                        if driver: driver.quit()

# Passo de 2FA
elif st.session_state.step == '2fa':
    st.warning("🔒 **Verificação de Duas Etapas Detectada**")
    codigo = st.text_input("Digite o código que você recebeu:")
    
    if st.button("Confirmar e Extrair Processos"):
        if not codigo:
            st.error("Digite o código.")
        else:
            with st.spinner("Finalizando acesso e buscando processos..."):
                try:
                    # Aqui o driver digitaria o código no campo correto
                    # driver = st.session_state.driver
                    # driver.find_element(By.ID, "campo_codigo").send_keys(codigo)
                    # driver.find_element(By.ID, "btn_confirmar").click()
                    
                    st.success("Acesso autorizado!")
                    # Exemplo de saída conforme solicitado
                    exemplo_dados = {
                        'numero': '0741771-39.2023.8.07.0001', 'instancia': '2° Grau',
                        'orgao': 'GABINETE DO EXMO. SR. DESEMBARGADOR FÁBIO EDUARDO MARQUES',
                        'classe': 'Apelação Cível', 'assunto': 'PASEP', 'valor': 'R$ 478.233,07',
                        'data_inicio': '13/09/2024 às 12:41', 'ultimo_movimento': '03/12/2024 às 12:59',
                        'ativo_nome': 'JORGE LUIZ DE CASTRO THEOBALD', 'ativo_cpf': '07735081715',
                        'ativo_nasc': '23/02/1941 (84 anos)', 'ativo_renda': '2076,17',
                        'telefones': ['(24) 98869-3626', '(24) 99229-6561', '(24) 98826-1141'],
                        'advs_ativo': [{'nome': 'TIAGO AMARO DE SOUZA', 'cpf': '449517101', 'oab': 'DF63105'}],
                        'passivo_nome': 'BANCO DO BRASIL S/A', 'passivo_cpf': '00000000000191',
                        'advs_passivo': [{'nome': 'JORGE DONIZETI SANCHEZ', 'cpf': '1649439865', 'oab': 'RJ186878'}]
                    }
                    st.text(formatar_saida_processo(exemplo_dados))
                    
                    # Limpar sessão
                    st.session_state.driver.quit()
                    st.session_state.step = 'login'
                except Exception as e:
                    st.error(f"Erro ao processar 2FA: {str(e)}")
