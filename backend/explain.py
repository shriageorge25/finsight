import json

import llm

RULES = (
    "You explain a small business's financial health to its owner in plain English. "
    "Use ONLY the facts in the JSON below. Never invent, estimate or recalculate a number, date or name. "
    "Write amounts as 'Rs.' followed by the number as given (you may add thousands separators but never round), "
    "and use dates exactly as given. "
    "Write 4 to 6 short sentences with no markdown and no bullet points: first the overall status and health score, "
    "then the main risks in order of severity, then the data-quality issue if there is one. "
    "This is decision support, not financial advice: do not recommend loans, investments or specific products. "
    "You may say which area the owner should look at first."
)


def build_prompt(summary):
    return RULES + "\n\nFACTS (JSON):\n" + json.dumps(summary, indent=1)


def explain_summary(summary):
    return llm.generate(build_prompt(summary)).strip()
