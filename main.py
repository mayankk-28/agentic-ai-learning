from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
import requests
import random
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


# Chat frontend
@app.get("/chat")
def chat():
    return FileResponse(Path(__file__).parent / "chat.html")


# Home - Open ASK Chat directly
@app.get("/")
def home():
    return FileResponse(Path(__file__).parent / "chat.html")


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

def route_tool(question: str):

    q = question.lower()

    tools = []

    # Tool 1: User data
    if "user" in q:
        tools.append("user")

    # Tool 2: Calculator
    calculator_words = [
        "add", "plus",
        "subtract", "minus",
        "multiply", "multiplied", "times",
        "divide", "divided"
    ]

    if any(word in q for word in calculator_words):
        tools.append("calculator")

    if any(symbol in q for symbol in ["+", "-", "*", "/"]):
        if "calculator" not in tools:
            tools.append("calculator")

    if "percent" in q or "%" in q:
        if "calculator" not in tools:
            tools.append("calculator")

    # Tool 3: Weather
    if "weather" in q or "temperature" in q:
        tools.append("weather")

    if not tools:
        return "none"

    return tools

def llm_detect_intents(question: str):
    q = question.lower().strip()

    # Handle greetings locally without calling Gemini
    greetings = {
        "hi", "hello", "hey", "hii", "hiii",
        "good morning", "good afternoon",
        "good evening", "how are you"
    }

    if q in greetings:
        return ["none"]

    try:
        response = client.with_options(
            timeout=5.0,
            max_retries=0
        ).chat.completions.create(
            model="gemini-3.8-flash",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify the user's question into these intents: "
                        "weather, calculator, user, none. "
                        "Return ONLY a JSON array. "
                        'Examples: ["weather"], ["calculator"], '
                        '["calculator", "weather"], ["user"], ["none"].'
                    ),
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
        )

        content = response.choices[0].message.content or "[]"
        intents = json.loads(content.strip())

        if not isinstance(intents, list):
            return route_tool(question)

        allowed_intents = {"weather", "calculator", "user", "none"}
        intents = [
            intent for intent in intents
            if isinstance(intent, str) and intent in allowed_intents
        ]

        if not intents or intents == ["none"]:
            fallback_tools = route_tool(question)

            if fallback_tools != "none":
                return fallback_tools

            return ["none"]

        return intents

    except Exception as e:
        print("Gemini unavailable or timed out; using fallback:", e)

        tools = route_tool(question)

        if tools == "none":
            return ["none"]

        return tools

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
    import re

    q = question.lower()
    numbers = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", q)]

    # Fast local calculation for simple questions
    if len(numbers) >= 2:
        result = numbers[0]

        if any(word in q for word in ["minus", "subtract"]):
            result -= numbers[1]

        elif any(word in q for word in ["plus", "add"]):
            result += numbers[1]

        elif any(word in q for word in ["multiply", "multiplied", "times"]):
            result *= numbers[1]

        elif any(word in q for word in ["divide", "divided"]):
            if numbers[1] == 0:
                return "Cannot divide by zero."
            result /= numbers[1]

        else:
            result = None

        # Handle a third number
        if result is not None and len(numbers) >= 3:
            if any(word in q for word in ["multiply", "multiplied", "times"]):
                result *= numbers[2]

            elif any(word in q for word in ["plus", "add"]):
                result += numbers[2]

            elif any(word in q for word in ["minus", "subtract"]):
                result -= numbers[2]

            elif any(word in q for word in ["divide", "divided"]):
                if numbers[2] == 0:
                    return "Cannot divide by zero."
                result /= numbers[2]

        if result is not None:
            return int(result) if result.is_integer() else result

    # Use Gemini for complex calculations
    plan = calculator_plan(question)

    if plan:
        result = execute_calculation_plan(plan)

        if result is not None:
            return result

    return "I couldn't understand the calculation."
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

def user_tool(question: str):
    try:
        response = requests.get(
            "https://jsonplaceholder.typicode.com/users/1",
            timeout=5
        )

        if response.status_code != 200:
            return {"error": "Unable to fetch user details."}

        user = response.json()

        return {
            "name": user["name"],
            "username": user["username"],
            "email": user["email"],
            "city": user["address"]["city"],
            "company": user["company"]["name"]
        }

    except requests.RequestException:
        return {"error": "User service is currently unavailable."}

def general_answer(question: str):

    for attempt in range(2):
        try:
            response = client.with_options(
                timeout=5.0,
                max_retries=0
            ).chat.completions.create(
                model="gemini-3.8-flash",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are ASK, a helpful AI assistant. "
                            "Answer the user's question clearly and accurately. "
                            "Use simple language. If you are unsure, say so."
                        )
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            )

            answer = response.choices[0].message.content

            if answer and answer.strip():
                return {"message": answer.strip()}

            return {
                "message": "I couldn't generate an answer. Please try again."
            }

        except Exception as e:
            print(f"General answer attempt {attempt + 1} failed:", e)

    return {
        "message": (
            "I'm unable to generate an answer right now because "
            "the AI service is unavailable. Please try again later."
        )
    }

def fun_zone(question: str):
    q = question.lower().strip()

    # Jokes
    if "joke" in q:
        jokes = [
            "😂 Teacher: Tum late kyun aaye? Student: Sir, sapne mein school ja raha tha. Raste mein traffic jam ho gaya!",
            "😂 Why do programmers prefer dark mode? Because light attracts bugs!",
            "😂 Teacher: Python kya hai? Student: Sir, ek programming language! Teacher: Aur asli Python? Student: Usse door hi rehna better hai!"
        ]
        return {"fun_zone": random.choice(jokes)}

    # Interesting facts
    if any(word in q for word in ["interesting", "fact", "facts"]):
        facts = [
            "🐙 An octopus has three hearts!",
            "🪐 A day on Venus is longer than its year.",
            "🦈 Sharks existed before trees appeared on Earth!"
        ]
        return {"fun_zone": random.choice(facts)}

    # Interactive Riddles

    if "riddle" in q:
        riddles = [
            {
                "question": "🧩 What has keys but cannot open locks?",
                "answer": "piano",
                "hint": "🎹 You can play music on it!"
            },
            {
                "question": "🧩 What has hands but cannot clap?",
                "answer": "clock",
                "hint": "🕒 It tells you the time!"
            },
            {
                "question": "🧩 What gets wetter as it dries?",
                "answer": "towel",
                "hint": "🛁 You use it after a bath!"
            }
        ]

        riddle = random.choice(riddles)
        save_memory("current_riddle_answer", riddle["answer"])
        save_memory("current_riddle_hint", riddle["hint"])

        return {
            "fun_zone": riddle["question"],
            "message": "Reply with your answer!"
        }

    # Check the user's riddle answer
    if "current_riddle_answer" in memory:
        user_answer = q.strip(" .!?").lower()
        correct_answer = memory["current_riddle_answer"].lower()

        accepted_answers = {
            "piano": ["piano", "a piano", "the piano"],
            "clock": ["clock", "a clock", "the clock"],
            "towel": ["towel", "a towel", "the towel"]
        }

        if user_answer in accepted_answers.get(correct_answer, [correct_answer]):
            memory.pop("current_riddle_answer", None)
            memory.pop("current_riddle_hint", None)

            with open("memory.json", "w") as file:
                json.dump(memory, file, indent=4)

            return {
                "fun_zone": "🎉 Correct! Great job!"
            }

        if any(word in q for word in ["hint", "clue", "help"]):
            return {
                "fun_zone": memory.get(
                    "current_riddle_hint",
                    "Try thinking about everyday objects!"
                )
            }

        return {
            "fun_zone": "❌ Not quite! Try again, or type 'hint' for a clue."
        }

    return None

def simple_agent(question: str):
    q = question.lower()

    # Handle greetings without calling Gemini
    greetings = {
        "hi", "hello", "hey", "hii", "hiii",
        "good morning", "good afternoon",
        "good evening"
    }

    if q.strip() in greetings:
        return {"message": "Hello! How can I help you today?"}

    # Fun Zone: jokes, facts, and riddles
    fun_result = fun_zone(question)
    if fun_result is not None:
        return fun_result

    # Memory: save user's name
    if "my name is " in q:
        name = question[q.index("my name is ") + len("my name is "):].strip()
        if name:
            save_memory("name", name.title())
        return f"Got it! I'll remember your name as {memory['name']}."

    # Memory: retrieve user's name
    if "what is my name" in q or "do you remember my name" in q:
        if "name" in memory:
            return f"Your name is {memory['name']}."
        return "I don't know your name yet."

    # Memory: save user's city
    if "my city is " in q:
        city = question.split("my city is ", 1)[1].strip()
        save_memory("city", city.title())
        return f"Got it! I'll remember your city as {memory['city']}."

    # Memory: retrieve user's city
    if "what is my city" in q or "do you remember my city" in q:
        if "city" in memory:
            return f"Your city is {memory['city']}."
        return "I don't know your city yet."

    # Fast routing for simple calculator questions
    tools = route_tool(question)

    if tools == ["calculator"] and not any(
        word in q for word in ["weather", "temperature", "user"]
    ):
        return {"calculator": calculator_tool(question)}

    # Use Gemini for other requests
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

     # General question: no tool matched
    if not results:
        return general_answer(question)

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
