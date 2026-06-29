# Patient Health Assistant Agent

An agentic AI system that analyzes patient health data, searches the web for relevant medical information, and returns structured health insights using FastAPI, Groq LLM, and Tavily search.

---

## What It Does

- Full CRUD for patient records stored in a JSON database
- AI-powered symptom checker that combines patient vitals, allergies, and user-reported symptoms
- Web search via Tavily to fetch real-time medical information
- Structured AI response with risk level, possible cause, recommendation, and sources
- Streamlit UI to interact with the entire system without touching the API directly

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Backend | FastAPI |
| AI Model | Groq (llama-3.3-70b-versatile) |
| Web Search | Tavily |
| Data Validation | Pydantic |
| Database | JSON file |
| Frontend | Streamlit |

---

## Project Structure

```
Patient Health Assistant Agent/
│
├── main.py           # FastAPI backend with all endpoints
├── app.py            # Streamlit frontend
├── patients.json     # Patient database
├── .env              # API keys (never commit this)
├── requirements.txt  # Dependencies
└── README.md
```

---

## Setup

### 1. Clone or download the project

### 2. Create and activate virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install fastapi uvicorn pydantic groq tavily-python streamlit python-dotenv requests
```

### 4. Add your API keys

Create a `.env` file in the root folder:

```
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Get your keys from:
- Groq: https://console.groq.com
- Tavily: https://tavily.com

### 5. Run the backend

```bash
uvicorn main:app --reload
```

FastAPI runs on: `http://127.0.0.1:8000`

### 6. Run the frontend (new terminal)

```bash
streamlit run app.py
```

Streamlit runs on: `http://localhost:8501`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/about` | About the API |
| GET | `/view` | View all patients |
| GET | `/patient/{patient_id}` | View single patient |
| GET | `/sort` | Sort patients by height, weight, or bmi |
| POST | `/create` | Create a new patient |
| PUT | `/edit/{patient_id}` | Update patient details |
| DELETE | `/delete/{patient_id}` | Delete a patient |
| POST | `/chat` | AI symptom checker |

---

## Symptom Checker - How It Works

1. User sends `patient_id` and `symptoms`
2. Agent fetches patient data from JSON (BMI, verdict, allergies)
3. Builds a search query combining symptoms + verdict + allergies
4. Tavily searches the web and returns relevant medical sources
5. Everything is packed into a prompt and sent to Groq LLM
6. LLM returns structured JSON response validated by Pydantic
7. Response is displayed in Streamlit UI

### Request Body

```json
{
  "id": "P001",
  "symptoms": "chest pain and dizziness"
}
```

### Response

```json
{
  "risk_level": "High",
  "possible_cause": "Cardiovascular issues related to obesity",
  "recommendation": "Seek emergency medical help immediately",
  "summary": "Patient has BMI 33, is obese, and has dust and peanut allergies",
  "source": [
    "https://www.healthline.com/...",
    "https://example.com/..."
  ]
}
```

---

## Patient JSON Structure

```json
{
  "P001": {
    "name": "Ananya Verma",
    "city": "Guwahati",
    "age": 28,
    "gender": "female",
    "height": 1.65,
    "weight": 90.0,
    "bmi": 33.06,
    "verdict": "Obese",
    "allergies": ["Peanuts", "Dust"]
  }
}
```

---

## Notes

- Never commit your `.env` file
- FastAPI must be running before Streamlit can connect to it
- Swagger UI available at `http://127.0.0.1:8000/docs` for API testing
- JSON file acts as a simple database, not suitable for production