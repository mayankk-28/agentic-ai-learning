# ASK — Agentic AI Assistant 🤖

ASK is a small Agentic AI project that I am building to learn how AI agents actually work.

The main idea is simple — user asks something, ASK understands the request, decides which tool is needed, and then gives the result.

I built this project while learning Python, FastAPI, APIs, LLMs and AI agent concepts.

## What can ASK do?

Currently ASK can:

* Understand different types of user requests
* Detect intents using Gemini
* Use different tools based on the request
* Perform calculations
* Handle some multi-step calculations
* Get weather information
* Work with user data
* Store basic memory in a JSON file
* Use fallback logic when Gemini is not available

## How ASK works

The basic flow is:

             User Question
                 ↓
                ASK
                 ↓
          Intent Detection
                 ↓
        Choose Required Tool
                 ↓
┌───────────┬────────────┬────────────┐
│ Calculator│   Weather  │    User    │
└───────────┴────────────┴────────────┘
                 ↓
            Final Result
           --------------

For example:

User:
"100 me se 20 minus karo, phir 5 se multiply karo"

ASK:
400
```

Another example:

User:
"20 times 5"

ASK:
100
```

## Tech Stack

* Python
* FastAPI
* Gemini API
* OpenAI Python SDK
* REST APIs
* JSON
* Uvicorn
* python-dotenv
* Git & GitHub

## Project Structure

agentic-ai-learning/
│
├── main.py
├── hello.py
├── memory.json
├── .env
├── .gitignore
├── README.md
│
├── main_backup.py
├── main_local_backup.py
│
└── venv/
    ````

Some backup files are kept locally while developing and testing the project.

## Main API Endpoints

### Home

GET /
```

Basic home route to check that the FastAPI application is running.

### Hello

GET /hello/{name}
```

Returns a simple hello message.

### Square

GET /square/{number}
```

Returns the square of a number.

Example:

/square/5

Result:
25
```

### User

POST /user
```

Used to create or process user information.

### Search

GET /search
```

Used for searching user information.

### External User

GET /external-user/{user_id}
```

Gets user data from an external API.

### LLM Test

GET /llm-test
```

Used to test the Gemini LLM connection.

### Route

GET /route
```

Tests the intent detection and tool routing system.

### ASK

GET /ask
```

This is the main endpoint of the project.

Example:

/ask?question=20%20times%205
```

ASK processes the question and returns the result from the required tool.

### Weather

GET /weather
```

Weather-related functionality.

## Gemini and Intent Detection

ASK uses Google's Gemini model for understanding the user's request.

The project uses the OpenAI Python SDK interface with Gemini's OpenAI-compatible API endpoint.

The basic idea is:
  
         User Question
              ↓
            Gemini
              ↓
       Intent Detection
              ↓
["calculator", "weather", "user"]
```

For example:

"Tell me the weather and calculate 20 times 5"
```

can be detected as:

["weather", "calculator"]
```

Then ASK can run the required tools.

## Calculator

The calculator is not only based on one simple operation.

It can handle examples like:

20 plus 5
20 minus 5
20 times 5
100 divided by 5
```

It also has support for simple multi-step calculations.

Example:

100 - 20
then × 5

Result:
400
```

There is also a fallback calculator.

If Gemini is unavailable or the API request fails, ASK tries to understand simple calculations using normal Python logic and regular expressions.

This was added so that the calculator does not completely stop working when the LLM is unavailable.

## Weather Tool

ASK also has a weather tool.

The weather functionality uses an external weather API to get weather information.

The tool can return information such as:

* Temperature
* Wind speed
* Weather related data

## Memory

ASK has a small memory system using:


memory.json
```

The purpose of this is to save basic information so that the project can remember data between requests.

This is a simple local memory system for learning purposes.

## Running the Project Locally

First clone the repository and go inside the project:

```bash
git clone <repository-url>
cd agentic-ai-learning
```

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Install the required packages:

```bash
pip install fastapi uvicorn python-dotenv requests openai
```

Create a `.env` file and add the required API key:

```env
GEMINI_API_KEY=your_api_key_here
```

Then start the FastAPI server:

```bash
uvicorn main:app --reload
```

The API will run locally on:

http://127.0.0.1:8000
```

FastAPI documentation is available at:

 
http://127.0.0.1:8000/docs
```

## Example Questions

Some examples that can be used for testing:

20 times 5

20 plus 5

100 divided by 5

100 me se 20 minus karo, phir 5 se multiply karo

What is the weather?

Show user details
```

## What I Learned

While building ASK, I learned about:

* Python functions
* FastAPI
* REST APIs
* API requests
* Environment variables
* `.env` files
* LLM API integration
* Gemini
* Intent detection
* Tool routing
* Fallback logic
* JSON memory
* Git and GitHub
* Debugging API errors
* Building an AI agent step by step

I am still improving this project and learning how real AI agents are designed.

## Future Improvements

Some things I want to add later:

* Better intent detection
* More reliable tool selection
* Better conversation memory
* More tools
* Better error handling
* More natural conversations
* Authentication
* Database based memory
* Better agent planning
* Deployment

## Project Status

This is an active learning project.

The main agent flow, tool routing, calculator, weather functionality, user tools and fallback logic are currently implemented.

I am continuing to improve ASK while learning more about AI agents and backend development.

## About

I am Mayank Chouhan, a B.Tech CSE student interested in:

* AI
* Python
* Backend Development
* FastAPI
* Agentic AI
* Automation

I built ASK mainly to understand AI agents by actually implementing the concepts instead of only watching tutorials.

---

**ASK — Ask something. Let the agent figure out the tool. 🤖**
