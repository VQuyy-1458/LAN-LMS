"""Build DOCX and figures from measured JSON and REPORT/REPORT_TEMPLATE.md.
Run using the bundled artifact Python. Export DOCX to PDF and inspect every page.
"""

import math
import argparse
import json
import re
from pathlib import Path
from statistics import median
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from reportlab.lib import colors
from pdf2image import convert_from_path

ROOT = Path(__file__).resolve().parents[1]
BLUE = colors.HexColor("#263f61")
RED = colors.HexColor("#bf2025")
PALE = colors.HexColor("#eef2f7")


def export_figure(drawing, name, poppler):
    folder = ROOT / "statics"
    folder.mkdir(exist_ok=True)
    pdf = folder / (name + ".pdf")
    png = folder / (name + ".png")
    renderPDF.drawToFile(drawing, str(pdf))
    convert_from_path(str(pdf), dpi=180, poppler_path=poppler)[0].save(png)


def box(d, x, y, w, h, title, subtitle=None):
    d.add(Rect(x, y, w, h, rx=7, ry=7, fillColor=PALE, strokeColor=BLUE, strokeWidth=1))
    d.add(
        String(
            x + w / 2,
            y + h / 2 + (5 if subtitle else -4),
            title,
            fontName="Helvetica-Bold",
            fontSize=13,
            textAnchor="middle",
            fillColor=BLUE,
        )
    )
    if subtitle:
        d.add(
            String(
                x + w / 2,
                y + h / 2 - 14,
                subtitle,
                fontSize=11,
                textAnchor="middle",
                fillColor=BLUE,
            )
        )


def arrow(d, x1, y1, x2, y2, label=None):
    d.add(Line(x1, y1, x2, y2, strokeColor=BLUE, strokeWidth=1.2))
    if abs(x2 - x1) >= abs(y2 - y1):
        sign = 1 if x2 > x1 else -1
        points = [x2, y2, x2 - sign * 7, y2 + 3, x2 - sign * 7, y2 - 3]
    else:
        sign = 1 if y2 > y1 else -1
        points = [x2, y2, x2 - 3, y2 - sign * 7, x2 + 3, y2 - sign * 7]
    d.add(Polygon(points, fillColor=BLUE, strokeColor=BLUE))
    if label:
        d.add(
            String(
                (x1 + x2) / 2,
                (y1 + y2) / 2 + 8,
                label,
                fontSize=11,
                textAnchor="middle",
                fillColor=BLUE,
            )
        )


def figures(network, judge, poppler):
    d = Drawing(640, 340)
    d.add(
        String(
            320,
            320,
            "LAN-LMS architecture",
            fontName="Helvetica-Bold",
            fontSize=18,
            textAnchor="middle",
            fillColor=BLUE,
        )
    )
    box(d, 20, 215, 150, 58, "Browsers 1 to N", "Student / Teacher")
    box(d, 230, 215, 150, 58, "Nginx", "one web origin")
    box(d, 450, 240, 160, 45, "Next.js UI")
    box(d, 450, 165, 160, 45, "FastAPI", "one API process")
    arrow(d, 170, 244, 230, 244, "REST / WS")
    arrow(d, 380, 255, 450, 262)
    arrow(d, 380, 230, 450, 188)
    box(d, 30, 70, 165, 58, "SQLite", "queue / grades / outbox")
    box(d, 240, 70, 155, 58, "Private storage", "source / tests / files")
    box(d, 450, 70, 160, 58, "Judge workers", "lease / fencing")
    arrow(d, 500, 165, 150, 128)
    arrow(d, 530, 165, 380, 128)
    arrow(d, 450, 98, 395, 98)
    d.add(Line(450, 90, 420, 90, strokeColor=BLUE))
    d.add(Line(420, 90, 420, 50, strokeColor=BLUE))
    d.add(Line(420, 50, 112, 50, strokeColor=BLUE))
    arrow(d, 112, 50, 112, 70)
    box(d, 450, 5, 160, 42, "Docker sandbox")
    arrow(d, 530, 70, 530, 47)
    d.add(
        String(
            25,
            20,
            "Expected outputs stay on host. Fresh run container per test.",
            fontSize=11,
            fillColor=BLUE,
        )
    )
    export_figure(d, "architecture", poppler)
    d = Drawing(640, 400)
    for x, label in [
        (70, "Browser"),
        (235, "API / WS"),
        (410, "SQLite"),
        (570, "Worker"),
    ]:
        d.add(
            String(
                x,
                378,
                label,
                textAnchor="middle",
                fontName="Helvetica-Bold",
                fontSize=13,
                fillColor=BLUE,
            )
        )
        d.add(
            Line(
                x,
                20,
                x,
                363,
                strokeColor=colors.HexColor("#b8c2d0"),
                strokeDashArray=[3, 3],
            )
        )
    for x1, x2, y, label in [
        (70, 235, 335, "POST code + key"),
        (235, 410, 300, "commit submission + job"),
        (235, 70, 265, "202 Pending"),
        (570, 410, 230, "claim lease + token"),
        (570, 410, 160, "result + outbox COMMIT"),
        (235, 410, 125, "read outbox"),
        (235, 70, 90, "WS update"),
        (70, 235, 50, "GET snapshot on reconnect"),
    ]:
        arrow(d, x1, y, x2, y, label)
    box(d, 485, 182, 145, 30, "Docker compile / run")
    export_figure(d, "protocol", poppler)
    datasets = [
        (
            "network_p95",
            "HTTP p95 latency across concurrent clients",
            [str(n) for n in (1, 5, 10, 20)],
            [
                median(r["p95_ms"] for r in network["runs"] if r["concurrency"] == n)
                for n in (1, 5, 10, 20)
            ],
            "Milliseconds",
            BLUE,
        ),
        (
            "judge_throughput",
            "Real Docker judge throughput",
            ["1 worker", "2 workers"],
            [
                median(
                    r["throughput_jobs_per_second"]
                    for r in judge["runs"]
                    if r["workers"] == n
                )
                for n in (1, 2)
            ],
            "Submissions / second",
            RED,
        ),
    ]
    for name, title, categories, values, unit, color in datasets:
        d = Drawing(640, 340)
        d.add(
            String(
                320,
                318,
                title,
                fontName="Helvetica-Bold",
                fontSize=16,
                textAnchor="middle",
                fillColor=BLUE,
            )
        )
        chart = VerticalBarChart()
        chart.x = 75
        chart.y = 60
        chart.width = 500
        chart.height = 220
        chart.data = [tuple(values)]
        chart.categoryAxis.categoryNames = categories
        chart.categoryAxis.labels.fontSize = 12
        chart.categoryAxis.labels.fontName = "Helvetica"
        chart.valueAxis.labels.fontSize = 11
        chart.valueAxis.labels.fontName = "Helvetica"
        chart.valueAxis.valueMin = 0
        raw = max(values) * 1.15 / 5
        power = 10 ** math.floor(math.log10(raw))
        step = next(n * power for n in (1, 2, 5, 10) if n * power >= raw)
        chart.valueAxis.valueMax = math.ceil(max(values) * 1.15 / step) * step
        chart.valueAxis.valueStep = step
        chart.valueAxis.labelTextFormat = "%.0f" if max(values) > 10 else "%.1f"
        chart.bars[0].fillColor = color
        chart.strokeColor = None
        chart.barLabelFormat = "%.2f"
        chart.barLabels.fontSize = 12
        chart.barLabels.fontName = "Helvetica"
        chart.barLabels.nudge = 8
        d.add(chart)
        d.add(String(75, 290, unit, fontSize=11, fillColor=BLUE))
        d.add(
            String(
                320,
                20,
                "Median of three trials; see raw data for run-to-run variation.",
                textAnchor="middle",
                fontSize=11,
                fillColor=BLUE,
            )
        )
        export_figure(d, name, poppler)


def plain(text):
    return (
        re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
        .replace("**", "")
        .replace("`", "")
    )


def set_cell(cell, text, header=False):
    cell.text = plain(text)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    tcpr = cell._tc.get_or_add_tcPr()
    margins = OxmlElement("w:tcMar")
    for edge in ("top", "left", "bottom", "right"):
        e = OxmlElement("w:" + edge)
        e.set(qn("w:w"), "90")
        e.set(qn("w:type"), "dxa")
        margins.append(e)
    tcpr.append(margins)
    for p in cell.paragraphs:
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.space_before = Pt(3)
        for r in p.runs:
            r.font.size = Pt(10)
            r.font.color.rgb = RGBColor.from_string("FFFFFF" if header else "000000")
            r.bold = header


def make_docx(source, destination):
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.2677)
    section.page_height = Inches(11.6929)
    section.top_margin = Inches(0.9)
    section.bottom_margin = Inches(0.85)
    section.left_margin = section.right_margin = Inches(0.95)
    for name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Caption"):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.color.rgb = RGBColor(0, 0, 0)
        fonts = style.element.get_or_add_rPr().rFonts
        for attribute in list(fonts.attrib):
            if "theme" in attribute.lower():
                del fonts.attrib[attribute]
        fonts.set(qn("w:eastAsia"), "Times New Roman")
        paragraph_properties = style.element.find(qn("w:pPr"))
        if paragraph_properties is not None:
            for border in list(paragraph_properties.findall(qn("w:pBdr"))):
                paragraph_properties.remove(border)
    normal = doc.styles["Normal"]
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.18
    normal.paragraph_format.space_after = Pt(7)
    for name, size in [
        ("Title", 22),
        ("Subtitle", 13),
        ("Heading 1", 16),
        ("Heading 2", 13),
    ]:
        st = doc.styles[name]
        st.font.size = Pt(size)
        st.font.bold = name != "Subtitle"
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.space_before = Pt(13)
        st.paragraph_format.space_after = Pt(7)
    doc.styles["Caption"].font.size = Pt(10)
    doc.styles["Caption"].paragraph_format.space_after = Pt(12)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run("LAN-LMS   ")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    for r in footer.runs:
        r.font.size = Pt(9)
    doc.core_properties.author = "Nhóm LAN-LMS"
    doc.core_properties.last_modified_by = "Nhóm LAN-LMS"
    doc.core_properties.title = "Hệ thống học tập và thi lập trình trong mạng LAN"
    lines = source.splitlines()
    i = 0
    code = False
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        if line == "<!-- pagebreak -->":
            doc.add_page_break()
            continue
        if line.startswith("```"):
            code = not code
            continue
        if code:
            p = doc.add_paragraph(line)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1
            for r in p.runs:
                r.font.name = "Consolas"
                r.font.size = Pt(9)
            continue
        if line.startswith("|"):
            data = [line]
            while i < len(lines) and lines[i].strip().startswith("|"):
                data.append(lines[i].strip())
                i += 1
            rows = [
                [c.strip() for c in l.strip("|").split("|")]
                for l in data
                if not re.fullmatch(r"[| :\-]+", l)
            ]
            table = doc.add_table(rows=1, cols=len(rows[0]))
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False
            widths = {
                4: [0.55, 2.55, 1.45, 1.8],
                5: [0.6, 1.15, 1.45, 1.55, 1.6],
                6: [1.0, 1.0, 1.0, 1.25, 1.1, 0.8],
            }.get(len(rows[0]), [6.35 / len(rows[0])] * len(rows[0]))
            # Widen the narrative cells when a four-column table is not a cover table.
            if len(rows[0]) == 3:
                widths = [1.5, 2.6, 2.25]
            for n, w in enumerate(widths):
                table.columns[n].width = Inches(w)
            for row_index, values in enumerate(rows):
                row = table.rows[0] if row_index == 0 else table.add_row()
                for n, text in enumerate(values):
                    cell = row.cells[n]
                    cell.width = Inches(widths[n])
                    set_cell(cell, text, row_index == 0)
                    shade = OxmlElement("w:shd")
                    shade.set(
                        qn("w:fill"),
                        (
                            "263F61"
                            if row_index == 0
                            else "F3F5F8" if row_index % 2 == 0 else "FFFFFF"
                        ),
                    )
                    cell._tc.get_or_add_tcPr().append(shade)
                if row_index == 0:
                    repeat = OxmlElement("w:tblHeader")
                    row._tr.get_or_add_trPr().append(repeat)
            borders = OxmlElement("w:tblBorders")
            for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
                e = OxmlElement("w:" + edge)
                e.set(qn("w:val"), "single")
                e.set(qn("w:sz"), "4")
                e.set(qn("w:color"), "D9D9D9")
                borders.append(e)
            table._tbl.tblPr.append(borders)
            doc.add_paragraph().paragraph_format.space_after = Pt(2)
            continue
        image = re.match(r"!\[([^]]*)\]\(([^)]+)\)", line)
        if image:
            path = (ROOT / "REPORT" / image.group(2)).resolve()
            p = doc.add_paragraph()
            p.paragraph_format.keep_with_next = True
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(path), width=Inches(6.2))
            p = doc.add_paragraph(image.group(1), style="Caption")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            continue
        if line.startswith("# "):
            p = doc.add_paragraph(
                line[2:].replace(" trong mạng LAN", "\ntrong mạng LAN"), style="Title"
            )
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:], level=1)
            continue
        p = doc.add_paragraph(plain(line))
        if line.startswith(("Báo cáo bài tập", "Nhóm [", "Tháng 10")):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.save(destination)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--network",
        type=Path,
        default=ROOT
        / "experiments/results/windows-loopback-2026-10-25/network-summary.json",
    )
    p.add_argument(
        "--judge",
        type=Path,
        default=ROOT / "experiments/results/ci-linux-40202701438/judge-summary.json",
    )
    p.add_argument("--poppler-path")
    a = p.parse_args()
    network = json.loads(a.network.read_text(encoding="utf-8"))
    judge = json.loads(a.judge.read_text(encoding="utf-8"))
    provenance = json.loads(
        (a.judge.parent / "provenance.json").read_text(encoding="utf-8")
    )
    if any(r["error_rate"] for r in network["runs"]) or any(
        x["verdict"] != "Accepted" for r in judge["runs"] for x in r["raw"]
    ):
        raise ValueError("Input measurements contain failures; review report")
    http = []
    workers = []
    throughput = {}
    for n in (1, 5, 10, 20):
        runs = [r for r in network["runs"] if r["concurrency"] == n]
        http.append(
            f"| {n} | {median(r['p50_ms'] for r in runs):.2f} | {median(r['p95_ms'] for r in runs):.2f} | {median(r['throughput_requests_per_second'] for r in runs):.2f} | {sum(r['requests'] for r in runs)} | 0% |"
        )
    for n in (1, 2):
        runs = [r for r in judge["runs"] if r["workers"] == n]
        throughput[n] = median(r["throughput_jobs_per_second"] for r in runs)
        workers.append(
            f"| {n} | {median(r['elapsed_seconds'] for r in runs):.2f} | {throughput[n]:.3f} | {median(r['p50_queue_wait_ms'] for r in runs)/1000:.2f} | {median(r['p50_end_to_end_ms'] for r in runs)/1000:.2f} |"
        )
    speedup = throughput[2] / throughput[1]
    env = judge["environment"]
    figures(network, judge, a.poppler_path)
    tokens = {
        "@@HTTP_TABLE@@": "\n".join(http),
        "@@WORKER_TABLE@@": "\n".join(workers),
        "@@SPEEDUP@@": f"{speedup:.2f}",
        "@@WINDOWS_OS@@": network["environment"]["os"],
        "@@JUDGE_ENV@@": f"{env['os']}; {env['cpu']}; {env['logical_cpus']} CPU logic; {env.get('ram_gib',0):.2f} GiB RAM; Python {env['python']}; Docker {env.get('docker_version','không ghi')}",
        "@@CI_URL@@": provenance["url"],
        "@@HEAD@@": provenance["head_sha"],
        "@@IMAGE@@": env.get("image_id", env["image"]),
    }
    text = (ROOT / "REPORT/REPORT_TEMPLATE.md").read_text(encoding="utf-8")
    for key, value in tokens.items():
        text = text.replace(key, value)
    if "@@" in text:
        raise ValueError("Unresolved report token")
    (ROOT / "REPORT/REPORT_SOURCE.md").write_text(text, encoding="utf-8")
    make_docx(text, ROOT / "REPORT/NhomXX_LANLMS_Report.docx")
    results = (ROOT / "experiments/RESULTS_TEMPLATE.md").read_text(encoding="utf-8")
    tokens["@@DATA_FOLDER@@"] = a.judge.parent.name
    for key, value in tokens.items():
        results = results.replace(key, value)
    (ROOT / "experiments/RESULTS.md").write_text(results, encoding="utf-8")
    print("DOCX, Markdown, figures and measured summary created")


if __name__ == "__main__":
    main()
