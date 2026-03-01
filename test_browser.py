import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        page.on('console', lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
        
        await page.goto("http://localhost:5000/")
        await page.fill('input[name="username"]', "admin")
        await page.fill('input[name="password"]', "admin")
        await page.click('button[type="submit"]')
        await page.wait_for_url("http://localhost:5000/dashboard")
        print("Logged in")
        
        await asyncio.sleep(2)
        
        is_dark = await page.evaluate("() => document.documentElement.classList.contains('dark')")
        print(f"IS DARK BEFORE CLICK: {is_dark}")
        
        await page.click("#themeToggle", timeout=2000)
        await asyncio.sleep(1)
        
        is_dark = await page.evaluate("() => document.documentElement.classList.contains('dark')")
        print(f"IS DARK AFTER CLICK: {is_dark}")
        
        await browser.close()

asyncio.run(main())
