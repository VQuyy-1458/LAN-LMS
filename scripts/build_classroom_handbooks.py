"""Authoring-only utility. Uses ReportLab; runtime LMS does not need ReportLab."""
from pathlib import Path
import shutil
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from demo.classroom_content import COURSES

ROOT=Path(__file__).resolve().parents[1]


def build():
    pdfmetrics.registerFont(TTFont("Body","C:/Windows/Fonts/arial.ttf"))
    pdfmetrics.registerFont(TTFont("BodyBold","C:/Windows/Fonts/arialbd.ttf"))
    pdfmetrics.registerFontFamily("Body",normal="Body",bold="BodyBold")
    ink=colors.HexColor("#102849");red=colors.HexColor("#bf242a");muted=colors.HexColor("#607089")
    body=ParagraphStyle("body",fontName="Body",fontSize=11,leading=17,textColor=ink,spaceAfter=15)
    title=ParagraphStyle("title",parent=body,fontName="BodyBold",fontSize=24,leading=30,spaceAfter=22)
    small=ParagraphStyle("small",parent=body,fontSize=9,leading=14,textColor=muted)
    label=ParagraphStyle("label",parent=small,fontName="BodyBold",textColor=red,spaceAfter=12)
    output=ROOT/"output/pdf";output.mkdir(parents=True,exist_ok=True)
    assets=ROOT/"demo/materials";assets.mkdir(parents=True,exist_ok=True)
    for course in COURSES:
        path=output/(course["key"]+"-handbook.pdf")
        def decorate(canvas,doc):
            width,height=A4
            canvas.setFillColor(red);canvas.rect(0,height-12,width,12,fill=1,stroke=0)
            canvas.setFont("BodyBold",9);canvas.setFillColor(ink);canvas.drawString(46,height-42,"LAN-LMS / HỌC LIỆU TỰ SOẠN")
            canvas.setStrokeColor(colors.HexColor("#dfe6ee"));canvas.line(46,48,width-46,48)
            canvas.setFont("Body",8);canvas.setFillColor(muted)
            canvas.drawString(46,32,"Dữ liệu lớp mẫu | 27/10/2026 | Tài liệu do nhóm tự biên soạn")
            canvas.drawRightString(width-46,32,f"{doc.page} / 6")
        story=[]
        for index,(heading,paragraphs) in enumerate(course["sections"]):
            story.append(Paragraph(escape(course["name"]),small))
            story.append(Spacer(1,12))
            story.append(Paragraph(f"CHUYÊN ĐỀ {index+1:02d} / 06",label))
            story.append(Paragraph(escape(heading),title))
            for paragraph in paragraphs: story.append(Paragraph(escape(paragraph),body))
            story.append(Spacer(1,10))
            prompts=["Giải thích một ý chính bằng ví dụ do bạn tự đặt.","Nêu ít nhất hai trường hợp biên hoặc tình huống lỗi.","Ghi lại cách kiểm tra và kết quả quan sát; không điền số liệu chưa đo."]
            cells=[[Paragraph("TỰ KIỂM TRA",label)]]+[[Paragraph(escape(f"{i+1}. {text}"),body)] for i,text in enumerate(prompts)]
            box=Table(cells,colWidths=[A4[0]-116])
            box.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#f0f4f9")),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#dfe6ee")),("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),("TOPPADDING",(0,0),(-1,0),12),("BOTTOMPADDING",(0,-1),(-1,-1),10)]))
            story.append(box)
            if index<5: story.append(PageBreak())
        doc=SimpleDocTemplate(str(path),pagesize=A4,leftMargin=46,rightMargin=46,topMargin=68,bottomMargin=64,
            title=course["name"]+" - Sổ tay thực hành",author="Nhóm LAN-LMS")
        doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
        shutil.copy2(path,assets/path.name)
        print(path)


if __name__=="__main__": build()
