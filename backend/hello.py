from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import uvicorn
from app.cloner import scrape_website, generate_html_from_context
from app.rendered_scraper import get_rendered_html
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Create FastAPI instance
app = FastAPI(
    title="Orchids Challenge API",
    description="A starter FastAPI template for the Orchids Challenge backend",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models


class Item(BaseModel):
    id: int
    name: str
    description: str = None


class ItemCreate(BaseModel):
    name: str
    description: str = None


# In-memory storage for demo purposes
items_db: List[Item] = [
    Item(id=1, name="Sample Item", description="This is a sample item"),
    Item(id=2, name="Another Item", description="This is another sample item")
]

# Root endpoint

class CloneRequest(BaseModel):
    url: str


@app.post("/clone")
async def clone_site(request: CloneRequest):
    try:
        logger.info(f"Starting to clone: {request.url}")

        # Get rendered HTML and other data
        rendered_html, screenshot_b64, layout_summary, style_text = await get_rendered_html(request.url)

        logger.info(f"Layout summary: {layout_summary}")
        logger.info(f"Style text length: {len(style_text)}")
        logger.info(f"Rendered HTML length: {len(rendered_html)}")

        # Create a more focused prompt
        # Truncate content more intelligently
        max_html_length = 3000
        max_style_length = 800

        # Truncate HTML at a reasonable point (try to end at a complete tag)
        truncated_html = rendered_html[:max_html_length]
        if len(rendered_html) > max_html_length:
            # Try to find the last complete tag
            last_tag_end = truncated_html.rfind('>')
            if last_tag_end > max_html_length - 500:  # If we're close to the end
                truncated_html = truncated_html[:last_tag_end + 1]

        # Truncate styles more safely
        truncated_styles = style_text[:max_style_length]
        if len(style_text) > max_style_length:
            # Try to end at a complete CSS rule
            last_brace = truncated_styles.rfind('}')
            if last_brace > max_style_length - 200:
                truncated_styles = truncated_styles[:last_brace + 1]

        prompt = f"""You are a frontend engineer tasked with creating a visually similar website clone.

LAYOUT SUMMARY: {layout_summary}

CSS STYLES:
{truncated_styles}

HTML STRUCTURE:
{truncated_html}

Instructions:
1. Create a complete HTML page that mimics the structure and styling
2. Use inline styles or internal CSS in a <style> tag
3. Focus on the main layout, colors, and typography
4. Make it responsive and clean
5. Do NOT include any <script> tags or JavaScript
6. Return only valid HTML code

Generate the HTML now:"""

        logger.info("Sending prompt to LLM...")

        # Generate HTML using the LLM
        html = generate_html_from_context(prompt)

        logger.info(f"Generated HTML length: {len(html)}")

        if not html or html.strip() == "":
            logger.error("LLM returned empty response")
            raise HTTPException(status_code=500, detail="LLM returned empty response")

        # Basic validation that we got HTML
        if not ("<html" in html.lower() or "<!doctype" in html.lower()):
            logger.warning("Response doesn't look like HTML, wrapping it...")
            html = f"<html><head><title>Cloned Site</title></head><body>{html}</body></html>"

        return {"html": html, "status": "success"}

    except Exception as e:
        logger.error(f"Error in clone_site: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clone website: {str(e)}")



@app.get("/")
async def root():
    return {"message": "Hello from FastAPI backend!", "status": "running"}

# Health check endpoint


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orchids-challenge-api"}

# Get all items


@app.get("/items", response_model=List[Item])
async def get_items():
    return items_db

# Get item by ID


@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    for item in items_db:
        if item.id == item_id:
            return item
    return {"error": "Item not found"}

# Create new item


@app.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    new_id = max([item.id for item in items_db], default=0) + 1
    new_item = Item(id=new_id, **item.dict())
    items_db.append(new_item)
    return new_item

# Update item


@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: ItemCreate):
    for i, existing_item in enumerate(items_db):
        if existing_item.id == item_id:
            updated_item = Item(id=item_id, **item.dict())
            items_db[i] = updated_item
            return updated_item
    return {"error": "Item not found"}

# Delete item


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            deleted_item = items_db.pop(i)
            return {"message": f"Item {item_id} deleted successfully", "deleted_item": deleted_item}
    return {"error": "Item not found"}


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
