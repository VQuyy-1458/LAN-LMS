"""Private material response projection; storage helpers are shared in services.files."""


def view(r):
    from datetime import datetime, timezone

    return dict(
        id=r.id,
        course_id=r.course_id,
        title=r.title,
        original_filename=r.original_filename,
        size_bytes=r.size_bytes,
        uploaded_at=datetime.fromtimestamp(r.uploaded_at, timezone.utc).isoformat(),
    )
