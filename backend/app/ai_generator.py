import logging
import json
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import base64

logger = logging.getLogger(__name__)

class AIHTMLGenerator:
    """AI-powered HTML generator with intelligent layout reconstruction"""

    def __init__(self, scraped_data: dict, design_tokens: dict, layout_analysis: dict):
        self.scraped_data = scraped_data
        self.design_tokens = design_tokens
        self.layout_analysis = layout_analysis
        self.components = []

    def generate_enhanced_html(self) -> str:
        """Generate enhanced HTML using AI-like analysis"""
        try:
            # Analyze and extract components
            self._analyze_page_components()

            # Generate CSS based on extracted styles
            css = self._generate_enhanced_css()

            # Generate HTML structure
            html_structure = self._generate_html_structure()

            # Combine everything
            full_html = self._combine_html_and_css(html_structure, css)

            return full_html

        except Exception as e:
            logger.error(f"Error in AI HTML generation: {str(e)}")
            return self._fallback_html()

    def _analyze_page_components(self):
        """Analyze page and extract reusable components"""
        semantic_analysis = self.scraped_data.get('semantic_analysis', {})
        computed_styles = self.scraped_data.get('computed_styles', [])

        # Extract navigation component
        if 'nav' in semantic_analysis.get('sections', []):
            nav_component = self._extract_navigation_component()
            if nav_component:
                self.components.append(nav_component)

        # Extract header component
        if 'header' in semantic_analysis.get('sections', []):
            header_component = self._extract_header_component()
            if header_component:
                self.components.append(header_component)

        # Extract content sections
        content_sections = self._extract_content_sections()
        self.components.extend(content_sections)

        # Extract footer component
        if 'footer' in semantic_analysis.get('sections', []):
            footer_component = self._extract_footer_component()
            if footer_component:
                self.components.append(footer_component)

    def _extract_navigation_component(self) -> dict:
        """Extract navigation component with styling"""
        nav_elements = self.scraped_data.get('semantic_analysis', {}).get('navigation_elements', [])

        if not nav_elements:
            return None

        # Find navigation styles
        nav_styles = {}
        for style_data in self.scraped_data.get('computed_styles', []):
            if 'nav' in style_data.get('selector', '').lower():
                nav_styles.update(style_data.get('styles', {}))

        return {
            'type': 'navigation',
            'styles': nav_styles,
            'data': nav_elements[0] if nav_elements else {},
            'priority': 10
        }

    def _extract_header_component(self) -> dict:
        """Extract header component"""
        text_content = self.scraped_data.get('text_content', {})
        header_text = text_content.get('header', '')

        # Find header styles
        header_styles = {}
        for style_data in self.scraped_data.get('computed_styles', []):
            if style_data.get('label', '').lower() in ['header', 'main heading']:
                header_styles.update(style_data.get('styles', {}))

        return {
            'type': 'header',
            'styles': header_styles,
            'content': header_text,
            'priority': 9
        }

    def _extract_content_sections(self) -> List[dict]:
        """Extract main content sections"""
        sections = []
        text_content = self.scraped_data.get('text_content', {})
        headings = text_content.get('headings', [])
        paragraphs = text_content.get('paragraphs', [])

        # Main content section
        main_content = text_content.get('main', '')
        if main_content:
            main_styles = {}
            for style_data in self.scraped_data.get('computed_styles', []):
                if style_data.get('label', '').lower() in ['main content', 'paragraph']:
                    main_styles.update(style_data.get('styles', {}))

            sections.append({
                'type': 'main_content',
                'styles': main_styles,
                'content': main_content,
                'headings': headings,
                'paragraphs': paragraphs,
                'priority': 8
            })

        return sections

    def _extract_footer_component(self) -> dict:
        """Extract footer component"""
        text_content = self.scraped_data.get('text_content', {})
        footer_text = text_content.get('footer', '')

        # Find footer styles
        footer_styles = {}
        for style_data in self.scraped_data.get('computed_styles', []):
            if 'footer' in style_data.get('selector', '').lower():
                footer_styles.update(style_data.get('styles', {}))

        return {
            'type': 'footer',
            'styles': footer_styles,
            'content': footer_text,
            'priority': 5
        }

    def _generate_enhanced_css(self) -> str:
        """Generate enhanced CSS based on extracted styles"""
        css_parts = []

        # Reset and base styles
        css_parts.append(self._generate_reset_css())

        # CSS Variables from design tokens
        css_parts.append(self._generate_css_variables())

        # Component-specific styles
        for component in self.components:
            component_css = self._generate_component_css(component)
            if component_css:
                css_parts.append(component_css)

        # Layout styles
        css_parts.append(self._generate_layout_css())

        # Responsive styles
        css_parts.append(self._generate_responsive_css())

        return '\n\n'.join(filter(None, css_parts))

    def _generate_reset_css(self) -> str:
        """Generate CSS reset"""
        return """/* CSS Reset */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

img {
    max-width: 100%;
    height: auto;
}

a {
    text-decoration: none;
    color: inherit;
}

button {
    border: none;
    background: none;
    cursor: pointer;
}"""

    def _generate_css_variables(self) -> str:
        """Generate CSS custom properties from design tokens"""
        colors = self.design_tokens.get('colors', {})
        typography = self.design_tokens.get('typography', {})

        # Extract color values
        primary_color = colors.get('primary', ['#007bff'])[0] if colors.get('primary') else '#007bff'
        text_color = colors.get('text', ['#333333'])[0] if colors.get('text') else '#333333'
        bg_color = colors.get('background', ['#ffffff'])[0] if colors.get('background') else '#ffffff'

        # Extract font
        primary_font = typography.get('primary_font', 'Arial, sans-serif')

        return f"""/* CSS Variables */
:root {{
    --color-primary: {primary_color};
    --color-secondary: #6c757d;
    --color-text: {text_color};
    --color-text-light: #666666;
    --color-background: {bg_color};
    --color-background-light: #f8f9fa;
    --color-border: #e0e0e0;

    --font-primary: {primary_font};
    --font-size-base: 16px;
    --font-size-sm: 14px;
    --font-size-lg: 18px;
    --font-size-xl: 24px;
    --font-size-xxl: 32px;

    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --spacing-xxl: 3rem;

    --border-radius: 0.375rem;
    --box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    --transition: all 0.3s ease;
}}"""

    def _generate_component_css(self, component: dict) -> str:
        """Generate CSS for a specific component"""
        component_type = component.get('type')
        styles = component.get('styles', {})

        if component_type == 'navigation':
            return self._generate_navigation_css(styles)
        elif component_type == 'header':
            return self._generate_header_css(styles)
        elif component_type == 'main_content':
            return self._generate_main_content_css(styles)
        elif component_type == 'footer':
            return self._generate_footer_css(styles)

        return ""

    def _generate_navigation_css(self, styles: dict) -> str:
        """Generate navigation CSS"""
        bg_color = styles.get('backgroundColor', 'var(--color-background-light)')

        return f"""/* Navigation */
.navbar {{
    background-color: {bg_color};
    padding: var(--spacing-md) 0;
    border-bottom: 1px solid var(--color-border);
    position: sticky;
    top: 0;
    z-index: 1000;
}}

.navbar .container {{
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.navbar-brand {{
    font-size: var(--font-size-xl);
    font-weight: bold;
    color: var(--color-primary);
}}

.navbar-nav {{
    display: flex;
    list-style: none;
    gap: var(--spacing-lg);
}}

.navbar-nav a {{
    color: var(--color-text);
    font-weight: 500;
    transition: var(--transition);
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--border-radius);
}}

.navbar-nav a:hover {{
    color: var(--color-primary);
    background-color: rgba(0, 123, 255, 0.1);
}}"""

    def _generate_header_css(self, styles: dict) -> str:
        """Generate header CSS"""
        bg_color = styles.get('backgroundColor', 'var(--color-primary)')
        color = styles.get('color', 'white')

        return f"""/* Header */
.hero {{
    background: {bg_color};
    color: {color};
    padding: var(--spacing-xxl) 0;
    text-align: center;
}}

.hero h1 {{
    font-size: var(--font-size-xxl);
    font-weight: bold;
    margin-bottom: var(--spacing-md);
    line-height: 1.2;
}}

.hero p {{
    font-size: var(--font-size-lg);
    opacity: 0.9;
    max-width: 600px;
    margin: 0 auto var(--spacing-lg);
}}

.hero .btn {{
    display: inline-block;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    padding: var(--spacing-md) var(--spacing-xl);
    border-radius: var(--border-radius);
    font-weight: 600;
    transition: var(--transition);
    border: 2px solid rgba(255, 255, 255, 0.3);
}}

.hero .btn:hover {{
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-2px);
}}"""

    def _generate_main_content_css(self, styles: dict) -> str:
        """Generate main content CSS"""
        return """/* Main Content */
.main-content {
    padding: var(--spacing-xxl) 0;
}

.content-section {
    margin-bottom: var(--spacing-xxl);
}

.content-section h2 {
    font-size: var(--font-size-xl);
    margin-bottom: var(--spacing-lg);
    color: var(--color-text);
}

.content-section p {
    font-size: var(--font-size-base);
    line-height: 1.7;
    margin-bottom: var(--spacing-md);
    color: var(--color-text-light);
}

.card {
    background: var(--color-background);
    border-radius: var(--border-radius);
    padding: var(--spacing-xl);
    box-shadow: var(--box-shadow);
    margin-bottom: var(--spacing-lg);
}

.btn {
    display: inline-block;
    background: var(--color-primary);
    color: white;
    padding: var(--spacing-md) var(--spacing-lg);
    border-radius: var(--border-radius);
    font-weight: 600;
    transition: var(--transition);
    text-align: center;
}

.btn:hover {
    background: var(--color-secondary);
    transform: translateY(-2px);
}"""

    def _generate_footer_css(self, styles: dict) -> str:
        """Generate footer CSS"""
        bg_color = styles.get('backgroundColor', 'var(--color-background-light)')

        return f"""/* Footer */
.footer {{
    background: {bg_color};
    padding: var(--spacing-xxl) 0;
    border-top: 1px solid var(--color-border);
    margin-top: var(--spacing-xxl);
}}

.footer p {{
    color: var(--color-text-light);
    text-align: center;
    font-size: var(--font-size-sm);
}}"""

    def _generate_layout_css(self) -> str:
        """Generate layout CSS"""
        layout_type = self.layout_analysis.get('layout_type', 'block')

        layout_css = """/* Layout */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--spacing-md);
}

.container-fluid {
    width: 100%;
    padding: 0 var(--spacing-md);
}

.section {
    padding: var(--spacing-xxl) 0;
}"""

        if layout_type == 'grid':
            layout_css += """
.grid {
    display: grid;
    gap: var(--spacing-lg);
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}"""
        elif layout_type == 'flexbox':
            layout_css += """
.flex {
    display: flex;
    gap: var(--spacing-lg);
}

.flex-wrap {
    flex-wrap: wrap;
}

.flex-center {
    justify-content: center;
    align-items: center;
}"""

        return layout_css

    def _generate_responsive_css(self) -> str:
        """Generate responsive CSS"""
        breakpoints = self.scraped_data.get('responsive_info', {}).get('breakpoints', [768, 1024])

        responsive_css = """/* Responsive Design */
@media (max-width: 768px) {
    .container {
        padding: 0 var(--spacing-sm);
    }

    .hero h1 {
        font-size: var(--font-size-xl);
    }

    .navbar .container {
        flex-direction: column;
        gap: var(--spacing-md);
    }

    .navbar-nav {
        flex-direction: column;
        width: 100%;
        text-align: center;
    }

    .grid {
        grid-template-columns: 1fr;
    }

    .flex {
        flex-direction: column;
    }
}

@media (max-width: 480px) {
    .hero {
        padding: var(--spacing-xl) 0;
    }

    .hero h1 {
        font-size: var(--font-size-lg);
    }

    .card {
        padding: var(--spacing-md);
    }
}"""

        return responsive_css

    def _generate_html_structure(self) -> str:
        """Generate HTML structure based on components"""
        html_parts = []

        # Sort components by priority
        sorted_components = sorted(self.components, key=lambda x: x.get('priority', 0), reverse=True)

        for component in sorted_components:
            component_html = self._generate_component_html(component)
            if component_html:
                html_parts.append(component_html)

        return '\n'.join(html_parts)

    def _generate_component_html(self, component: dict) -> str:
        """Generate HTML for a component"""
        component_type = component.get('type')

        if component_type == 'navigation':
            return self._generate_navigation_html(component)
        elif component_type == 'header':
            return self._generate_header_html(component)
        elif component_type == 'main_content':
            return self._generate_main_content_html(component)
        elif component_type == 'footer':
            return self._generate_footer_html(component)

        return ""

    def _generate_navigation_html(self, component: dict) -> str:
        """Generate navigation HTML"""
        return """    <nav class="navbar">
        <div class="container">
            <div class="navbar-brand">Brand</div>
            <ul class="navbar-nav">
                <li><a href="#home">Home</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#services">Services</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </div>
    </nav>"""

    def _generate_header_html(self, component: dict) -> str:
        """Generate header HTML"""
        content = component.get('content', '')
        title = content.split('\n')[0] if content else 'Welcome'
        subtitle = content.split('\n')[1] if '\n' in content else 'Discover amazing content'

        return f"""    <header class="hero">
        <div class="container">
            <h1>{title[:50] or 'Welcome'}</h1>
            <p>{subtitle[:100] or 'Discover amazing content and services'}</p>
            <a href="#learn-more" class="btn">Learn More</a>
        </div>
    </header>"""

    def _generate_main_content_html(self, component: dict) -> str:
        """Generate main content HTML"""
        content = component.get('content', '')
        headings = component.get('headings', [])
        paragraphs = component.get('paragraphs', [])

        sections_html = []

        # Use headings and paragraphs if available
        if headings and paragraphs:
            for i, heading in enumerate(headings[:3]):
                section_content = paragraphs[i] if i < len(paragraphs) else 'Content coming soon...'
                sections_html.append(f"""            <div class="content-section">
                <h2>{heading.get('text', f'Section {i+1}')}</h2>
                <p>{section_content[:300]}</p>
            </div>""")
        else:
            # Fallback to content splitting
            content_parts = content.split('\n\n') if content else ['Welcome to our website']
            for i, part in enumerate(content_parts[:3]):
                if part.strip():
                    if i == 0:
                        sections_html.append(f"""            <div class="content-section">
                <h2>{part.strip()[:100]}</h2>
            </div>""")
                    else:
                        sections_html.append(f"""            <div class="content-section">
                <p>{part.strip()[:300]}</p>
            </div>""")

        sections_content = '\n'.join(sections_html) if sections_html else """            <div class="content-section">
                <h2>Welcome</h2>
                <p>This is the main content area of the website.</p>
            </div>"""

        return f"""    <main class="main-content">
        <div class="container">
{sections_content}
            <div class="content-section">
                <a href="#contact" class="btn">Get Started</a>
            </div>
        </div>
    </main>"""

    def _generate_footer_html(self, component: dict) -> str:
        """Generate footer HTML"""
        content = component.get('content', '')
        footer_text = content[:100] if content else '© 2024 All rights reserved.'

        return f"""    <footer class="footer">
        <div class="container">
            <p>{footer_text}</p>
        </div>
    </footer>"""

    def _combine_html_and_css(self, html_structure: str, css: str) -> str:
        """Combine HTML structure with CSS"""
        title = self.scraped_data.get('text_content', {}).get('title', 'Cloned Website')

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{css}
    </style>
</head>
<body>
{html_structure}
</body>
</html>"""

    def _fallback_html(self) -> str:
        """Generate fallback HTML if AI generation fails"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Clone</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; margin-bottom: 20px; }
        p { line-height: 1.6; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Website Clone</h1>
        <p>AI enhancement failed, but basic structure generated.</p>
    </div>
</body>
</html>"""

async def generate_enhanced_html(scraped_data: dict, design_tokens: dict, layout_analysis: dict) -> str:
    """Main function to generate enhanced HTML using AI-like processing"""
    try:
        logger.info("Starting AI-enhanced HTML generation...")

        # Create AI generator instance
        ai_generator = AIHTMLGenerator(scraped_data, design_tokens, layout_analysis)

        # Generate enhanced HTML
        enhanced_html = ai_generator.generate_enhanced_html()

        logger.info(f"AI-enhanced HTML generated successfully ({len(enhanced_html)} characters)")
        return enhanced_html

    except Exception as e:
        logger.error(f"AI HTML generation failed: {str(e)}")
        # Return None to trigger fallback in main application
        return None

class ComponentExtractor:
    """Extract and classify page components"""

    @staticmethod
    def extract_buttons(soup) -> List[dict]:
        """Extract button elements and their styles"""
        buttons = []
        button_elements = soup.find_all(['button', 'input']) + soup.find_all('a', class_=re.compile(r'btn|button'))

        for btn in button_elements[:5]:  # Limit to first 5
            button_data = {
                'text': btn.get_text(strip=True),
                'type': btn.name,
                'classes': btn.get('class', []),
                'href': btn.get('href') if btn.name == 'a' else None
            }
            buttons.append(button_data)

        return buttons

    @staticmethod
    def extract_forms(soup) -> List[dict]:
        """Extract form elements"""
        forms = []
        form_elements = soup.find_all('form')

        for form in form_elements:
            form_data = {
                'action': form.get('action'),
                'method': form.get('method', 'GET'),
                'inputs': []
            }

            inputs = form.find_all(['input', 'textarea', 'select'])
            for inp in inputs:
                input_data = {
                    'type': inp.get('type', inp.name),
                    'name': inp.get('name'),
                    'placeholder': inp.get('placeholder')
                }
                form_data['inputs'].append(input_data)

            forms.append(form_data)

        return forms

def intelligent_color_extraction(computed_styles: List[dict]) -> dict:
    """Intelligently extract and categorize colors"""
    colors = {
        'primary': [],
        'secondary': [],
        'text': [],
        'background': [],
        'accent': []
    }

    color_usage = {}

    for style_data in computed_styles:
        styles = style_data.get('styles', {})
        for prop, value in styles.items():
            if 'color' in prop.lower() and value:
                if value not in color_usage:
                    color_usage[value] = 0
                color_usage[value] += 1

    # Sort colors by usage frequency
    sorted_colors = sorted(color_usage.items(), key=lambda x: x[1], reverse=True)

    # Categorize colors based on usage and properties
    for color, usage in sorted_colors[:10]:
        if _is_background_color(color):
            colors['background'].append(color)
        elif _is_text_color(color):
            colors['text'].append(color)
        elif usage > 3:  # Frequently used colors are likely primary
            colors['primary'].append(color)
        else:
            colors['accent'].append(color)

    return colors

def _is_background_color(color: str) -> bool:
    """Check if color is likely a background color"""
    if not color or 'rgb' not in color:
        return False

    rgb_values = re.findall(r'\d+', color)
    if len(rgb_values) >= 3:
        avg = sum(int(x) for x in rgb_values[:3]) / 3
        return avg > 200  # Light colors are likely backgrounds

    return False

def _is_text_color(color: str) -> bool:
    """Check if color is likely a text color"""
    if not color or 'rgb' not in color:
        return False

    rgb_values = re.findall(r'\d+', color)
    if len(rgb_values) >= 3:
        avg = sum(int(x) for x in rgb_values[:3]) / 3
        return avg < 100  # Dark colors are likely text

    return False
