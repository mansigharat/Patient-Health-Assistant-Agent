import json
from dotenv import load_dotenv
import os
from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel,Field, computed_field
from typing import Annotated,Literal, Optional,List

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

from tavily import TavilyClient

tavily = TavilyClient(api_key=TAVILY_API_KEY)
results = tavily.search("chest pain dizziness obese patient dust allergy")