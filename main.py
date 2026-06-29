import json
from dotenv import load_dotenv
import os
from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional, List
from groq import Groq
from tavily import TavilyClient

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=TAVILY_API_KEY)

client = Groq(api_key=GROQ_API_KEY)

app = FastAPI()


class Patient(BaseModel):

    id: Annotated[str, Field(..., description='ID of the patient', examples=['P1001'])]
    name: Annotated[str, Field(..., description='Name of the patient')]
    city: Annotated[str, Field(..., description='City where the patient is living')]
    age: Annotated[int, Field(..., description='Age of the patient')]
    gender: Annotated[Literal['male', 'female', 'others'], Field(..., description="Gender of the patient")]
    height: Annotated[float, Field(..., gt=0, description='Height of Patient in meters')]
    weight: Annotated[float, Field(..., gt=0, description='Weight of the Patient in kgs')]
    allergy: Annotated[Optional[List[str]], Field(default=None)]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight / (self.height ** 2), 2)
        return bmi

    @computed_field
    @property
    def verdict(self) -> str:
        # BUG FIXED: previously 25-30 was lumped in with 'Normal'. It's Overweight.
        if self.bmi < 18.5:
            return 'Underweight'
        elif self.bmi < 25:
            return 'Normal'
        elif self.bmi < 30:
            return 'Overweight'
        else:
            return 'Obese'


class PatientUpdate(BaseModel):

    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female', 'others']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]


class ChatRequest(BaseModel):
    id: str
    symptoms: str


class AgentResponse(BaseModel):
    risk_level: Literal['High', "Medium", 'Low']
    possible_cause: str
    recommendation: str
    summary: str
    source: List[str]


def load_data():
    with open("patients.json", "r") as f:
        data = json.load(f)
    return data


def save_data(data):
    with open("patients.json", 'w') as f:
        json.dump(data, f)


@app.get("/")
def hello():
    return {"message": "Patient Management System API"}


@app.get("/about")
def about():
    return {
        "message": "A fully functional API to manage your patient records"
    }


@app.get("/view")
def view():
    data = load_data()
    return data


# Path Parameter
@app.get("/patient/{patient_id}")
def view_patient(
    patient_id: str = Path(
        ...,
        description="ID of the patient in the database",
        examples=["P001"]
    )
):
    data = load_data()

    if patient_id in data:
        return data[patient_id]

    raise HTTPException(
        status_code=404,
        detail="Patient not found"
    )


# Query Parameter
@app.get("/sort")
def sort_patients(
    sort_by: str = Query(
        ...,
        description="Sort on the basis of height, weight, or BMI"
    ),
    order: str = Query(
        "asc",
        description="Sort order: asc or desc"
    )
):
    valid_fields = ["height", "weight", "bmi"]

    if sort_by not in valid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field. Select from {valid_fields}"
        )

    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid order. Select either 'asc' or 'desc'"
        )

    data = load_data()

    sort_order = (order == "desc")

    sorted_data = sorted(
        data.values(),
        key=lambda x: x.get(sort_by, 0),
        reverse=sort_order
    )

    return sorted_data


@app.post('/create')
def create_patient(patient: Patient):
    # load existing data
    data = load_data()

    # check new patient if that already exists or not
    if patient.id in data:
        raise HTTPException(status_code=400, detail='Patient already exists')

    # new patient add to the database
    data[patient.id] = patient.model_dump(exclude={'id'})  # convert pydantic object into dictionary

    # save into json file
    save_data(data)

    return JSONResponse(status_code=201, content={'message': 'Patient Created Successfully'})


@app.put('/edit/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')

    existing_patient_info = data[patient_id]

    updated_patient_info = patient_update.model_dump(exclude_unset=True)

    for key, value in updated_patient_info.items():
        existing_patient_info[key] = value

    existing_patient_info['id'] = patient_id
    patient_pydantic_obj = Patient(**existing_patient_info)
    # BUG FIXED: exclude='id' was a string, pydantic iterated over its
    # characters ('i', 'd') instead of excluding the 'id' field. Needs a set.
    existing_patient_info = patient_pydantic_obj.model_dump(exclude={'id'})

    data[patient_id] = existing_patient_info

    save_data(data)
    return JSONResponse(status_code=200, content={'message': 'patient updated'})


@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')

    del data[patient_id]

    save_data(data)
    return JSONResponse(status_code=200, content={'message': 'Patient Deleted'})


@app.post('/chat')
def chat_patient(patient: ChatRequest):
    data = load_data()

    if patient.id not in data:
        raise HTTPException(status_code=400, detail='Patient not exists')

    patient_data = data[patient.id]
    verdict = patient_data['verdict']
    # BUG FIXED: model field is 'allergy', not 'allergies'. This was a guaranteed
    # KeyError on every call. Also guard against None since allergy is optional.
    allergies = patient_data.get('allergy') or []
    symptoms = patient.symptoms

    query = f"{symptoms} {verdict} patient {' '.join(allergies)} possible causes"
    search_results = tavily.search(query)

    prompt = f"""
                You are a medical assistant. Analyze this patient data and return response in JSON format only.

                Patient Data:
                - Verdict: {verdict}
                - Allergies: {allergies}
                - BMI: {patient_data['bmi']}

                Symptoms reported: {symptoms}

                Web Search Results: {search_results}

                Return ONLY this JSON structure, nothing else:
                {{
                    "risk_level": "High/Medium/Low",
                    "possible_cause": "...",
                    "recommendation": "...",
                    "summary": "...",
                    "source": ["url1", "url2"]
                }}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response.choices[0].message.content
    response_text = response_text.strip().strip("```json").strip("```").strip()
    response_dict = json.loads(response_text)
    agent_response = AgentResponse(**response_dict)
    return agent_response

# PUT = updating
# GET = retrieve
# POST = Creating
# DELETE = deletion