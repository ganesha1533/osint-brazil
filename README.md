# 🔍 OSINT Brasil

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20MacOS-lightgrey.svg)

**Ferramenta avançada de OSINT (Open Source Intelligence) para dados brasileiros**

[Instalação](#-instalação) •
[Uso](#-uso) •
[Funcionalidades](#-funcionalidades) •
[API](#-api) •
[Contribuir](#-contribuir)

</div>

---

## 🎯 O que é?

OSINT Brasil é uma ferramenta poderosa para consulta e validação de dados públicos brasileiros. Utiliza apenas **APIs oficiais e dados públicos**, seguindo todas as normas da LGPD.

## ⚡ Funcionalidades

| Módulo | Descrição | Fonte |
|--------|-----------|-------|
| **CNPJ** | Consulta completa de empresas | ReceitaWS, BrasilAPI |
| **CPF** | Validação matemática + estado de origem | Algoritmo oficial |
| **CEP** | Endereço completo + DDD + código IBGE | ViaCEP, BrasilAPI |
| **Telefone** | Operadora, região, tipo (móvel/fixo) | Base de DDDs |
| **Domínio** | DNS, MX, NS, status online | Google DNS |
| **Email** | Validação, hash, verificação de domínio | DNS MX |
| **Placa** | Formato (Mercosul/Antigo), estado | Base oficial |

## 🚀 Instalação

```bash
# Clone o repositório
git clone https://github.com/ganesha1533/osint-brazil.git
cd osint-brazil

# Instale as dependências
pip install -r requirements.txt

# Execute
python osint_brasil.py
```

## 📖 Uso

### Modo Interativo

```bash
python osint_brasil.py
```

```
OSINT> cnpj 00.000.000/0001-91
OSINT> cep 01310-100
OSINT> phone 11999998888
OSINT> email teste@empresa.com.br
OSINT> auto 12345678000195  # Detecta automaticamente
```

### Linha de Comando

```bash
python osint_brasil.py 00.000.000/0001-91
python osint_brasil.py 01310100
python osint_brasil.py 11999998888
```

### Como Biblioteca Python

```python
from osint_brasil import OSINTBrasil

osint = OSINTBrasil()

# Consulta CNPJ
empresa = osint.cnpj.lookup("00.000.000/0001-91")
print(empresa['razao_social'])

# Valida CPF
cpf_info = osint.cpf.validate("123.456.789-09")
print(f"Válido: {cpf_info['valid']}")

# Consulta CEP
endereco = osint.cep.lookup("01310-100")
print(f"{endereco['logradouro']}, {endereco['cidade']}")

# Detecção automática
resultado = osint.auto_detect("11999998888")
print(resultado)

# Consulta em massa
queries = ["12345678000195", "01310100", "11999998888"]
resultados = osint.bulk_lookup(queries)
```

## 🔥 Exemplos de Saída

### Consulta CNPJ

```json
{
  "cnpj": "00000000000191",
  "razao_social": "EMPRESA EXEMPLO LTDA",
  "nome_fantasia": "EXEMPLO",
  "situacao": "ATIVA",
  "data_abertura": "01/01/2000",
  "cnae_principal": "Desenvolvimento de software",
  "endereco": {
    "logradouro": "Avenida Paulista",
    "numero": "1000",
    "bairro": "Bela Vista",
    "cidade": "São Paulo",
    "uf": "SP",
    "cep": "01310100"
  },
  "telefone": "(11) 3000-0000",
  "email": "contato@empresa.com.br",
  "socios": [...]
}
```

### Validação CPF

```json
{
  "cpf": "12345678909",
  "cpf_formatado": "123.456.789-09",
  "valid": true,
  "estado_origem_provavel": "SP"
}
```

## 📡 API REST (Opcional)

Execute como servidor:

```bash
python osint_api.py
```

Endpoints:
- `GET /cnpj/{cnpj}`
- `GET /cpf/{cpf}`
- `GET /cep/{cep}`
- `GET /phone/{phone}`
- `GET /email/{email}`
- `GET /domain/{domain}`
- `GET /auto/{query}`

## ⚠️ Aviso Legal

Esta ferramenta foi desenvolvida para fins **educacionais e de pesquisa**. Utiliza apenas:

- APIs públicas oficiais (ReceitaWS, ViaCEP, BrasilAPI)
- Algoritmos de validação públicos
- Dados disponíveis publicamente

**Não armazenamos ou coletamos dados pessoais.**

O uso indevido desta ferramenta é de responsabilidade do usuário. Respeite a LGPD e as leis brasileiras.

## 🤝 Contribuir

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/NovaFeature`)
3. Commit suas mudanças (`git commit -m 'Add: nova feature'`)
4. Push para a branch (`git push origin feature/NovaFeature`)
5. Abra um Pull Request

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

<div align="center">

### 🎨 Desenvolvido por **VanGogh Dev**

[![GitHub](https://img.shields.io/badge/GitHub-ganesha1533-black?style=flat&logo=github)](https://github.com/ganesha1533)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-+595%20987%20352983-25D366?style=flat&logo=whatsapp)](https://wa.me/595987352983)

**☕ Me apoie:**

[![Crypto](https://img.shields.io/badge/Donate-Crypto-orange?style=flat&logo=bitcoin)](https://plisio.net/donate/phlGd6L5)
[![Donate](https://img.shields.io/badge/Donate-PIX%2FOther-green?style=flat)](https://vendas.snoopintelligence.space/#donate)

</div>


