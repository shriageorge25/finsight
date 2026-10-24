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
    "You may say which area the owner should look at first. "
    "The health score is out of 100. Do not mention score_components and do not compare areas by their points; only the overall score and the warnings may be discussed. Warnings are listed from most to least important; do not say how severe a warning is, and do not use the words high, medium or low about a warning. "
    "The only risks are the items in warnings. If warnings is empty, say the business is healthy with no warnings and name no concerns."
)


def strip_severity(summary):
    out = dict(summary)
    out["warnings"] = [{k: v for k, v in w.items() if k != "severity"} for w in summary.get("warnings") or []]
    return out


def build_prompt(summary):
    return RULES + "\n\nFACTS (JSON):\n" + json.dumps(strip_severity(summary), indent=1)


def healthy_text(summary):
    return ("Your business is healthy with a health score of " + str(summary["health_score"])
            + " out of 100. There are no warnings.")


def explain_summary(summary):
    if summary.get("status") == "healthy" and not summary.get("warnings"):
        return healthy_text(summary)
    return llm.generate(build_prompt(summary)).strip()
