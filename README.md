# FitRoast –  Outfit Roaster & Style Suggestion Agent

FitRoast is a fun Visual AI agent that analyzes outfit images, roasts bad fashion choices, and suggests better styling using Gemini Vision.
Built for the **Agents World: Visual AI Hackathon**, this project demonstrates how multimodal AI and FiftyOne plugins can be used to create a creative vision agent workflow.


##  What it does

1. User uploads an outfit image through the frontend
2. Gemini Vision analyzes the image
3. The agent generates:
   - Funny roast
   - Rating
   - Style feedback
   - Suggested outfit improvements (in text)
4. The result is shown to the user
5. The same image can be inspected using FiftyOne plugins

This creates a complete

Vision Agent → Roast → Suggest → Inspect workflow



##  Hackathon Requirements Covered

- Working Visual AI prototype
- Vision agent concept
- Demo using FiftyOne plugins
- Fun / creative hack
- Multimodal AI workflow

Bonus:
- Frontend + Gemini + FiftyOne integration


## Agent Concept

FitRoast is a fashion vision agent that can:

- Understand outfit images
- Critique styling
- Suggest better outfit combinations
- Provide humorous feedback
- Inspect results using FiftyOne

Instead of manually reviewing outfits, the agent automates the process using visual AI.



## 🛠 Tech Stack

- Python
- Gemini Vision API
- FiftyOne
- FiftyOne Plugins
- Frontend (image upload UI)
- dotenv


## Project Structure

FitRoast/
│
├── frontend/
├── backend/
├── images/
├── agent.py
├── .env
├── README.md


frontend/ → upload UI  
backend/ → agent logic  
images/ → input outfits  
.env → API key  

##  Setup

Install dependencies

pip install fiftyone  
pip install python-dotenv  
pip install google-generativeai  


Add API key

GEMINI_API_KEY=your_key_here


Run backend

python agent.py


Launch FiftyOne

fiftyone app


##  Demo Workflow

1. Upload outfit image
2. Agent roasts the outfit
3. Agent suggests improvements
4. Open FiftyOne
5. Use Gemini plugin to analyze image
6. Show visual AI workflow

##  Why FiftyOne?

FiftyOne is used to demonstrate a real visual AI workflow.

It allows:

- Inspecting images interactively
- Running Gemini plugin queries
- Exploring outputs visually
- Debugging vision results

This makes the project more than just an API call.


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
