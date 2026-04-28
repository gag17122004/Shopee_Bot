🤖 Shopee Auto-Reply Bot — PRATIK Distribuidora

Bot de resposta automática para a Central do Vendedor da Shopee.  
Mantém a Taxa de Resposta durante horários fora do atendimento humano.

---

## 📋 Regra de Horário

| Período          | Comportamento                        |
|------------------|--------------------------------------|
| Seg–Sex 16:00–09:00 | ✅ Responde automaticamente        |
| Seg–Sex 09:01–15:59 | ⏸️ Standby (atendimento humano)   |
| Sábado / Domingo    | ✅ Responde automaticamente (24h) |

---

## ⚙️ Instalação

```bash
# 1. Clone / copie os arquivos para uma pasta
cd shopee_bot

# 2. Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Instale os navegadores do Playwright
playwright install chromium
```

---

## 🚀 Uso

### Passo 1 — Salvar a sessão (apenas uma vez)

```bash
python login.py
```

O navegador abrirá **visivelmente**. Faça o login normalmente na Shopee Central do Vendedor. Quando estiver na página principal, pressione **ENTER** no terminal.  
Isso cria o arquivo `session/shopee_session.json`.

### Passo 2 — Iniciar o bot

```bash
python bot.py
```

O bot roda em **loop infinito** verificando novas mensagens a cada **5 minutos**.

---

## 📟 Exemplo de Logs

```
[2025-06-10 17:30:00] [INÍCIO] Bot iniciado. Entrando no loop de monitoramento…
[2025-06-10 17:30:03] [ATIVO] Ciclo #1 | 10/06/2025 17:30:03 — Verificando chats não lidos…
[2025-06-10 17:30:08] [SCAN] Encontrados 3 chat(s) na lista.
[2025-06-10 17:30:09] [ALVO] Mensagem não lida de: João Silva
[2025-06-10 17:30:09] [DELAY] Simulando comportamento humano… aguardando 7.3s
[2025-06-10 17:30:17] [RESPOSTA ENVIADA] João Silva
[2025-06-10 17:30:22] [RESUMO] 1 resposta(s) enviada(s) neste ciclo.

[2025-06-10 10:00:00] [AGUARDANDO] Fora do período de gatilho | 10/06/2025 10:00:00 — Próxima verificação em 5 min.
```

---

## 🔧 Configurações (`bot.py`)

| Variável          | Padrão | Descrição                          |
|-------------------|--------|------------------------------------|
| `LOOP_INTERVAL`   | 300    | Segundos entre verificações (5min) |
| `REPLY_DELAY_MIN` | 5      | Delay mínimo antes de responder    |
| `REPLY_DELAY_MAX` | 10     | Delay máximo antes de responder    |
| `MENSAGEM_RESPOSTA` | —    | Texto da resposta automática       |

Para rodar em **modo visível** (depuração), altere em `bot.py`:
```python
browser = await p.chromium.launch(headless=False, ...)
```

---

## 🔄 Atualizar Seletores

A Shopee atualiza o front-end periodicamente. Se o bot parar de encontrar mensagens:

1. Abra o DevTools (F12) na página de chat
2. Inspecione o elemento da bolinha de "não lida"
3. Atualize a lista `SELETORES_NAO_LIDA` e `SELETORES_INPUT` em `bot.py`

---

## 📁 Estrutura do Projeto

```
shopee_bot/
├── bot.py              ← Script principal do robô
├── login.py            ← Script de login (execute uma vez)
├── requirements.txt    ← Dependências Python
├── README.md           ← Este arquivo
└── session/
    └── shopee_session.json  ← Gerado após login.py
```

---

## ⚠️ Aviso

Mantenha o arquivo `session/shopee_session.json` **privado e seguro** — ele contém seus cookies de sessão.  
Se a sessão expirar (geralmente 30 dias), execute `python login.py` novamente.
ME.md…]()
