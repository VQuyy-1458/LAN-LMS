"use client";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { date, type Page } from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import Feedback from "@/components/Feedback";
type Student = {
  student_id: string;
  full_name: string;
  class_name: string;
  email: string | null;
};
type Preview = {
  preview_id: string;
  expires_at: string;
  total_rows: number;
  valid_rows: number;
  new_accounts: number;
  existing_accounts: number;
  can_confirm: boolean;
  errors: { row: number; field?: string; message: string }[];
};
type ImportResult = {
  created_accounts: number;
  existing_accounts: number;
  new_enrollments: number;
  existing_enrollments: number;
};
export default function StudentsPanel({ courseId }: { courseId: number }) {
  const [students, setStudents] = useState<Student[]>([]),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0),
    [preview, setPreview] = useState<Preview | null>(null),
    [result, setResult] = useState<ImportResult | null>(null);
  const action = useAction();
  const load = useCallback(async () => {
    const r = await apiRequest<Page<Student>>(
      `/api/courses/${courseId}/students?page=${page}&page_size=50`,
    );
    setStudents(r.items);
    setTotal(r.total);
  }, [courseId, page]);
  useEffect(() => {
    load().catch(action.setError);
  }, [load, action.setError]);
  function errorsCSV() {
    if (!preview) return;
    const safe = (s: string) =>
      `"${(/^[=+@-]/.test(s) ? "'" : "") + s.replaceAll('"', '""')}"`;
    const text =
      "\ufeffrow,field,message\r\n" +
      preview.errors
        .map((e) =>
          [e.row, e.field || "", e.message]
            .map((v) => safe(String(v)))
            .join(","),
        )
        .join("\r\n");
    const url = URL.createObjectURL(
      new Blob([text], { type: "text/csv;charset=utf-8" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "csv-errors.csv";
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      <section className="panel">
        <h2>Import sinh viên từ CSV</h2>
        <p className="section-note">
          UTF-8 · tối đa 2 MiB / 2.000 dòng. Cột: student_id, full_name,
          date_of_birth (DDMMYYYY), class_name, email (tùy chọn).
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            void action.run(async () => {
              setPreview(null);
              setResult(null);
              setPreview(
                await apiRequest<Preview>(
                  `/api/courses/${courseId}/students/import-preview`,
                  { method: "POST", body: f },
                ),
              );
            }, "Đã kiểm tra file. Hãy xem kết quả trước khi xác nhận.");
          }}
        >
          <label style={{ marginTop: 15 }}>
            File danh sách
            <input type="file" name="file" accept=".csv" required />
          </label>
          <div className="actions">
            <button disabled={action.busy}>Xem trước dữ liệu</button>
            <a className="button-link" href="/samples/students.csv" download>
              Tải CSV mẫu
            </a>
          </div>
        </form>
        {preview && (
          <div className="details-box">
            <div className="grid-3">
              <div>
                <strong>{preview.total_rows}</strong>
                <p className="muted">Tổng dòng</p>
              </div>
              <div>
                <strong>{preview.new_accounts}</strong>
                <p className="muted">Tài khoản mới</p>
              </div>
              <div>
                <strong>{preview.existing_accounts}</strong>
                <p className="muted">Tài khoản đã có</p>
              </div>
            </div>
            <p className="section-note">
              {preview.valid_rows} dòng hợp lệ · Hết hạn{" "}
              {date(preview.expires_at)}. Tài khoản cũ giữ nguyên mật khẩu.
            </p>
            {preview.errors.length > 0 && (
              <>
                <div className="alert error" style={{ marginTop: 12 }}>
                  Có lỗi; chưa thể import. Sửa file rồi xem trước lại.
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Dòng</th>
                        <th>Trường</th>
                        <th>Lỗi</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.errors.slice(0, 100).map((r, i) => (
                        <tr key={i}>
                          <td>{r.row}</td>
                          <td>{r.field}</td>
                          <td>{r.message}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <button className="secondary" onClick={errorsCSV}>
                  Tải báo cáo lỗi
                </button>
              </>
            )}
            <div className="actions">
              <button
                disabled={!preview.can_confirm || action.busy}
                onClick={() =>
                  void action.run(async () => {
                    setResult(
                      await apiRequest<ImportResult>(
                        `/api/courses/${courseId}/students/import-confirm`,
                        {
                          method: "POST",
                          headers: {
                            "Idempotency-Key": `csv-${preview.preview_id}`,
                          },
                          body: JSON.stringify({
                            preview_id: preview.preview_id,
                          }),
                        },
                      ),
                    );
                    await load();
                    setPreview(null);
                  }, "Import thành công.")
                }
              >
                Xác nhận import
              </button>
            </div>
          </div>
        )}
        {result && (
          <div className="alert success" style={{ marginTop: 14 }}>
            Đã tạo {result.created_accounts} tài khoản, thêm{" "}
            {result.new_enrollments} sinh viên vào khóa.{" "}
            {result.existing_accounts} tài khoản và{" "}
            {result.existing_enrollments} đăng ký đã có.
          </div>
        )}
      </section>
      <section className="panel">
        <div className="panel-title">
          <h2>Sinh viên trong khóa</h2>
          <span className="badge">{total} sinh viên</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Mã sinh viên</th>
                <th>Họ tên</th>
                <th>Lớp</th>
                <th>Email</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.student_id}>
                  <td>{s.student_id}</td>
                  <td>{s.full_name}</td>
                  <td>{s.class_name}</td>
                  <td>{s.email || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!students.length && (
          <div className="empty">
            Chưa có sinh viên. Import CSV để thêm danh sách lớp.
          </div>
        )}
        <div className="actions">
          <button
            className="secondary"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Trước
          </button>
          <span>Trang {page}</span>
          <button
            className="secondary"
            disabled={page * 50 >= total}
            onClick={() => setPage((p) => p + 1)}
          >
            Sau
          </button>
        </div>
      </section>
    </div>
  );
}
