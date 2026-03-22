# Outfit Roaster - Visual AI Outfit Judge

Outfit Roaster is a fun Visual AI agent that analyzes outfit photos, roasts bad fashion choices, gives a rating, and suggests improvements using Gemini Vision.
Built for the **Agents World: Visual AI Hackathon**, this project demonstrates how multimodal AI and FiftyOne plugins can be used to create a visual AI workflow.

##  What it does

1. User uploads an outfit image through the frontend
2. Gemini Vision analyzes the image
3. The system generates:
   - Roast
   - Rating
   - Suggestions
4. Results are shown in the frontend
5. Image and metadata are saved to FiftyOne automatically
6. Plugins are used to inspect and analyze results

This creates a workflow:

Frontend → Gemini → Roast & Rating → Save → FiftyOne → Plugins


## Agent Concept

Outfit Roaster works like a visual AI agent.

- Receives an image
- Understands clothing and style
- Generates feedback automatically
- Suggests improvements in text
- Stores results as structured data
- Allows visual inspection using FiftyOne

Along with generating roast, rating, and outfit improvement suggestions in text, each result is automatically stored in FiftyOne as part of a visual dataset.

Instead of just returning text, every analyzed outfit becomes part of a searchable visual collection.



## 🛠 Tech Stack

- Python  
- Streamlit (frontend)  
- Gemini API  
- FiftyOne  
- FiftyOne Plugins  
- dotenv  



## Project Structure

OutfitRoaster/
│
├── app.py
├── agent.py
├── images/
├── .env
├── README.md


frontend/ → upload UI  
backend/ → agent logic  
images/ → input outfits  
.env → API key  

##  Setup

Install dependencies

pip install fiftyone  
pip install streamlit
pip install python-dotenv  
pip install google-generativeai  


Add API key in `.env`
GEMINI_API_KEY=your_key_here
Run frontend
streamlit run app.py
Open FiftyOne
fiftyone app

##  Demo Workflow


1. Upload outfit image
2. Gemini analyzes the outfit
3. Roast, rating, and suggestions appear
4. Image is saved to FiftyOne
5. Caption Viewer plugin shows captions
6. Dashboard plugin shows statistics

## FiftyOne Plugins Used

We used the following plugins:

- Caption Viewer plugin  
  → Used to display AI-generated captions and metadata

- Dashboard plugin  
  → Used to visualize rating and verdict statistics

These plugins allow us to explore the results visually inside FiftyOne.

## Why FiftyOne
FiftyOne allows us to treat images as structured data.

Each outfit is saved with metadata like:
- rating
- caption
- verdict
- tags

Using plugins, we can filter, inspect, and analyze all outfits visually.

This makes the project a visual AI workflow, not just an API call.

##  Disclaimer

Roasts are meant to be funny, not offensive.  
This project was built for creativity during the hackathon.


## Team

- Sneha Nannapaneni
- Moksha Smruthi Morapakula
- Sree Padma Priya Abburi
  


## Hackathon

Agents World: Visual AI Hackathon  
Voxel51 / FiftyOne
