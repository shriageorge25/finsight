import re
from datetime import datetime

import pdfplumber

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")
AMOUNT_RE = re.compile(r"^-?[\d,]+\.\d{2}$")
HEADER_ALIASES = {
    "date": {"date"},
    "description": {"description", "particulars", "narration"},
    "debit": {"debit", "withdrawal", "dr"},
    "credit": {"credit", "deposit", "cr"},
    "balance": {"balance"},
}
AMOUNT_ZONE_PAD = 45


def _parse_date(text):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def _group_lines(words, tol=3):
    lines = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if lines and abs(lines[-1][0] - w["top"]) <= tol:
            lines[-1][1].append(w)
        else:
            lines.append([w["top"], [w]])
    return [sorted(ws, key=lambda w: w["x0"]) for _, ws in lines]


def _find_header(lines):
    for i, line in enumerate(lines):
        found = {}
        for w in line:
            text = w["text"].lower()
            for col, names in HEADER_ALIASES.items():
                if text in names and col not in found:
                    found[col] = (w["x0"] + w["x1"]) / 2
        if len(found) == 5:
            return i, found
    return None, None


def parse_statement(path):
    rows = []
    opening_balance = None
    header = None
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            lines = _group_lines(page.extract_words())
            start = 0
            idx, cols = _find_header(lines)
            if cols:
                header = cols
                start = idx + 1
            if not header:
                continue
            zone = header["debit"] - AMOUNT_ZONE_PAD
            for line in lines[start:]:
                date = _parse_date(line[0]["text"])
                if date is None:
                    continue
                desc, amounts = [], {}
                for w in line[1:]:
                    center = (w["x0"] + w["x1"]) / 2
                    if AMOUNT_RE.match(w["text"]) and center >= zone:
                        col = min(("debit", "credit", "balance"), key=lambda c: abs(header[c] - center))
                        amounts[col] = float(w["text"].replace(",", ""))
                    else:
                        desc.append(w["text"])
                debit = amounts.get("debit")
                credit = amounts.get("credit")
                balance = amounts.get("balance")
                if debit is None and credit is None:
                    if opening_balance is None and balance is not None:
                        opening_balance = balance
                    continue
                rows.append({"date": date, "description": " ".join(desc),
                             "debit": debit, "credit": credit, "balance": balance})
    mismatches = []
    prev = opening_balance
    for r in rows:
        if prev is not None and r["balance"] is not None:
            expected = round(prev + (r["credit"] or 0) - (r["debit"] or 0), 2)
            if abs(expected - r["balance"]) > 0.01:
                mismatches.append({"date": r["date"], "description": r["description"],
                                   "expected_balance": expected, "balance": r["balance"]})
        if r["balance"] is not None:
            prev = r["balance"]
    return {"opening_balance": opening_balance, "rows": rows, "balance_mismatches": mismatches}
