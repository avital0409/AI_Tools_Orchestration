from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, Runner, input_guardrail, output_guardrail
from agents import TResponseInputItem
from models import GuardrailCheck, FinalAnswer

SAFETY_TEXT = "I cannot process this request due to safety protocols"

input_guardrail_agent = Agent(
    name="Input Safety Guardrail",
    instructions=(
        "Check if input is empty, political, asks for malicious code, or unrelated to supported tasks. "
        "Return blocked=true only for unsafe/invalid input."
    ),
    output_type=GuardrailCheck,
)

output_guardrail_agent = Agent(
    name="Output Safety Guardrail",
    instructions=(
        "Check if output contains political persuasion, malicious code, or violates expected answer safety. "
        "Return blocked=true if unsafe."
    ),
    output_type=GuardrailCheck,
)

@input_guardrail(run_in_parallel=False)
async def input_safety_guardrail(ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]) -> GuardrailFunctionOutput:
    text = input if isinstance(input, str) else str(input)
    if not text.strip():
        return GuardrailFunctionOutput(output_info={"reason": "empty input"}, tripwire_triggered=True)
    result = await Runner.run(input_guardrail_agent, text, context=ctx.context)
    return GuardrailFunctionOutput(output_info=result.final_output, tripwire_triggered=result.final_output.blocked)

@output_guardrail
async def output_safety_guardrail(ctx: RunContextWrapper, agent: Agent, output: FinalAnswer) -> GuardrailFunctionOutput:
    result = await Runner.run(output_guardrail_agent, output.response, context=ctx.context)
    return GuardrailFunctionOutput(output_info=result.final_output, tripwire_triggered=result.final_output.blocked)

@output_guardrail
async def output_format_guardrail(ctx: RunContextWrapper, agent: Agent, output: FinalAnswer) -> GuardrailFunctionOutput:
    bad = not isinstance(output.response, str) or len(output.response.strip()) == 0
    return GuardrailFunctionOutput(output_info={"valid": not bad}, tripwire_triggered=bad)
