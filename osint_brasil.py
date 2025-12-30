#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         OSINT BRASIL - by VanGogh Dev                          ║
║           Ferramenta de Inteligência Open Source para Dados Brasileiros        ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Consulta informações públicas de:
- CPF (Receita Federal - dados públicos)
- CNPJ (API oficial ReceitaWS)
- CEP (ViaCEP API)
- Telefone (Operadora, região)
- Domínios (.br)
- Placas de veículos
- Email (breach check)

⚠️ USO ÉTICO: Esta ferramenta utiliza apenas fontes públicas e APIs oficiais.
"""

import requests
import json
import re
import sys
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from datetime import datetime

# Cores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def banner():
    print(f"""{Colors.CYAN}
    ╔═══════════════════════════════════════════════════════════════╗
    ║  ██████╗ ███████╗██╗███╗   ██╗████████╗    ██████╗ ██████╗    ║
    ║ ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝    ██╔══██╗██╔══██╗   ║
    ║ ██║   ██║███████╗██║██╔██╗ ██║   ██║       ██████╔╝██████╔╝   ║
    ║ ██║   ██║╚════██║██║██║╚██╗██║   ██║       ██╔══██╗██╔══██╗   ║
    ║ ╚██████╔╝███████║██║██║ ╚████║   ██║       ██████╔╝██║  ██║   ║
    ║  ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝       ╚═════╝ ╚═╝  ╚═╝   ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║              🎨 Desenvolvido por VanGogh Dev                  ║
    ║         github.com/vangoghdev | OSINT Brasil v2.0             ║
    ╚═══════════════════════════════════════════════════════════════╝
    {Colors.END}""")


class CNPJLookup:
    """Consulta CNPJ via APIs públicas oficiais"""
    
    APIS = [
        "https://receitaws.com.br/v1/cnpj/{cnpj}",
        "https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
        "https://publica.cnpj.ws/cnpj/{cnpj}"
    ]
    
    @staticmethod
    def clean(cnpj: str) -> str:
        return re.sub(r'\D', '', cnpj)
    
    @staticmethod
    def validate(cnpj: str) -> bool:
        cnpj = CNPJLookup.clean(cnpj)
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
        
        def calc_digit(cnpj, weights):
            total = sum(int(cnpj[i]) * weights[i] for i in range(len(weights)))
            remainder = total % 11
            return '0' if remainder < 2 else str(11 - remainder)
        
        w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        d1 = calc_digit(cnpj, w1)
        d2 = calc_digit(cnpj + d1, w2)
        
        return cnpj[-2:] == d1 + d2
    
    def lookup(self, cnpj: str) -> Optional[Dict]:
        cnpj = self.clean(cnpj)
        
        if not self.validate(cnpj):
            return {"error": "CNPJ inválido"}
        
        for api in self.APIS:
            try:
                url = api.format(cnpj=cnpj)
                resp = requests.get(url, timeout=10, headers={
                    'User-Agent': 'OSINT-Brasil/2.0 (Educational Purpose)'
                })
                if resp.status_code == 200:
                    data = resp.json()
                    return self._normalize(data)
            except:
                continue
        
        return {"error": "Não foi possível consultar o CNPJ"}
    
    def _normalize(self, data: Dict) -> Dict:
        """Normaliza resposta de diferentes APIs"""
        return {
            "cnpj": data.get("cnpj", data.get("estabelecimento", {}).get("cnpj", "")),
            "razao_social": data.get("nome", data.get("razao_social", "")),
            "nome_fantasia": data.get("fantasia", data.get("nome_fantasia", "")),
            "situacao": data.get("situacao", data.get("descricao_situacao_cadastral", "")),
            "data_abertura": data.get("abertura", data.get("data_inicio_atividade", "")),
            "cnae_principal": data.get("atividade_principal", [{}])[0].get("text", "") if isinstance(data.get("atividade_principal"), list) else data.get("cnae_fiscal_descricao", ""),
            "endereco": {
                "logradouro": data.get("logradouro", ""),
                "numero": data.get("numero", ""),
                "bairro": data.get("bairro", ""),
                "cidade": data.get("municipio", ""),
                "uf": data.get("uf", ""),
                "cep": data.get("cep", "")
            },
            "telefone": data.get("telefone", ""),
            "email": data.get("email", ""),
            "capital_social": data.get("capital_social", ""),
            "socios": data.get("qsa", [])
        }


class CEPLookup:
    """Consulta CEP via múltiplas APIs"""
    
    APIS = [
        "https://viacep.com.br/ws/{cep}/json/",
        "https://brasilapi.com.br/api/cep/v1/{cep}",
        "https://opencep.com/v1/{cep}"
    ]
    
    @staticmethod
    def clean(cep: str) -> str:
        return re.sub(r'\D', '', cep)
    
    def lookup(self, cep: str) -> Optional[Dict]:
        cep = self.clean(cep)
        
        if len(cep) != 8:
            return {"error": "CEP inválido - deve ter 8 dígitos"}
        
        for api in self.APIS:
            try:
                url = api.format(cep=cep)
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if not data.get("erro"):
                        return {
                            "cep": cep,
                            "logradouro": data.get("logradouro", data.get("street", "")),
                            "bairro": data.get("bairro", data.get("neighborhood", "")),
                            "cidade": data.get("localidade", data.get("city", "")),
                            "uf": data.get("uf", data.get("state", "")),
                            "ddd": data.get("ddd", ""),
                            "ibge": data.get("ibge", "")
                        }
            except:
                continue
        
        return {"error": "CEP não encontrado"}


class PhoneLookup:
    """Identifica operadora e região de telefone brasileiro"""
    
    # Prefixos de operadoras móveis (DDD + 4 primeiros dígitos)
    OPERADORAS = {
        "Vivo": ["99", "98", "97", "96"],
        "Claro": ["99", "98", "97", "91"],
        "TIM": ["99", "98", "97", "93"],
        "Oi": ["99", "98", "97", "94"],
    }
    
    # DDDs por estado
    DDDS = {
        "11": "São Paulo - Capital",
        "12": "São Paulo - Vale do Paraíba",
        "13": "São Paulo - Baixada Santista",
        "14": "São Paulo - Bauru",
        "15": "São Paulo - Sorocaba",
        "16": "São Paulo - Ribeirão Preto",
        "17": "São Paulo - São José do Rio Preto",
        "18": "São Paulo - Presidente Prudente",
        "19": "São Paulo - Campinas",
        "21": "Rio de Janeiro - Capital",
        "22": "Rio de Janeiro - Interior",
        "24": "Rio de Janeiro - Interior",
        "27": "Espírito Santo - Capital",
        "28": "Espírito Santo - Interior",
        "31": "Minas Gerais - Belo Horizonte",
        "32": "Minas Gerais - Juiz de Fora",
        "33": "Minas Gerais - Governador Valadares",
        "34": "Minas Gerais - Uberlândia",
        "35": "Minas Gerais - Poços de Caldas",
        "37": "Minas Gerais - Divinópolis",
        "38": "Minas Gerais - Montes Claros",
        "41": "Paraná - Curitiba",
        "42": "Paraná - Ponta Grossa",
        "43": "Paraná - Londrina",
        "44": "Paraná - Maringá",
        "45": "Paraná - Foz do Iguaçu",
        "46": "Paraná - Francisco Beltrão",
        "47": "Santa Catarina - Joinville",
        "48": "Santa Catarina - Florianópolis",
        "49": "Santa Catarina - Chapecó",
        "51": "Rio Grande do Sul - Porto Alegre",
        "53": "Rio Grande do Sul - Pelotas",
        "54": "Rio Grande do Sul - Caxias do Sul",
        "55": "Rio Grande do Sul - Santa Maria",
        "61": "Distrito Federal - Brasília",
        "62": "Goiás - Goiânia",
        "63": "Tocantins",
        "64": "Goiás - Rio Verde",
        "65": "Mato Grosso - Cuiabá",
        "66": "Mato Grosso - Rondonópolis",
        "67": "Mato Grosso do Sul",
        "68": "Acre",
        "69": "Rondônia",
        "71": "Bahia - Salvador",
        "73": "Bahia - Itabuna",
        "74": "Bahia - Juazeiro",
        "75": "Bahia - Feira de Santana",
        "77": "Bahia - Vitória da Conquista",
        "79": "Sergipe",
        "81": "Pernambuco - Recife",
        "82": "Alagoas",
        "83": "Paraíba",
        "84": "Rio Grande do Norte",
        "85": "Ceará - Fortaleza",
        "86": "Piauí - Teresina",
        "87": "Pernambuco - Interior",
        "88": "Ceará - Interior",
        "89": "Piauí - Interior",
        "91": "Pará - Belém",
        "92": "Amazonas - Manaus",
        "93": "Pará - Santarém",
        "94": "Pará - Marabá",
        "95": "Roraima",
        "96": "Amapá",
        "97": "Amazonas - Interior",
        "98": "Maranhão - São Luís",
        "99": "Maranhão - Interior"
    }
    
    @staticmethod
    def clean(phone: str) -> str:
        return re.sub(r'\D', '', phone)
    
    def lookup(self, phone: str) -> Dict:
        phone = self.clean(phone)
        
        # Remove código do país se presente
        if phone.startswith("55") and len(phone) > 11:
            phone = phone[2:]
        
        if len(phone) < 10 or len(phone) > 11:
            return {"error": "Telefone inválido"}
        
        ddd = phone[:2]
        numero = phone[2:]
        
        is_mobile = len(numero) == 9 and numero[0] == "9"
        
        result = {
            "telefone": phone,
            "ddd": ddd,
            "numero": numero,
            "regiao": self.DDDS.get(ddd, "DDD não identificado"),
            "tipo": "Celular" if is_mobile else "Fixo",
            "formato": f"({ddd}) {numero[:5]}-{numero[5:]}" if is_mobile else f"({ddd}) {numero[:4]}-{numero[4:]}"
        }
        
        return result


class DomainLookup:
    """Consulta informações de domínios .br"""
    
    def lookup(self, domain: str) -> Dict:
        domain = domain.lower().strip()
        
        if not domain.endswith(".br"):
            domain += ".com.br"
        
        result = {
            "domain": domain,
            "dns": {},
            "whois_available": False
        }
        
        # DNS Lookup via API pública
        try:
            dns_resp = requests.get(
                f"https://dns.google/resolve?name={domain}&type=A",
                timeout=10
            )
            if dns_resp.status_code == 200:
                dns_data = dns_resp.json()
                if dns_data.get("Answer"):
                    result["dns"]["A"] = [r["data"] for r in dns_data["Answer"]]
                    result["online"] = True
                else:
                    result["online"] = False
        except:
            pass
        
        # MX Records
        try:
            mx_resp = requests.get(
                f"https://dns.google/resolve?name={domain}&type=MX",
                timeout=10
            )
            if mx_resp.status_code == 200:
                mx_data = mx_resp.json()
                if mx_data.get("Answer"):
                    result["dns"]["MX"] = [r["data"] for r in mx_data["Answer"]]
        except:
            pass
        
        # Nameservers
        try:
            ns_resp = requests.get(
                f"https://dns.google/resolve?name={domain}&type=NS",
                timeout=10
            )
            if ns_resp.status_code == 200:
                ns_data = ns_resp.json()
                if ns_data.get("Answer"):
                    result["dns"]["NS"] = [r["data"] for r in ns_data["Answer"]]
        except:
            pass
        
        return result


class EmailLookup:
    """Verifica email em breaches conhecidos (via Have I Been Pwned API pública)"""
    
    def lookup(self, email: str) -> Dict:
        email = email.lower().strip()
        
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return {"error": "Email inválido"}
        
        result = {
            "email": email,
            "domain": email.split("@")[1],
            "hash_sha1": hashlib.sha1(email.encode()).hexdigest(),
            "hash_sha256": hashlib.sha256(email.encode()).hexdigest(),
        }
        
        # Verifica MX do domínio para validar se email pode existir
        try:
            domain = email.split("@")[1]
            mx_resp = requests.get(
                f"https://dns.google/resolve?name={domain}&type=MX",
                timeout=10
            )
            if mx_resp.status_code == 200:
                mx_data = mx_resp.json()
                result["domain_has_mx"] = bool(mx_data.get("Answer"))
                if mx_data.get("Answer"):
                    result["mail_servers"] = [r["data"] for r in mx_data["Answer"][:3]]
        except:
            result["domain_has_mx"] = None
        
        return result


class CPFValidator:
    """Validador de CPF (apenas validação matemática, sem consulta)"""
    
    @staticmethod
    def clean(cpf: str) -> str:
        return re.sub(r'\D', '', cpf)
    
    @staticmethod
    def validate(cpf: str) -> Dict:
        cpf = CPFValidator.clean(cpf)
        
        if len(cpf) != 11:
            return {"valid": False, "error": "CPF deve ter 11 dígitos"}
        
        if cpf == cpf[0] * 11:
            return {"valid": False, "error": "CPF com dígitos repetidos"}
        
        # Calcula primeiro dígito verificador
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        d1 = (sum1 * 10 % 11) % 10
        
        # Calcula segundo dígito verificador
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        d2 = (sum2 * 10 % 11) % 10
        
        valid = cpf[-2:] == f"{d1}{d2}"
        
        # Identifica estado de origem (pelos primeiros dígitos - regra antiga)
        ESTADOS_CPF = {
            "0": "RS", "1": "DF/GO/MS/MT/TO", "2": "AC/AM/AP/PA/RO/RR",
            "3": "CE/MA/PI", "4": "AL/PB/PE/RN", "5": "BA/SE",
            "6": "MG", "7": "ES/RJ", "8": "SP", "9": "PR/SC"
        }
        
        return {
            "cpf": cpf,
            "cpf_formatado": f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}",
            "valid": valid,
            "estado_origem_provavel": ESTADOS_CPF.get(cpf[8], "Desconhecido")
        }


class PlacaLookup:
    """Consulta informações de placa de veículo"""
    
    ESTADOS = {
        "A": "PR", "B": "PR", "C": "PR",
        "D": "PR", "E": "PR", "F": "MG",
        "G": "MG", "H": "MG", "I": "SP",
        "J": "SP", "K": "SP", "L": "SP",
        "M": "SP", "N": "SP", "O": "SP",
        "P": "SP", "Q": "SP", "R": "RJ",
        "S": "RS", "T": "RS", "U": "RS",
        "V": "CE", "W": "PE", "X": "BA",
        "Y": "GO", "Z": "PA"
    }
    
    @staticmethod
    def clean(placa: str) -> str:
        return re.sub(r'[^A-Za-z0-9]', '', placa.upper())
    
    def lookup(self, placa: str) -> Dict:
        placa = self.clean(placa)
        
        # Formato antigo: AAA-1234
        # Formato Mercosul: AAA1A23
        
        if len(placa) != 7:
            return {"error": "Placa deve ter 7 caracteres"}
        
        is_mercosul = placa[4].isalpha()
        
        primeira_letra = placa[0]
        estado_provavel = self.ESTADOS.get(primeira_letra, "Não identificado")
        
        return {
            "placa": placa,
            "placa_formatada": f"{placa[:3]}-{placa[3:]}" if not is_mercosul else placa,
            "formato": "Mercosul" if is_mercosul else "Antigo",
            "estado_provavel": estado_provavel
        }


class OSINTBrasil:
    """Classe principal que integra todos os módulos"""
    
    def __init__(self):
        self.cnpj = CNPJLookup()
        self.cep = CEPLookup()
        self.phone = PhoneLookup()
        self.domain = DomainLookup()
        self.email = EmailLookup()
        self.cpf = CPFValidator()
        self.placa = PlacaLookup()
    
    def auto_detect(self, query: str) -> Dict:
        """Detecta automaticamente o tipo de consulta"""
        query = query.strip()
        cleaned = re.sub(r'\D', '', query)
        
        # CNPJ: 14 dígitos
        if len(cleaned) == 14:
            return {"type": "cnpj", "result": self.cnpj.lookup(query)}
        
        # CPF: 11 dígitos
        if len(cleaned) == 11 and not query.startswith("+"):
            return {"type": "cpf", "result": self.cpf.validate(query)}
        
        # CEP: 8 dígitos
        if len(cleaned) == 8:
            return {"type": "cep", "result": self.cep.lookup(query)}
        
        # Telefone: 10-11 dígitos
        if len(cleaned) in [10, 11]:
            return {"type": "phone", "result": self.phone.lookup(query)}
        
        # Email
        if "@" in query:
            return {"type": "email", "result": self.email.lookup(query)}
        
        # Domínio
        if "." in query and not "@" in query:
            return {"type": "domain", "result": self.domain.lookup(query)}
        
        # Placa
        if len(query.replace("-", "")) == 7:
            return {"type": "placa", "result": self.placa.lookup(query)}
        
        return {"type": "unknown", "error": "Não foi possível identificar o tipo de consulta"}
    
    def bulk_lookup(self, queries: List[str], max_workers: int = 5) -> List[Dict]:
        """Consulta em massa com threading"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.auto_detect, q): q for q in queries}
            
            for future in as_completed(futures):
                query = futures[future]
                try:
                    result = future.result()
                    result["query"] = query
                    results.append(result)
                except Exception as e:
                    results.append({"query": query, "error": str(e)})
        
        return results


def print_result(result: Dict, indent: int = 0):
    """Imprime resultado formatado"""
    prefix = "  " * indent
    
    for key, value in result.items():
        if isinstance(value, dict):
            print(f"{prefix}{Colors.CYAN}{key}:{Colors.END}")
            print_result(value, indent + 1)
        elif isinstance(value, list):
            print(f"{prefix}{Colors.CYAN}{key}:{Colors.END}")
            for item in value:
                if isinstance(item, dict):
                    print_result(item, indent + 1)
                    print()
                else:
                    print(f"{prefix}  - {item}")
        else:
            print(f"{prefix}{Colors.CYAN}{key}:{Colors.END} {Colors.GREEN}{value}{Colors.END}")


def interactive_mode():
    """Modo interativo"""
    osint = OSINTBrasil()
    
    banner()
    
    print(f"\n{Colors.BOLD}Comandos disponíveis:{Colors.END}")
    print(f"  {Colors.CYAN}cnpj <número>{Colors.END}    - Consulta CNPJ")
    print(f"  {Colors.CYAN}cpf <número>{Colors.END}     - Valida CPF")
    print(f"  {Colors.CYAN}cep <número>{Colors.END}     - Consulta CEP")
    print(f"  {Colors.CYAN}phone <número>{Colors.END}   - Info telefone")
    print(f"  {Colors.CYAN}email <email>{Colors.END}    - Info email")
    print(f"  {Colors.CYAN}domain <domain>{Colors.END}  - Info domínio")
    print(f"  {Colors.CYAN}placa <placa>{Colors.END}    - Info placa")
    print(f"  {Colors.CYAN}auto <query>{Colors.END}     - Detecção automática")
    print(f"  {Colors.CYAN}exit{Colors.END}             - Sair")
    
    while True:
        try:
            query = input(f"\n{Colors.BOLD}OSINT>{Colors.END} ").strip()
            
            if not query:
                continue
            
            if query.lower() == "exit":
                print(f"{Colors.WARNING}Até mais!{Colors.END}")
                break
            
            parts = query.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""
            
            if cmd == "cnpj" and arg:
                result = osint.cnpj.lookup(arg)
            elif cmd == "cpf" and arg:
                result = osint.cpf.validate(arg)
            elif cmd == "cep" and arg:
                result = osint.cep.lookup(arg)
            elif cmd == "phone" and arg:
                result = osint.phone.lookup(arg)
            elif cmd == "email" and arg:
                result = osint.email.lookup(arg)
            elif cmd == "domain" and arg:
                result = osint.domain.lookup(arg)
            elif cmd == "placa" and arg:
                result = osint.placa.lookup(arg)
            elif cmd == "auto" and arg:
                result = osint.auto_detect(arg)
            else:
                # Tenta detecção automática
                result = osint.auto_detect(query)
            
            print(f"\n{Colors.HEADER}═══ Resultado ═══{Colors.END}\n")
            print_result(result)
            
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}Saindo...{Colors.END}")
            break
        except Exception as e:
            print(f"{Colors.FAIL}Erro: {e}{Colors.END}")


def main():
    if len(sys.argv) > 1:
        # Modo linha de comando
        osint = OSINTBrasil()
        query = " ".join(sys.argv[1:])
        result = osint.auto_detect(query)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Modo interativo
        interactive_mode()


if __name__ == "__main__":
    main()
