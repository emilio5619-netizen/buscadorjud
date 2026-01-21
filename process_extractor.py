"""
Módulo para extração de dados de processos dos portais de tribunais.
Suporta múltiplos formatos e estruturas de dados.
"""

import re
from typing import List, Dict, Any

class ProcessoExtractor:
    """Extrai dados de processos de páginas HTML dos portais de tribunais."""
    
    @staticmethod
    def extrair_numero_processo(texto: str) -> str:
        """Extrai número de processo no formato NNNNNNN-DD.AAAA.J.TT.OOOO"""
        padrao = r'\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}'
        match = re.search(padrao, texto)
        return match.group(0) if match else "N/A"
    
    @staticmethod
    def extrair_cpf_cnpj(texto: str) -> str:
        """Extrai CPF ou CNPJ do texto."""
        # CPF: 000.000.000-00 ou 00000000000
        cpf_padrao = r'\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11}'
        # CNPJ: 00.000.000/0000-00 ou 00000000000000
        cnpj_padrao = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14}'
        
        match_cnpj = re.search(cnpj_padrao, texto)
        if match_cnpj:
            return match_cnpj.group(0)
        
        match_cpf = re.search(cpf_padrao, texto)
        return match_cpf.group(0) if match_cpf else "N/A"
    
    @staticmethod
    def extrair_telefones(texto: str) -> List[str]:
        """Extrai números de telefone do texto."""
        # Padrão para telefones brasileiros: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
        padrao = r'\(\d{2}\)\s?\d{4,5}-\d{4}'
        telefones = re.findall(padrao, texto)
        return telefones if telefones else []
    
    @staticmethod
    def extrair_data(texto: str) -> str:
        """Extrai data no formato DD/MM/AAAA HH:MM"""
        padrao = r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}'
        match = re.search(padrao, texto)
        return match.group(0) if match else "N/A"
    
    @staticmethod
    def extrair_valor_monetario(texto: str) -> str:
        """Extrai valor monetário em formato brasileiro."""
        padrao = r'R\$\s+[\d.,]+'
        match = re.search(padrao, texto)
        return match.group(0) if match else "R$ 0,00"
    
    @staticmethod
    def extrair_advogados(texto: str) -> List[Dict[str, str]]:
        """Extrai dados de advogados (nome, CPF, OAB)."""
        advogados = []
        
        # Padrão para buscar blocos de advogados
        # Assume estrutura: NOME ... CPF: XXX ... OAB: XX123456
        linhas = texto.split('\n')
        
        i = 0
        while i < len(linhas):
            linha = linhas[i].strip()
            
            # Procurar por indicadores de advogado
            if 'advogado' in linha.lower() or 'oab' in linha.lower():
                adv_data = {'nome': '', 'cpf': '', 'oab': ''}
                
                # Procurar nos próximos 10 linhas
                for j in range(i, min(i + 10, len(linhas))):
                    proxima = linhas[j]
                    
                    # Extrair nome (primeira linha não vazia após "Advogado")
                    if not adv_data['nome'] and proxima.strip() and 'cpf' not in proxima.lower():
                        adv_data['nome'] = proxima.strip()
                    
                    # Extrair CPF
                    if 'cpf' in proxima.lower():
                        cpf = ProcessoExtractor.extrair_cpf_cnpj(proxima)
                        if cpf != "N/A":
                            adv_data['cpf'] = cpf
                    
                    # Extrair OAB
                    if 'oab' in proxima.lower():
                        oab_match = re.search(r'([A-Z]{2})\s*(\d+)', proxima)
                        if oab_match:
                            adv_data['oab'] = f"{oab_match.group(1)}{oab_match.group(2)}"
                
                if adv_data['nome']:
                    advogados.append(adv_data)
            
            i += 1
        
        return advogados if advogados else [{'nome': 'N/A', 'cpf': 'N/A', 'oab': 'N/A'}]
    
    @staticmethod
    def extrair_dados_pessoa(texto: str) -> Dict[str, Any]:
        """Extrai dados completos de uma pessoa (nome, CPF, nascimento, renda, telefones)."""
        pessoa = {
            'nome': 'N/A',
            'cpf_cnpj': ProcessoExtractor.extrair_cpf_cnpj(texto),
            'nascimento': 'N/A',
            'renda': 'N/A',
            'telefones': ProcessoExtractor.extrair_telefones(texto)
        }
        
        # Extrair nome (geralmente primeira linha significativa)
        linhas = [l.strip() for l in texto.split('\n') if l.strip()]
        if linhas:
            pessoa['nome'] = linhas[0]
        
        # Extrair nascimento (padrão: DD/MM/AAAA)
        data_padrao = r'(\d{2}/\d{2}/\d{4})'
        match_data = re.search(data_padrao, texto)
        if match_data:
            pessoa['nascimento'] = match_data.group(0)
        
        # Extrair renda
        renda_padrao = r'[Rr]enda[:\s]+R\$\s+([\d.,]+)'
        match_renda = re.search(renda_padrao, texto)
        if match_renda:
            pessoa['renda'] = match_renda.group(1)
        
        return pessoa
    
    @staticmethod
    def extrair_processo_completo(html: str) -> Dict[str, Any]:
        """Extrai todos os dados de um processo a partir do HTML."""
        processo = {
            'numero': ProcessoExtractor.extrair_numero_processo(html),
            'instancia': 'N/A',
            'orgao': 'N/A',
            'classe': 'N/A',
            'assunto': 'N/A',
            'valor': ProcessoExtractor.extrair_valor_monetario(html),
            'data_inicio': 'N/A',
            'ultimo_movimento': 'N/A',
            'polo_ativo': {'nome': 'N/A', 'cpf_cnpj': 'N/A', 'advogados': []},
            'polo_passivo': {'nome': 'N/A', 'cpf_cnpj': 'N/A', 'advogados': []}
        }
        
        # Extrair campos específicos usando regex
        campos = {
            'instancia': r'[Ii]nstância[:\s]+([^\n]+)',
            'orgao': r'[Ó]rgão[:\s]+([^\n]+)',
            'classe': r'[Cc]lasse[:\s]+([^\n]+)',
            'assunto': r'[Aa]ssunto[:\s]+([^\n]+)',
            'data_inicio': r'[Dd]ata[:\s]+([^\n]+)',
        }
        
        for campo, padrao in campos.items():
            match = re.search(padrao, html)
            if match:
                processo[campo] = match.group(1).strip()
        
        return processo

def formatar_processo_saida(dados: Dict[str, Any]) -> str:
    """Formata os dados do processo para exibição conforme modelo solicitado."""
    
    # Extrair sequência do número do processo
    numero_seq = dados.get('numero', 'N/A').split('-')[0] if dados.get('numero') != 'N/A' else 'N/A'
    
    polo_ativo = dados.get('polo_ativo', {})
    polo_passivo = dados.get('polo_passivo', {})
    
    # Formatar advogados
    advogados_ativo = "\n".join([
        f"👤 NOME: {adv['nome']}\n🪪 CPF: {adv['cpf']}\n🪪 OAB: {adv['oab']}"
        for adv in polo_ativo.get('advogados', [])
    ]) or "N/A"
    
    advogados_passivo = "\n".join([
        f"👤 NOME: {adv['nome']}\n🪪 CPF: {adv['cpf']}\n🪪 OAB: {adv['oab']}"
        for adv in polo_passivo.get('advogados', [])
    ]) or "N/A"
    
    # Formatar telefones
    telefones = "\n".join([f"📞 {tel}" for tel in polo_ativo.get('telefones', [])]) or "N/A"
    
    saida = f"""
====== PROCESSO {numero_seq} ============

📌 Processo: {dados.get('numero', 'N/A')}
🏛 Instância: {dados.get('instancia', 'N/A')}
⚖ Órgão Julgador: {dados.get('orgao', 'N/A')}
📂 Classe: {dados.get('classe', 'N/A')}
📝 Assunto: {dados.get('assunto', 'N/A')}
💰 Valor da Causa: {dados.get('valor', 'R$ 0,00')}

📅 Data Início: {dados.get('data_inicio', 'N/A')}
📅 Último Movimento: {dados.get('ultimo_movimento', 'N/A')}

🗒 Polo Ativo:
👤 NOME: {polo_ativo.get('nome', 'N/A')}
🪪 CPF/CNPJ: {polo_ativo.get('cpf_cnpj', 'N/A')}
🎂 Nascimento: {polo_ativo.get('nascimento', 'N/A')}
💰 Renda: {polo_ativo.get('renda', 'N/A')}

📞 Telefones:
{telefones}

⚖ Advogados (POLO ATIVO):
{advogados_ativo}

🗒 Polo Passivo:
👤 NOME: {polo_passivo.get('nome', 'N/A')}
🪪 CPF/CNPJ: {polo_passivo.get('cpf_cnpj', 'N/A')}

⚖ Advogados (Passivo):
{advogados_passivo}

---------------------------------------------------------------
=========== FIM PROCESSO {numero_seq} ===========
"""
    
    return saida
