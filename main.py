from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import requests
import os

# Load environment variables
load_dotenv()

client = OpenAI()

app_name = os.getenv("APP_NAME", "Agentic AI")
environment = os.getenv("ENVIRONMENT", "development")
secret_key = os.getenv("MY_SECRET_KEY")
                       
print("App:", app_name)
print("Environment:", environment)


app = FastAPI()


# Home
@app.get("/")
def home():
    return {"message": "Hello Agentic AI!"}


# Hello
@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"hello {name}!"}


# Square
@app.get("/square/{number}")
def square(number: int):
    return {
        "number": number,
        "square": number * number
    }


# User model
class User(BaseModel):
    name: str
    age: int


# Create user
@app.post("/user")
def create_user(user: User):
    return {
        "message": f"hello {user.name}!",
        "age": user.age
    }


# Search
@app.get("/search")
def search(name: str, age: int):
    return {
        "message": f"hello {name}!",
        "age": age
    }


# External API
@app.get("/external-user/{user_id}")
def external_user(user_id: int):

    response = requests.get(
        f"https://jsonplaceholder.typicode.com/users/{user_id}"
    )

    # Error handling
    if response.status_code != 200:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Convert response to JSON
    data = response.json()

    # Return only required fields
    return {
        "name": data.get("name"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "username": data.get("username"),
        "website": data.get("website")
    }

def get_user_data(user_id: int):

    response = requests.get(
        f"https://jsonplaceholder.typicode.com/users/{user_id}"
    )

    if response.status_code != 200:
        return None

    data = response.json()

    return {
        "name": data.get("name"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "username": data.get("username"),
        "website": data.get("website")
    }

def calculate(a: float, b: float, operation: str):

    if operation == "add":
        return a + b

    elif operation == "subtract":
        return a - b

    elif operation == "multiply":
        return a * b

    elif operation == "divide":
        if b == 0:
            return "Cannot divide by zero"
        return a / b

    return "Unknown operation"

 
@app.get("/ask")
def ask_ai(question: str):
 
    result = simple_agent(question)

    return{
        "question": question,
        "result": result
        }

def route_tool(question: str):

    q = question.lower()

    # Tool 1: User data
    if "user" in q:
        return "user"

    # Tool 2: Calculator
    calculator_words = [
        "add", "plus",
        "subtract", "minus",
        "multiply", "multiplied", "times",
        "divide", "divided"
    ]

    if any(word in q for word in calculator_words):
        return "calculator"

    if any(symbol in q for symbol in ["+", "-", "*", "/"]):
        return "calculator"

    # Tool 3: Weather
    if "weather" in q or "temperature" in q:
        return "weather"

    return "none"

@app.get("/route")
def test_route(question: str):
    return{
        "question": question,
        "tool": route_tool(question)
    }

def calculator_tool(question: str):

    q = question.lower().replace("?", "")

    replacements = {
        "plus": "+",
        "add": "+",
        "minus": "-",
        "subtract": "-",
        "multiplied by": "*",
        "multiply by": "*",
        "multiply": "*",
        "times": "*",
        "divided by": "/",
        "divide by": "/",
        "divide": "/"
         
    }

    for word, symbol in replacements.items():
        q = q.replace(word, f" {symbol} ")

    parts = q.split()

    # Keep only numbers and calculator operators
    expression_parts = []

    for part in parts:
        if part in ["+", "-", "*", "/"]:
            expression_parts.append(part)
        else:
            try:
                float(part)
                expression_parts.append(part)
            except ValueError:
                continue

    if not expression_parts:
        return "I couldn't understand the calculation."

    expression = " ".join(expression_parts)

    try:
        result = eval(expression, {"__builtins__": None}, {})
        return result
    except (TypeError, ZeroDivisionError, SyntaxError):
        return "I couldn't calculate that."

def weather_tool(question: str):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": 23.18,
        "longitude": 75.78,
        "current": "temperature_2m,wind_speed_10m"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

    except requests.RequestException:
        return {
        "tool": "weather",
        "error": "Unable to fetch weather data"
    }

    data = response.json()

    return {
        "tool": "weather",
        "temperature": data["current"]["temperature_2m"],
        "wind_speed": data["current"]["wind_speed_10m"]
    }


def simple_agent(question: str):

    tool = route_tool(question)

    # Tool 1: User
    if tool == "user":
        return user_tool(question)

    # Tool 2: Calculator
    if tool == "calculator":
        return calculator_tool(question)

    # Tool 3: Weather
    if tool == "weather":
        return weather_tool(question)

    return f"You asked: {question}"


@app.get("/weather")
def weather():
    return get_weather(23.18, 75.78)


def get_weather(latitude , longitude):

    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m"
        }
    )

    if response.status_code != 200:
        return None

    data = response.json()

    return {
        "temperature": data["current"]["temperature_2m"],
        "wind_speed": data["current"]["wind_speed_10m"]
    }
    