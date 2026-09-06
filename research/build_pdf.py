#!/usr/bin/env python3
"""Build the Truss brief PDF.

    ./pdfenv/bin/python build_pdf.py [out.pdf]

Everything is generated. Edit CONTENT at the bottom, then re-run.
"""
import sys, os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, KeepTogether,
                                PageBreak, Flowable, ListFlowable, ListItem,
                                NextPageTemplate)

# ---------------------------------------------------------------- palette
INK        = colors.HexColor("#0B0D12")
INK2       = colors.HexColor("#12151C")
CHORD      = colors.HexColor("#E8EAED")
CHORD_LOW  = colors.HexColor("#6E7686")
STEEL      = colors.HexColor("#8B93A3")
AMBER      = colors.HexColor("#F5A524")
AMBER_SOFT = colors.HexColor("#FFD08A")
TENSION    = colors.HexColor("#5B9DD9")
VERIFIED   = colors.HexColor("#3FB27F")
FAULT      = colors.HexColor("#E5484D")
PAPER      = colors.HexColor("#FBFBF9")
BODY       = colors.HexColor("#1A1D24")
DIM        = colors.HexColor("#5C6373")
HAIR       = colors.HexColor("#D8DAD5")
BAND       = colors.HexColor("#F1F1ED")

# ---------------------------------------------------------------- fonts
NOTO = "/usr/share/fonts/noto"
JB   = "/usr/share/fonts/TTF"
def _reg(name, path):
    if os.path.exists(path):
        pdfmetrics.registerFont(TTFont(name, path)); return True
    return False

HAVE = all([
    _reg("Body",    f"{NOTO}/NotoSans-Regular.ttf"),
    _reg("Body-B",  f"{NOTO}/NotoSans-Bold.ttf"),
    _reg("Body-I",  f"{NOTO}/NotoSans-Italic.ttf"),
    _reg("Body-M",  f"{NOTO}/NotoSans-Medium.ttf"),
    _reg("Head",    f"{NOTO}/NotoSerif-Bold.ttf"),
    _reg("Head-R",  f"{NOTO}/NotoSerif-Regular.ttf"),
    _reg("Mono",    f"{JB}/JetBrainsMonoNerdFontMono-Regular.ttf"),
    _reg("Mono-B",  f"{JB}/JetBrainsMonoNerdFontMono-Bold.ttf"),
])
if HAVE:
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    registerFontFamily("Body", normal="Body", bold="Body-B", italic="Body-I",
                       boldItalic="Body-B")
    F, FB, FI, FM, FH, FHR, FMB = ("Body","Body-B","Body-I","Body-M","Head","Head-R","Mono-B")
    FMONO = "Mono"
else:                                   # graceful fallback to core fonts
    F, FB, FI, FM, FH, FHR = ("Helvetica","Helvetica-Bold","Helvetica-Oblique",
                              "Helvetica","Times-Bold","Times-Roman")
    FMONO, FMB = "Courier", "Courier-Bold"

# ---------------------------------------------------------------- page geom
PW, PH = A4
ML, MR, MT, MB = 24*mm, 22*mm, 26*mm, 22*mm
CW = PW - ML - MR

# ---------------------------------------------------------------- styles
def S(name, **kw):
    base = dict(name=name, fontName=F, fontSize=9.6, leading=14.6,
                textColor=BODY, spaceAfter=0, alignment=TA_LEFT)
    base.update(kw); return ParagraphStyle(**base)

st = {
 "p":     S("p", spaceAfter=7.5),
 "lead":  S("lead", fontSize=11.2, leading=17.4, textColor=colors.HexColor("#2A2F3A"),
            spaceAfter=10),
 "h1":    S("h1", fontName=FH, fontSize=21, leading=25, textColor=INK, spaceAfter=3),
 "h1n":   S("h1n", fontName=FMONO, fontSize=8.4, leading=11, textColor=AMBER, spaceAfter=5),
 "h2":    S("h2", fontName=FH, fontSize=13.2, leading=17, textColor=INK,
            spaceBefore=13, spaceAfter=5),
 "h3":    S("h3", fontName=FB, fontSize=10, leading=13.5, textColor=INK,
            spaceBefore=9, spaceAfter=3),
 "li":    S("li", spaceAfter=3.4),
 "cell":  S("cell", fontSize=8.5, leading=12.2),
 "cellb": S("cellb", fontName=FB, fontSize=8.5, leading=12.2),
 "cellh": S("cellh", fontName=FB, fontSize=8.1, leading=11.4, textColor=INK),
 "code":  S("code", fontName=FMONO, fontSize=7.7, leading=11.4,
            textColor=colors.HexColor("#22262F")),
 "cap":   S("cap", fontSize=8.1, leading=11.6, textColor=DIM, spaceBefore=3),
 "callh": S("callh", fontName=FB, fontSize=9.4, leading=13, textColor=INK, spaceAfter=3),
 "callp": S("callp", fontSize=9.2, leading=14, textColor=colors.HexColor("#2A2F3A")),
 "pull":  S("pull", fontName=FHR, fontSize=13, leading=19, textColor=INK),
}

# ---------------------------------------------------------------- truss art
def truss_path(w):
    """Return (top, bottom, web, joint) in a 0..w x 0..w box, y measured UP."""
    s = w / 64.0
    X = lambda v: v * s
    Y = lambda v: (64 - v) * s
    top    = ((X(5), Y(18)),  (X(32), Y(13.5)), (X(59), Y(18)))
    bottom = ((X(5), Y(48)),  (X(32), Y(43.5)), (X(59), Y(48)))
    web = [(5,48),(10.4,17.19),(15.8,46.56),(21.2,16.11),(26.6,45.84),(32,15.75),
           (37.4,45.84),(42.8,16.11),(48.2,46.56),(53.6,17.19),(59,48)]
    web = [(X(a), Y(b)) for a, b in web]
    return top, bottom, web, (X(32), Y(15.75)), s

def _quad(c, p0, p1, p2):
    c1 = (p0[0] + 2/3*(p1[0]-p0[0]), p0[1] + 2/3*(p1[1]-p0[1]))
    c2 = (p2[0] + 2/3*(p1[0]-p2[0]), p2[1] + 2/3*(p1[1]-p2[1]))
    c.bezier(p0[0], p0[1], c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])

def draw_truss(c, x, y, w, force=False, chord_col=CHORD, halo=True):
    """Draw the mark with its bottom-left at (x, y)."""
    top, bot, web, joint, s = truss_path(w)
    c.saveState(); c.translate(x, y); c.setLineCap(1); c.setLineJoin(1)
    if halo:
        for i, a in enumerate((0.05, 0.035, 0.022)):
            c.setFillColor(AMBER, alpha=a)
            c.circle(joint[0], joint[1], (5 + i*4.5) * s, stroke=0, fill=1)
    # web
    c.setLineWidth(1.9 * s)
    for i in range(len(web) - 1):
        if force:
            c.setStrokeColor(AMBER if i % 2 == 0 else TENSION)
        else:
            d = abs(i - 4.5) / 4.5
            c.setStrokeColor(AMBER if d < .25 else (STEEL if d > .6 else
                             colors.HexColor("#C39461")))
        c.line(web[i][0], web[i][1], web[i+1][0], web[i+1][1])
    # bottom chord
    c.setStrokeColor(CHORD_LOW); c.setLineWidth(2.6 * s)
    path = c.beginPath(); path.moveTo(*bot[0])
    c1 = (bot[0][0] + 2/3*(bot[1][0]-bot[0][0]), bot[0][1] + 2/3*(bot[1][1]-bot[0][1]))
    c2 = (bot[2][0] + 2/3*(bot[1][0]-bot[2][0]), bot[2][1] + 2/3*(bot[1][1]-bot[2][1]))
    path.curveTo(c1[0], c1[1], c2[0], c2[1], bot[2][0], bot[2][1])
    c.drawPath(path)
    # top chord
    c.setStrokeColor(chord_col); c.setLineWidth(3.8 * s)
    path = c.beginPath(); path.moveTo(*top[0])
    c1 = (top[0][0] + 2/3*(top[1][0]-top[0][0]), top[0][1] + 2/3*(top[1][1]-top[0][1]))
    c2 = (top[2][0] + 2/3*(top[1][0]-top[2][0]), top[2][1] + 2/3*(top[1][1]-top[2][1]))
    path.curveTo(c1[0], c1[1], c2[0], c2[1], top[2][0], top[2][1])
    c.drawPath(path)
    if not force:
        c.setFillColor(AMBER_SOFT); c.circle(joint[0], joint[1], 2.9*s, stroke=0, fill=1)
    c.restoreState()

class TrussFig(Flowable):
    def __init__(self, w=132, force=False):
        Flowable.__init__(self); self.w = w; self.height = w * 0.60
        self.force = force
    def wrap(self, *a): return (CW, self.height + 4)
    def draw(self):
        draw_truss(self.canv, (CW - self.w)/2, -self.w*0.16, self.w,
                   force=self.force, chord_col=INK, halo=False)

# ---------------------------------------------------------------- flowables
class Rule(Flowable):
    def __init__(self, col=HAIR, w=None, thick=0.6, pad=0):
        Flowable.__init__(self); self.col=col; self.w=w; self.t=thick; self.pad=pad
    def wrap(self, aw, ah): self.aw = self.w or aw; return (self.aw, self.t + self.pad)
    def draw(self):
        self.canv.setStrokeColor(self.col); self.canv.setLineWidth(self.t)
        self.canv.line(0, self.pad/2, self.aw, self.pad/2)

def para(t, s="p"): return Paragraph(t, st[s])

def bullets(items, style="li", bullet="–"):
    return ListFlowable([ListItem(para(i, style), leftIndent=13, value=bullet)
                         for i in items],
                        bulletType="bullet", start=bullet, leftIndent=11,
                        bulletFontName=F, bulletFontSize=9, spaceAfter=7)

def numbers(items):
    return ListFlowable([ListItem(para(i, "li"), leftIndent=15) for i in items],
                        bulletType="1", leftIndent=13, bulletFontName=FB,
                        bulletFontSize=9, spaceAfter=7)

def table(header, rows, widths, zebra=True, head=True):
    data = []
    if head and header:
        data.append([Paragraph(h, st["cellh"]) for h in header])
    for r in rows:
        data.append([c if isinstance(c, Flowable) else Paragraph(str(c), st["cell"])
                     for c in r])
    t = Table(data, colWidths=[w*CW for w in widths], repeatRows=1 if head else 0)
    cmds = [("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LINEBELOW", (0,0), (-1,-2), 0.4, HAIR)]
    if head and header:
        cmds += [("BACKGROUND", (0,0), (-1,0), BAND),
                 ("LINEBELOW", (0,0), (-1,0), 0.9, colors.HexColor("#B9BDB4"))]
    if zebra:
        off = 1 if (head and header) else 0
        for i in range(off, len(data)):
            if (i - off) % 2 == 1:
                cmds.append(("BACKGROUND", (0,i), (-1,i), colors.HexColor("#F7F7F4")))
    t.setStyle(TableStyle(cmds))
    return t

def code(txt, tint=colors.HexColor("#F4F4F1")):
    lines = [Paragraph(l.replace(" ", "&nbsp;").replace("<","&lt;").replace(">","&gt;")
                       or "&nbsp;", st["code"]) for l in txt.strip("\n").split("\n")]
    t = Table([[l] for l in lines], colWidths=[CW])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), tint),
                           ("LEFTPADDING", (0,0), (-1,-1), 9),
                           ("RIGHTPADDING", (0,0), (-1,-1), 7),
                           ("TOPPADDING", (0,0), (-1,-1), 0.6),
                           ("BOTTOMPADDING", (0,0), (-1,-1), 0.6),
                           ("LINEBEFORE", (0,0), (0,-1), 2, AMBER)]))
    return t

def callout(title, body, accent=AMBER, tint=colors.HexColor("#FFF8EC")):
    inner = [Paragraph(title, st["callh"])] if title else []
    inner += [Paragraph(b, st["callp"]) for b in
              (body if isinstance(body, (list, tuple)) else [body])]
    t = Table([[inner]], colWidths=[CW])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), tint),
                           ("LEFTPADDING", (0,0), (-1,-1), 11),
                           ("RIGHTPADDING", (0,0), (-1,-1), 11),
                           ("TOPPADDING", (0,0), (-1,-1), 9),
                           ("BOTTOMPADDING", (0,0), (-1,-1), 9),
                           ("LINEBEFORE", (0,0), (0,-1), 2.4, accent)]))
    return t

# ---------------------------------------------------------------- doc template
class Brief(BaseDocTemplate):
    def __init__(self, path):
        BaseDocTemplate.__init__(self, path, pagesize=A4,
            leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
            title="Truss — a coordination layer for shared electrical capacity",
            author="Truss", subject="Code2Create 7.0 project brief")
        frame = Frame(ML, MB, CW, PH-MT-MB, id="body",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[frame], onPage=self.cover),
            PageTemplate(id="body",  frames=[frame], onPage=self.chrome),
        ])
        self.section = ""
        self._sec_n = 0

    def afterFlowable(self, f):
        """Feed the table of contents and the PDF outline from H1 paragraphs.

        The bookmark key must be derived from the title, not a counter: a
        counter keeps incrementing across multiBuild passes, so the TOC never
        converges and reportlab gives up after ten passes.
        """
        if isinstance(f, Paragraph) and f.style.name == "h1":
            text = f.getPlainText()
            key = "sec_" + re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, 0, 0)
            self.notify("TOCEntry", (0, text, self.page, key))

    def cover(self, c, doc):
        c.saveState()
        c.setFillColor(INK); c.rect(0, 0, PW, PH, stroke=0, fill=1)

        # the mark
        MW = 196
        draw_truss(c, (PW-MW)/2, PH - 300, MW, halo=True)

        # wordmark, held between its own two chords
        wm_y = PH - 372
        CS = 8.0
        tw = c.stringWidth("TRUSS", FB, 33) + CS*4
        x0 = (PW - tw) / 2
        to = c.beginText(); to.setTextOrigin(x0, wm_y)
        to.setFont(FB, 33); to.setFillColor(CHORD); to.setCharSpace(CS)
        to.textOut("TRUSS")
        to.setCharSpace(0)          # Tc is text state and persists — reset it
        c.drawText(to)
        c.setStrokeColor(CHORD);     c.setLineWidth(2.6)
        c.line(x0, wm_y+42, x0+tw, wm_y+42)
        c.setStrokeColor(CHORD_LOW); c.setLineWidth(1.3)
        c.line(x0, wm_y-14, x0+tw, wm_y-14)

        c.setFont(F, 11.2); c.setFillColor(colors.HexColor("#AEB6C2"))
        c.drawCentredString(PW/2, wm_y-40,
            "A coordination layer for shared electrical capacity")
        c.setFont(FI if HAVE else F, 9.8); c.setFillColor(colors.HexColor("#7E8695"))
        c.drawCentredString(PW/2, wm_y-58,
            "Five members. Thirty devices. One hard limit — and it will not lie about it.")

        # stat row
        stats = [("6", "safety invariants"),
                 ("5", "failing members"),
                 ("48h", "execution plan")]
        y = 300; step = (PW - 2*ML) / 3
        c.setStrokeColor(colors.HexColor("#242A34")); c.setLineWidth(0.7)
        c.line(ML, y+44, PW-MR, y+44); c.line(ML, y-28, PW-MR, y-28)
        for i, (big, small) in enumerate(stats):
            cx = ML + step*i + step/2
            c.setFont(FH, 26); c.setFillColor(AMBER)
            c.drawCentredString(cx, y, big)
            c.setFont(F, 8.6); c.setFillColor(colors.HexColor("#8B93A3"))
            c.drawCentredString(cx, y-16, small)

        # pull quote
        c.setFont(FHR, 12); c.setFillColor(colors.HexColor("#C7CDD6"))
        for i, line in enumerate([
            "A truss carries a load no single beam could,",
            "by giving every member only what it can bear."]):
            c.drawCentredString(PW/2, 196 - i*19, line)

        c.setFont(FMONO, 7.4); c.setFillColor(colors.HexColor("#5C6373"))
        c.drawString(ML, MB+4, "CODE2CREATE 7.0  /  GRAVITAS '26")
        c.drawRightString(PW-MR, MB+4, "PROJECT BRIEF  /  REV 2")
        c.restoreState()

    def chrome(self, c, doc):
        c.saveState()
        c.setFillColor(PAPER); c.rect(0, 0, PW, PH, stroke=0, fill=1)
        # header
        c.setFont(FMONO, 6.9); c.setFillColor(colors.HexColor("#8A9099"))
        c.drawString(ML, PH-MT+16, "TRUSS")
        c.drawRightString(PW-MR, PH-MT+16, self.section.upper()[:62])
        c.setStrokeColor(HAIR); c.setLineWidth(0.5)
        c.line(ML, PH-MT+11, PW-MR, PH-MT+11)
        # footer
        c.line(ML, MB-13, PW-MR, MB-13)
        c.setFont(FMONO, 6.9); c.setFillColor(colors.HexColor("#9AA0A9"))
        c.drawString(ML, MB-24, "Truss never switches mains voltage.")
        c.setFillColor(colors.HexColor("#6E7686"))
        c.drawRightString(PW-MR, MB-24, str(c.getPageNumber()))
        c.restoreState()

class SectionMark(Flowable):
    """Zero-height marker that updates the running header."""
    def __init__(self, doc, title): Flowable.__init__(self); self.doc=doc; self.t=title
    def wrap(self, *a): return (0, 0)
    def draw(self): self.doc.section = self.t

# ---------------------------------------------------------------- build
def build(out):
    from reportlab.platypus.tableofcontents import TableOfContents
    doc = Brief(out)
    # page 1 uses the "cover" template; everything after it uses "body"
    story = [NextPageTemplate("body"), PageBreak()]

    # ---- contents
    doc.section = "Contents"
    story.append(Paragraph("CONTENTS", st["h1n"]))
    story.append(Paragraph("What is in here", st["h1"]))
    story.append(Spacer(1, 3)); story.append(Rule(colors.HexColor("#C8CBC4"), thick=1.1))
    story.append(Spacer(1, 14))
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle(name="toc0", fontName=F, fontSize=10.2,
                                      leading=21, textColor=BODY,
                                      firstLineIndent=0, leftIndent=0)]
    toc.dotsMinLevel = 0
    story.append(toc)
    story.append(Spacer(1, 26))
    story.append(callout("The three sentences that matter", [
        "<b>1.</b> The flexibility is already there. What is missing is a way to express it "
        "without surrendering privacy or control.",
        "<b>2.</b> A budget is not a command — it is a lease, and an unrenewed lease expires "
        "into safety.",
        "<b>3.</b> A system that cannot meet its constraint must say so, not fake it.",
        "Everything else in this document is consequence."]))

    def H1(num, title):
        story.append(Paragraph(num, st["h1n"]))
        story.append(Paragraph(title, st["h1"]))
        story.append(Spacer(1, 3)); story.append(Rule(colors.HexColor("#C8CBC4"), thick=1.1))
        story.append(Spacer(1, 11))

    def H2(t): story.append(Paragraph(t, st["h2"]))
    def H3(t): story.append(Paragraph(t, st["h3"]))
    def P(t, s="p"): story.append(Paragraph(t, st[s]))
    def SP(h=7): story.append(Spacer(1, h))
    def NP(): story.append(PageBreak())

    from content import SECTIONS
    for sec in SECTIONS:
        # emitted before the break so the *next* page's running header is right
        story.append(SectionMark(doc, sec["title"]))
        story.append(PageBreak())
        H1(sec["num"], sec["title"])
        for kind, *arg in sec["blocks"]:
            if   kind == "p":     P(arg[0])
            elif kind == "lead":  P(arg[0], "lead")
            elif kind == "h2":    H2(arg[0])
            elif kind == "h3":    H3(arg[0])
            elif kind == "ul":    story.append(bullets(arg[0])); SP(1)
            elif kind == "ol":    story.append(numbers(arg[0])); SP(1)
            elif kind == "table": story.append(table(arg[0], arg[1], arg[2])); SP(9)
            elif kind == "code":  story.append(code(arg[0])); SP(9)
            elif kind == "call":  story.append(callout(arg[0], arg[1])); SP(9)
            elif kind == "callb": story.append(callout(arg[0], arg[1], TENSION,
                                       colors.HexColor("#EEF5FC"))); SP(9)
            elif kind == "callr": story.append(callout(arg[0], arg[1], FAULT,
                                       colors.HexColor("#FDF0F0"))); SP(9)
            elif kind == "cap":   P(arg[0], "cap")
            elif kind == "pull":  story.append(callout(None, arg[0], INK,
                                       colors.HexColor("#F2F2EE"))); SP(9)
            elif kind == "rule":  SP(4); story.append(Rule()); SP(8)
            elif kind == "sp":    SP(arg[0] if arg else 7)
            elif kind == "fig":   story.append(TrussFig(*arg)); SP(4)
            elif kind == "np":    NP()

    doc.multiBuild(story)
    return out

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    out = sys.argv[1] if len(sys.argv) > 1 else "Truss_Brief.pdf"
    print("wrote", build(out))
