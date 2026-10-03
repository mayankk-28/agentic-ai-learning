from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import requests
import json
import os
 
try:
    with open("memory.json", "r") as file:
        memory = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    memory = {}

def save_memory(key: str, value: str):
    memory[key] = value

    with open("memory.json", "w") as file:
        json.dump(memory, file, indent=4)

    return f"Saved: {key} = {value}"

# Load environment variables
load_dotenv()

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

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

def llm_test(question: str):
    response = client.chat.completions.create(
        model="gemini-3.8-flash",
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the user question into exactly one category: "
                    "weather, calculator, user, none. "
                    "Return only the category name."
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    return response.choices[0].message.content.strip()


@app.get("/llm-test")
def test_llm(question: str):
    return {
        "question": question,
        "intent": llm_test(question)
    }

def llm_detect_intents(question: str):
    try:
        response = client.chat.completions.create(
            model="gemini-3.8-flash",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an intent classifier for an AI agent. "
                        "Classify the user's question into one or more of these intents: "
                        "weather, calculator, user, none. "
                        "Return ONLY a JSON array. "
                        'Examples: ["weather"] '
                        '["calculator"] '
                        '["calculator", "weather"] '
                        '["user"] '
                        '["none"]'
                    ),
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
        )

        content = response.choices[0].message.content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return ["none"]

    except Exception as e:
        print("Gemini unavailable, using fallback:", e)

        # Fallback to existing keyword-based routing
        tool = route_tool(question)

        if tool == "none":
            return ["none"]

        return [tool]

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

    if "percent" in q or "%" in q:
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

def calculator_plan(question: str):
    try:
        response = client.chat.completions.create(
            model="gemini-3.8-flash",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a calculator planning assistant. "
                        "Convert the user's calculation request into a JSON array "
                        "of sequential operations. "
                        "Allowed operations: add, subtract, multiply, divide. "
                        "Every operation must contain operation, a and b. "
                        "For later operations, use the previous result as a "
                        "and the new number as b. "
                        "Return ONLY valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
        )

        content = response.choices[0].message.content.strip()
        plan = json.loads(content)

        if not isinstance(plan, list):
            return None

        return plan

    except Exception as e:
        print("Calculator planning failed:", e)
        return None


def execute_calculation_plan(plan):
    if not plan:
        return None

    result = None

    try:
        for step in plan:
            operation = step.get("operation")

            if result is None:
                a = step["a"]
                b = step["b"]
            else:
                a = result
                b = step["b"]

            if operation == "multiply":
                result = a * b

            elif operation == "add":
                result = a + b

            elif operation == "subtract":
                result = a - b

            elif operation == "divide":
                if b == 0:
                    return "Cannot divide by zero."
                result = a / b

            else:
                return None

        return result

    except (KeyError, TypeError, ValueError):
        return None


def calculator_tool(question: str):
    plan = calculator_plan(question)

    if plan:
        result = execute_calculation_plan(plan)

        if result is not None:
            return result

    # Fallback when Gemini is unavailable
    q = question.lower()

    import re

    numbers = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", q)]

    if len(numbers) < 2:
        return "I couldn't understand the calculation."

    result = numbers[0]

    if "minus" in q or "subtract" in q:
        result = result - numbers[1]

    elif "plus" in q or "add" in q:
        result = result + numbers[1]

    elif "multiply" in q or "times" in q:
        result = result * numbers[1]

    elif "divide" in q or "divided by" in q:
        if numbers[1] == 0:
            return "Cannot divide by zero."
        result = result / numbers[1]

    else:
        return "I couldn't understand the calculation."

    if len(numbers) >= 3:

        if "multiply" in q or "times" in q:
            result = result * numbers[2]

        elif "plus" in q or "add" in q:
            result = result + numbers[2]

        elif "minus" in q or "subtract" in q:
            result = result - numbers[2]

        elif "divide" in q or "divided by" in q:
            if numbers[2] == 0:
                return "Cannot divide by zero."
            result = result / numbers[2]

    return result

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

@app.get("/ask")
def ask_ai(question: str):
    result = simple_agent(question)

    return {
        "question": question,
        "result": result
    }

def simple_agent(question: str):

    # Memory: save user's name
    q = question.lower()

    if "my name is " in q:
        name = question.lower().split("my name is ")[1].strip()
        save_memory("name", name.title())
        return f"Got it! I'll remember your name as {memory['name']}."

    # Memory: retrieve user's name
    if "what is my name" in q or "do you remember my name" in q:
        if "name" in memory:
            return f"Your name is {memory['name']}."
        return "I don't know your name yet."

    # Memory: save user's city
    if "my city is " in q:
        city = question.lower().split("my city is ")[1].strip()
        save_memory("city", city.title())
        return f"Got it! I'll remember your city as {memory['city']}."

    # Memory: retrieve user's city
    if "what is my city" in q or "do you remember my city" in q:
        if "city" in memory:
            return f"Your city is {memory['city']}."
        return "I don't know your city yet."

    # Gemini intent detection
    intents = llm_detect_intents(question)

    results = {}

    # User tool
    if "user" in intents:
        results["user"] = user_tool(question)

    # Calculator tool
    if "calculator" in intents:
        results["calculator"] = calculator_tool(question)

    # Weather tool
    if "weather" in intents:
        results["weather"] = weather_tool(question)

    # No matching intent
    if not results:
        results["message"] = f"You asked: {question}"

    return results


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