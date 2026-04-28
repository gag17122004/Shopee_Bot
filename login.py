"""
╔══════════════════════════════════════════════════════════════╗
║   SHOPEE SESSION SAVER — Execute UMA VEZ para fazer login    ║
╚══════════════════════════════════════════════════════════════╝

Abre o navegador visivelmente para você logar manualmente.
Após o login, pressione ENTER no terminal para salvar a sessão.
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

SESSION_FILE = Path("session/shopee_session.json")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

async def salvar_sessao():
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("""
╔══════════════════════════════════════════════════════════════╗
║              SHOPEE — SALVAR SESSÃO DE LOGIN                 ║
╠══════════════════════════════════════════════════════════════╣
║  1. O navegador vai abrir automaticamente.                   ║
║  2. Faça login normalmente na Shopee Central do Vendedor.    ║
║  3. Após estar logado, volte aqui e pressione ENTER.         ║
╚══════════════════════════════════════════════════════════════╝
    """)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,    # VISÍVEL para login manual
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                f"--user-agent={USER_AGENT}",
                "--start-maximized",
            ]
        )

        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
        )

        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

        page = await context.new_page()
        await page.goto(
            "https://seller.shopee.com.br/account/login",
            wait_until="domcontentloaded"
        )

        print("⏳ Navegador aberto. Faça seu login na Shopee...")
        print("   Quando estiver logado e na página principal, pressione ENTER aqui.")
        input()

        # Salva estado completo (cookies + localStorage)
        state = await context.storage_state()
        SESSION_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

        print(f"✅ Sessão salva com sucesso em: {SESSION_FILE}")
        print(f"   Cookies salvos: {len(state.get('cookies', []))}")
        print("\n   Agora você pode executar: python bot.py")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(salvar_sessao())
