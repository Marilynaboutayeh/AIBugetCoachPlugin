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
    """

    # api_key = os.getenv("OPENAI_API_KEY")

    # if not api_key:
    #     return base_answer
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("OPENAI_API_KEY is missing")
        return base_answer

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")

    client = OpenAI(api_key=api_key)

    system_prompt = """
You are a financial insight assistant inside an AI Budget Coach system.

Rules:
- Answer only using the provided backend context.
- Do not invent transactions, merchants, categories, amounts, dates, percentages, forecasts, recurring expenses, or anomalies.
- Do not give investment, tax, legal, loan, or banking advice.
- Do not mention JSON, backend, API, model, or system prompts.
- Keep the answer short, clear, and understandable for a non-technical banking user.
- Use a helpful but cautious tone.
- If the backend context is insufficient, say that the available analyzed data is not enough to answer.
"""

    context = {
        "intent": intent,
        "user_question": user_question,
        "base_answer": base_answer,
        "used_data": used_data,
        "data_sources": data_sources,
    }

    try:
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

        if not final_answer:
            return base_answer

        return final_answer

    # except Exception:
    #     return base_answer

    except Exception as e:
        print("OpenAI call failed:", repr(e))
        return base_answer