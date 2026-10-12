"""Build the one-page StockSense digital poster from verified project results."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "StockSense_AI_Poster.pdf"
SCREENSHOT = ROOT / "docs" / "assets" / "stocksense-ready.png"

pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "C:/Windows/Fonts/arialbd.ttf"))

NAVY = colors.HexColor("#172b4d")
TEAL = colors.HexColor("#0f766e")
MUTED = colors.HexColor("#526174")
PALE = colors.HexColor("#e8f4f0")
LINE = colors.HexColor("#dce3ed")

PAGE_W, PAGE_H = landscape(A3)
pdf = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_W, PAGE_H))
pdf.setTitle("StockSense AI digital poster")
pdf.setAuthor("VUT AI Solutions")


def label(text, x, y, size=11, color=NAVY, bold=False):
    pdf.setFont("Arial-Bold" if bold else "Arial", size)
    pdf.setFillColor(color)
    pdf.drawString(x * mm, y * mm, text)


def paragraph(text, x, top, width, size=11, leading=16, color=NAVY):
    style = ParagraphStyle(
        "poster", fontName="Arial", fontSize=size, leading=leading,
        textColor=color, alignment=TA_LEFT,
    )
    item = Paragraph(text, style)
    _, height = item.wrap(width * mm, 1000)
    item.drawOn(pdf, x * mm, top * mm - height)
    return top - height / mm


def heading(text, x, y):
    label(text, x, y, size=18, bold=True)


# Header
pdf.setFillColor(NAVY)
pdf.rect(0, PAGE_H - 8 * mm, PAGE_W, 8 * mm, fill=1, stroke=0)
label("VUT AI SOLUTIONS  /  BUSINESS ANALYSIS 3.2", 20, 271, size=10, color=MUTED, bold=True)
label("StockSense AI", 20, 247, size=42, bold=True)
label("Sales forecasts and clearer stock orders for Sunrise Mini Market", 21, 230, size=16, color=TEAL)
label("Fictional retailer using anonymous Kaggle Store 1 and Item 1–5", 21, 220, size=10, color=MUTED)
pdf.setStrokeColor(LINE)
pdf.setLineWidth(1)
pdf.line(20 * mm, 213 * mm, 400 * mm, 213 * mm)

# Left column: business case and workflow
heading("The problem", 20, 198)
paragraph(
    "A small retailer must choose an order quantity before knowing next week's sales. "
    "Guessing can leave too little or too much stock. StockSense gives the manager "
    "a consistent estimate to check before ordering.", 20, 189, 110,
)
heading("What the app does", 20, 141)
paragraph("<b>1.</b> Shows seven daily sales estimates for a selected product.", 20, 132, 108)
paragraph("<b>2.</b> Combines the forecast with stock and delivery inputs.", 20, 112, 108)
paragraph("<b>3.</b> Shows a suggested order and warns about shortages before delivery.", 20, 92, 108)

# Centre column: real prototype screenshot
heading("Working prototype", 147, 198)
pdf.setStrokeColor(LINE)
pdf.setLineWidth(0.8)
pdf.rect(147 * mm, 73 * mm, 128 * mm, 110 * mm, fill=0, stroke=1)
pdf.drawImage(str(SCREENSHOT), 149 * mm, 75 * mm,
              width=124 * mm, height=106 * mm, preserveAspectRatio=True, anchor="c")
label("Product 1 example: 38 units suggested with the entered stock values", 147, 65,
      size=9, color=MUTED)

# Right column: measured evidence
heading("Measured forecast error", 293, 198)
label("2017 final test: daily MAE in units. Lower is better.", 293, 187, size=10, color=MUTED)
max_value = 7.0
bar_x = 293 * mm
bar_w = 80 * mm
for name, value, y, fill in [
    ("Weekly benchmark", 6.273, 169, colors.HexColor("#8d9cac")),
    ("Small LSTM", 5.411, 147, colors.HexColor("#547894")),
    ("Random forest", 4.812, 125, TEAL),
]:
    label(name, 293, y + 8, size=10, bold=(name == "Random forest"))
    pdf.setFillColor(PALE)
    pdf.rect(bar_x, (y - 1) * mm, bar_w, 6 * mm, fill=1, stroke=0)
    pdf.setFillColor(fill)
    pdf.rect(bar_x, (y - 1) * mm, bar_w * value / max_value, 6 * mm, fill=1, stroke=0)
    label(f"{value:.3f}", 376, y + 1, size=10, bold=True)
paragraph(
    "Random forest was chosen using 2016 validation results. Its 2017 daily MAE "
    "was 23.3% lower than the weekly benchmark. The LSTM had the lowest overall "
    "weekly-total error.", 293, 119, 106, size=10, leading=14,
)

# Footer: project coverage and limits
pdf.setFillColor(PALE)
pdf.rect(20 * mm, 25 * mm, 380 * mm, 29 * mm, fill=1, stroke=0)
paragraph(
    "<b>Scope and techniques:</b> 9,130 sales records from 2013–2017; one store and five anonymous items. "
    "The app compares a weekly benchmark, random forest and a small LSTM. Its text assistant "
    "classifies five request types and retrieves the displayed results.",
    25, 50, 222, size=10, leading=14,
)
paragraph(
    "<b>Limit:</b> Stock inputs are demonstration values. January 2018 has no observed outcomes "
    "in this dataset. No real stockout or cost savings are claimed.",
    261, 50, 133, size=10, leading=14,
)
label("Source: Kaggle Store Item Demand Forecasting Challenge; frozen StockSense evaluation, 12 October 2026.",
      20, 15, size=9, color=MUTED)

pdf.showPage()
pdf.save()
print(OUTPUT)
