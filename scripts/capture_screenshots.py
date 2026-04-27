"""
Capture screenshots of the running Streamlit app for the slide deck.
Run while streamlit is serving on http://localhost:8501.
"""
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright

OUT = Path(__file__).parent.parent / "docs" / "slide_assets"
OUT.mkdir(parents=True, exist_ok=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1600, "height": 1100},
                                         device_scale_factor=2)
        page = await ctx.new_page()
        await page.goto("http://localhost:8501/", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(4000)

        # 1. Risk Dashboard (default tab)
        await page.screenshot(path=str(OUT / "01_dashboard.png"), full_page=False)
        print(f"  saved {OUT}/01_dashboard.png")

        # Helper: click a tab by visible text
        async def click_tab(label):
            await page.locator(f'button[role="tab"]:has-text("{label}")').first.click()
            await page.wait_for_timeout(2500)

        # 2. Map tab
        await click_tab("Map")
        await page.wait_for_timeout(3500)
        await page.screenshot(path=str(OUT / "02_map.png"), full_page=False)
        print(f"  saved {OUT}/02_map.png")

        # 3. Comparative Analysis
        await click_tab("Comparative Analysis")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=str(OUT / "03_compare.png"), full_page=False)
        print(f"  saved {OUT}/03_compare.png")

        # 4. Risk Library
        await click_tab("Risk Library")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=str(OUT / "04_risklib.png"), full_page=False)
        print(f"  saved {OUT}/04_risklib.png")

        # 5. Supplier Engagement Tiers
        await click_tab("Supplier Engagement Tiers")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=str(OUT / "05_tiers.png"), full_page=False)
        print(f"  saved {OUT}/05_tiers.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
