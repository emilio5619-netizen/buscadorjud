import streamlit as st
import requests
import json
from requests.auth import HTTPBasicAuth
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Buscador de Processos - DataJud",
    page_icon="⚖️",
    layout="wide"
)

# Mapeamento de Regiões para Tribunais
REGION_MAP = {
    "df": "tjdft",
    "sp": "tjsp",
    "rj": "tjrj",
    "mg": "tjmg",
    "rs": "tjrs",
    "pr": "tjpr",
    "sc": "tjsc",
    "ba": "tjba",
    "pe": "tjpe",
    "ce": "tjce",
    "go": "tjgo",
    "mt": "tjmt",
    "ms": "tjms",
    "es": "tjes",
    "am": "tjam",
    "pa": "tjpa",
    "ma": "tjma",
    "pi": "tjpi",
    "rn": "tjrn",
    "pb": "tjpb",
    "al": "tjal",
    "se": "tjse",
    "to": "tjto",
    "ac": "tjac",
    "ro": "tjro",
    "rr": "tjrr",
    "ap": "tjap"
}

def format_date(date_str):
    if not date_str:
        return "N/A"
    try:
        # Formato comum da API: 2023-05-09T14:30:00.000Z
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return date_str

def search_datajud(tribunal, query_text, user, password):
    # A URL da API Pública do DataJud segue o padrão api-publica.datajud.cnj.jus.br/api_publica_{tribunal}/_search
    # Cada tribunal pode ter sua própria instância da API
    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal}/_search"
    
    # Query Elasticsearch
    payload = {
        "size": 50,
        "query": {
            "bool": {
                "should": [
                    {"match": {"assuntos.nome": query_text}},
                    {"match": {"classeProcessual.nome": query_text}},
                    {"match": {"numeroProcesso": query_text}}
                ],
                "minimum_should_match": 1
            }
        }
    }

    try:
        response = requests.post(
            url,
            json=payload,
            auth=HTTPBasicAuth(user, password),
            timeout=30
        )
        
        if response.status_code == 401:
            return {"error": "Credenciais inválidas (401). Verifique seu usuário e senha do tribunal."}
        elif response.status_code == 404:
            return {"error": f"Tribunal '{tribunal}' não encontrado ou API indisponível para este tribunal."}
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        return {"error": "A requisição expirou (Timeout). Tente novamente mais tarde."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Erro na conexão: {str(e)}"}

# Interface Streamlit
st.title("⚖️ Buscador de Processos - DataJud")
st.markdown("---")

# Sidebar com informações e LGPD
with st.sidebar:
    st.header("🔐 Acesso Restrito")
    st.info("Cada profissional deve utilizar suas próprias credenciais do tribunal correspondente.")
    
    st.markdown("---")
    st.header("Sobre")
    st.markdown("""
    Esta aplicação consulta a API do DataJud do CNJ. 
    As credenciais informadas são utilizadas apenas para a consulta atual e **não são armazenadas** em nosso servidor.
    """)
    
    st.warning("⚠️ **Aviso LGPD:** Os dados acessados são de responsabilidade do profissional. Utilize estas informações com ética e sigilo profissional.")
    st.markdown("[Obter credenciais DataJud](https://www.cnj.jus.br/sistemas/datajud/api-publica/)")

# Formulário de Busca e Credenciais
with st.form("search_form"):
    st.subheader("1. Credenciais do Tribunal")
    col_user, col_pass = st.columns(2)
    with col_user:
        user_input = st.text_input("Usuário / E-mail", placeholder="ex: luan@ijsm.org.br", help="Seu login de acesso ao tribunal")
    with col_pass:
        pass_input = st.text_input("Senha", type="password", placeholder="Sua senha", help="Sua senha de acesso ao tribunal")

    st.markdown("---")
    st.subheader("2. Parâmetros de Busca")
    col1, col2 = st.columns(2)
    
    with col1:
        region_input = st.text_input("Região (ex: sc, sp, df)", placeholder="Preenche o tribunal automaticamente").lower().strip()
        
        default_tribunal = "tjsc" # Padrão para o exemplo de SC
        if region_input in REGION_MAP:
            default_tribunal = REGION_MAP[region_input]
            
        tribunal = st.text_input("Tribunal (ID)", value=default_tribunal, help="Ex: tjsc, tjdft, tjsp, tjrj")
        
    with col2:
        causa = st.text_input("Causa / Assunto / Número", placeholder="Ex: PASEP, Apelação, 0000000-00.0000.0.00.0000")
        st.caption("Dica: Você pode buscar por assunto ou pelo número do processo.")

    submit = st.form_submit_button("🔍 Realizar Busca com Minhas Credenciais")

if submit:
    if not causa or not user_input or not pass_input:
        st.error("Por favor, preencha o Usuário, Senha e o termo de busca.")
    else:
        with st.spinner(f"Consultando API do {tribunal.upper()} com suas credenciais..."):
            results = search_datajud(tribunal.lower(), causa, user_input, pass_input)
            
            if "error" in results:
                st.error(results["error"])
                st.info("Certifique-se de que o Tribunal selecionado corresponde às suas credenciais.")
            else:
                hits = results.get("hits", {}).get("hits", [])
                total = results.get("hits", {}).get("total", {}).get("value", 0)
                
                if total == 0:
                    st.warning("Nenhum processo encontrado para os critérios informados.")
                else:
                    st.success(f"Sucesso! Encontrados {total} processos (exibindo até 50).")
                    
                    summary_data = []
                    
                    for hit in hits:
                        p = hit.get("_source", {})
                        num = p.get("numeroProcesso", "N/A")
                        classe = p.get("classeProcessual", {}).get("nome", "N/A")
                        assuntos = ", ".join([a.get("nome", "") for a in p.get("assuntos", [])])
                        valor = p.get("valorCausa", 0.0)
                        
                        summary_data.append({
                            "Número": num,
                            "Classe": classe,
                            "Assunto": assuntos,
                            "Valor": f"R$ {valor:,.2f}"
                        })
                        
                        with st.expander(f"📄 Processo: {num}"):
                            st.markdown(f"""
                            📌 **Processo:** {num}
                            🏛 **Instância:** {p.get('grau', 'N/A')}
                            ⚖ **Órgão Julgador:** {p.get('orgaoJulgador', {}).get('nome', 'N/A')}
                            📂 **Classe:** {classe}
                            📝 **Assunto:** {assuntos}
                            💰 **Valor da Causa:** R$ {valor:,.2f}
                            📅 **Data Início:** {format_date(p.get('dataAjuizamento'))}
                            📅 **Último Movimento:** {format_date(p.get('movimentos', [{}])[-1].get('dataHora')) if p.get('movimentos') else 'N/A'}
                            """)
                            
                            # Polos
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                st.markdown("### 🗒 Polo Ativo")
                                for parte in p.get("poloAtivo", []):
                                    st.markdown(f"- **{parte.get('nome', 'N/A')}**")
                                    if parte.get('cpfCnpj'): st.text(f"CPF/CNPJ: {parte.get('cpfCnpj')}")
                                    
                                    # Advogados Polo Ativo
                                    advs = parte.get("advogados", [])
                                    if advs:
                                        st.markdown("*Advogados:*")
                                        for adv in advs:
                                            st.text(f"  • {adv.get('nome')} (OAB: {adv.get('oab', 'N/A')})")

                            with col_b:
                                st.markdown("### 🗒 Polo Passivo")
                                for parte in p.get("poloPassivo", []):
                                    st.markdown(f"- **{parte.get('nome', 'N/A')}**")
                                    if parte.get('cpfCnpj'): st.text(f"CPF/CNPJ: {parte.get('cpfCnpj')}")
                                    
                                    # Advogados Polo Passivo
                                    advs = parte.get("advogados", [])
                                    if advs:
                                        st.markdown("*Advogados:*")
                                        for adv in advs:
                                            st.text(f"  • {adv.get('nome')} (OAB: {adv.get('oab', 'N/A')})")

                    # Tabela Resumo
                    st.markdown("### 📊 Tabela Resumo")
                    st.dataframe(summary_data, use_container_width=True)
