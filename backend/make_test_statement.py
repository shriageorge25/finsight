from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ROWS = [
    ("2026-09-01", "OPENING BALANCE", "", "", "250000.00"),
    ("2026-09-02", "NEFT FROM MEHTA TRADERS INV 41", "", "60000.00", "310000.00"),
    ("2026-09-04", "UPI TO RAJ PACKAGING", "18500.00", "", "291500.00"),
    ("2026-09-05", "SALARY SEP", "75000.00", "", "216500.00"),
    ("2026-09-09", "NEFT FROM SHARMA STORES INV 42", "", "42000.00", "258500.00"),
    ("2026-09-12", "RENT WORKSHOP", "30000.00", "", "228500.00"),
    ("2026-09-15", "ELECTRICITY BILL", "6400.00", "", "222100.00"),
    ("2026-09-18", "NEFT FROM PATEL AGENCIES INV 44", "", "90000.00", "312100.00"),
    ("2026-09-22", "LOAN EMI", "44000.00", "", "268100.00"),
    ("2026-09-25", "UPI TO STEEL SUPPLIER", "52000.00", "", "216100.00"),
    ("2026-09-29", "NEFT FROM KUMAR TEXTILES INV 45", "", "38000.00", "254100.00"),
]
COLS = (40, 110, 330, 400, 470)

out = Path("test_data")
out.mkdir(exist_ok=True)
c = canvas.Canvas(str(out / "test_statement.pdf"), pagesize=A4)
c.setFont("Courier-Bold", 10)
c.drawString(40, 800, "SAMPLE BANK STATEMENT (SYNTHETIC - DEMO ONLY)")
c.setFont("Courier", 9)
c.drawString(40, 785, "Account: DEMO CURRENT ACCOUNT   Period: 2026-09-01 to 2026-09-30")
y = 750
for x, h in zip(COLS, ("Date", "Description", "Debit", "Credit", "Balance")):
    c.drawString(x, y, h)
y -= 18
for row in ROWS:
    for x, cell in zip(COLS, row):
        if cell:
            c.drawString(x, y, cell)
    y -= 16
c.save()
print("wrote", out / "test_statement.pdf")
