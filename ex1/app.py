import json
import logging
import os
import sys
import textwrap
from typing import List, Dict, Any, Optional

import gradio as gr
import requests
from dotenv import load_dotenv
from openai import OpenAI
from simpleeval import simple_eval

# --- Configuration & Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

HISTORY_FILE = "history.json"
GEMINI_MODEL_NAME = "gemini-2.5-flash-lite"

load_dotenv(override=True)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    logger.critical("Gemini API key not set in .env. The application cannot function.")
    sys.exit(1)

logger.info("Gemini API key initialized successfully.")

# --- Gemini Initialization ---
gemini = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# --- Tool Implementations & Schemas ---

def getWeather(city: str) -> str:
    """Retrieves the current weather for a given city."""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        current = data['current_condition'][0]
        temp_c = current['temp_C']
        description = current['weatherDesc'][0]['value']
        
        return f"The current weather in {city.title()} is {temp_c}°C, {description}."
    except Exception as e:
        logger.error(f"Weather Tool Error: {e}")
        return f"I'm sorry, I couldn't retrieve the weather for {city} right now. Please try again later."

getWeather_schema = {
    "name": "getWeather",
    "description": "Use this tool ONLY if the user explicitly asks about the current weather or temperature. DO NOT use if a city is just mentioned in context.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "The city to get the weather for"}
        },
        "required": ["city"]
    }
}

def getExchangeRate(currencyCode: str) -> str:
    """Retrieves the current exchange rate from a given currency to ILS."""
    try:
        url = f"https://api.frankfurter.app/latest?from={currencyCode}&to=ILS"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        rate = data['rates']['ILS']
        return f"The current {currencyCode} rate is {rate:.2f} ILS"
    except Exception as e:
        logger.error(f"Exchange Rate Tool Error: {e}")
        return f"I'm sorry, I can't find the exchange rate for {currencyCode} at the moment."

getExchangeRate_schema = {
    "name": "getExchangeRate",
    "description": "Use this tool ONLY if the user explicitly asks to convert money to ILS or for a rate. DO NOT use for general mentions of $ or currency.",
    "parameters": {
        "type": "object",
        "properties": {
            "currencyCode": {"type": "string", "description": "The currency code to get the exchange rate for"}
        },
        "required": ["currencyCode"],
    }
}

def calculateMath(expression: str) -> Any:
    """Evaluates a mathematical expression safely."""
    try:
        logger.info(f"Calculating expression: {expression}")
        return simple_eval(expression)
    except Exception as e:
        logger.error(f"Math Tool Error: {e}")
        return "I'm sorry, I couldn't calculate that expression. Please check the syntax."

calculateMath_schema = {
    "name": "calculateMath",
    "description": "REQUIRED for all numerical calculations. If you have retrieved exchange rates, you MUST use this tool to perform the final conversion. Never calculate in your head.",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "The expression to evaluate (e.g. '100 * 3.52 / 2.99')"}
        },
        "required": ["expression"],
    }
}

# Unified tools list for the AI
TOOLS = [
    {"type": "function", "function": getWeather_schema},
    {"type": "function", "function": getExchangeRate_schema},
    {"type": "function", "function": calculateMath_schema}
]

# --- History Persistence Logic ---

def load_history_from_disk() -> List[Dict[str, str]]:
    """Loads conversation history from the local JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load history: {e}")
        return []

def save_history_to_disk(history: List[Dict[str, str]]) -> None:
    """Saves conversation history to the local JSON file."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
    except IOError as e:
        logger.error(f"Failed to save history: {e}")

def welcome_back() -> List[Dict[str, str]]:
    """Shows only the greeting in the UI for returning users, keeping old history hidden."""
    disk_history = load_history_from_disk()
    if disk_history:
        logger.info(f"Returning user detected. Showing only greeting in UI.")
        # Return ONLY the greeting. Old history remains on disk and will be loaded in chat() for context.
        return [{"role": "assistant", "content": "👋 Welcome back!"}]
    
    logger.info("New user: No history found.")
    return []

# Global state for UI initialization (maintained for cross-session UI sync)
conversation_history = load_history_from_disk()

# --- Orchestration & Chat Logic ---

def handle_tool_calls(tool_calls: list) -> List[Dict[str, Any]]:
    """Executes tool calls requested by the AI and packages results."""
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        logger.info(f"Executing tool: {tool_name}")
        
        # Dispatch to the appropriate function
        tool_func = globals().get(tool_name)
        if tool_func:
            result = tool_func(**arguments)
            logger.info(f"Tool result: {result}")
        else:
            logger.warning(f"Attempted to call unknown tool: {tool_name}")
            result = "Error: Tool not found."
            
        results.append({
            "role": "tool",
            "content": json.dumps(result),
            "tool_call_id": tool_call.id
        })
    return results

def get_system_prompt() -> str:
    """Constructs the dynamic system prompt based on user status."""
    disk_history = load_history_from_disk()
    status_msg = (
        "The user is returning from a previous session. A 'Welcome back' message has already been displayed at the top of this session, so just continue where you left off naturally."
        if disk_history else
        "This is a brand new user. Be welcoming and ask how you can assist them today."
    )
    
    prompt = textwrap.dedent(f"""\
        You are a friendly and engaging AI assistant, named 'Agent J'
        {status_msg}
        Your primary goal is to build a genuine relationship with the user while efficiently managing your technical tools.

        ### OPERATIONAL PROTOCOL:
        - Phase A (Thought): Evaluate query:
            - If Technical -> Identify tool.
            - If Casual -> answer.
          If a query requires multiple data points (like temperatures for two different cities), you MUST call the necessary tools sequentially or in parallel. Do not ask for permission to check the weather; just do it.
        - Phase B (Tool Call): Use formal API for tools.
        - Phase C (Response): Take the tool results (if any) and weave it into a warm, conversational response. Always end with a thought or a question that keeps the conversation alive.
        
        ### CONVERSATIONAL RULES:
        1. **Never say "How can I help you?"** or "What can I do for you?". It feels robotic and it's forbidden. 
        2. **Be Curious**: If a user shares something, ask a follow-up question. If they use a tool, comment on the result (e.g., "Wow, that's a lot of dollars!" or "Stay warm in that weather!").
        3. **Be Empathetic**: If the user shares something personal or a feeling, acknowledge it with empathy before moving to tools.
        4. **Reference the Past**: You have access to history. Use it! (e.g., "Earlier you mentioned X, how is that going?").
        5. **Be Human**: Use natural transitions. Don't just give facts; give context and personality.
        6. **Guardrails**: Do NOT hallucinate. If asked for weather/math/rates, use tools.

        ### MANDATORY CALCULATION RULE:
        - ANY and ALL numerical transformations (multiplication, division, percentages) MUST be performed by the `calculateMath` tool. 
        - Even if the math seems simple (like 100 * rate), you are FORBIDDEN from calculating it yourself. 
        - NEVER guess or estimate a final financial total.

        ### CURRENCY CONVERSION RULE:
        When converting from Currency A to Currency B using ILS as a bridge, the formula MUST be:
            Amount * (Rate_of_Currency_A / Rate_of_Currency_B).
        Example: To convert 100 USD to EUR, call calculateMath with 100 * (USD_rate / EUR_rate)

        ### WEATHER COMPARISON TOOL RULES:
        When the user asks to compare temperatures between two cities (by how many times, or by how much hotter/colder), you MUST follow these steps IN ORDER — no exceptions:
        Step 1: Call `getWeather` for city A.
        Step 2: Call `getWeather` for city B.
        Step 3: ALWAYS call `calculateMath` to compute the result. You are FORBIDDEN from computing the number yourself.
        - For "by how much hotter/colder": call `calculateMath` with `temp_A - temp_B`
        - For "by how many times hotter/colder": call `calculateMath` with `temp_A / temp_B`
        Skipping Step 3 is a critical violation. Even if the math seems obvious, you MUST use the tool.

        Available Tools: getWeather, getExchangeRate, calculateMath.
        You are a friend who happens to have a calculator and a weather station, not a machine.
    """)
    return prompt

def chat(message: str, history: List[Dict[str, str]]) -> str:
    """Main chat handler for Gradio."""
    global conversation_history
    
    # --- Special Commands ---
    if message.strip().lower() == "/reset":
        try:
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
            conversation_history.clear()
            save_history_to_disk([])
            logger.info("Session history reset.")
            
            gif_url = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExaXB5dTV1c2NyaDE4ank1a2g1NzZobXRwcHZ4ajhyNzJsbzVsZHd6MyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/vClUiaIwe8eUEZw2jJ/giphy.gif"
            return f"""
                ### 🗑️ **Memory Reset Successful**

                ![Neuralyzer]({gif_url})

                Wait, what were we talking about? I just saw a bright flash of light... 🕶️ 
                My memory has been wiped. How can I help you (again) for the first time?
            """
        except Exception as e:
            logger.error(f"Reset Error: {e}")
            return "Something went wrong while trying to reset my memory. Please try again."

    try:
        # Load the persistent history from disk (which is NOT shown in the UI)
        disk_history = load_history_from_disk()
        
        # Combine everything for Gemini:
        # System Prompt + Hidden Disk History + Visible UI History + New Message
        messages = [{"role": "system", "content": get_system_prompt()}] + \
                   disk_history + \
                   history + \
                   [{"role": "user", "content": message}]
        
        while True:
            response = gemini.chat.completions.create(
                model=GEMINI_MODEL_NAME,
                messages=messages,
                tools=TOOLS,
                tool_choice='auto',
                temperature=0.7
            )
            response_msg = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            if finish_reason == "tool_calls":
                results = handle_tool_calls(response_msg.tool_calls)
                messages.append(response_msg)
                messages.extend(results)
                continue
            
            if not (response_msg.content and response_msg.content.strip()): 
                messages.append({
                    "role": "user", 
                    "content": "The tools finished. Now, please provide the final conversational answer to the user."
                })

            final_content = response_msg.content
            break
        
        # --- Persistence ---
        # We save the 'real' history to disk (excluding the transient greeting if we want, 
        # but actually saving the whole session flow is usually better).
        # To avoid the greeting accumulating on disk, we load current disk history and append only the new exchange.
        current_disk_history = load_history_from_disk()
        updated_history = current_disk_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": final_content}
        ]
        save_history_to_disk(updated_history)
        
        # Update global state (if needed for other components)
        conversation_history.clear()
        conversation_history.extend(updated_history)
        
        return final_content

    except Exception as e:
        logger.exception(f"Chat logic crash: {e}")
        gif_url = "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3OTQwYzg1aXE3dHZhb3JpYjczbGZqbzJmNXdsdnNpZXNkZjhyeGRsOCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/qTUTbUhwpAG0yRakna/giphy.gif"
        return f"Oh no, something went wrong behind the scenes. Can we try again?\n\n![Failure GIF]({gif_url})"

# --- Launch ---
with gr.Blocks(fill_height=True) as demo:
    chatbot = gr.Chatbot(height="80vh", value=welcome_back)
    
    gr.ChatInterface(
        fn=chat,
        chatbot=chatbot
    )
    
demo.launch()