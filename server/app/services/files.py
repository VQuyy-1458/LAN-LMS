"""Bounded streaming uploads and private UUID storage; never unpack or execute uploaded files."""
import uuid
from pathlib import Path
from ..core.security import fail


async def read_upload(upload, limit, suffixes):
    name=Path((upload.filename or '').replace('\\','/')).name
    if not name or Path(name).suffix.lower() not in suffixes:
        fail(400,'INVALID_FILE_TYPE','Loại file không được phép')
    data=bytearray()
    while chunk:=await upload.read(65536):
        data.extend(chunk)
        if len(data)>limit: fail(413,'FILE_TOO_LARGE','File vượt quá dung lượng')
    return name,bytes(data)


def save(root, directory, content):
    folder=Path(root)/directory
    folder.mkdir(parents=True,exist_ok=True)
    name=f'{directory}/{uuid.uuid4().hex}'
    path=Path(root)/name
    with path.open('xb') as stream: stream.write(content)
    return name


def resolve(root, relative):
    base=Path(root).resolve(); path=(base/relative).resolve()
    if not path.is_relative_to(base) or not path.is_file(): fail(404,'NOT_FOUND','File không tồn tại')
    return path
