"use client";
import {useCourseReadonly} from "@/components/CourseAccess";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { date, type Page } from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import Feedback from "@/components/Feedback";
type Material = {
  id: number;
  title: string;
  original_filename: string;
  size_bytes: number;
  uploaded_at: string;
};
export default function MaterialsPanel({
  courseId,
  teacher,
}: {
  courseId: number;
  teacher: boolean;
}) {
  const [rows, setRows] = useState<Material[]>([]),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0);
  const readonly=useCourseReadonly();
  const action = useAction();
  const load = useCallback(async () => {
    const r = await apiRequest<Page<Material>>(
      `/api/courses/${courseId}/materials?page=${page}&page_size=10`,
    );
    setRows(r.items);
    setTotal(r.total);
  }, [courseId, page]);
  useEffect(() => {
    load().catch(action.setError);
  }, [load, action.setError]);
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      {teacher && !readonly && (
        <section className="panel">
          <h2>Đăng tài liệu</h2>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const form = e.currentTarget,
                data = new FormData(form);
              void action.run(async () => {
                await apiRequest(`/api/courses/${courseId}/materials`, {
                  method: "POST",
                  body: data,
                });
                form.reset();
                await load();
              }, "Đã đăng tài liệu.");
            }}
          >
            <div className="form-grid" style={{ marginTop: 15 }}>
              <label>
                Tên tài liệu
                <input name="title" maxLength={200} required />
              </label>
              <label>
                File tài liệu
                <input
                  type="file"
                  name="file"
                  accept=".pdf,.doc,.docx,.ppt,.pptx,.txt,.zip"
                  required
                />
              </label>
            </div>
            <p className="section-note">
              Tối đa 20 MiB. Chỉ thành viên khóa học được tải file.
            </p>
            <div className="actions">
              <button disabled={action.busy}>Đăng tài liệu</button>
            </div>
          </form>
        </section>
      )}
      <section className="panel">
        <div className="panel-title">
          <h2>Tài liệu khóa học</h2>
          <span className="badge">{total} tài liệu</span>
        </div>
        {rows.map((r) => (
          <div key={r.id} className="file-row">
            <div>
              <h3>{r.title}</h3>
              <p className="section-note">
                {r.original_filename} · {(r.size_bytes / 1024).toFixed(1)} KB ·{" "}
                {date(r.uploaded_at)}
              </p>
            </div>
            <a className="download" href={`/api/materials/${r.id}/download`}>
              Tải xuống ↓
            </a>
          </div>
        ))}
        {!rows.length && (
          <div className="empty">Chưa có tài liệu trong khóa học.</div>
        )}
        <div className="actions">
          <button
            className="secondary"
            disabled={page === 1}
            onClick={() => setPage((x) => x - 1)}
          >
            Trước
          </button>
          <span>Trang {page}</span>
          <button
            className="secondary"
            disabled={page * 10 >= total}
            onClick={() => setPage((x) => x + 1)}
          >
            Sau
          </button>
        </div>
      </section>
    </div>
  );
}
