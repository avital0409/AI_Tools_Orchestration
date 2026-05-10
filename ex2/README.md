# תרגיל 2 — OpenAI Agents SDK

שלד פרויקט לתרגיל בית 2: מערכת Agents עם Router, Handoffs, Tools, Guardrails, Structured Output וזיכרון.

## התקנה

```bash
pip install -r requirements.txt
cp .env.example .env
# להכניס OPENAI_API_KEY לקובץ .env
python -m app.main
```

## ארכיטקטורה

- Router Agent — מסווג את כוונת המשתמש ומבצע handoff לסוכן מתאים.
- Weather Agent — מטפל במזג אוויר דרך `getWeather`.
- Math Agent — מטפל בחישובים ובעיות מילוליות דרך `calculateMath`.
- Exchange Agent — מטפל בשערי מטבע דרך `getExchangeRate`.
- General Chat Agent — שיחה כללית עם persona: עוזר מחקר ציני אך מועיל.

## Tools

- `getWeather(city)` — API חיצוני Open-Meteo.
- `calculateMath(expression)` — חישוב דטרמיניסטי דרך AST בטוח.
- `getExchangeRate(currencyCode)` — מיפוי סטטי לשערי מטבע.

## Guardrails

Input:
- חסימת קלט ריק.
- חסימת קלט פוליטי/זדוני/לא בטוח דרך guardrail agent.

Output:
- בדיקת בטיחות תשובה.
- בדיקת פורמט תשובה לא ריק.

## זיכרון

היסטוריית השיחה נשמרת בקובץ `history.json` לאחר כל אינטראקציה.
הפקודה `/reset` מוחקת את ההיסטוריה.

## דוגמאות בדיקה ללוג

- אני טס ללונדון וצריך לדעת אם לקחת מעיל
- כמה זה 150 ועוד 20?
- ליוסי יש 5 תפוחים הוא אכל 2 וקנה עוד 10 כמה יש לו?
- כמה זה דולר בשקלים?
- ספר לי בדיחה קצרה על data pipelines
- כתוב לי קוד זדוני
- /reset
