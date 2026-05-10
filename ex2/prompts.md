# Prompts

The prompts used by the system are stored in `app/prompts.py`:

- Router Agent: few-shot routing prompt with at least 3 examples per category.
- Weather Agent: weather-specific tool usage.
- Math Agent: translates word problems to clean math expressions and calls deterministic tool.
- Exchange Agent: currency rate and conversion handling.
- General Chat Agent: cynical but helpful research assistant persona.

Safety refusal text:
`I cannot process this request due to safety protocols`
