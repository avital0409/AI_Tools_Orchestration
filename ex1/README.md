# AI Orchestration Assistant 🤖

## Overview
This project is an advanced AI Orchestrator built for **EX1 - Orchestration**. It demonstrates the power of a "Service Coordinator" model, where a central AI (Gemini) manages technical tools and casual conversation while building rapport with the user.

The assistant doesn't just chat; it evaluates user intent to dynamically call external APIs for weather, currency conversion, and mathematical computations, providing unified natural language responses.

## ✨ Key Features
- **Intelligent Tool-Calling**: Seamlessly switches between casual chat and technical tasks.
- **Live Weather**: Real-time forecasts via the `wttr.in` API.
- **Currency Exchange**: Up-to-the-minute conversion to ILS via `Frankfurter.app`.
- **Math Engine**: High-accuracy expression evaluation using `simpleeval`.
- **Session Persistence**: Saves your conversation history to `history.json` so you can pick up where you left off.
- **Smart Memory Control**: Type `/reset` in the chat to clear your history and start fresh with a clean slate.
- **Empathetic Persona**: Designed to match user energy, avoid hallucinations, and proactively suggest helpful actions.

## 🛠️ Architecture: The Orchestrator Protocol
The system follows a strict internal operational loop:
1.  **Phase A (Thought)**: Evaluate the query for casual vs. technical intent.
2.  **Phase B (Tool Call)**: Generate and execute structured API calls if needed.
3.  **Phase C (Response Generation)**: Synthesize tool outputs into a friendly, natural response.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- A Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### Installation
1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd EX1-Orchestration
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration
Create a `.env` file in the root directory and add your API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## 🎮 Usage
To start the assistant, run:
```bash
python app.py
```
This will launch a **Gradio ChatInterface** in your browser.

### Commands
- **`/reset`**: Wipes the local history file (`history.json`) and resets the assistant's memory.

## 📦 Dependencies
- `gradio`: Web interface.
- `openai`: Client for Gemini (OpenAI-compatible mode).
- `python-dotenv`: Environment variable management.
- `requests`: External API calls.
- `simpleeval`: Safe math evaluation.
