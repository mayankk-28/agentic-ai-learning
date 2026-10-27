# ASK — Agentic AI Assistant 🤖

> **Ask something. Let the agent figure out the tool.**

ASK is a learning-focused Agentic AI application built with Python and FastAPI. It combines a browser-based chat interface with an API backend, Gemini-powered intent detection and general answers, tool routing, calculator logic, weather data, external user data, and a small JSON-based memory system.

- **Live application:** https://agentic-ai-learning.onrender.com
- **API documentation:** https://agentic-ai-learning.onrender.com/docs
- **Source code:** https://github.com/mayankk-28/agentic-ai-learning

> **Project status:** Active learning project. Features and implementation may change as the project develops.

---

## Table of contents

1. [Project goals](#-project-goals)
2. [Architecture and request lifecycle](#-architecture-and-request-lifecycle)
3. [Technology stack](#-technology-stack)
4. [Backend walkthrough](#-backend-walkthrough)
5. [Agent orchestration and routing](#-agent-orchestration-and-routing)
6. [Gemini integration](#-gemini-integration)
7. [Calculator tool](#-calculator-tool)
8. [Weather tool](#-weather-tool)
9. [User data tools](#-user-data-tools)
10. [Memory system](#-memory-system)
11. [Fun Zone](#-fun-zone)
12. [Browser chat interface](#-browser-chat-interface)
13. [API reference](#-api-reference)
14. [Run locally](#-run-locally)
15. [Environment variables and secrets](#-environment-variables-and-secrets)
16. [Error handling and current limitations](#-error-handling-and-current-limitations)
17. [Learning outcomes](#-learning-outcomes)
18. [Future improvements](#-future-improvements)

---

## 🎯 Project goals

ASK was created to learn how an AI-agent-style application can:

- Accept a user's question through a web interface or API.
- Detect the likely task or intent.
- Choose an appropriate tool for supported requests.
- Call external APIs when required.
- Perform calculations locally or execute a model-generated calculation plan.
- Remember selected values using a local JSON file.
- Continue to support some simple calculations when Gemini is unavailable.
- Return structured results to the browser.

The project is built incrementally to understand the components behind an agent rather than treating an LLM as a standalone chatbot.

## 🏗️ Architecture and request lifecycle

The main chat request follows this high-level flow:

```text
User
 |
 v
Browser chat interface (chat.html)
 |
 | GET /ask?question=...
 v
FastAPI endpoint: ask_ai()
 |
 v
simple_agent(question)
 |
 +--> Greeting check
 |
 +--> Fun Zone check
 |
 +--> Save/read selected memory
 |
 +--> Fast keyword routing for simple calculations
 |
 +--> Gemini intent detection for other requests
 |       |
 |       +--> Local keyword fallback if needed
 |
 +--> Execute matching tools
 |       +--> Calculator
 |       +--> Weather
 |       +--> User data
 |
 +--> General Gemini answer if no tool result exists
 |
 v
JSON response from FastAPI
 |
 v
Browser formats and displays the result
```

This diagram describes the implementation's main path. Exact behavior depends on the request and whether the relevant external service is available.

### Example: calculator request

For a request such as `20 times 5`:

1. The browser sends the question to `/ask`.
2. `ask_ai()` passes the question to `simple_agent()`.
3. `simple_agent()` tries the local keyword router.
4. If the request is classified as a simple calculator request, `calculator_tool()` is called directly.
5. The backend returns the result in JSON.
6. The browser displays the result.

### Example: general question

For a question that does not match a supported tool:

1. The request reaches `simple_agent()`.
2. Greeting, Fun Zone, memory, and fast calculator checks run first.
3. Gemini is asked to classify the intent.
4. If no tool result is produced, `general_answer()` attempts to generate a response.
5. The response is returned to the browser.

---

## 🧰 Technology stack

| Technology | Role in this project |
|---|---|
| Python | Backend logic and tool functions |
| FastAPI | HTTP API and route definitions |
| Pydantic | Validation of the `User` request model |
| Gemini API | Intent detection, calculator planning, and general answers |
| OpenAI Python SDK | Client interface used with Gemini's OpenAI-compatible endpoint |
| Uvicorn | Local ASGI server |
| Requests | HTTP requests to external services |
| python-dotenv | Loads values from `.env` |
| JSON | Backend memory storage and API data |
| HTML, CSS, JavaScript | Browser chat interface |
| `localStorage` | Browser-side saved chat history and theme preference |
| Git and GitHub | Version control and source hosting |
| Render | Hosted application |

---

## 🔍 Backend walkthrough

The backend lives primarily in `main.py`.

### 1. Imports and application setup

The file imports the libraries used for HTTP routes, HTML responses, request validation, environment variables, external HTTP requests, JSON, random choices, and the Gemini client.

The FastAPI application is created with:

```python
app = FastAPI()
```

The project loads environment variables using `load_dotenv()` and creates an OpenAI-compatible client pointed at Gemini's endpoint:

```python
client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
```

The model used in the current code is `gemini-3.8-flash`.

The application also reads `APP_NAME` and `ENVIRONMENT`, with defaults if those variables are not set.

### 2. Serving the chat page

The `/` and `/chat` routes return `chat.html` using `FileResponse`. This lets a browser open the chat UI rather than seeing only a JSON response.

### 3. Request validation with Pydantic

The `User` model declares two fields:

```python
class User(BaseModel):
    name: str
    age: int
```

FastAPI uses this model to parse and validate the JSON body for `POST /user`.

### 4. External HTTP requests

The backend uses `requests.get()` to call external services. Some calls check HTTP status codes or catch `requests.RequestException` so an external service failure can be represented as an error result.

---

## 🧭 Agent orchestration and routing

The main coordinator is:

```python
simple_agent(question: str)
```

It processes a request through a sequence of checks. The order matters because a request may be handled before Gemini is called.

### Processing order

1. **Greeting check:** common greetings receive a direct response without calling Gemini.
2. **Fun Zone:** checks whether the request asks for a joke, interesting fact, or riddle interaction.
3. **Memory commands:** recognizes supported phrases to save or retrieve the user's name and city.
4. **Fast calculator routing:** calls `route_tool()` for a quick keyword-based classification. Simple calculator-only questions can be handled locally.
5. **Gemini intent detection:** other requests are passed to `llm_detect_intents()`.
6. **Tool execution:** the returned intents determine whether the user, calculator, and/or weather tools are called.
7. **General answer:** if no tool result is produced, `general_answer()` is used.

The function may return a dictionary containing one or more tool results. The `/ask` endpoint wraps that value with the original question.

### `route_tool(question)`

This is a lightweight, rule-based router. It looks for terms such as:

- Calculator: `add`, `plus`, `subtract`, `minus`, `multiply`, `times`, `divide`
- Weather: `weather`, `temperature`
- User information: `user`
- Arithmetic symbols: `+`, `-`, `*`, `/`
- Percentages: `percent`, `%`

It returns a list of matched tools, or the string `"none"` if it finds no match. Because it uses keywords, it is a basic heuristic rather than a full natural-language understanding system.

### `llm_detect_intents(question)`

This function asks Gemini to classify a question into the supported intents:

- `weather`
- `calculator`
- `user`
- `none`

The model is instructed to return a JSON array, for example `["calculator", "weather"]`. The code parses the response with `json.loads()` and filters out values outside the allowed set.

If the response is malformed or the Gemini request fails, the function uses `route_tool()` as a fallback. This gives the application a local routing path for some requests, although keyword routing cannot understand every phrasing.

---

## 🧠 Gemini integration

The project uses the OpenAI Python SDK's chat-completions interface with Gemini's OpenAI-compatible API endpoint.

Gemini is used for three distinct tasks in the current code:

1. **Intent detection** in `llm_detect_intents()`.
2. **Calculation planning** in `calculator_plan()`.
3. **General question answering** in `general_answer()`.

The `/llm-test` endpoint separately calls `llm_test()` and returns the detected category.

### Intent detection versus general answers

These are different operations:

- Intent detection is expected to return structured classification data.
- General answering is expected to return helpful natural-language text.
- Calculator planning is expected to return a JSON list of arithmetic operations.

Keeping these tasks separate makes the program easier to inspect and debug.

### API availability

Gemini requests can fail because of missing or invalid credentials, quota limits, network issues, timeouts, or unexpected model output. Some paths include fallback logic; not every Gemini call uses identical timeout and retry behavior.

---

## 🧮 Calculator tool

The calculator implementation uses two approaches.

### 1. Local arithmetic

`calculator_tool(question)` extracts numbers from the question with a regular expression and checks for supported operation words.

For supported simple requests, it performs the arithmetic in Python. The current local logic checks the operation words in the request and supports a limited multi-number path.

Examples of intended inputs include:

```text
20 plus 5
20 minus 5
20 times 5
100 divided by 5
```

**Current limitation:** the local parser is keyword-based and limited. It should not be assumed to correctly interpret every expression, mixed operators, or every natural-language ordering.

### 2. Model-generated calculation plan

If the local calculation path cannot return a result, `calculator_tool()` calls:

```python
calculator_plan(question)
```

Gemini is asked to return a JSON list of sequential operations. Each operation contains an operation name and operands.

Example of the expected plan shape:

```json
[
  {"operation": "subtract", "a": 100, "b": 20},
  {"operation": "multiply", "a": 80, "b": 5}
]
```

This is an illustrative example of the schema expected by the code, not a guarantee that Gemini will always return that exact plan.

### 3. Plan execution

`execute_calculation_plan(plan)` iterates over the list and applies supported operations:

- `add`
- `subtract`
- `multiply`
- `divide`

For subsequent steps, the previous result is used as the next operation's first operand. Division by zero returns a specific error message. Missing or invalid plan fields cause the function to return `None`.

If planning or execution fails, the calculator returns a message that it could not understand the calculation.

---

## 🌦️ Weather tool

The function:

```python
weather_tool(question)
```

calls the Open-Meteo forecast endpoint:

```text
https://api.open-meteo.com/v1/forecast
```

The current implementation uses fixed coordinates:

- Latitude: `23.18`
- Longitude: `75.78`

It requests these current weather fields:

- `temperature_2m`
- `wind_speed_10m`

The function returns a dictionary containing the tool name, temperature, and wind speed. If the HTTP request raises a `requests.RequestException`, it returns an error dictionary.

**Current limitation:** the question is accepted by the function, but the current code does not geocode a city from the question. The coordinates are fixed, so the returned weather data is for that configured location, not automatically the user's location.

There is also a separate `/weather` route and a `get_weather(latitude, longitude)` helper in `main.py`; consult `/docs` and the source code for the exact behavior of that route.

---

## 👤 User data tools

### `user_tool(question)`

This function requests user `1` from JSONPlaceholder:

```text
https://jsonplaceholder.typicode.com/users/1
```

It returns selected fields:

- Name
- Username
- Email
- City
- Company

It uses a timeout and catches `requests.RequestException`. If the request fails or the service returns a non-success status, the function returns an error result.

**Current limitation:** the function's `question` argument is not used to choose a user ID; the request is currently hard-coded to user `1`.

### `GET /external-user/{user_id}`

This route accepts a user ID as a path parameter, calls JSONPlaceholder, and returns selected contact fields. If the HTTP status is not `200`, it raises an HTTP 404 error.

### `POST /user`

This route accepts a JSON body validated by the `User` Pydantic model and returns a greeting and the submitted age. It does not create an account or save the submitted user to a database.

### `GET /search`

This basic route accepts `name` and `age` query parameters and returns a greeting and age. Despite the name, the current implementation does not search a database.

---

## 💾 Memory system

The backend uses a local JSON file named `memory.json`.

### Loading memory

When `main.py` starts, it attempts to read and parse `memory.json`. If the file is missing or contains invalid JSON, the in-memory dictionary starts empty.

### Saving memory

The helper:

```python
save_memory(key, value)
```

updates the in-memory dictionary and writes it to `memory.json`.

The current agent supports explicit phrases for saving and retrieving:

- `my name is ...`
- `what is my name`
- `do you remember my name`
- `my city is ...`
- `what is my city`
- `do you remember my city`

The Fun Zone also stores the current riddle's answer and hint in this file so a later message can be checked against the active riddle.

**Important distinction:** `memory.json` is backend-side application memory. It is not the same as the browser's chat history, which is stored in `localStorage`.

**Current limitation:** this is a simple local file, not a multi-user database. Shared hosting, multiple workers, concurrent writes, and per-user privacy need a more robust storage design for production use.

---

## 🎲 Fun Zone

`fun_zone(question)` provides a small set of non-LLM interactions:

- Random jokes
- Interesting facts
- Riddles
- Riddle hints
- Checking an answer against the stored riddle answer

The function returns a result when it recognizes a supported Fun Zone request, and `simple_agent()` returns that result before normal intent detection. Riddle state is saved in `memory.json`.

This is a rule-based feature; it does not require Gemini to generate the stored jokes, facts, or riddles.

---

## 💬 Browser chat interface

The browser UI is implemented in `chat.html` with HTML, CSS, and JavaScript.

### Sending a question

The JavaScript `sendQuestion()` function sends a GET request to:

```text
/ask?question=<URL-encoded-question>
```

It uses `encodeURIComponent()` to safely encode the question, parses the JSON response, formats the result, and displays the assistant's answer. A typing indicator is displayed while the request is in progress.

### Chat history

The interface stores conversations under the browser storage key:

```text
ask_chat_history_v1
```

The UI can save and render chat history, open an earlier conversation, start a new chat, and filter saved conversations. This history is stored in the browser's `localStorage`; it is not sent to `memory.json` by the chat-history code described here.

### Additional interface features

The current frontend code also includes:

- Suggested question buttons
- A Fun Zone view
- A quiz with category and difficulty selection
- Quiz loading from an external trivia API
- Joke display
- A surprise-me action
- Light/dark theme preference stored under `ask-theme`
- Responsive navigation and history panel behavior

The quiz uses a separate external trivia API and is distinct from the backend's `/ask` agent flow.

---

## 🔌 API reference

The following table reflects the route definitions present in the current source inspected for this README.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Serves `chat.html` |
| `GET` | `/chat` | Serves `chat.html` |
| `GET` | `/hello/{name}` | Returns a hello message |
| `GET` | `/square/{number}` | Returns the square of an integer |
| `POST` | `/user` | Accepts a name and age, then returns a greeting and age |
| `GET` | `/search?name=...&age=...` | Returns a greeting and age |
| `GET` | `/external-user/{user_id}` | Retrieves selected fields for an external user |
| `GET` | `/llm-test?question=...` | Tests single-category Gemini intent classification |
| `GET` | `/route?question=...` | Tests keyword-based tool routing |
| `GET` | `/ask?question=...` | Runs the main agent flow |
| `GET` | `/weather` | Runs the separate weather endpoint |

### Example requests

**Chat / ASK endpoint**

```text
GET /ask?question=20%20times%205
```

**Square**

```text
GET /square/5
```

Example response:

```json
{
  "number": 5,
  "square": 25
}
```

**Create/process user input**

```http
POST /user
Content-Type: application/json
```

```json
{
  "name": "Mayank",
  "age": 21
}
```

The age above is an example value only.

### Interactive API documentation

FastAPI automatically provides interactive documentation at:

```text
/docs
```

For a local run, open `http://127.0.0.1:8000/docs`. For the deployed service, open the live API documentation link at the top of this README.

---

## 🚀 Run locally

### 1. Clone the repository

```bash
git clone https://github.com/mayankk-28/agentic-ai-learning.git
cd agentic-ai-learning
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

If creating the virtual environment fails on Ubuntu, install the system package that provides `venv`, then retry.

### 3. Install dependencies

```bash
pip install fastapi uvicorn python-dotenv requests openai
```

### 4. Configure `.env`

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
APP_NAME=Agentic AI
ENVIRONMENT=development
```

Replace the API key placeholder with your own key. Do not commit the real key.

### 5. Start the server

```bash
uvicorn main:app --reload
```

Then open:

- Chat: `http://127.0.0.1:8000/`
- Alternate chat path: `http://127.0.0.1:8000/chat`
- API docs: `http://127.0.0.1:8000/docs`

---

## 🔐 Environment variables and secrets

The code reads these environment variables:

| Variable | Purpose | Required? |
|---|---|---|
| `GEMINI_API_KEY` | Authenticates the Gemini client | Required for Gemini-backed functionality |
| `APP_NAME` | Application name printed at startup | Optional; defaults to `Agentic AI` |
| `ENVIRONMENT` | Environment label printed at startup | Optional; defaults to `development` |
| `MY_SECRET_KEY` | Read by the current source | Its use is not established by the inspected code sections |

Keep `.env`, API credentials, virtual environments, Python cache files, and local runtime memory out of Git. The repository's `.gitignore` is intended to exclude sensitive and local-only files.

---

## ⚠️ Error handling and current limitations

The project is an educational prototype. Important limitations visible in the current implementation include:

- Keyword routing may miss differently phrased requests.
- The local calculator supports a limited set of patterns; complex or ambiguous expressions may be misinterpreted.
- Gemini may return malformed JSON, time out, or become unavailable. Fallback routing handles some, but not all, failure cases.
- The weather tool uses fixed coordinates instead of selecting a location from the user's question.
- The user tool currently fetches a fixed external user ID.
- The backend JSON memory is a shared local file, not a per-user database.
- The browser history is stored locally in each browser and is separate from backend memory.
- The app uses GET for `/ask`, so questions are placed in the URL. A POST endpoint would be more suitable for longer or sensitive prompts.
- External services can be unavailable or change their response behavior.
- The project does not currently provide production-grade authentication, authorization, or multi-user data isolation.

Use only non-sensitive sample prompts and data when testing the public demo.

---

## 📚 Learning outcomes

This project has provided hands-on practice with:

- Python functions and control flow
- FastAPI routes and request handling
- Pydantic data validation
- REST APIs and HTTP requests
- Environment variables and API-key management
- Gemini integration through an OpenAI-compatible client
- LLM intent detection
- Rule-based routing and fallback logic
- Calculator planning and sequential operation execution
- JSON-backed persistence
- Browser `fetch()`, DOM updates, and `localStorage`
- Error handling and debugging
- Git, GitHub, and deployment workflows

---

## 🛣️ Future improvements

Potential next steps include:

- Stronger parsing and validation of calculator plans
- More reliable tool selection and multi-tool planning
- User-selected locations for weather requests
- Configurable user IDs for external user lookups
- Per-user memory stored in a database
- Better tests for tool routing and calculation edge cases
- A POST-based chat endpoint for longer prompts
- More consistent API timeouts and error responses
- Authentication and access control
- Clearer separation of frontend, tools, and orchestration modules
- Automated deployment checks and improved observability

---

## 👨‍💻 About

I'm **Mayank Chouhan**, a B.Tech CSE student interested in Artificial Intelligence, Python, backend development, FastAPI, Agentic AI, and automation.

ASK is part of my hands-on learning journey: understanding AI agents by building, testing, debugging, and improving a working application.

---

**ASK — Ask something. Let the agent figure out the tool. 🤖**
