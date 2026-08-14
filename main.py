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

def simple_agent(question: str):

    q = question.lower()

    # Tool 1: User data
    if "user" in q:
        user_data = get_user_data(1)

        if user_data:
            if "name" in user_data:
                return f"Hello {user_data['name']}, you asked: {question}"

        return "User not found"

    # Tool 2: Calculator
    if len(q.split()) == 3:

        parts = q.split()

        try:
            a = float(parts[0])
            operator = parts[1]
            b = float(parts[2])
        except ValueError:
            return f"You asked: {question}"

        if operator == "+":
            return calculate(a, b, "add")

        elif operator == "-":
            return calculate(a, b, "subtract")

        elif operator == "*":
            return calculate(a, b, "multiply")

        elif operator == "/":
            return calculate(a, b, "divide")

    return f"You asked: {question}"


@app.get("/weather")
def weather():
    return get_weather(23.18, 75.78)


def get_weather(latitude: float, longitude: float):

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
    