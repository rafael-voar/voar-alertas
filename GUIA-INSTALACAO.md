# ✈️ Voar — Sistema de Alertas de Passagens
## Guia de Instalação e Configuração

---

## O que esse sistema faz

- **Painel web** para cadastrar demandas de passagens dos seus clientes
- **Verificação automática** de preços a cada 1 hora via Skyscanner (Air Scraper API)
- **Email automático** para o cliente quando o preço atingir o orçamento desejado
- **Cópia do alerta** sempre chega no seu email também
- **Resumo diário** às 8h com todas as demandas e status

---

## PASSO 1 — Configurar o Gmail para enviar emails

> O sistema usa uma conta Gmail para enviar os alertas. Recomendamos criar um email específico para isso, ex: `alertas.voar@gmail.com`

1. Acesse sua conta Gmail
2. Vá em **Minha Conta** → **Segurança** → ative a **Verificação em duas etapas**
3. Ainda em Segurança, procure por **"Senhas de app"**
4. Crie uma senha de app com o nome "Voar Alertas"
5. Anote a senha gerada (formato: `xxxx xxxx xxxx xxxx`)

---

## PASSO 2 — Sua chave da API (Air Scraper / RapidAPI)

Sua chave já está configurada no arquivo `.env`:
```
RAPIDAPI_KEY=45f7b39c16msh813f05b61a46613p140b1cjsn2cede9924194
```
✅ Não precisa fazer nada aqui!

---

## PASSO 3 — Subir o sistema no Railway (gratuito)

### 3.1 — Criar conta no Railway
1. Acesse **[railway.app](https://railway.app)**
2. Clique em **"Login with GitHub"**
3. Se não tiver GitHub, crie em [github.com](https://github.com) (é de graça)

### 3.2 — Colocar os arquivos no GitHub
1. Acesse [github.com](https://github.com) → clique em **"New repository"**
2. Nomeie como `voar-alertas` e clique em **Create**
3. Siga as instruções para fazer upload dos arquivos da pasta `voar-alertas`

### 3.3 — Criar o projeto no Railway
1. No Railway, clique em **"New Project"**
2. Escolha **"Deploy from GitHub repo"**
3. Selecione o repositório `voar-alertas`
4. O Railway vai detectar automaticamente que é Python/Flask

### 3.4 — Configurar as variáveis de ambiente
No Railway, vá em **Variables** e adicione uma a uma:

| Variável | Valor |
|---|---|
| `RAPIDAPI_KEY` | `45f7b39c16msh813f05b61a46613p140b1cjsn2cede9924194` |
| `EMAIL_REMETENTE` | `seugmail@gmail.com` |
| `EMAIL_SENHA` | `xxxx xxxx xxxx xxxx` (senha de app) |
| `EMAIL_VOAR` | `seu@email.com` (seu email da Voar) |
| `SECRET_KEY` | `voar-2024-seguro` |

5. Clique em **Deploy** — em 2-3 minutos o sistema estará no ar!
6. O Railway vai gerar uma URL pública tipo: `https://voar-alertas.up.railway.app`

---

## PASSO 4 — Usar o sistema

### Acessar o painel
- Abra a URL gerada pelo Railway no navegador
- Você vai ver o dashboard com todas as demandas

### Cadastrar uma nova demanda
1. Clique em **"+ Nova Demanda"**
2. Preencha os dados do cliente e do voo
3. Use os **códigos IATA** dos aeroportos:
   - GRU = Guarulhos (SP)
   - GIG = Galeão (RJ)
   - BSB = Brasília
   - SSA = Salvador
   - REC = Recife
   - FOR = Fortaleza
   - MIA = Miami
   - LIS = Lisboa
   - MAD = Madri
   - JFK = Nova York
4. Clique em **"Cadastrar e Começar a Monitorar"**

### Verificar preços manualmente
- No painel, clique no ícone 🔍 na linha da demanda
- Ou dentro da demanda, clique em **"Verificar Agora"**

### Pausar/Reativar monitoramento
- Use o botão ⏸ para pausar uma demanda
- Use o botão ▶ para reativar

---

## Funcionamento automático

| Ação | Frequência |
|---|---|
| Verificação de preços | A cada 1 hora |
| Email de alerta ao cliente | Quando preço ≤ orçamento |
| Resumo diário para Voar | Todo dia às 8h |

---

## Dúvidas frequentes

**O sistema para quando fecho o computador?**
Não! Ele roda no Railway (na nuvem), 24h por dia.

**Quantas demandas posso ter?**
No plano gratuito do Railway, sem limite de demandas. O limite é de chamadas à API (500/mês no plano gratuito do RapidAPI).

**E se a API de voos não encontrar resultado?**
O sistema tenta novamente na próxima hora. Isso pode acontecer para rotas muito específicas.

**Como troco a frequência de verificação?**
No arquivo `scheduler.py`, troque `hours=1` para `hours=2` (a cada 2h) ou `minutes=30` (a cada 30min).

---

## Suporte

Sistema desenvolvido especialmente para a **Voar Passagens Aéreas**.
