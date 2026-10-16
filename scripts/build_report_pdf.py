"""Build the group-review report PDF from docs/report.md."""
import re
import hashlib
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable, Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from PIL import Image as PILImage, ImageOps, ImageDraw
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs'
PDF_OUT = OUT
RENDER = ROOT / 'artifacts' / 'preview' / 'report_render'
RENDER.mkdir(parents=True, exist_ok=True)

for family, name in [('Arial', 'arial.ttf'), ('Arial-Bold', 'arialbd.ttf'),
                     ('Arial-Italic', 'ariali.ttf')]:
    pdfmetrics.registerFont(TTFont(family, str(Path('C:/Windows/Fonts') / name)))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold',
                              italic='Arial-Italic', boldItalic='Arial-Bold')

WIDTH = A4[0] - 50 * mm
body = ParagraphStyle('Body', fontName='Arial', fontSize=12, leading=18,
                      alignment=TA_JUSTIFY, spaceAfter=8, splitLongWords=True,
                      allowWidows=0, allowOrphans=0)
heading = ParagraphStyle('Heading', parent=body, fontName='Arial-Bold',
                         alignment=TA_LEFT, keepWithNext=True, spaceBefore=14,
                         spaceAfter=7)
subheading = ParagraphStyle('Subheading', parent=heading, spaceBefore=10)
cell = ParagraphStyle('Cell', parent=body, alignment=TA_LEFT, spaceAfter=0)
cell_head = ParagraphStyle('CellHead', parent=cell, fontName='Arial-Bold')
cover = ParagraphStyle('Cover', parent=body, alignment=TA_CENTER, spaceAfter=8)
cover_title = ParagraphStyle('CoverTitle', parent=cover, fontName='Arial-Bold',
                            spaceAfter=18)
caption = ParagraphStyle('Caption', parent=body, alignment=TA_LEFT,
                         spaceBefore=5, spaceAfter=10)
reference = ParagraphStyle('Reference', parent=body, alignment=TA_LEFT)
before_object = ParagraphStyle('BeforeObject', parent=body, keepWithNext=True)
list_item = ParagraphStyle('ListItem', parent=body, leftIndent=18, bulletIndent=0,
                           bulletFontName='Arial', bulletFontSize=12, spaceAfter=6)

def inline(value):
    value = escape(value)
    value = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)
    return value

def make_table(lines):
    raw = [[v.strip() for v in line.strip().strip('|').split('|')]
           for line in lines]
    raw = [row for row in raw
           if not all(re.fullmatch(r':?-+:?', v) for v in row)]
    count = len(raw[0])
    first = raw[0][0]
    if first == 'Full name':
        proportions = [.43, .21, .23, .13]
    elif first == 'Field':
        proportions = [.14, .28, .22, .36] if count == 4 else [.16, .36, .48]
    elif first == 'Reviewer':
        proportions = [.22, .14, .20, .44]
    elif first == 'date':
        proportions = [.34, .20, .20, .26]
    elif first == 'Period':
        proportions = [.22, .44, .34]
    elif count == 2:
        proportions = [.34, .66]
    else:
        proportions = [1 / count] * count
    data = [[Paragraph(inline(v), cell_head if i == 0 else cell)
             for v in row] for i, row in enumerate(raw)]
    table = Table(data, colWidths=[WIDTH * p for p in proportions],
                  minRowHeights=[0] + [48] * (len(data) - 1) if first == 'Reviewer' else None,
                  repeatRows=1, hAlign='LEFT', spaceBefore=5, spaceAfter=12)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eeeeee')),
        ('GRID', (0, 0), (-1, -1), .5, colors.HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    return table

source = (OUT / 'report.md').read_text(encoding='utf-8')
problem_section = source.split('## 2 Problem definition', 1)[1].split('## 3', 1)[0]
problem = problem_section.split('### The problem', 1)[1].split('### The benefit', 1)[0]
total_problem = re.sub(r'^### .*$', '', problem_section, flags=re.M)
assert len(problem.split()) <= 190
assert len(total_problem.split()) <= 250

class ReportCover(Flowable):
    """Reserve the first page for the original assignment cover."""
    def __init__(self):
        super().__init__()
        self.width = WIDTH
        self.height = 670

    def draw(self):
        pass

class ReportDocument(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == 'Heading':
            text = flowable.getPlainText()
            key = 'section-' + hashlib.sha1(text.encode('utf-8')).hexdigest()[:14]
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=0, closed=False)
            self.notify('TOCEntry', (0, text, self.page - 2, key))

toc = TableOfContents()
toc.levelStyles = [ParagraphStyle('ContentsEntry', fontName='Arial', fontSize=12,
                                  leading=18, spaceBefore=6, spaceAfter=4,
                                  textColor=colors.HexColor('#142d43'),
                                  leftIndent=0, firstLineIndent=0, rightIndent=24)]
toc.dotsMinLevel = 0
contents_title = ParagraphStyle('ContentsTitle', parent=heading, fontSize=22,
                               leading=28, spaceAfter=22)
lines = ('## Declaration and group members' + source.split('## Declaration and group members', 1)[1]).splitlines()
story = [ReportCover(), PageBreak(), Paragraph('Table of contents', contents_title),
         toc, PageBreak()]
in_cover = False
i = 0
def attach_context(objects):
    """Keep an object's introductory paragraph and heading on the same page."""
    context = []
    if story and isinstance(story[-1], Paragraph) and (
        story[-1].style.name == 'BeforeObject' or getattr(story[-1].style, 'keepWithNext', False)
    ):
        context.insert(0, story.pop())
        while story and isinstance(story[-1], Paragraph) and getattr(story[-1].style, 'keepWithNext', False):
            context.insert(0, story.pop())
    return KeepTogether(context + objects)

while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    if line == '<!-- PAGE -->':
        story.append(PageBreak())
        in_cover = False
        i += 1
        continue
    if line.startswith('|'):
        block = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            block.append(lines[i])
            i += 1
        story.append(attach_context([make_table(block)]))
        continue
    if line.startswith('!['):
        matched = re.fullmatch(r'!\[(.*?)\]\((.*?)\)', line)
        path = OUT / matched.group(2)
        with PILImage.open(path) as im:
            h = WIDTH * im.height / im.width
        figure = [Image(str(path), width=WIDTH, height=h)]
        i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i < len(lines) and lines[i].startswith('Figure '):
            figure.append(Paragraph(inline(lines[i]), caption))
            i += 1
        story.append(attach_context(figure))
        continue
    if line.startswith('#'):
        level = len(line) - len(line.lstrip('#'))
        text = line[level:].strip()
        if level == 1:
            story.extend([Spacer(1, 30 * mm), Paragraph(inline(text), cover_title),
                          Paragraph('Project report', cover)])
        elif in_cover and text == 'Retail sales forecasting and stock replenishment':
            story.extend([Paragraph(inline(text), cover_title), Spacer(1, 6 * mm)])
        else:
            story.append(Paragraph(inline(text), heading if level == 2 else subheading))
        i += 1
        continue
    numbered = re.match(r'^(\d+)\.\s+(.+)$', line)
    if numbered:
        story.append(Paragraph(inline(numbered.group(2)), list_item,
                               bulletText=numbered.group(1) + '.'))
        i += 1
        continue
    paragraph = [line]
    i += 1
    while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(('#', '|', '![', '<!--')):
        paragraph.append(lines[i].strip())
        i += 1
    text = ' '.join(paragraph)
    # Keep cover metadata centred; the overview remains justified body text.
    style = cover if in_cover and len(text.split()) < 15 else body
    if re.match(r'^\[\d+\]', text):
        style = reference
    next_index = i
    while next_index < len(lines) and not lines[next_index].strip():
        next_index += 1
    if next_index < len(lines) and lines[next_index].strip().startswith(('|', '![')):
        style = before_object
    story.append(Paragraph(inline(text), style))

def footer(canvas, document):
    if document.page <= 2:
        return
    canvas.saveState()
    canvas.setFont('Arial', 12)
    canvas.drawString(25 * mm, 13 * mm, 'StockSense AI project report')
    canvas.drawRightString(A4[0] - 25 * mm, 13 * mm, str(document.page - 2))
    canvas.restoreState()

pdf_path = PDF_OUT / 'StockSense_AI_Report_Review.pdf'
doc = ReportDocument(str(pdf_path), pagesize=A4, leftMargin=25 * mm,
                        rightMargin=25 * mm, topMargin=22 * mm,
                        bottomMargin=23 * mm, title='StockSense AI - Project report',
                        author='VUT AI Solutions')
doc.multiBuild(story, onFirstPage=footer, onLaterPages=footer)
# Preserve the university's original cover graphics and text without redrawing them.
composed = PdfWriter(clone_from=BytesIO(pdf_path.read_bytes()))
official_cover = PdfReader(OUT / 'assets' / 'assignment-cover.pdf')
composed.pages[0].merge_page(official_cover.pages[0])
# Remove the original brief's 'Page 1 of 7' footer from the unnumbered cover.
from reportlab.pdfgen.canvas import Canvas
cover_mask = BytesIO()
mask_canvas = Canvas(cover_mask, pagesize=A4)
mask_canvas.setFillColor(colors.white)
mask_canvas.rect(0, 0, A4[0], 32, fill=1, stroke=0)
mask_canvas.save()
composed.pages[0].merge_page(PdfReader(BytesIO(cover_mask.getvalue())).pages[0])
from pypdf.constants import PageLabelStyle
composed.set_page_label(0, 1, prefix='')
composed.set_page_label(2, len(composed.pages) - 1, style=PageLabelStyle.DECIMAL, start=1)
composed.write(pdf_path)

reader = PdfReader(pdf_path)
text = '\n'.join(page.extract_text() for page in reader.pages)
normalised_text = ' '.join(text.split())
assert '913,000' in text and '9,130' in text
assert 'Sunrise Mini Market' in text
assert '79 tests' in normalised_text
assert 'For the community' in normalised_text and 'municipality' in normalised_text
assert 'Categorical ID' in normalised_text and 'Temporal:' in normalised_text and 'Numerical:' in normalised_text
assert 'python -m stocksense.terminal' in normalised_text
assert len(reader.pages) >= 10
print('Created:', pdf_path)
print('Pages:', len(reader.pages))
print('Problem words:', len(problem.split()), 'Combined:', len(total_problem.split()))
for n, page in enumerate(reader.pages, 1):
    print('Page', n, 'words', len(page.extract_text().split()))

pdf = pdfium.PdfDocument(str(pdf_path))
thumbs = []
for n in range(len(pdf)):
    im = pdf[n].render(scale=1.5).to_pil()
    im.save(RENDER / f'page-{n+1:02}.png')
    thumb = ImageOps.contain(im, (298, 422))
    tile = PILImage.new('RGB', (318, 452), 'white')
    tile.paste(thumb, ((318 - thumb.width) // 2, 5))
    ImageDraw.Draw(tile).text((12, 432), f'Page {n+1}', fill='black')
    thumbs.append(tile)
sheet = PILImage.new('RGB', (318 * 4, 452 * ((len(thumbs) + 3) // 4)), '#dddddd')
for n, im in enumerate(thumbs):
    sheet.paste(im, ((n % 4) * 318, (n // 4) * 452))
sheet.save(RENDER / 'contact-sheet.png')
print('Rendered pages:', RENDER)
