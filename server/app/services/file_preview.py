"""Bounded, local-only previews. Never execute submitted markup or source files."""
from pathlib import Path
import zipfile
from xml.etree import ElementTree
from ..core.security import fail

LIMIT = 2 * 1024 * 1024
TEXT = {".txt", ".c", ".cpp", ".h", ".java", ".py", ".md", ".csv", ".json", ".in", ".out", ".log"}

def preview(path, filename, entry=None):
    suffix=Path(filename).suffix.lower()
    if suffix==".pdf": return {"kind":"pdf"}
    if suffix in TEXT:
        with path.open("rb") as stream: data=stream.read(LIMIT+1)
        return {"kind":"text","text":data[:LIMIT].decode("utf-8-sig",errors="replace"),"truncated":len(data)>LIMIT}
    if suffix in {".zip", ".docx", ".pptx"}:
        try:
            with zipfile.ZipFile(path) as archive:
                infos=archive.infolist()
                if len(infos)>2000: fail(413,"PREVIEW_LIMIT","File có quá nhiều mục để xem trước")
                if suffix==".zip":
                    if entry is None: return {"kind":"archive","entries":[{"name":i.filename,"size":i.file_size,"readable":Path(i.filename).suffix.lower() in TEXT and i.file_size<=LIMIT} for i in infos if not i.is_dir()]}
                    info=archive.getinfo(entry)
                    if info.file_size>LIMIT or Path(entry).suffix.lower() not in TEXT: fail(422,"PREVIEW_UNSUPPORTED","Chỉ xem trực tiếp file văn bản/mã nguồn nhỏ hơn 2 MiB trong ZIP")
                    return {"kind":"text","text":archive.read(info).decode("utf-8-sig",errors="replace"),"truncated":False}
                names=[i for i in infos if i.filename=="word/document.xml" or (i.filename.startswith("ppt/slides/slide") and i.filename.endswith(".xml"))]
                if sum(i.file_size for i in names)>LIMIT: fail(413,"PREVIEW_LIMIT","Nội dung quá lớn để xem trước")
                text=[]
                for info in sorted(names,key=lambda x:x.filename):
                    root=ElementTree.fromstring(archive.read(info))
                    text.extend(''.join(p.itertext()) for p in root.iter() if p.tag.rsplit('}',1)[-1]=='t')
                return {"kind":"text","text":"\n".join(text),"truncated":False,"note":"Bản xem nội dung văn bản; bố cục gốc nằm trong file tải xuống."}
        except (zipfile.BadZipFile,KeyError,ElementTree.ParseError): fail(422,"INVALID_PREVIEW_FILE","File hỏng hoặc không đúng định dạng")
    return {"kind":"unsupported","text":"Định dạng này chưa hỗ trợ xem trực tiếp. Với .doc/.ppt, hãy lưu lại dưới dạng PDF hoặc .docx/.pptx để xem trên web."}
