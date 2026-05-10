import ast
import logging
import operator
import sys
import requests
from agents import function_tool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Unsupported math expression")

@function_tool
def calculateMath(expression: str) -> str:
    """Calculate a clean mathematical expression deterministically."""
    tree = ast.parse(expression, mode="eval")
    result = _eval_node(tree.body)
    return f"{expression} = {result}"


@function_tool
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

@function_tool
def getWeather(city: str) -> str:
    """Return current weather for a city using Open-Meteo geocoding + forecast APIs."""
    city = city.strip()
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo = requests.get(geo_url, params={"name": city, "count": 1, "language": "en"}, timeout=10).json()
    if not geo.get("results"):
        return f"לא מצאתי עיר בשם {city}"
    item = geo["results"][0]
    forecast_url = "https://api.open-meteo.com/v1/forecast"
    data = requests.get(
        forecast_url,
        params={"latitude": item["latitude"], "longitude": item["longitude"], "current": "temperature_2m,weather_code"},
        timeout=10,
    ).json()
    temp = data.get("current", {}).get("temperature_2m")
    return f"ב{city} הטמפרטורה כרגע היא בערך {temp}°C"
