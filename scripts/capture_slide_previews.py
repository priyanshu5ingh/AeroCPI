import asyncio
import os
from playwright.async_api import async_playwright

async def capture_all_slides():
    os.makedirs('pitch_slide_previews', exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        page.on('console', lambda msg: print('CONSOLE:', msg.text))
        page.on('pageerror', lambda exc: print('PAGE ERROR:', exc))
        
        index_path = os.path.abspath('cinematic_pitch/index.html')
        url = 'file:///' + index_path.replace(chr(92), '/')
        print('Opening:', url)
        await page.goto(url)
        await page.wait_for_timeout(1000)
        
        for i in range(6):
            await page.evaluate('window.app.goToSlide(' + str(i) + ')')
            await page.wait_for_timeout(500)
            out_path = f'pitch_slide_previews/slide_{i+1}.png'
            await page.locator('#app-viewport').screenshot(path=out_path)
            print(f'[CAPTURED] Slide {i+1} saved to: {out_path}')
            
        await browser.close()
        print('[SUCCESS] All 6 slides captured!')

if __name__ == '__main__':
    asyncio.run(capture_all_slides())
