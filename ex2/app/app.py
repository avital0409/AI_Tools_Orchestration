import asyncio
import gradio as gr
from dotenv import load_dotenv
from typing import List, Dict

from agents import (
    Runner,
    trace,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)

from .agents_setup import (
    router_agent,
    weather_agent,
    math_agent,
    exchange_agent,
    general_chat_agent,
)

from .history import load_history, save_history, reset_history
from .guardrails import SAFETY_TEXT
from .logger_config import setup_logger

logger = setup_logger(__name__)

load_dotenv()

conversation_history = []

AGENTS_BY_INTENT = {
    "getWeather": weather_agent,
    "calculateMath": math_agent,
    "getExchangeRate": exchange_agent,
    "generalChat": general_chat_agent,
}


def history_to_text(items):
    return "\n".join(
        f'{item.get("role")}: {item.get("content")}'
        for item in items
        if isinstance(item, dict)
        and item.get("role") in ["user", "assistant"]
        and item.get("content")
    )


def build_agent_input(
    message: str,
    disk_history: List[Dict[str, str]]
) -> str:
    return f"""
Previous conversation:
{history_to_text(disk_history)}

Current user message:
{message}

Use the previous conversation only if it is relevant.
"""


async def run_agents(message: str) -> str:
    disk_history = load_history()

    agent_input = build_agent_input(
        message,
        disk_history
    )

    with trace(workflow_name="HW2 Agents Router"):
        router_result = await Runner.run(
            router_agent,
            agent_input
        )

    decision = router_result.final_output

    intent = getattr(
        decision,
        "intent",
        "generalChat"
    )

    target_agent = AGENTS_BY_INTENT.get(
        intent,
        general_chat_agent
    )

    with trace(workflow_name=f"HW2 Handoff To {intent}"):
        final_result = await Runner.run(
            target_agent,
            agent_input
        )

    answer = getattr(
        final_result.final_output,
        "response",
        final_result.final_output
    )

    return str(answer)


def save_conversation(user_message: str, assistant_message: str):
    current_disk_history = load_history()

    updated_history = current_disk_history + [
        {
            "role": "user",
            "content": user_message
        },
        {
            "role": "assistant",
            "content": assistant_message
        },
    ]

    save_history(updated_history)

    conversation_history.clear()
    conversation_history.extend(updated_history)


def load_chat_history():
    if load_history():
        return [{
            "role": "assistant",
            "content": "ברוך שובך — נמצאה היסטוריית שיחה.",
        }]

    return [{
        "role": "assistant",
        "content": "שלום לך! נעים להכיר. אני בוט התמיכה John",
    }]


def reset_message():
    gif_url = (
        "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjEx"
        "aXB5dTV1c2NyaDE4ank1a2g1NzZobXRwcHZ4ajhyNzJsbzVsZHd6My"
        "ZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/vClUiaIwe8eUEZw2jJ/giphy.gif"
    )

    return f"""
# 🗑️ ההיסטוריה אופסה

<img src="{gif_url}" width="300">

הזיכרון נמחק בהצלחה.  
אפשר להתחיל שיחה חדשה 🙂
"""


def chat(message: str, history) -> str:
    global conversation_history

    message = (message or "").strip()

    if not message:
        return ""

    logger.info(f"User Message: {message}")

    if message.lower() == "/reset":
        logger.info("Command received: /reset - Clearing history.")
        reset_history()
        conversation_history.clear()

        return reset_message()


    try:
        answer = asyncio.run(
            run_agents(message)
        )

        save_conversation(
            message,
            answer
        )

        return answer

    except (
        InputGuardrailTripwireTriggered,
        OutputGuardrailTripwireTriggered,
    ):
        save_conversation(
            message,
            SAFETY_TEXT
        )

        return SAFETY_TEXT

    except Exception as e:
        return f"שגיאה: {e}"


with gr.Blocks(fill_height=True) as demo:
    chatbot = gr.Chatbot(
        height="80vh",
        rtl=True
    )

    gr.ChatInterface(
        fn=chat,
        chatbot=chatbot,
        textbox=gr.Textbox(
            placeholder="לדוגמה: אני טס ללונדון, צריך לקחת מעיל?",
            container=False,
            scale=7,
            rtl=True
        ),
    )

    demo.load(
        fn=load_chat_history,
        inputs=None,
        outputs=chatbot,
    )


if __name__ == "__main__":
    demo.launch()