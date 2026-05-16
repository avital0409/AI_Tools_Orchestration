import os
from agents import Agent, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from models import RouterDecision, FinalAnswer
from tools import getWeather, calculateMath, getExchangeRate
from prompts import ROUTER_PROMPT, GENERAL_CHAT_PROMPT, MATH_AGENT_PROMPT, WEATHER_AGENT_PROMPT, EXCHANGE_AGENT_PROMPT
from guardrails import input_safety_guardrail, output_safety_guardrail, output_format_guardrail

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

weather_agent = Agent(
    name="weather_agent",
    handoff_description="Handles weather questions and weather-related city comparisons.",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n{WEATHER_AGENT_PROMPT}",
    tools=[getWeather],
    output_type=FinalAnswer,
    output_guardrails=[output_safety_guardrail, output_format_guardrail],
    model=MODEL,
)

math_agent = Agent(
    name="math_agent",
    handoff_description="Handles direct math expressions and word problems.",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n{MATH_AGENT_PROMPT}",
    tools=[calculateMath],
    output_type=FinalAnswer,
    output_guardrails=[output_safety_guardrail, output_format_guardrail],
    model=MODEL,
)

exchange_agent = Agent(
    name="exchange_agent",
    handoff_description="Handles currency-rate questions and simple currency conversions.",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n{EXCHANGE_AGENT_PROMPT}",
    tools=[getExchangeRate, calculateMath],
    output_type=FinalAnswer,
    output_guardrails=[output_safety_guardrail, output_format_guardrail],
    model=MODEL,
)

general_chat_agent = Agent(
    name="general_chat_agent",
    handoff_description="Handles supported general conversation.",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n{GENERAL_CHAT_PROMPT}",
    output_type=FinalAnswer,
    output_guardrails=[output_safety_guardrail, output_format_guardrail],
    model=MODEL,
)

router_agent = Agent(
    name="router_agent",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n{ROUTER_PROMPT}\nAfter deciding, hand off to the correct specialist agent.",
    output_type=RouterDecision,
    handoffs=[
        handoff(weather_agent),
        handoff(math_agent),
        handoff(exchange_agent),
        handoff(general_chat_agent),
    ],
    input_guardrails=[input_safety_guardrail],
    model=MODEL,
)
