from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import uvicorn
#from app.cloner import scrape_website, generate_html_from_context
from app.rendered_scraper import get_rendered_html
from fastapi import HTTPException
from collections import Counter
import logging
import re
import os
import requests
import json
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI instance
app = FastAPI(
    title="Orchids Challenge API",
    description="A starter FastAPI template for the Orchids Challenge backend",
    version="1.0.0"
)

# Serve static files from the 'static' directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CloneRequest(BaseModel):
    url: str

def extract_visual_color_map(computed_styles_str: str) -> dict:
    color_map = {}

    try:
        style_entries = json.loads(computed_styles_str)
        for entry in style_entries:
            selector = entry.get("selector")
            if not selector:
                continue

            bg = entry.get("backgroundColor")
            text = entry.get("color")

            if (bg and bg != "transparent") or (text and text != "inherit"):
                color_map[selector] = {
                    "background": bg,
                    "text": text
                }

    except Exception as e:
        logger.warning(f"Failed to parse computed_styles JSON: {e}")

    return color_map


def generate_html_phased(prompt_parts: dict, screenshot_b64: str) -> str:
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    # Phase 1: Layout
    layout_prompt = f"""
You are a web layout expert. Based on the following screenshot and layout summary, generate only the HTML structure of the page. Do not add any CSS or styling.

Screenshot:
[screenshot]

Layout Summary:
{prompt_parts['layout_summary']}

JavaScript Interactions Summary:
{prompt_parts['js_summary']}

Visible Content Summary:
{prompt_parts['visible_text']}

Output only raw HTML with semantic tags (header, main, section, nav, footer, etc.). Do not style.
"""

    logger.info("Starting Phase 1: Layout")

    phase1 = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json={
        "model": "claude-3-opus-20240229",
        "max_tokens": 3000,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": layout_prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot_b64
                        }
                    }
                ]
            }
        ]
    })
    phase1_html = phase1.json()["content"][0]["text"]
    logger.info(f"Phase 1 HTML length: {len(phase1_html)}")

    # Phase 2: Styling
    styling_prompt = f"""
You are a frontend developer.

Your task is to apply internal CSS styles to the following raw HTML layout, based on:
- 📷 The provided screenshot of the original website
- 🧱 The semantic HTML structure generated in Phase 1
- 🎨 The extracted design tokens (colors, typography, spacing, layout)

Your goal is to recreate the original visual appearance and feel of the target website.

🎨 Section + Class Colors:
Apply the following CSS rules to their corresponding elements. Section tags (like `header`, `footer`, etc.) should use the section styles. Class selectors apply to elements using those classes.
{prompt_parts['color_summary']}

🔤 Typography:
- Use primary fonts across the page
- Apply bold weights and large sizes to <h1> and <h2>
- Use smaller, readable fonts for <p> and <a>
{prompt_parts['typography_summary']}

📐 Layout Tokens:
{prompt_parts['layout_tokens']}

📏 Spacing System:
- Use margin and padding values between sections and around text blocks
- Keep spacing consistent across buttons, headers, and content areas
{prompt_parts['spacing_tokens']}

🎮 JavaScript Interactions:
Try to visually reflect these interactive elements where possible (e.g. sliders, modals, dropdowns):
{prompt_parts['js_summary']}

🛠 Instructions:
- Insert a <style> tag inside the <head> of the HTML
- Apply styles using CSS selectors — not inline styles
- Add class names if necessary for cleaner styling
- **Do not alter the HTML structure**

✅ Final Check:
Before submitting:
- Confirm that the <style> tag is included
- Apply all key colors and fonts
- Visually style at least one heading, one link, one button, and one section

📄 HTML Layout to Style:
{phase1_html}
"""


    logger.info("Starting Phase 2: Styling")

    phase2 = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json={
        "model": "claude-3-opus-20240229",
        "max_tokens": 3500,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": styling_prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot_b64
                        }
                    }
                ]
            }
        ]
    })
    phase2_html = phase2.json()["content"][0]["text"]
    logger.info(f"Phase 2 HTML length: {len(phase2_html)}")

    # Phase 3: Content Filling
    content_prompt = f"""
You are a web content assistant.

This is Phase 3 of a 3-phase cloning process. You are given:
- A screenshot of the original website (for spatial and visual context)
- A styled HTML layout generated in Phase 2
- A visible text summary extracted from the original site
- A summary of JavaScript behaviors

Your job is to **insert the correct textual content** into the appropriate sections of the HTML, using the screenshot and visible summary to guide placement.

📄 Visible Content Summary:
{prompt_parts['visible_text']}

🎮 JavaScript Interactions (for context only):
{prompt_parts['js_summary']}

🧱 HTML Layout (from Phase 2):
{phase2_html}

🛠 Instructions:
- DO NOT change the HTML structure or the <style> block
- DO NOT generate extra styles or placeholder content
- Just fill in real content where it belongs, preserving layout and visual integrity

✅ Final Output:
A complete HTML page with content placed accurately into the given layout, matching the original site.
"""

    logger.info("Starting Phase 3: Content Filling")

    phase3 = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json={
        "model": "claude-3-opus-20240229",
        "max_tokens": 3500,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": content_prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot_b64
                        }
                    }
                ]
            }
        ]
    })
    final_html = phase3.json()["content"][0]["text"]
    logger.info(f"Final HTML length: {len(final_html)}")

    return final_html


def summarize_spacing_system(computed_styles: str) -> dict:
    margin_values = []
    padding_values = []

    for line in computed_styles.split("\n"):
        line = line.strip()
        if "margin" in line and ":" in line and "auto" not in line:
            values = re.findall(r"(\d+px)", line)
            margin_values.extend(values)

        if "padding" in line and ":" in line:
            values = re.findall(r"(\d+px)", line)
            padding_values.extend(values)

    margin_counts = Counter(margin_values).most_common(5)
    padding_counts = Counter(padding_values).most_common(5)

    return {
        "common_margins": [m[0] for m in margin_counts],
        "common_paddings": [p[0] for p in padding_counts]
    }


def summarize_layout_system(computed_styles: str) -> dict:
    layout_methods = {
        "flex": 0,
        "grid": 0,
        "block": 0,
        "inline-block": 0,
        "absolute": 0,
        "relative": 0,
        "fixed": 0,
        "sticky": 0,
        "float": 0
    }

    for line in computed_styles.split("\n"):
        line = line.strip()

        if "display:" in line:
            if "flex" in line:
                layout_methods["flex"] += 1
            elif "grid" in line:
                layout_methods["grid"] += 1
            elif "block" in line:
                layout_methods["block"] += 1
            elif "inline-block" in line:
                layout_methods["inline-block"] += 1

        if "position:" in line:
            if "absolute" in line:
                layout_methods["absolute"] += 1
            elif "relative" in line:
                layout_methods["relative"] += 1
            elif "fixed" in line:
                layout_methods["fixed"] += 1
            elif "sticky" in line:
                layout_methods["sticky"] += 1

        if "float:" in line:
            layout_methods["float"] += 1

    # Filter to top used layout methods
    layout_summary = {k: v for k, v in layout_methods.items() if v > 0}
    return layout_summary



def summarize_typography(computed_styles: str) -> dict:
    fonts = []
    font_sizes = []
    font_weights = []

    for line in computed_styles.split("\n"):
        line = line.strip()

        if "font-family" in line:
            match = re.search(r"font-family:\s*([^;]+);", line)
            if match:
                fonts.append(match.group(1).strip())

        elif "font-size" in line:
            match = re.search(r"font-size:\s*([^;]+);", line)
            if match:
                font_sizes.append(match.group(1).strip())

        elif "font-weight" in line:
            match = re.search(r"font-weight:\s*([^;]+);", line)
            if match:
                font_weights.append(match.group(1).strip())

    # Count most common items
    top_fonts = Counter(fonts).most_common(3)
    top_sizes = Counter(font_sizes).most_common(3)
    top_weights = Counter(font_weights).most_common(3)

    return {
        "font_families": [f[0] for f in top_fonts],
        "font_sizes": [s[0] for s in top_sizes],
        "font_weights": [w[0] for w in top_weights],
    }


def generate_html_with_claude(prompt: str, screenshot_b64: str) -> str:
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 4000,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot_b64
                        }
                    }
                ]
            }
        ]
    }

    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"Claude API error: {response.status_code} - {response.text}")

    output = response.json()
    return output["content"][0]["text"]


def extract_section_styles(computed_styles: str) -> dict:
    """Extract styles organized by page sections"""
    sections = {
        'header': {'bg': [], 'text': [], 'fonts': []},
        'main': {'bg': [], 'text': [], 'fonts': []},
        'body': {'bg': [], 'text': [], 'fonts': []},
        'nav': {'bg': [], 'text': [], 'fonts': []},
        'footer': {'bg': [], 'text': [], 'fonts': []},
        'buttons': {'bg': [], 'text': [], 'fonts': []},
        'general': {'bg': [], 'text': [], 'fonts': []}
    }

    current_section = 'general'
    lines = computed_styles.split('\n')

    for line in lines:
        line = line.strip()

        # Detect section changes based on comments
        if '/*' in line and '*/' in line:
            line_lower = line.lower()
            if 'header' in line_lower:
                current_section = 'header'
            elif 'main' in line_lower:
                current_section = 'main'
            elif 'body' in line_lower:
                current_section = 'body'
            elif 'nav' in line_lower:
                current_section = 'nav'
            elif 'footer' in line_lower:
                current_section = 'footer'
            elif 'button' in line_lower:
                current_section = 'buttons'
            else:
                current_section = 'general'
            continue

        # Extract colors and fonts for current section
        if ("background-color" in line or "background:" in line) and "rgb" in line:
            color = line.split(':')[1].strip().rstrip(';')
            if 'rgba(0, 0, 0, 0)' not in color and color not in sections[current_section]['bg']:
                sections[current_section]['bg'].append(color)
        elif 'color:' in line and 'rgb' in line:
            color = line.split(':')[1].strip().rstrip(';')
            if color not in sections[current_section]['text']:
                sections[current_section]['text'].append(color)
        elif 'font-family:' in line:
            font = line.split(':')[1].strip().rstrip(';')
            if font not in sections[current_section]['fonts']:
                sections[current_section]['fonts'].append(font)

    return sections

def extract_layout_patterns(html_structure: str) -> dict:
    """Extract common layout patterns and class names"""
    patterns = {
        'containers': [],
        'headers': [],
        'navigation': [],
        'buttons': [],
        'cards': [],
        'sections': []
    }

    # Find class patterns
    class_matches = re.findall(r'class="([^"]*)"', html_structure)
    for classes in class_matches:
        class_list = classes.split()
        for cls in class_list:
            if any(word in cls.lower() for word in ['container', 'wrap', 'main']):
                if cls not in patterns['containers']:
                    patterns['containers'].append(cls)
            elif any(word in cls.lower() for word in ['header', 'hero', 'banner']):
                if cls not in patterns['headers']:
                    patterns['headers'].append(cls)
            elif any(word in cls.lower() for word in ['nav', 'menu']):
                if cls not in patterns['navigation']:
                    patterns['navigation'].append(cls)
            elif any(word in cls.lower() for word in ['btn', 'button']):
                if cls not in patterns['buttons']:
                    patterns['buttons'].append(cls)
            elif any(word in cls.lower() for word in ['card', 'item', 'product']):
                if cls not in patterns['cards']:
                    patterns['cards'].append(cls)
            elif any(word in cls.lower() for word in ['section', 'block', 'area']):
                if cls not in patterns['sections']:
                    patterns['sections'].append(cls)

    return patterns

def create_enhanced_prompt(visible_text: str, html_structure: str, section_styles: dict, layout_patterns: dict, layout_summary: str) -> str:
    """Create a section-aware prompt with better styling instructions"""

    # Limit content
    text_content = visible_text[:1200]
    html_content = html_structure[:2500]

    # Build section-specific styles
    style_instructions = []

    # Header/Hero section
    if section_styles['header']['bg'] or section_styles['header']['text']:
        header_bg = section_styles['header']['bg'][0] if section_styles['header']['bg'] else 'rgb(0, 0, 0)'
        header_text = section_styles['header']['text'][0] if section_styles['header']['text'] else 'rgb(255, 255, 255)'
        style_instructions.append(f"Header/Hero section: background {header_bg}, text color {header_text}")

    # Main content area
    if section_styles['main']['bg'] or section_styles['body']['bg']:
        main_bg = (section_styles['main']['bg'] + section_styles['body']['bg'])[0] if (section_styles['main']['bg'] + section_styles['body']['bg']) else 'rgb(255, 255, 255)'
        main_text = (section_styles['main']['text'] + section_styles['body']['text'])[0] if (section_styles['main']['text'] + section_styles['body']['text']) else 'rgb(0, 0, 0)'
        style_instructions.append(f"Main content: background {main_bg}, text color {main_text}")

    # Navigation
    if section_styles['nav']['bg'] or section_styles['nav']['text']:
        nav_bg = section_styles['nav']['bg'][0] if section_styles['nav']['bg'] else 'transparent'
        nav_text = section_styles['nav']['text'][0] if section_styles['nav']['text'] else 'inherit'
        style_instructions.append(f"Navigation: background {nav_bg}, text color {nav_text}")

    # Buttons
    if section_styles['buttons']['bg'] or section_styles['buttons']['text']:
        btn_bg = section_styles['buttons']['bg'][0] if section_styles['buttons']['bg'] else 'rgb(0, 123, 255)'
        btn_text = section_styles['buttons']['text'][0] if section_styles['buttons']['text'] else 'rgb(255, 255, 255)'
        style_instructions.append(f"Buttons: background {btn_bg}, text color {btn_text}")

    # Footer
    if section_styles['footer']['bg'] or section_styles['footer']['text']:
        footer_bg = section_styles['footer']['bg'][0] if section_styles['footer']['bg'] else 'rgb(248, 249, 250)'
        footer_text = section_styles['footer']['text'][0] if section_styles['footer']['text'] else 'rgb(108, 117, 125)'
        style_instructions.append(f"Footer: background {footer_bg}, text color {footer_text}")

    # Get primary font
    all_fonts = []
    for section in section_styles.values():
        all_fonts.extend(section['fonts'])
    primary_font = all_fonts[0] if all_fonts else 'Arial, sans-serif'

    prompt = f"""Create a complete HTML page that recreates this website design.

CONTENT:
{text_content}

SECTION STYLING:
{chr(10).join(style_instructions)}
Primary font: {primary_font}

LAYOUT INFO: {layout_summary}

KEY CLASSES FOUND: {', '.join(layout_patterns['containers'][:3] + layout_patterns['headers'][:2] + layout_patterns['buttons'][:2])}

HTML STRUCTURE REFERENCE:
{html_content}

INSTRUCTIONS:
1. Create complete HTML with DOCTYPE
2. Use internal CSS in <style> tags
3. Apply the section-specific colors above
4. Use the class names from the original
5. Create distinct visual sections (header, main, footer)
6. Style buttons, navigation, and content areas differently
7. Make text readable with proper contrast
8. Include proper spacing and layout

Generate the complete HTML:"""

    return prompt

@app.post("/clone")
async def clone_site(request: CloneRequest):
    try:
        logger.info(f"Starting to clone: {request.url}")

        # Get rendered HTML and other data
        rendered_html, screenshot_b64, layout_summary, style_text, visible_text_summary, computed_styles_str, js_behavior_summary, section_colors, computed_styles_json = await get_rendered_html(request.url)

        visual_color_map = extract_visual_color_map(computed_styles_str)
        logger.info(f"Class-based color map: {visual_color_map}")

        typography = summarize_typography(computed_styles_str)
        logger.info(f"Typography summary: {typography}")

        layout_info = summarize_layout_system(computed_styles_str)
        logger.info(f"Layout system detected: {layout_info}")

        spacing_info = summarize_spacing_system(computed_styles_str)
        logger.info(f"Spacing system: {spacing_info}")

        # ---- Build unified color summary ----
        color_summary = "/* COMPREHENSIVE STYLES - PRIMARY COLORS */\n"

        priority_patterns = ['.btn', '.button', '.nav', '.header', '.footer', '.hero', '.banner', '.card']
        skip_selectors = ['div', 'span', 'p', 'a', 'body', '[style*="background"]', '[style*="color"]']
        seen = set()

        # Split selectors into important and regular
        important_selectors = []
        regular_selectors = []

        for item in computed_styles_json:
            selector = item.get("selector", "").strip()
            if not selector:
                continue

            if any(p in selector.lower() for p in priority_patterns):
                important_selectors.append(item)
            else:
                regular_selectors.append(item)

        # Combine and process
        for item in important_selectors + regular_selectors[:10]:  # Limit regulars for clarity
            selector = item.get("selector", "").strip()
            background = item.get("backgroundColor")
            text_color = item.get("color")

            # 🛑 Skip generic or useless selectors
            if selector in skip_selectors:
                continue

            # 🧼 Clean meaningless color values
            if background in ["transparent", "rgba(0, 0, 0, 0)", "inherit", "initial"]:
                background = None
            if text_color in ["inherit", "initial", "currentcolor"]:
                text_color = None

            if not background and not text_color:
                continue

            # ✅ Deduplicate
            key = (selector, background, text_color)
            if key in seen:
                continue
            seen.add(key)

            # ✅ Format
            css_lines = [f"{selector} {{"]
            if background:
                css_lines.append(f"  background-color: {background};")
            if text_color:
                css_lines.append(f"  color: {text_color};")
            css_lines.append("}")

            color_summary += "\n".join(css_lines) + "\n"

        # ✳️ Add fallback section styles
        color_summary += "\n\n/* SECTION FALLBACKS */\n"
        for section, colors in section_colors.items():
            bg = colors.get("background", "transparent")
            text = colors.get("text", "inherit")
            color_summary += f"{section} {{ background-color: {bg}; color: {text}; }}\n"

        typography_summary = f"""
        TYPOGRAPHY SYSTEM:
        - Font families: {', '.join(typography['font_families'])}
        - Font sizes: {', '.join(typography['font_sizes'])}
        - Font weights: {', '.join(typography['font_weights'])}
        """
        layout_summary_text = f"""
        LAYOUT SYSTEM:
        {', '.join(f"{key}: {val} uses" for key, val in layout_info.items())}
        """
        spacing_summary_text = f"""
        SPACING SYSTEM:
        - Common margins: {', '.join(spacing_info['common_margins'])}
        - Common paddings: {', '.join(spacing_info['common_paddings'])}
        """


        logger.info(f"Data extracted successfully")

        # Extract section-specific styles
        section_styles = extract_section_styles(computed_styles_str)

        # Extract layout patterns
        layout_patterns = extract_layout_patterns(rendered_html)

        logger.info(f"Section styles: {section_styles}")
        logger.info(f"Layout patterns: {layout_patterns}")

        # Create enhanced prompt
        prompt = create_enhanced_prompt(
            visible_text_summary,
            rendered_html,
            section_styles,
            layout_patterns,
            layout_summary
        )

        logger.info(f"Prompt created, length: {len(prompt)}")

        # 🔸 Extract top 5 visually important selectors for emphasis
        primary_colors = []
        priority_patterns = ['.btn', '.button', '.nav', '.header', '.footer', '.hero', '.banner', '.card']
        highlighted = 0

        for item in computed_styles_json:
            selector = item.get("selector", "")
            bg = item.get("backgroundColor")
            text = item.get("color")

            if any(p in selector.lower() for p in priority_patterns):
                if bg or text:
                    primary_colors.append(f"{selector}: bg={bg}, text={text}")
                    highlighted += 1
            if highlighted >= 5:
                break
        color_emphasis = f"""
        🎨 KEY COLORS (Apply these first):
        {chr(10).join(primary_colors)}

        🎨 COMPLETE COLOR SYSTEM:
        {color_summary}
        """

        # Generate HTML using the LLM
        prompt_parts = {
            "layout_summary": layout_summary,
            "color_summary": color_emphasis,
            "typography_summary": typography_summary,
            "layout_tokens": layout_summary_text,
            "spacing_tokens": spacing_summary_text,
            "visible_text": visible_text_summary,
            "js_summary": js_behavior_summary,
        }
        html = generate_html_phased(prompt_parts, screenshot_b64)


        logger.info(f"Generated HTML length: {len(html)}")

        if not html or html.strip() == "":
            logger.error("LLM returned empty response")
            raise HTTPException(status_code=500, detail="LLM returned empty response")

        # Check if we got a refusal
        if any(word in html.lower() for word in ["can't", "cannot", "basic structure", "not possible", "too complex"]):
            logger.warning("LLM refused, trying fallback")

            # Simplified fallback
            fallback_prompt = f"""Create an HTML page with this content:

{visible_text_summary[:800]}

Make it look good with:
- Dark header with white text
- Light main content with dark text
- Styled buttons and sections
- Proper spacing and fonts

Complete HTML with internal CSS:"""

            html = generate_html_from_context(fallback_prompt)

        # Ensure we have valid HTML
        if not ("<html" in html.lower() or "<!doctype" in html.lower()):
            html = f"<!DOCTYPE html><html><head><title>Cloned Site</title></head><body>{html}</body></html>"

        return {"html": html, "status": "success"}

    except Exception as e:
        logger.error(f"Error in clone_site: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clone website: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI backend!", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orchids-challenge-api"}

def main():
    """Run the application"""
    uvicorn.run(
        "hello:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
