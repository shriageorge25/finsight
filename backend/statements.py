import io

from fastapi import APIRouter, File, HTTPException, UploadFile

from statement_parser import parse_statement

router = APIRouter()
MAX_BYTES = 5 * 1024 * 1024


@router.post("/statements/parse")
def parse_uploaded_statement(file: UploadFile = File(...)):
    name = file.filename or "statement.pdf"
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    data = file.file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 5 MB")
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File is not a valid PDF")
    try:
        result = parse_statement(io.BytesIO(data))
    except Exception:
        raise HTTPException(status_code=422, detail="Could not read this PDF")
    rows = result["rows"]
    if not rows:
        raise HTTPException(status_code=422, detail="No transaction rows found in this PDF")
    return {
        "filename": name,
        "source": "local_pdf_parser",
        "opening_balance": result["opening_balance"],
        "row_count": len(rows),
        "total_debits": round(sum(r["debit"] or 0 for r in rows), 2),
        "total_credits": round(sum(r["credit"] or 0 for r in rows), 2),
        "rows": rows,
        "balance_mismatches": result["balance_mismatches"],
    }
