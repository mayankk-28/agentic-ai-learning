from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import requests
import os

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

def user_tool(question: str):

    words = question.split()

    user_id = None

    for word in words:
        try:
            number = int(word)
            user_id = number
            break
        except ValueError:
            continue

    if user_id is None:
        return {
            "tool": "user",
            "error": "Please provide a user ID."
        }

    data = get_user_data(user_id)

    if data is None:
        return {
            "tool": "user",
            "error": "User not found."
        }

    return {
        "tool": "user",
        "user_id": user_id,
        "data": data
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

def detect_intent(question: str):

    q = question.lower()

    # Weather intent
    weather_phrases = [
        "weather",
        "temperature",
        "how hot",
        "how cold",
        "mausam",
        "garmi",
        "thand",
        "baarish",
        "barish",
        "rain"
    ]

    if any(phrase in q for phrase in weather_phrases):
        return "weather"

    # Calculator intent
    calculator_phrases = [
        "add",
        "plus",
        "subtract",
        "minus",
        "multiply",
        "times",
        "divide",
        "percent",
        "calculate",
        "kitna",
        "jod",
        "ghata",
        "guna",
        "bhaag"
    ]

    if any(phrase in q for phrase in calculator_phrases):
        return "calculator"

    # User intent
    user_phrases = [
        "user",
        "user details",
        "user information",
        "user data",
        "details of user"
    ]

    if any(phrase in q for phrase in user_phrases):
        return "user"

    return "none"

def detect_intents(question: str):

    intents = []

    q = question.lower()

    weather_phrases = [
        "weather",
        "temperature",
        "mausam",
        "garmi",
        "thand",
        "baarish",
        "barish",
        "rain"
    ]

    calculator_phrases = [
        "add",
        "plus",
        "subtract",
        "minus",
        "multiply",
        "times",
        "divide",
        "percent",
        "calculate",
        "kitna",
        "jod",
        "ghata",
        "guna",
        "bhaag"
    ]

    user_phrases = [
        "user",
        "user details",
        "user information",
        "user data"
    ]

    if any(phrase in q for phrase in weather_phrases):
        intents.append("weather")

    if any(phrase in q for phrase in calculator_phrases):
        intents.append("calculator")

    if any(phrase in q for phrase in user_phrases):
        intents.append("user")

    if not intents:
        intents.append("none")

    return intents

def route_tool(question: str):

    intents = detect_intents(question)

    return intents

@app.get("/route")
def test_route(question: str):
    return{
        "question": question,
        "tool": route_tool(question)
    }

def calculator_tool(question: str):

    q = question.lower().replace("?", "")

    # Percentage calculation
    if "percent of" in q:
        parts = q.split()

        try:
            percent = float(parts[parts.index("percent") - 1])
            value = float(parts[parts.index("of") + 1])

            return (percent / 100) * value
        except (ValueError, IndexError):
            return "I couldn't understand the percentage calculation."

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

def extract_calculator_query(question: str):
    q = question.lower()

    # User-related part ko remove karo
    if "user" in q:
        parts = q.split("user", 1)
        q = parts[1]

        # User ID ke baad remaining question lo
        q = q.split("details", 1)[-1]

    calculator_words = [
        "add",
        "plus",
        "subtract",
        "minus",
        "multiply",
        "times",
        "divide",
        "percent",
        "calculate",
        "kitna",
        "jod",
        "ghata",
        "guna",
        "bhaag"
    ]

    words = q.split()
    relevant_words = []

    for word in words:
        if any(calc_word in word for calc_word in calculator_words):
            relevant_words.append(word)
        else:
            try:
                float(word)
                relevant_words.append(word)
            except ValueError:
                pass

    return " ".join(relevant_words)

@app.get("/test-extract")
def test_extract(question: str):
    return {
        "question": question,
        "extracted": extract_calculator_query(question)
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

def simple_agent(question: str):

    intents = detect_intents(question)

    results = {}

    if "user" in intents:
        results["user"] = user_tool(question)

    if "calculator" in intents:
        calculator_query = extract_calculator_query(question)
        results["calculator"] = calculator_tool(calculator_query)

    if "weather" in intents:
        results["weather"] = weather_tool(question)

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
    