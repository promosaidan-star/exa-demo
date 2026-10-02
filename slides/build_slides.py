"""
build_slides.py
===============

WHAT THIS FILE DOES
    It builds the three slides for the Break Check demo and saves them as
    slides/break_check.pptx. You run it once:

        python slides\\build_slides.py

    Then you open the .pptx in PowerPoint or upload it to Google Slides.

WHY A SCRIPT INSTEAD OF DRAWING THE SLIDES BY HAND
    1. Every number on a slide lives in one place (the CONTENT section below).
       If a number changes, you edit one line and rebuild.
    2. The slides can never drift away from what the app shows, because both
       are built from the same facts.
    3. If the interviewer asks "how did you make these?", the answer is
       "forty lines of content and a few helper functions", which is a good
       answer for an engineering role.

HOW THE FILE IS LAID OUT (top to bottom)
    1. Imports           : the tools we borrow from the python-pptx library.
    2. Look and feel     : colors, fonts and the slide size, named once.
    3. Helper functions  : small functions that each draw ONE kind of thing
                           (a text box, a colored box, a bullet list, a table).
    4. Slide builders    : slide_1(), slide_2(), slide_3(). Each one places
                           helpers on the page and adds the speaker notes.
    5. main()            : creates the deck, calls the three builders, saves.

A NOTE ON UNITS
    PowerPoint measures everything in a tiny unit called an EMU. Nobody thinks
    in EMUs, so python-pptx gives us Inches(...) and Pt(...) to convert.
    Inches(1) means "one inch on the slide". Pt(18) means "18 point text".

RULES THE SLIDE TEXT FOLLOWS
    - Every number is either measured (and says so) or labeled an assumption.
    - No former client is named.
    - Vendor A and Vendor B values are illustrative and the slide says so.
    - No em dashes anywhere.
"""

# ---------------------------------------------------------------------------
# 1. IMPORTS
# ---------------------------------------------------------------------------

# Path lets us build file paths that work on Windows without typing slashes.
from pathlib import Path

# Presentation is the whole deck. We create one, add slides, then save it.
from pptx import Presentation

# RGBColor turns three numbers (red, green, blue) into a color PowerPoint knows.
from pptx.dml.color import RGBColor

# MSO_SHAPE is a catalog of shape types (rectangle, arrow, and so on).
from pptx.enum.shapes import MSO_SHAPE

# PP_ALIGN sets left, center or right alignment for a paragraph.
# MSO_ANCHOR sets top, middle or bottom alignment inside a box.
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

# Inches and Pt convert human units into PowerPoint's internal unit (EMU).
from pptx.util import Inches, Pt


# ---------------------------------------------------------------------------
# 2. LOOK AND FEEL
# ---------------------------------------------------------------------------
# Naming colors once means a color change is a one-line edit, and the code
# below reads as "NAVY" instead of a mystery number.

NAVY = RGBColor(0x0B, 0x1F, 0x3A)    # dark blue: title bars and headings
BLUE = RGBColor(0x1F, 0x6F, 0xEB)    # bright blue: accents and arrows
INK = RGBColor(0x1A, 0x1A, 0x1A)     # near black: normal body text
MUTED = RGBColor(0x5B, 0x65, 0x73)   # gray: footnotes and labels
PALE = RGBColor(0xF3, 0xF5, 0xF8)    # very light gray: card backgrounds
WHITE = RGBColor(0xFF, 0xFF, 0xFF)   # white: text on dark bars
AMBER = RGBColor(0xC2, 0x41, 0x0C)   # orange: the value that is in dispute
GREEN = RGBColor(0x15, 0x80, 0x3D)   # green: measured results

# One font for the whole deck. Segoe UI ships with Windows. If the file is
# opened somewhere without it, PowerPoint swaps in a similar font.
FONT = "Segoe UI"

# A widescreen slide is 13.333 inches wide and 7.5 inches tall (16 by 9).
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# How many slides the deck has, for the "n / 4" marker in the title bar.
SLIDE_COUNT = 4

# The left and right margin we keep clear on every slide.
MARGIN = Inches(0.5)

# The usable width between the two margins. We compute it once so every
# slide builder can divide it into columns.
BODY_W = SLIDE_W - MARGIN - MARGIN

# Where the finished deck is saved: the same folder this script lives in.
# __file__ is a name Python fills in with the path of the running script.
OUT_PATH = Path(__file__).resolve().parent / "break_check.pptx"


# ---------------------------------------------------------------------------
# 3. HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def style_run(run, size, bold=False, color=INK, italic=False):
    """Apply font settings to one "run" of text.

    A run is a stretch of text that shares one style. A paragraph can hold
    several runs, which is how one line can have a bold start and a normal
    ending.
    """
    # Set the typeface so every run in the deck matches.
    run.font.name = FONT
    # Set the text size in points.
    run.font.size = Pt(size)
    # Turn bold on or off.
    run.font.bold = bold
    # Turn italic on or off.
    run.font.italic = italic
    # Set the text color.
    run.font.color.rgb = color


def add_box(slide, left, top, width, height, fill=PALE, shape=MSO_SHAPE.RECTANGLE):
    """Draw a filled shape with no outline and return it.

    We use this for cards (pale rectangles), title bars (navy rectangles)
    and arrows.
    """
    # add_shape draws the shape at the given position and size.
    box = slide.shapes.add_shape(shape, left, top, width, height)
    # solid() says "fill with one flat color" (as opposed to a gradient).
    box.fill.solid()
    # Pick the flat color.
    box.fill.fore_color.rgb = fill
    # Remove the outline. background() means "no visible line".
    box.line.fill.background()
    # Remove the drop shadow PowerPoint adds by default. Flat looks cleaner.
    box.shadow.inherit = False
    # Hand the shape back so the caller can put text in it if it wants.
    return box


def add_text(slide, left, top, width, height, text, size=16, bold=False,
             color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False):
    """Draw one text box holding one paragraph and return it."""
    # add_textbox creates an empty, invisible box we can type into.
    box = slide.shapes.add_textbox(left, top, width, height)
    # text_frame is the part of the box that holds paragraphs.
    frame = box.text_frame
    # word_wrap makes long lines wrap inside the box instead of running off.
    frame.word_wrap = True
    # vertical_anchor places the text at the top, middle or bottom of the box.
    frame.vertical_anchor = anchor
    # A new text frame always starts with one empty paragraph. We use it.
    para = frame.paragraphs[0]
    # Set left, center or right alignment.
    para.alignment = align
    # add_run creates the stretch of text inside the paragraph.
    run = para.add_run()
    # Put the words in.
    run.text = text
    # Apply the font settings.
    style_run(run, size, bold=bold, color=color, italic=italic)
    # Return the box in case the caller needs it.
    return box


def add_lines(slide, left, top, width, height, items, size=14, gap=6):
    """Draw a list of lines. Each line can start with a bold lead-in.

    items is a list. Each entry is one of two things:
        "plain text"                  -> a normal line
        ("Bold lead.", "rest of it")  -> a line that starts in bold

    A pair written in round brackets like ("a", "b") is called a tuple. It is
    a fixed-size group of values. We use it here to carry two pieces of text.
    """
    # Create the invisible box that will hold every line.
    box = slide.shapes.add_textbox(left, top, width, height)
    # Get the part of the box that holds paragraphs.
    frame = box.text_frame
    # Wrap long lines inside the box.
    frame.word_wrap = True

    # enumerate gives us a counter (index) alongside each item, starting at 0.
    for index, item in enumerate(items):
        # The first line reuses the paragraph the frame was born with.
        # Every later line needs a new paragraph.
        if index == 0:
            para = frame.paragraphs[0]
        else:
            para = frame.add_paragraph()

        # space_after is the blank space under the paragraph, in points.
        para.space_after = Pt(gap)

        # isinstance asks "is this item a tuple?". If so it has two parts.
        if isinstance(item, tuple):
            # Unpack the two parts into two names.
            lead, rest = item
            # First run: the bold lead-in, in navy.
            lead_run = para.add_run()
            lead_run.text = lead + " "
            style_run(lead_run, size, bold=True, color=NAVY)
            # Second run: the rest of the line, in normal ink.
            rest_run = para.add_run()
            rest_run.text = rest
            style_run(rest_run, size)
        else:
            # A plain string: one run, normal style.
            run = para.add_run()
            run.text = item
            style_run(run, size)

    # Return the box in case the caller needs it.
    return box


def add_title(slide, number, title):
    """Draw the navy title bar that sits at the top of every slide."""
    # The bar spans the full width of the slide and is 1.15 inches tall.
    add_box(slide, 0, 0, SLIDE_W, Inches(1.15), fill=NAVY)
    # The title text sits inside the bar, vertically centered, in white.
    add_text(slide, MARGIN, 0, BODY_W - Inches(0.8), Inches(1.15), title,
             size=26, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    # A small slide number on the right side of the bar, so the presenter
    # and the audience can refer to "slide 2" out loud.
    add_text(slide, SLIDE_W - Inches(1.3), 0, Inches(0.8), Inches(1.15),
             str(number) + " / " + str(SLIDE_COUNT), size=12, color=WHITE,
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)


def add_card(slide, left, top, width, height, heading, items, size=14,
             heading_color=NAVY, heading_lines=1):
    """Draw a pale card with a heading and a list of lines inside it.

    heading_lines is how many lines the heading is expected to take up.
    Narrow cards have headings that wrap onto a second line, and the body
    text has to start lower to make room. Passing heading_lines=2 does that.
    """
    # The pale rectangle is the card background.
    add_box(slide, left, top, width, height, fill=PALE)
    # pad is the space between the card edge and the text.
    pad = Inches(0.2)
    # The heading sits at the top of the card.
    add_text(slide, left + pad, top + Inches(0.1), width - pad - pad,
             Inches(0.45), heading, size=size + 2, bold=True,
             color=heading_color)
    # Work out where the body text starts. One heading line needs 0.6 inch.
    # Each extra heading line pushes the body down by another 0.28 inch.
    body_offset = Inches(0.6) + Inches(0.28) * (heading_lines - 1)
    # The lines sit under the heading and fill the rest of the card.
    add_lines(slide, left + pad, top + body_offset, width - pad - pad,
              height - body_offset - Inches(0.1), items, size=size)


def add_table(slide, left, top, width, height, rows, col_widths, size=13,
              highlight_row=None):
    """Draw a simple table. rows is a list of rows; each row is a list of text.

    The first row is treated as the header. highlight_row is the number of a
    row whose values should be shown in amber (the disputed value).
    """
    # Count the rows and columns so we can ask for a table of the right shape.
    n_rows = len(rows)
    n_cols = len(rows[0])
    # add_table returns a wrapper; the real table is its .table attribute.
    table = slide.shapes.add_table(n_rows, n_cols, left, top, width, height).table

    # Set each column's width from the list the caller gave us.
    for col_index, col_width in enumerate(col_widths):
        table.columns[col_index].width = col_width

    # Walk every cell: outer loop is rows, inner loop is columns.
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            # Look up the cell at row r, column c.
            cell = table.cell(r, c)
            # Fill the cell with a flat color: navy for the header row,
            # white for every other row.
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if r == 0 else WHITE
            # Center the text vertically inside the cell.
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            # Each cell starts with one empty paragraph. We fill it.
            para = cell.text_frame.paragraphs[0]
            run = para.add_run()
            run.text = value

            # Decide the text style for this cell.
            if r == 0:
                # Header row: white and bold on navy.
                style_run(run, size, bold=True, color=WHITE)
            elif r == highlight_row and c > 0:
                # The disputed values: amber and bold so the eye lands there.
                style_run(run, size, bold=True, color=AMBER)
            elif c == 0:
                # First column holds the field names: bold navy.
                style_run(run, size, bold=True, color=NAVY)
            else:
                # Everything else: normal ink.
                style_run(run, size)


def add_notes(slide, text):
    """Attach speaker notes to a slide.

    Speaker notes are the presenter's private script. The audience does not
    see them when the deck is shared in presenter view.
    """
    # notes_slide is created the first time we ask for it.
    slide.notes_slide.notes_text_frame.text = text


def new_slide(deck):
    """Add one blank slide to the deck and return it."""
    # Layout number 6 in the default template is the fully blank layout.
    # We use blank so nothing appears that we did not draw ourselves.
    blank_layout = deck.slide_layouts[6]
    # add_slide creates the slide at the end of the deck.
    return deck.slides.add_slide(blank_layout)


# ---------------------------------------------------------------------------
# 4. SLIDE BUILDERS
# ---------------------------------------------------------------------------

def slide_1(deck):
    """Slide 1: who the customer is, who the user is, and what hurts."""
    # Start with a blank slide and draw the title bar.
    slide = new_slide(deck)
    add_title(slide, 2, "7:40 AM. Two data vendors disagree on one security. Who is right?")

    # The slide body is split into a left card and a right card.
    # gap is the space between them.
    gap = Inches(0.3)
    # The left card takes a bit less than half the width.
    left_w = Inches(5.6)
    # The right card takes whatever width is left over.
    right_w = BODY_W - left_w - gap
    # Both cards start just under the title bar.
    top = Inches(1.4)
    # Both cards are the same height.
    card_h = Inches(3.35)

    # LEFT CARD: the customer, the user and today's manual process.
    add_card(slide, MARGIN, top, left_w, card_h, "Who this is for", [
        ("Customer:", "a US asset manager running index and total-market "
                      "equity funds plus investment-grade credit."),
        ("User:", "a security master analyst. A team of 3 to 4 shares one "
                  "queue of breaks and must clear it before the 9:30 open."),
        ("Today:", "each break needs proof found by hand on Google, EDGAR "
                   "and Nasdaq Trader, then links pasted into the ticket. "
                   "About 15 to 25 minutes each (assumption to confirm)."),
        ("The worse case:", "both vendors agree because both are missing "
                            "an event. Reconciling the feeds can never "
                            "catch that."),
    ], size=13)

    # RIGHT CARD: one real break, shown the way the analyst sees it.
    right_left = MARGIN + left_w + gap
    # Draw the pale background for the right card.
    add_box(slide, right_left, top, right_w, card_h, fill=PALE)
    # Heading for the right card.
    add_text(slide, right_left + Inches(0.2), top + Inches(0.1),
             right_w - Inches(0.4), Inches(0.45),
             "A real event from this week: CDT Equity (Nasdaq: CDT)",
             size=16, bold=True, color=NAVY)
    # The table of vendor values. Row 3 (effective date) is the dispute,
    # so we ask for it to be highlighted in amber.
    # table_w is the space inside the card once both side pads are removed.
    table_w = right_w - Inches(0.4)
    # Split that width into three equal columns. int(...) rounds to a whole
    # number because PowerPoint does not accept fractions of its unit.
    one_col = int(table_w / 3)
    add_table(
        slide,
        right_left + Inches(0.2), top + Inches(0.65),
        table_w, Inches(1.5),
        rows=[
            ["Field", "Vendor A", "Vendor B"],
            ["Event", "Reverse split", "Reverse split"],
            ["Terms", "1-for-25", "1-for-25"],
            ["Effective date", "2026-09-28", "2026-09-29"],
        ],
        col_widths=[one_col, one_col, one_col],
        highlight_row=3,
    )
    # What the issuer's own press release says. This is the tiebreaker.
    add_lines(slide, right_left + Inches(0.2), top + Inches(2.3),
              right_w - Inches(0.4), Inches(1.0), [
        ("Issuer release:", "effective Sep 28 at 5:00 pm Eastern. "
                            "Split-adjusted trading starts Sep 29."),
        "Both vendors can be right. They mean two different things by \"effective\".",
    ], size=13, gap=3)

    # BOTTOM STRIP: what goes wrong when the fix is late or wrong.
    strip_top = Inches(4.95)
    # Heading above the four small boxes.
    add_text(slide, MARGIN, strip_top, BODY_W, Inches(0.4),
             "What a wrong or late fix breaks", size=16, bold=True, color=NAVY)

    # The four consequences. Each entry is (bold heading, explanation).
    harms = [
        ("NAV check trips", "Price and share count are out of step by 25 times."),
        ("Orders reject", "The broker refuses an order on a retired CUSIP."),
        ("Compliance misfires", "Ownership limits divide by the wrong share count."),
        ("Dead bonds stay open", "A bond redeemed Sep 15 is still live at one vendor."),
    ]
    # Work out the width of each small box so four fit with gaps between.
    small_gap = Inches(0.2)
    small_w = (BODY_W - small_gap * 3) / 4
    # Draw the four boxes left to right.
    for index, (head, body) in enumerate(harms):
        # Each box sits one box-width plus one gap to the right of the last.
        x = MARGIN + (small_w + small_gap) * index
        # int(...) rounds the position to a whole number, which PowerPoint needs.
        add_card(slide, int(x), strip_top + Inches(0.45), int(small_w),
                 Inches(1.25), head, [body], size=12, heading_color=AMBER)

    # FOOTNOTE: define the jargon and say which values are made up.
    add_text(slide, MARGIN, Inches(6.75), BODY_W, Inches(0.6),
             "Break: a row where two vendors disagree. CUSIP: the 9-character "
             "US security ID. NAV: a fund's daily net asset value. Vendor A "
             "and B values are illustrative. The event and the issuer release "
             "are real.",
             size=10, color=MUTED, italic=True)

    # SPEAKER NOTES: what AJ says while this slide is up (about 2 minutes).
    add_notes(slide, (
        "OPEN WITH THE CUSTOMER, NOT THE TOOL.\n\n"
        "It is 7:40 in the morning at an asset manager. The security master "
        "team has a queue of breaks. A break is a row where their two data "
        "vendors disagree about a security. They have until the 9:30 open.\n\n"
        "CREDIBILITY (say it once, plainly):\n"
        "I spent two and a half years at Charles River as the primary FIX "
        "analyst for five buy-side clients. When security reference data was "
        "wrong, trades busted, and I was the one working out with the trader "
        "and the data team which provider caused it.\n\n"
        "THE EXAMPLE:\n"
        "This one is from this week. CDT Equity did a 1-for-25 reverse split. "
        "One vendor says effective the 28th, the other says the 29th. The "
        "issuer's release says effective the 28th at 5:00 pm, trading on the "
        "new basis from the 29th. So both vendors are right about something. "
        "The analyst has to know which date the golden copy should carry, "
        "and today they find that out by hand.\n\n"
        "THE STAKES:\n"
        "Load it wrong and the price and the share count are off by a factor "
        "of 25, which trips the NAV check. That is the morning this tool is "
        "built for.\n\n"
        "HANDOFF: So where does the answer live? On the public web."
    ))


def slide_2(deck):
    """Slide 2: where Exa fits in the workflow, and why Exa."""
    # Start with a blank slide and draw the title bar.
    slide = new_slide(deck)
    add_title(slide, 3, "The proof is on the public web. Exa finds what the feeds missed.")

    # FLOW DIAGRAM: five boxes joined by four arrows, left to right.
    # Each entry is (heading, one line of detail).
    steps = [
        ("1. Watchlist", "The held securities. Holdings stay local; only the public identity goes out."),
        ("2. One Exa search each", "Recent corporate actions by this issuer. The event is not named."),
        ("3. Proof attached", "Each announcement comes back as fields, a passage and a link."),
        ("4. Code matches", "To the holdings and to both vendor records. No model makes the call."),
        ("5. New finding", "An event neither vendor has lands in the queue. The analyst approves."),
    ]
    # Sizes for the flow: five boxes and four arrows must fit in BODY_W.
    arrow_w = Inches(0.35)
    step_w = (BODY_W - arrow_w * 4) / 5
    flow_top = Inches(1.45)
    step_h = Inches(1.95)

    # Draw each step, and an arrow after every step except the last.
    for index, (head, body) in enumerate(steps):
        # The left edge of this step.
        x = MARGIN + (step_w + arrow_w) * index
        # Steps 2 and 3 are the Exa steps, so they get the blue heading.
        is_exa_step = index in (1, 2)
        # heading_lines=2 because these cards are narrow and the headings wrap.
        add_card(slide, int(x), flow_top, int(step_w), step_h, head, [body],
                 size=12, heading_color=BLUE if is_exa_step else NAVY,
                 heading_lines=2)
        # len(steps) - 1 is the number of the last step. No arrow after it.
        if index < len(steps) - 1:
            add_box(slide, int(x + step_w + Inches(0.04)),
                    flow_top + Inches(0.7), int(arrow_w - Inches(0.08)),
                    Inches(0.35), fill=BLUE, shape=MSO_SHAPE.RIGHT_ARROW)

    # MEASURED LINE under the flow: the numbers from the live calls.
    add_text(slide, MARGIN, Inches(3.5), BODY_W, Inches(0.4),
             "Measured 2026-09-29 on live calls: every field filled in 2 to 4 "
             "seconds, $0.007 per search, a source link on every field.",
             size=13, bold=True, color=GREEN)

    # THREE COLUMNS: the argument for why this design and why Exa.
    col_gap = Inches(0.3)
    col_w = (BODY_W - col_gap * 2) / 3
    col_top = Inches(4.0)
    col_h = Inches(2.65)

    # Column 1: the licensed feeds are not being replaced.
    add_card(slide, MARGIN, col_top, int(col_w), col_h,
             "Two jobs, one search", [
        "Resolve a known break: the issuer's words and the exchange "
        "notice settle what the two licensed feeds cannot.",
        "Find an unknown event: the same search, with no event named, "
        "surfaces an announcement neither feed carries yet.",
        "The licensed feeds stay the system of record.",
    ], size=13)

    # Column 2: why a search API beats writing scrapers.
    add_card(slide, int(MARGIN + col_w + col_gap), col_top, int(col_w), col_h,
             "Why Exa, not a scraper", [
        "One exchange page is easy to scrape. The long tail is not: "
        "thousands of issuer sites, bond redemption notices, SEC filings.",
        "One plain-language search covers all of them and returns "
        "structured fields, so there is no scraper per site to maintain.",
    ], size=13)

    # Column 3: the trust and security story an asset manager will ask for.
    add_card(slide, int(MARGIN + (col_w + col_gap) * 2), col_top, int(col_w),
             col_h, "Built to pass review", [
        "Code checks the page names the right security before any field "
        "is trusted. A missing value is shown as missing.",
        "An issuer release and its syndicated copy count as one source. "
        "Two sources means issuer plus exchange or SEC.",
        "Zero data retention is available on search, so lookups do not "
        "reveal holdings.",
    ], size=13)

    # FOOTNOTE: the honest limit, stated up front.
    add_text(slide, MARGIN, Inches(6.75), BODY_W, Inches(0.6),
             "Vendor records in the demo are simulated. Every announcement is "
             "real and retrieved by Exa. Nothing found is not proof that "
             "nothing happened.",
             size=10, color=MUTED, italic=True)

    # SPEAKER NOTES: what AJ says while this slide is up (about 2 minutes).
    add_notes(slide, (
        "THE ONE IDEA: reconciling two feeds can only find where they "
        "disagree. It can never find what both are missing. The issuer and "
        "the exchange publish on the open web, and Exa can read it.\n\n"
        "WALK THE FLOW LEFT TO RIGHT:\n"
        "Start from the watchlist. One Exa search per issuer asks for recent "
        "corporate actions without naming an event. Each announcement comes "
        "back as fields with the passage and the page it came from. Then "
        "plain code matches it to the holdings and to both vendor records. "
        "When neither vendor has it, a new finding lands in the queue. I kept "
        "the decision out of the model on purpose, because an operations "
        "team has to explain every label to an auditor.\n\n"
        "WHY EXA:\n"
        "For Nasdaq names alone you could scrape one page. The hard part is "
        "the long tail: issuer sites, bond redemptions, 8-K filings. One "
        "search covers that without a scraper per site.\n\n"
        "WHAT I MEASURED:\n"
        "On live calls this week, type auto filled all eight fields in 2 to "
        "4 seconds for $0.007. I also tried deep-lite on the same call. It "
        "cost more, took longer and found nothing extra, so auto is the "
        "default.\n\n"
        "IF ASKED ABOUT ZERO DATA RETENTION: it is available on search, "
        "which carries every routine lookup here. I would confirm coverage "
        "for the other endpoints with you before promising it to a customer.\n\n"
        "HANDOFF: Let me show it running, starting with a break we already know about, then the one we did not."
    ))


def slide_3(deck):
    """Slide 3: why Exa in particular, and why this project is worth doing."""
    # Start with a blank slide and draw the title bar.
    slide = new_slide(deck)
    add_title(slide, 1, "Why Exa, and why this is the right first workload")

    # TOP: a comparison table. Each column is a way the team could get the
    # same evidence today; each row is something the workflow needs.
    # "yes" and "no" are kept as plain words so the table reads on any screen.
    add_text(slide, MARGIN, Inches(1.35), BODY_W, Inches(0.4),
             "Four ways to get the same evidence", size=16, bold=True, color=NAVY)
    rows = [
        ["What the workflow needs", "Keyword news feed", "Scraper per site", "A model alone (no retrieval)", "Exa"],
        ["Finds an event you did not name", "no, keyword-tagged", "no, one page per site", "no; a browsing model runs keyword search and returns prose", "yes, meaning-based search"],
        ["Covers issuer sites, wires, Nasdaq, SEC", "partly", "one scraper each", "no", "yes, one query"],
        ["Structured fields with a passage and a link", "no", "build it yourself", "no citation", "yes, in the same call"],
        ["Cost to add the next 1,000 issuers", "license", "1,000 scrapers to maintain", "n/a", "about $7 a day at list"],
    ]
    # Column widths: the first column is wider because it holds sentences.
    first = Inches(3.4)
    rest = int((BODY_W - first) / 4)
    add_table(slide, MARGIN, Inches(1.8), BODY_W, Inches(2.2), rows,
              col_widths=[first, rest, rest, rest, rest], size=12)

    # BOTTOM: two cards. Left is the technical case, right is the business case.
    col_gap = Inches(0.3)
    col_w = (BODY_W - col_gap) / 2
    col_top = Inches(4.5)
    col_h = Inches(2.2)

    # Left card: what Exa does here that nothing else on the table does.
    add_card(slide, MARGIN, col_top, int(col_w), col_h,
             "What Exa does here (measured this week)", [
        ("Meaning, not keywords:", "the query asks for recent corporate "
                                   "actions by an issuer. Exa returns the "
                                   "split notice, the 8-K or the redemption "
                                   "release without any of them being named."),
        ("One call, grounded:", "fields plus the passage and the link, in 2 "
                                "to 4 seconds for $0.007, across issuer "
                                "sites, wires, Nasdaq and the SEC."),
        ("Verifiable:", "every answer is a sentence you can click. A stale "
                        "page is re-fetched live for $0.001."),
    ], size=12)

    # Right card: why a buyer and Exa should both want this project.
    add_card(slide, int(MARGIN + col_w + col_gap), col_top, int(col_w), col_h,
             "Why this project is compelling", [
        ("It finds what reconciliation cannot:", "an event both feeds "
                                                "missed, found today on a "
                                                "10-name watchlist in 11 "
                                                "seconds for $0.07."),
        ("It is cheap to prove:", "one week, count breaks still open at "
                                  "9:30 and events missed by both feeds, "
                                  "with and without."),
        ("It is the wedge:", "a low-risk workload that takes Exa through "
                             "security review and zero data retention. "
                             "Research and credit monitoring then run on "
                             "the same approval."),
    ], size=12)

    # FOOTNOTE: keep the claims honest.
    add_text(slide, MARGIN, Inches(6.8), BODY_W, Inches(0.5),
             "Costs are Exa list prices. Feed and scraper costs are the "
             "customer's to confirm. Vendor records in the demo are simulated.",
             size=10, color=MUTED, italic=True)

    # SPEAKER NOTES: what AJ says while this slide is up (about 90 seconds).
    add_notes(slide, (
        "WHY EXA, IN ONE BREATH: the thing this workflow needs is to find "
        "an announcement you did not know to look for, across sites you do "
        "not control, and get it back as fields with proof. A keyword feed "
        "only finds what someone tagged. A scraper only reads the page you "
        "pointed it at. A model alone has nothing to cite. Exa does the "
        "finding and the structuring in one call.\n\n"
        "THE TABLE: walk one row, the first one. Finds an event you did not "
        "name. That is the scan you just saw.\n\n"
        "WHY COMPELLING: the value is not the $0.07. It is that the feeds "
        "can never catch their own shared blind spot, and this does, and "
        "you can measure it in a week. Then the commercial point: this is "
        "the workload that gets Exa approved inside an asset manager.\n\n"
        "HANDOFF: so who is this for, and what goes wrong without it."
    ))


def slide_4(deck):
    """Slide 4: business impact, what Exa costs, and the proof of concept."""
    # Start with a blank slide and draw the title bar.
    slide = new_slide(deck)
    add_title(slide, 4, "Impact, cost, and a four-week proof of concept")

    # Three equal columns fill the body of the slide.
    col_gap = Inches(0.3)
    col_w = (BODY_W - col_gap * 2) / 3
    top = Inches(1.4)
    col_h = Inches(4.55)

    # COLUMN 1: the value to the customer. Every number here is an assumption
    # and the card says so, because we have not met the customer yet.
    add_card(slide, MARGIN, top, int(col_w), col_h,
             "Impact (assumptions to confirm)", [
        ("First, the deadline.", "Finding proof by hand for 12 to 20 breaks "
                                 "takes 180 to 500 analyst-minutes. The "
                                 "team has 450 to 600 before the open."),
        ("With Break Check:", "a 3 to 5 minute review each, so 36 to 100 "
                              "minutes. Fewer breaks still open at 9:30."),
        ("Second, analyst time:", "about $45K to $126K a year at $75 an "
                                  "hour loaded cost."),
        ("How we prove it:", "count open breaks at 9:30 with and without "
                             "the tool for one week."),
    ], size=13)

    # COLUMN 2: what Exa costs. These numbers are measured, so the heading
    # is green to set them apart from the assumptions in column 1.
    add_card(slide, int(MARGIN + col_w + col_gap), top, int(col_w), col_h,
             "Exa cost (measured 2026-09-29)", [
        ("Per break:", "2 searches at $0.007 each, so $0.014."),
        ("Per year:", "under $100 at list price for 12 to 20 breaks a day."),
        ("Speed:", "2 to 4 seconds per search."),
        ("Accuracy so far:", "across 22 live calls, no invented values. "
                             "When a fact was not on the page the field "
                             "came back \"not stated\"."),
        ("Why it still matters to Exa:", "this is the workload that gets "
                                         "Exa through security review at "
                                         "an asset manager. Research and "
                                         "credit monitoring follow."),
    ], size=13, heading_color=GREEN)

    # COLUMN 3: the proof of concept plan and what counts as passing.
    add_card(slide, int(MARGIN + (col_w + col_gap) * 2), top, int(col_w),
             col_h, "Proof of concept", [
        ("Week 0:", "security review, zero data retention turned on."),
        ("Week 1:", "public test on about 230 Nasdaq notices. No holdings sent."),
        ("Week 2:", "replay 150 of the customer's closed tickets."),
        ("Week 3:", "analysts use it alongside today's process."),
        ("Pass means:", "issuer source found 90% or more, fields match the "
                        "analyst 95% or more, zero wrong-issuer citations, "
                        "median under 8 seconds."),
    ], size=13)

    # BOTTOM BAR: the discovery questions AJ would ask the customer first.
    # A navy bar with white text makes it the last thing the eye lands on.
    bar_top = Inches(6.15)
    add_box(slide, MARGIN, bar_top, BODY_W, Inches(0.85), fill=NAVY)
    add_text(slide, MARGIN + Inches(0.25), bar_top, BODY_W - Inches(0.5),
             Inches(0.85),
             "First questions for the customer: how many breaks a day need "
             "an outside check, how many are still open at 9:30, and what "
             "did the last wrong one cost?",
             size=14, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)

    # SPEAKER NOTES: what AJ says while this slide is up (about 3 minutes).
    add_notes(slide, (
        "LEAD WITH THE DEADLINE, NOT THE DOLLARS.\n\n"
        "The value the head of operations cares about first is breaks still "
        "open at 9:30, because that is where a wrong NAV or a rejected order "
        "comes from. On a heavy day, finding proof by hand can use up most "
        "of the team's window before the open. A review of 3 to 5 minutes "
        "per break gives that window back.\n\n"
        "BE CLEAR ABOUT WHAT IS MEASURED AND WHAT IS ASSUMED:\n"
        "The left column is assumptions. I would confirm every one in "
        "discovery. The middle column I measured myself this week.\n\n"
        "THE COST POINT:\n"
        "Exa spend for this queue is under $100 a year at list price. I am "
        "not going to pretend that is the deal. The deal is that this is a "
        "low-risk, easy-to-measure workload that takes Exa through security "
        "review at an asset manager. Once Exa is approved there, research "
        "and credit monitoring can run on the same approval.\n\n"
        "THE PROOF OF CONCEPT:\n"
        "Week 1 uses only public data, so it can start before security "
        "review finishes. The customer's own tickets wait until zero data "
        "retention is on.\n\n"
        "CLOSE WITH A QUESTION FOR RYAN:\n"
        "How does Exa size an enterprise agreement when the first workload "
        "is small but the account is large?"
    ))


# ---------------------------------------------------------------------------
# 5. MAIN
# ---------------------------------------------------------------------------

def main():
    """Create the deck, build the three slides, and save the file."""
    # Presentation() with no arguments starts from the default blank template.
    deck = Presentation()
    # The default template is the old 4 by 3 shape. Set widescreen instead.
    deck.slide_width = SLIDE_W
    deck.slide_height = SLIDE_H

    # Build the slides in the order they are presented.
    # Order of presentation: why Exa first, then the customer, the workflow,
    # and the business case. The function names keep their build order.
    slide_3(deck)
    slide_1(deck)
    slide_2(deck)
    slide_4(deck)

    # Write the finished deck to disk. If the file is open in PowerPoint,
    # Windows refuses to overwrite it, so fall back to a second name instead
    # of crashing. try runs the first attempt; except runs if it fails.
    try:
        deck.save(OUT_PATH)
        print("Saved", OUT_PATH)
    except PermissionError:
        alt = OUT_PATH.with_name("break_check_new.pptx")
        deck.save(alt)
        print("break_check.pptx is open in another program. Saved", alt)


# This check means "only run main() when this file is run directly".
# If another file imports this one, nothing is built by accident.
if __name__ == "__main__":
    main()
