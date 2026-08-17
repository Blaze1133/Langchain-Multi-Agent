"""Render the README architecture image without requiring a browser or Graphviz."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "architecture.png"
WIDTH, HEIGHT = 2400, 1480

COLORS = {
    "canvas": "#F8F7F4",
    "ink": "#1E293B",
    "muted": "#637083",
    "line": "#D7D3CA",
    "blue": "#1F4B99",
    "blue_soft": "#E8EFFB",
    "green": "#277A62",
    "green_soft": "#E8F4EF",
    "gold": "#AA6B10",
    "gold_soft": "#FFF3DD",
    "violet": "#6A4C93",
    "violet_soft": "#F0EAF8",
    "card": "#FFFFFF",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    font_path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(font_path, size)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int, *, color: str = COLORS["ink"], bold: bool = False) -> None:
    draw.text(xy, value, font=font(size, bold), fill=color)


def wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int, max_width: int, *, color: str = COLORS["muted"], bold: bool = False, line_gap: int = 10) -> int:
    active_font = font(size, bold)
    words = value.split()
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=active_font) <= max_width:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    y = xy[1]
    for line in lines:
        draw.text((xy[0], y), line, font=active_font, fill=color)
        y += size + line_gap
    return y


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, fill: str, outline: str = COLORS["line"], radius: int = 22, width: int = 3) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], *, color: str = COLORS["blue"], width: int = 7, dashed: bool = False) -> None:
    if dashed:
        dx, dy = end[0] - start[0], end[1] - start[1]
        distance = max(1, int((dx * dx + dy * dy) ** 0.5))
        step = 26
        for offset in range(0, distance - 18, step):
            a = offset / distance
            b = min(offset + 14, distance) / distance
            draw.line((start[0] + dx * a, start[1] + dy * a, start[0] + dx * b, start[1] + dy * b), fill=color, width=width)
    else:
        draw.line((start, end), fill=color, width=width)
    draw.polygon(
        [(end[0], end[1]), (end[0] - 22, end[1] - 12), (end[0] - 22, end[1] + 12)],
        fill=color,
    )


def agent_card(draw: ImageDraw.ImageDraw, x: int, title: str, number: str, accent: str, soft: str, tool: str, handoff: str) -> None:
    y, w, h = 650, 505, 360
    rounded(draw, (x, y, x + w, y + h), fill=COLORS["card"])
    rounded(draw, (x + 28, y + 28, x + 108, y + 108), fill=soft, outline=soft, radius=18, width=1)
    text(draw, (x + 51, y + 46), number, 36, color=accent, bold=True)
    text(draw, (x + 136, y + 36), title, 34, bold=True)
    text(draw, (x + 136, y + 80), "Specialist agent", 19, color=COLORS["muted"])
    draw.line((x + 28, y + 136, x + w - 28, y + 136), fill=COLORS["line"], width=2)
    text(draw, (x + 30, y + 163), "MODEL + TOOL", 16, color=accent, bold=True)
    wrapped(draw, (x + 30, y + 194), tool, 22, w - 60, color=COLORS["ink"])
    text(draw, (x + 30, y + 270), "HANDOFF", 16, color=accent, bold=True)
    wrapped(draw, (x + 30, y + 300), handoff, 21, w - 60, color=COLORS["muted"])


def main() -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["canvas"])
    draw = ImageDraw.Draw(image)

    text(draw, (100, 78), "RELAY / MULTI-AGENT RESEARCH PIPELINE", 23, color=COLORS["blue"], bold=True)
    text(draw, (100, 128), "From one question to an inspectable research trail", 64, bold=True)
    wrapped(
        draw,
        (100, 218),
        "The orchestrator runs four focused agents in sequence. Each stage receives the prior handoff, uses only its assigned tool, and records its output for the interface.",
        28,
        1660,
    )
    draw.line((100, 330, 2300, 330), fill=COLORS["line"], width=3)

    rounded(draw, (100, 410, 610, 548), fill=COLORS["card"])
    text(draw, (132, 438), "Streamlit workspace", 30, bold=True)
    text(draw, (132, 483), "Research question + live agent status", 22, color=COLORS["muted"])

    rounded(draw, (785, 390, 1615, 568), fill=COLORS["blue_soft"], outline="#C7D8F4")
    text(draw, (825, 425), "Pipeline orchestrator", 34, color=COLORS["blue"], bold=True)
    wrapped(draw, (825, 475), "run_research_pipeline(topic) owns the order, state, callbacks, and final handoffs.", 23, 700, color=COLORS["ink"])

    rounded(draw, (1790, 410, 2300, 548), fill=COLORS["green_soft"], outline="#C8E5DB")
    text(draw, (1822, 438), "Session state", 30, color=COLORS["green"], bold=True)
    text(draw, (1822, 483), "Sources · evidence · report · critique", 22, color=COLORS["muted"])

    arrow(draw, (615, 479), (775, 479))
    arrow(draw, (1625, 479), (1780, 479), color=COLORS["green"])

    agent_card(draw, 100, "Scout", "01", COLORS["blue"], COLORS["blue_soft"], "Groq LLM + Tavily web search", "Search results: titles, URLs, and snippets")
    agent_card(draw, 665, "Reader", "02", COLORS["green"], COLORS["green_soft"], "Groq LLM + webpage scraper", "Evidence brief: key points and source insights")
    agent_card(draw, 1230, "Writer", "03", COLORS["gold"], COLORS["gold_soft"], "Prompt template + Groq LLM", "Structured report with introduction, findings, conclusion, sources")
    agent_card(draw, 1795, "Critic", "04", COLORS["violet"], COLORS["violet_soft"], "Review prompt + Groq LLM", "Score, strengths, weaknesses, and improvements")

    arrow(draw, (605, 830), (655, 830))
    arrow(draw, (1170, 830), (1220, 830), color=COLORS["green"])
    arrow(draw, (1735, 830), (1785, 830), color=COLORS["gold"])
    text(draw, (496, 788), "source list", 18, color=COLORS["muted"])
    text(draw, (1048, 788), "evidence brief", 18, color=COLORS["muted"])
    text(draw, (1613, 788), "draft report", 18, color=COLORS["muted"])

    rounded(draw, (100, 1110, 2300, 1355), fill="#F0F4FA", outline="#D1DCEB")
    text(draw, (140, 1150), "External integrations", 25, color=COLORS["blue"], bold=True)
    text(draw, (140, 1200), "Tavily provides discovery. Reader fetches cited pages directly. Groq supplies the LLM used by both agents and chains.", 25, color=COLORS["ink"])
    text(draw, (140, 1252), "The app does not persist research runs; results live in the active Streamlit session.", 22, color=COLORS["muted"])

    arrow(draw, (350, 1100), (350, 1025), color=COLORS["blue"], dashed=True)
    arrow(draw, (900, 1100), (900, 1025), color=COLORS["green"], dashed=True)
    arrow(draw, (1510, 1100), (1510, 1025), color=COLORS["gold"], dashed=True)
    arrow(draw, (2050, 1100), (2050, 1025), color=COLORS["violet"], dashed=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, optimize=True)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
