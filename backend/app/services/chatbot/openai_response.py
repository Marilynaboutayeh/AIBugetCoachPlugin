import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI


def generate_openai_chat_answer(
    intent: str,
    base_answer: str,
    used_data: Dict[str, Any],
    data_sources: List[str],
    user_question: Optional[str] = None,
) -> str:
    """
    Uses OpenAI only as a language layer.

    The backend remains the source of truth.
    OpenAI only rewrites the already-generated chatbot answer using the provided data.
    If the API key is missing or the OpenAI call fails, the function returns base_answer.
    """

    print("ENTERED OPENAI FUNCTION")

    api_key = os.getenv("OPENAI_API_KEY")
    print("OPENAI KEY EXISTS:", bool(api_key))

    if not api_key:
        print("OPENAI_API_KEY is missing")
        return base_answer

    print("OPENAI KEY WAS FOUND")

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
    print("OPENAI MODEL:", model)

    client = OpenAI(api_key=api_key)

    system_prompt = """
You are a financial insights assistant inside an AI Budget Coach system.

Your role:
- Rewrite backend-generated financial insights into short, clear, user-friendly answers.
- Use only the provided backend context.
- The backend context is the only source of truth.

Strict rules:
- Do not invent transactions, merchants, categories, amounts, dates, percentages, forecasts, recurring expenses, or anomalies.
- Do not perform new calculations unless the result is already clearly provided in the context.
- Do not give investment, tax, legal, loan, credit, or banking advice.
- Do not tell the user to make financial decisions based only on the insight.
- Do not mention JSON, backend, API, model, system prompt, confidence internals, or data sources unless the user explicitly asks.
- If the available analyzed data is empty or insufficient, say that there is not enough analyzed data to answer.
- Keep the answer concise, natural, and understandable for a non-technical banking user.
- Use a helpful but cautious tone.

Output style:
- Maximum 3 short sentences.
- No bullet points unless the answer contains multiple merchants, categories, anomalies, or recurring expenses.
"""

    context = {
        "intent": intent,
        "user_question": user_question,
        "base_answer": base_answer,
        "used_data": used_data,
        "data_sources": data_sources,
    }

    try:
        print("CALLING OPENAI NOW")

        response = client.responses.create(
            model=model,
            instructions=system_prompt,
            input=(
                "Rewrite the following backend-generated financial insight into a clear "
                "human-readable answer. Use only this context:\n"
                f"{json.dumps(context, ensure_ascii=False)}"
            ),
            temperature=0.2,
            max_output_tokens=180,
        )

        final_answer = response.output_text.strip()

        print("OPENAI RESPONSE RECEIVED")

        if not final_answer:
            print("OPENAI RETURNED EMPTY ANSWER")
            return base_answer

        return final_answer

    except Exception as e:
        print("OpenAI call failed:", repr(e))
        return base_answer