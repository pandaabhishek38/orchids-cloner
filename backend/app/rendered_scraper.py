import base64
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def summarize_layout(soup: BeautifulSoup) -> str:
    layout = []

    if soup.find('header'):
        layout.append("Header present")

    if soup.find('nav'):
        layout.append("Navigation bar present")

    sections = soup.find_all('section')
    layout.append(f"{len(sections)} sections found")

    divs = soup.find_all('div')
    layout.append(f"{len(divs)} div containers found")

    if soup.find('footer'):
        layout.append("Footer present")

    headings = soup.find_all(re.compile('^h[1-6]$'))
    layout.append(f"{len(headings)} heading tags found")

    buttons = soup.find_all('button')
    layout.append(f"{len(buttons)} buttons found")

    links = soup.find_all('a')
    layout.append(f"{len(links)} links found")

    images = soup.find_all('img')
    layout.append(f"{len(images)} images found")

    return " | ".join(layout)

async def get_rendered_html(url: str) -> tuple[str, str, str, str]:
    logger.info(f"Starting to scrape: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Set viewport for consistent rendering
            await page.set_viewport_size({"width": 1280, "height": 720})

            # Navigate to the page
            logger.info("Loading page...")
            await page.goto(url, timeout=30000, wait_until="networkidle")

            # Wait a bit more for dynamic content
            await page.wait_for_timeout(2000)

            # Get the HTML content
            content = await page.content()
            logger.info(f"Raw HTML length: {len(content)}")

            # Take screenshot
            logger.info("Taking screenshot...")
            screenshot_bytes = await page.screenshot(full_page=True)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            logger.info(f"Screenshot size: {len(screenshot_base64)} chars")

            # Clean and parse HTML
            soup = BeautifulSoup(content, 'html.parser')

            # Remove script and other non-visual elements
            for tag in soup(['script', 'noscript', 'iframe']):
                tag.decompose()

            # Extract inline <style> tags and linked stylesheets
            styles = soup.find_all('style')
            style_text = "\n".join(style.get_text() for style in styles if style.get_text())

            # Also try to get some basic computed styles (this is limited)
            logger.info("Extracting layout summary...")
            layout_summary = summarize_layout(soup)

            cleaned_html = str(soup)
            logger.info(f"Cleaned HTML length: {len(cleaned_html)}")
            logger.info(f"Extracted styles length: {len(style_text)}")
            logger.info(f"Layout summary: {layout_summary}")

        except Exception as e:
            logger.error(f"Playwright error: {str(e)}")
            cleaned_html = f"<html><body><h2>Playwright Error</h2><p>{str(e)}</p></body></html>"
            layout_summary = "Could not extract layout"
            screenshot_base64 = ""
            style_text = ""

        finally:
            await browser.close()

        return cleaned_html, screenshot_base64, layout_summary, style_text
