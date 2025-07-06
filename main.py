from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import openai
import requests
import base64
import json
import dotenv
import os
import uvicorn
import re


dotenv.load_dotenv()
app = FastAPI()

# Optional: set your API key via environment variable instead
openai.api_key = os.environ.get('OPENAI_KEY')


def image_url_to_base64(image_url: str) -> str:
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return base64.b64encode(response.content).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error downloading image: {str(e)}")

def build_prompt():
    return """
Evaluate this image of the sky for planetary observation suitability. Based on visual analysis, return a JSON object with scores from 1 to 5 for the following:
- cloud_cover: 1 = fully overcast, 5 = clear sky
- sky_brightness: 1 = very bright, 5 = very dark
- star_visibility: 1 = no stars visible, 5 = many stars visible
- atmospheric_stability: 1 = very turbulent, 5 = very stable
- obstructions: 1 = sky blocked, 5 = fully open view
Also include an overall_score as the average of the five categories.
Return only the raw JSON object, with no commentary, formatting, or explanation.
"""

favicon_path = 'favicon.ico'

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)

@app.get("/")
async def evaluate_sky(image_url: str = Query(..., description="Direct URL to a sky image")):
    """
    Evaluate this image of the sky for planetary observation suitability. Based on visual analysis, return a JSON object with scores from 1 to 5 for the following:
    - cloud_cover: 1 = fully overcast, 5 = clear sky
    - sky_brightness: 1 = very bright, 5 = very dark
    - star_visibility: 1 = no stars visible, 5 = many stars visible
    - atmospheric_stability: 1 = very turbulent, 5 = very stable
    - obstructions: 1 = sky blocked, 5 = fully open view
    Also include an overall_score as the average of the five categories.
    Return only the raw JSON object, with no commentary, formatting, or explanation.
    """
    base64_image = image_url_to_base64(image_url)

    try:
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": build_prompt()},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
        response = openai.chat.completions.create(
            messages=messages,
            model="gpt-4o",
            max_tokens=300
        )
        text_response = response.choices[0].message.content
        # Try to extract JSON using a regular expression
        match = re.search(r'\{.*\}', text_response, re.DOTALL)
        if not match:
            raise HTTPException(status_code=500, detail="Failed to extract JSON from model response.")

        try:
            result = json.loads(match.group(0))
            return result
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Invalid JSON from model: {e}")

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Error from OpenAI API: {str(e)}")