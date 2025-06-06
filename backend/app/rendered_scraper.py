import base64
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import logging
import json

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

def clean_html_preserve_structure(soup: BeautifulSoup) -> str:
    """Clean HTML while preserving important structural information"""

    # Remove scripts and non-visual elements
    for tag in soup(['script', 'noscript', 'iframe', 'meta', 'link']):
        tag.decompose()

    # Keep important attributes (class, id) but remove others that aren't needed
    for tag in soup.find_all():
        # List of attributes to keep
        keep_attrs = ['class', 'id', 'href', 'src', 'alt', 'title', 'style']

        # Remove all attributes except the ones we want to keep
        if tag.attrs:
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in keep_attrs}

    return str(soup)

async def get_comprehensive_styles(page) -> str:
    """Extract comprehensive styling information from the page"""

    try:
        # Get computed styles for key elements with more detailed extraction
        styles_info = await page.evaluate("""
            () => {
                function getElementStyles(selector, label) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length === 0) return null;

                    const results = [];
                    elements.forEach((element, index) => {
                        const styles = window.getComputedStyle(element);

                        // Get the actual background color by checking parent elements
                        function getActualBackgroundColor(element) {
                            let currentElement = element;
                            while (currentElement) {
                                const bgColor = window.getComputedStyle(currentElement).backgroundColor;
                                if (bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent') {
                                    return bgColor;
                                }
                                currentElement = currentElement.parentElement;
                            }
                            return 'transparent';
                        }

                        // Get the actual font size by converting to pixels
                        function getActualFontSize(element) {
                            const fontSize = window.getComputedStyle(element).fontSize;
                            if (fontSize.endsWith('rem')) {
                                const remValue = parseFloat(fontSize);
                                const rootFontSize = window.getComputedStyle(document.documentElement).fontSize;
                                return (remValue * parseFloat(rootFontSize)) + 'px';
                            }
                            if (fontSize.endsWith('em')) {
                                const emValue = parseFloat(fontSize);
                                const parentFontSize = window.getComputedStyle(element.parentElement).fontSize;
                                return (emValue * parseFloat(parentFontSize)) + 'px';
                            }
                            return fontSize;
                        }

                        // Get CSS variables used in the element
                        function getCSSVariables(element) {
                            const variables = {};
                            const styles = window.getComputedStyle(element);
                            for (const prop of styles) {
                                if (prop.startsWith('--')) {
                                    variables[prop] = styles.getPropertyValue(prop);
                                }
                            }
                            return variables;
                        }

                        const styleObj = {
                            label: label + (elements.length > 1 ? ` (${index + 1})` : ''),
                            selector: selector,
                            backgroundColor: getActualBackgroundColor(element),
                            backgroundImage: styles.backgroundImage,
                            backgroundSize: styles.backgroundSize,
                            backgroundPosition: styles.backgroundPosition,
                            color: styles.color,
                            fontSize: getActualFontSize(element),
                            fontFamily: styles.fontFamily,
                            fontWeight: styles.fontWeight,
                            lineHeight: styles.lineHeight,
                            textAlign: styles.textAlign,
                            padding: styles.padding,
                            paddingTop: styles.paddingTop,
                            paddingRight: styles.paddingRight,
                            paddingBottom: styles.paddingBottom,
                            paddingLeft: styles.paddingLeft,
                            margin: styles.margin,
                            marginTop: styles.marginTop,
                            marginRight: styles.marginRight,
                            marginBottom: styles.marginBottom,
                            marginLeft: styles.marginLeft,
                            display: styles.display,
                            position: styles.position,
                            top: styles.top,
                            right: styles.right,
                            bottom: styles.bottom,
                            left: styles.left,
                            width: styles.width,
                            height: styles.height,
                            maxWidth: styles.maxWidth,
                            minHeight: styles.minHeight,
                            borderRadius: styles.borderRadius,
                            border: styles.border,
                            borderTop: styles.borderTop,
                            borderRight: styles.borderRight,
                            borderBottom: styles.borderBottom,
                            borderLeft: styles.borderLeft,
                            boxShadow: styles.boxShadow,
                            textDecoration: styles.textDecoration,
                            textTransform: styles.textTransform,
                            letterSpacing: styles.letterSpacing,
                            opacity: styles.opacity,
                            zIndex: styles.zIndex,
                            flexDirection: styles.flexDirection,
                            justifyContent: styles.justifyContent,
                            alignItems: styles.alignItems,
                            gridTemplateColumns: styles.gridTemplateColumns,
                            gridGap: styles.gridGap,
                            cssVariables: getCSSVariables(element)
                        };

                        // Get styles for pseudo-elements
                        const pseudoStyles = {
                            '::before': window.getComputedStyle(element, ':before'),
                            '::after': window.getComputedStyle(element, ':after')
                        };

                        for (const [pseudo, styles] of Object.entries(pseudoStyles)) {
                            if (styles.content !== 'none') {
                                styleObj[pseudo] = {
                                    content: styles.content,
                                    backgroundColor: styles.backgroundColor,
                                    color: styles.color,
                                    fontSize: styles.fontSize,
                                    fontFamily: styles.fontFamily
                                };
                            }
                        }

                        results.push(styleObj);
                    });

                    return results.length === 1 ? results[0] : results;
                }

                const results = [];

                // Get styles for common elements - more comprehensive list
                const selectors = [
                    ['body', 'Body'],
                    ['header', 'Header'],
                    ['nav', 'Navigation'],
                    ['main', 'Main Content'],
                    ['footer', 'Footer'],
                    ['h1', 'Main Heading'],
                    ['h2', 'Sub Heading'],
                    ['h3', 'Third Level Heading'],
                    ['p', 'Paragraph'],
                    ['a', 'Link'],
                    ['button', 'Button'],
                    ['div', 'Div Container (first 3)'],
                    ['.container', 'Container Class'],
                    ['.wrapper', 'Wrapper Class'],
                    ['.navbar', 'Navbar Class'],
                    ['.nav', 'Nav Class'],
                    ['.hero', 'Hero Section'],
                    ['.banner', 'Banner Section'],
                    ['.content', 'Content Section'],
                    ['.main', 'Main Section'],
                    ['.header', 'Header Section'],
                    ['.footer', 'Footer Section'],
                    ['.card', 'Card'],
                    ['.btn', 'Button Class'],
                    ['.button', 'Button Class Alt'],
                    ['[class*="bg-"]', 'Background Classes'],
                    ['[class*="text-"]', 'Text Classes'],
                    ['[style*="background"]', 'Inline Background Styles'],
                    ['[style*="color"]', 'Inline Color Styles'],
                    // Add more specific selectors for common patterns
                    ['.section', 'Generic Section'],
                    ['.container-fluid', 'Fluid Container'],
                    ['.row', 'Row'],
                    ['.col', 'Column'],
                    ['.card-body', 'Card Body'],
                    ['.card-title', 'Card Title'],
                    ['.card-text', 'Card Text'],
                    ['.btn-primary', 'Primary Button'],
                    ['.btn-secondary', 'Secondary Button'],
                    ['.text-center', 'Centered Text'],
                    ['.text-right', 'Right-aligned Text'],
                    ['.text-left', 'Left-aligned Text']
                ];

                selectors.forEach(([selector, label]) => {
                    const styleInfo = getElementStyles(selector, label);
                    if (styleInfo) {
                        if (Array.isArray(styleInfo)) {
                            // Limit to first 3 elements for selectors that match many elements
                            results.push(...styleInfo.slice(0, 3));
                        } else {
                            results.push(styleInfo);
                        }
                    }
                });

                return results;
            }
        """)

        # Format the styles information with better organization
        formatted_styles = []
        for style_info in styles_info:
            formatted_styles.append(f"\n/* {style_info['label']} ({style_info['selector']}) */")

            # Group related properties
            background_props = []
            text_props = []
            layout_props = []
            spacing_props = []
            border_props = []
            other_props = []

            for prop, value in style_info.items():
                if prop in ['label', 'selector', 'cssVariables'] or not value or value in ['none', 'auto', 'normal', 'initial', 'inherit']:
                    continue

                clean_prop = prop.replace('_', '-')
                clean_prop = re.sub(r'([A-Z])', r'-\1', clean_prop).lower()

                if 'background' in clean_prop:
                    background_props.append(f"  {clean_prop}: {value};")
                elif clean_prop in ['color', 'font-size', 'font-family', 'font-weight', 'line-height', 'text-align', 'text-decoration', 'text-transform', 'letter-spacing']:
                    text_props.append(f"  {clean_prop}: {value};")
                elif clean_prop in ['display', 'position', 'top', 'right', 'bottom', 'left', 'width', 'height', 'max-width', 'min-height', 'flex-direction', 'justify-content', 'align-items', 'grid-template-columns', 'grid-gap', 'z-index']:
                    layout_props.append(f"  {clean_prop}: {value};")
                elif 'padding' in clean_prop or 'margin' in clean_prop:
                    spacing_props.append(f"  {clean_prop}: {value};")
                elif 'border' in clean_prop or clean_prop in ['border-radius', 'box-shadow']:
                    border_props.append(f"  {clean_prop}: {value};")
                else:
                    other_props.append(f"  {clean_prop}: {value};")

            # Add CSS variables if present
            if 'cssVariables' in style_info and style_info['cssVariables']:
                formatted_styles.append("\n  /* CSS Variables */")
                for var_name, var_value in style_info['cssVariables'].items():
                    formatted_styles.append(f"  {var_name}: {var_value};")

            # Add pseudo-element styles if present
            for pseudo in ['::before', '::after']:
                if pseudo in style_info:
                    formatted_styles.append(f"\n  /* {pseudo} */")
                    formatted_styles.append("  {")
                    for prop, value in style_info[pseudo].items():
                        if value and value not in ['none', 'auto', 'normal', 'initial', 'inherit']:
                            formatted_styles.append(f"    {prop}: {value};")
                    formatted_styles.append("  }")

            # Add properties in logical order
            all_props = background_props + text_props + layout_props + spacing_props + border_props + other_props
            if all_props:
                formatted_styles.append("{")
                formatted_styles.extend(all_props)
                formatted_styles.append("}")

        return "\n".join(formatted_styles)

    except Exception as e:
        logger.warning(f"Could not extract comprehensive styles: {str(e)}")
        return ""

async def get_rendered_html(url: str) -> tuple[str, str, str, str, str, str]:
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

            # Wait a bit more for dynamic content and styles to load
            await page.wait_for_timeout(5000)

            # Extract visible text content with better structure preservation
            try:
                header_text = await page.locator("header").inner_text()
            except:
                header_text = ""

            try:
                main_text = await page.locator("main").inner_text()
            except:
                try:
                    # Fallback to body if no main
                    main_text = await page.locator("body").inner_text()
                    main_text = main_text[:2000]  # Increased limit
                except:
                    main_text = ""

            try:
                footer_text = await page.locator("footer").inner_text()
            except:
                footer_text = ""

            visible_text_summary = f"Header: {header_text[:400]}\n\nMain: {main_text[:1200]}\n\nFooter: {footer_text[:300]}"

            # Get comprehensive computed styles
            logger.info("Extracting comprehensive styles...")
            computed_styles_str = await get_comprehensive_styles(page)

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

            # Clean HTML while preserving structure
            cleaned_html = clean_html_preserve_structure(soup)

            # Extract inline <style> tags and linked stylesheets with better parsing
            styles = soup.find_all('style')
            style_text = "\n".join(style.get_text() for style in styles if style.get_text())

            # Also extract inline styles from elements
            inline_styles = []
            for element in soup.find_all(attrs={"style": True}):
                if element.get('style'):
                    tag_name = element.name
                    classes = ' '.join(element.get('class', []))
                    element_id = element.get('id', '')

                    selector = tag_name
                    if element_id:
                        selector += f"#{element_id}"
                    if classes:
                        selector += f".{classes.replace(' ', '.')}"

                    inline_styles.append(f"/* Inline: {selector} */\n{selector} {{ {element['style']} }}")

            if inline_styles:
                style_text += "\n\n/* INLINE STYLES */\n" + "\n".join(inline_styles)

            # Get layout summary
            logger.info("Extracting layout summary...")
            layout_summary = summarize_layout(soup)

            logger.info(f"Cleaned HTML length: {len(cleaned_html)}")
            logger.info(f"Extracted styles length: {len(style_text)}")
            logger.info(f"Computed styles length: {len(computed_styles_str)}")
            logger.info(f"Layout summary: {layout_summary}")

        except Exception as e:
            logger.error(f"Playwright error: {str(e)}")
            cleaned_html = f"<html><body><h2>Playwright Error</h2><p>{str(e)}</p></body></html>"
            layout_summary = "Could not extract layout"
            screenshot_base64 = ""
            style_text = ""
            visible_text_summary = ""
            computed_styles_str = ""

        finally:
            await browser.close()

        return cleaned_html, screenshot_base64, layout_summary, style_text, visible_text_summary, computed_styles_str
