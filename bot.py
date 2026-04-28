"""
╔══════════════════════════════════════════════════════════════╗
║       SHOPEE AUTO-REPLY BOT — PRATIK Distribuidora           ║
║       Engenheiro: Script Python + Playwright                 ║
╚══════════════════════════════════════════════════════════════╝

Regra de Horário:
  • Seg–Sex → responde entre 16:00–23:59 e 00:00–09:00
  • Sáb–Dom → responde qualquer horário
  • 09:01–15:59 (Seg–Sex) → standby (atendimento humano)
"""

import asyncio
import random
import json
import os
from datetime import datetime, time
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────
SESSION_FILE   = Path("session/shopee_session.json")
LOOP_INTERVAL  = 300          # segundos entre cada varredura (5 min)
REPLY_DELAY_MIN = 5           # delay humano mínimo (seg)
REPLY_DELAY_MAX = 10          # delay humano máximo (seg)

MENSAGEM_RESPOSTA = (
    "Nosso horário de atendimento é de Segunda-feira a Sexta-feira das 09:00 as 16:00. "
    "Agradecemos o contato. Equipe PRATIK Distribuidora."
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

SHOPEE_CHAT_URL = "https://seller.shopee.com.br/portal/chat"

# ─────────────────────────────────────────────
# HELPERS DE LOG
# ─────────────────────────────────────────────
def log(tag: str, msg: str, color: str = ""):
    cores = {
        "green":  "\033[92m",
        "yellow": "\033[93m",
        "red":    "\033[91m",
        "cyan":   "\033[96m",
        "reset":  "\033[0m",
    }
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c  = cores.get(color, "")
    r  = cores["reset"]
    print(f"{c}[{ts}] [{tag}] {msg}{r}")

# ─────────────────────────────────────────────
# LÓGICA DE HORÁRIO
# ─────────────────────────────────────────────
def deve_responder() -> bool:
    """
    Retorna True se o bot deve enviar resposta agora.
    Seg–Sex: responde se hora < 09:01 OU hora >= 16:00
    Sáb–Dom: sempre responde
    """
    agora    = datetime.now()
    dia_sem  = agora.weekday()   # 0=Seg … 6=Dom
    hora_att = agora.time()

    inicio_comercial = time(9, 1)    # 09:01
    fim_comercial    = time(16, 0)   # 16:00

    fim_de_semana = dia_sem >= 5     # Sáb(5) ou Dom(6)

    if fim_de_semana:
        return True

    # Dias de semana: responde FORA do horário comercial
    em_horario_comercial = inicio_comercial <= hora_att < fim_comercial
    return not em_horario_comercial

# ─────────────────────────────────────────────
# MOVIMENTOS DE MOUSE HUMANIZADOS
# ─────────────────────────────────────────────
async def mover_mouse_humano(page, x: int, y: int):
    """Move o mouse de forma não-linear para simular humano."""
    passos = random.randint(8, 15)
    cur_x, cur_y = random.randint(100, 800), random.randint(100, 600)
    for i in range(passos):
        fator = (i + 1) / passos
        nx = int(cur_x + (x - cur_x) * fator + random.randint(-5, 5))
        ny = int(cur_y + (y - cur_y) * fator + random.randint(-5, 5))
        await page.mouse.move(nx, ny)
        await asyncio.sleep(random.uniform(0.03, 0.08))

async def delay_humano():
    """Espera aleatória entre REPLY_DELAY_MIN e REPLY_DELAY_MAX segundos."""
    espera = random.uniform(REPLY_DELAY_MIN, REPLY_DELAY_MAX)
    log("DELAY", f"Simulando comportamento humano… aguardando {espera:.1f}s", "cyan")
    await asyncio.sleep(espera)

async def digitar_humano(page, selector: str, texto: str):
    """Digita caractere por caractere com delay variável."""
    await page.click(selector)
    await asyncio.sleep(random.uniform(0.3, 0.7))
    for char in texto:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.04, 0.12))

# ─────────────────────────────────────────────
# CORE DO BOT
# ─────────────────────────────────────────────
async def buscar_e_responder(page) -> int:
    """
    Varre a lista de chats procurando mensagens não lidas.
    Retorna o número de respostas enviadas neste ciclo.
    """
    respostas_enviadas = 0

    try:
        await page.goto(SHOPEE_CHAT_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(random.uniform(2, 4))
    except PlaywrightTimeout:
        log("ERRO", "Timeout ao carregar página de chat.", "red")
        return 0

    # ── Seletores da Shopee (Central do Vendedor BR) ──────────────────────────
    # A Shopee atualiza o front com frequência; ajuste os seletores se necessário.
    SELETORES_NAO_LIDA = [
        "[class*='unread-badge']",
        "[class*='unread_count']",
        "[class*='badge--unread']",
        "span[class*='unread']",
        ".chat-list-item .badge",
    ]

    SELETORES_INPUT = [
        "div[contenteditable='true'][class*='input']",
        "textarea[class*='chat']",
        "div[contenteditable='true']",
        "[placeholder*='mensagem']",
        "[placeholder*='message']",
    ]

    # Aguarda lista de chats carregar
    try:
        await page.wait_for_selector(
            "[class*='chat-list'], [class*='conversation-list'], [class*='session-list']",
            timeout=15000
        )
    except PlaywrightTimeout:
        log("AVISO", "Lista de chats não encontrada. Verifique se está logado.", "yellow")
        return 0

    # Busca itens de chat
    chat_items = await page.query_selector_all(
        "[class*='chat-item'], [class*='conversation-item'], [class*='session-item']"
    )

    if not chat_items:
        log("INFO", "Nenhum chat encontrado na lista.", "cyan")
        return 0

    log("SCAN", f"Encontrados {len(chat_items)} chat(s) na lista.", "cyan")

    for idx, item in enumerate(chat_items):
        # Verifica se há badge de não lida neste item
        tem_nao_lida = False
        nome_cliente = f"Cliente #{idx+1}"

        for seletor in SELETORES_NAO_LIDA:
            badge = await item.query_selector(seletor)
            if badge:
                tem_nao_lida = True
                break

        if not tem_nao_lida:
            continue

        # Tenta extrair nome do cliente
        try:
            nome_el = await item.query_selector(
                "[class*='name'], [class*='username'], [class*='buyer']"
            )
            if nome_el:
                nome_cliente = (await nome_el.inner_text()).strip() or nome_cliente
        except Exception:
            pass

        log("ALVO", f"Mensagem não lida de: {nome_cliente}", "yellow")

        # Clique no chat com mouse humanizado
        box = await item.bounding_box()
        if box:
            cx = int(box["x"] + box["width"] / 2)
            cy = int(box["y"] + box["height"] / 2)
            await mover_mouse_humano(page, cx, cy)
            await asyncio.sleep(random.uniform(0.2, 0.5))
            await page.mouse.click(cx, cy)
        else:
            await item.click()

        await asyncio.sleep(random.uniform(1.5, 3.0))

        # Delay humano antes de responder
        await delay_humano()

        # Localiza input de mensagem
        input_el = None
        for seletor in SELETORES_INPUT:
            try:
                input_el = await page.wait_for_selector(seletor, timeout=5000)
                if input_el:
                    break
            except PlaywrightTimeout:
                continue

        if not input_el:
            log("ERRO", f"Input de mensagem não encontrado para {nome_cliente}.", "red")
            continue

        # Digita a resposta de forma humanizada
        await digitar_humano(page, SELETORES_INPUT[0] if input_el else "body", MENSAGEM_RESPOSTA)
        await asyncio.sleep(random.uniform(0.5, 1.2))

        # Envia com Enter
        await page.keyboard.press("Enter")
        await asyncio.sleep(random.uniform(1.0, 2.0))

        respostas_enviadas += 1
        log("RESPOSTA ENVIADA", nome_cliente, "green")

        # Pequena pausa antes do próximo chat
        await asyncio.sleep(random.uniform(2, 4))

    return respostas_enviadas


# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────
async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║       SHOPEE AUTO-REPLY BOT — PRATIK Distribuidora           ║
╠══════════════════════════════════════════════════════════════╣
║  Horário de resposta automática:                             ║
║    Seg–Sex  → 16:00 até 09:00 (fora do comercial)           ║
║    Sáb–Dom  → 24h                                            ║
╚══════════════════════════════════════════════════════════════╝
    """)

    if not SESSION_FILE.exists():
        log("ERRO",
            "Arquivo de sessão não encontrado! Execute 'python login.py' primeiro.",
            "red")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,   # Mude para False para depuração visual
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                f"--user-agent={USER_AGENT}",
            ]
        )

        # Carrega contexto com cookies salvos
        context = await browser.new_context(
            storage_state=str(SESSION_FILE),
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
        )

        # Oculta sinais de automação
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)

        page = await context.new_page()

        log("INÍCIO", "Bot iniciado. Entrando no loop de monitoramento…", "green")
        ciclo = 0

        while True:
            ciclo += 1
            agora_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            if deve_responder():
                log("ATIVO", f"Ciclo #{ciclo} | {agora_str} — Verificando chats não lidos…", "green")
                try:
                    enviadas = await buscar_e_responder(page)
                    if enviadas == 0:
                        log("SCAN", "Nenhuma mensagem nova encontrada.", "cyan")
                    else:
                        log("RESUMO", f"{enviadas} resposta(s) enviada(s) neste ciclo.", "green")
                except Exception as e:
                    log("ERRO", f"Falha no ciclo #{ciclo}: {e}", "red")
            else:
                log("AGUARDANDO",
                    f"Fora do período de gatilho | {agora_str} — Próxima verificação em {LOOP_INTERVAL//60} min.",
                    "yellow")

            log("SLEEP", f"Aguardando {LOOP_INTERVAL//60} minuto(s)…", "cyan")
            await asyncio.sleep(LOOP_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
