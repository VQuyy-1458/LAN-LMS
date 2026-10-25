"use client";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { request } from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import Feedback from "@/components/Feedback";
type Weights = {
  attendance: number;
  homework: number;
  midterm: number;
  final: number;
};
type Grade = {
  student_id: string;
  full_name: string;
  class_name: string;
  attendance_score: number | null;
  homework_score: number | null;
  midterm_score: number | null;
  final_score: number | null;
  total_score: number | null;
};
type Book = { weights: Weights; published: boolean; items: Grade[] };
const names: Record<keyof Weights, string> = {
  attendance: "Chuyên cần",
  homework: "Bài tập",
  midterm: "Giữa kỳ",
  final: "Cuối kỳ",
};
export default function GradebookPanel({
  courseId,
  teacher,
}: {
  courseId: number;
  teacher: boolean;
}) {
  const [book, setBook] = useState<Book | null>(null),
    [weights, setWeights] = useState<Weights>({
      attendance: 10,
      homework: 20,
      midterm: 30,
      final: 40,
    }),
    [search, setSearch] = useState("");
  const action = useAction();
  const load = useCallback(async () => {
    const r = await apiRequest<Book>(`/api/courses/${courseId}/gradebook`);
    setBook(r);
    setWeights(r.weights);
  }, [courseId]);
  useEffect(() => {
    load().catch(action.setError);
  }, [load, action.setError]);
  const total = Object.values(weights).reduce((a, b) => a + b, 0);
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      {teacher && (
        <section className="panel">
          <details>
            <summary>Cấu hình trọng số và điều chỉnh điểm</summary>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void action.run(async () => {
                  await request(
                    `/api/courses/${courseId}/grade-components`,
                    "PATCH",
                    weights,
                  );
                  await load();
                }, "Đã lưu trọng số. Bảng điểm cần được công bố lại.");
              }}
            >
              <div className="form-grid">
                {(Object.keys(names) as (keyof Weights)[]).map((k) => (
                  <label key={k}>
                    {names[k]} (%)
                    <input
                      type="number"
                      min={0}
                      max={100}
                      step="0.01"
                      required
                      value={weights[k]}
                      onChange={(e) =>
                        setWeights((v) => ({
                          ...v,
                          [k]: Number(e.target.value),
                        }))
                      }
                    />
                  </label>
                ))}
              </div>
              <div className="actions">
                <button
                  disabled={action.busy || Math.abs(total - 100) > 0.000001}
                >
                  Lưu trọng số
                </button>
                <span className="badge">Tổng {total}% / 100%</span>
              </div>
            </form>
            <div className="details-box">
              <h3>Điều chỉnh điểm thành phần</h3>
              <p className="section-note">
                Điểm để trống sẽ bỏ điều chỉnh thủ công và dùng lại điểm tự
                động. Mọi thay đổi đều lưu lý do và thu hồi công bố.
              </p>
              <form
                style={{ marginTop: 15 }}
                onSubmit={(e) => {
                  e.preventDefault();
                  const form = e.currentTarget,
                    f = new FormData(form),
                    v = String(f.get("score"));
                  void action.run(async () => {
                    await request(`/api/courses/${courseId}/grades`, "PATCH", {
                      items: [
                        {
                          student_id: f.get("student_id"),
                          component: f.get("component"),
                          score: v === "" ? null : Number(v),
                          reason: f.get("reason"),
                        },
                      ],
                    });
                    form.reset();
                    await load();
                  }, "Đã lưu điều chỉnh điểm.");
                }}
              >
                <div className="form-grid">
                  <label>
                    Mã sinh viên
                    <input name="student_id" required />
                  </label>
                  <label>
                    Thành phần
                    <select name="component">
                      {Object.entries(names).map(([k, n]) => (
                        <option key={k} value={k}>
                          {n}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Điểm (0–10)
                    <input
                      name="score"
                      type="number"
                      min={0}
                      max={10}
                      step="0.01"
                    />
                  </label>
                  <label>
                    Lý do
                    <input
                      name="reason"
                      required
                      minLength={3}
                      maxLength={1000}
                    />
                  </label>
                </div>
                <div className="actions">
                  <button disabled={action.busy}>Lưu điều chỉnh</button>
                </div>
              </form>
            </div>
          </details>
        </section>
      )}
      <section className="panel">
        <div className="panel-title">
          <div>
            <h2>
              {teacher ? "Bảng điểm khóa học" : "Kết quả học tập của tôi"}
            </h2>
            <p className="section-note">
              Thang điểm 10 · Điểm trống là chưa đủ dữ liệu.
            </p>
          </div>
          <span className="badge">
            {book?.published ? "Đã công bố" : "Chưa công bố"}
          </span>
        </div>
        {teacher && (
          <div className="toolbar">
            <input
              aria-label="Tìm sinh viên"
              placeholder="Tìm mã hoặc họ tên…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <div className="actions" style={{ marginTop: 0 }}>
              <button
                disabled={action.busy || !book}
                onClick={() =>
                  void action.run(
                    async () => {
                      await request(
                        `/api/courses/${courseId}/gradebook/publish`,
                        "POST",
                        { published: !book?.published },
                      );
                      await load();
                    },
                    book?.published
                      ? "Đã thu hồi công bố."
                      : "Đã công bố bảng điểm.",
                  )
                }
              >
                {book?.published ? "Thu hồi công bố" : "Công bố điểm"}
              </button>
              <a
                className="button-link"
                href={`/api/courses/${courseId}/gradebook/export-csv`}
              >
                Xuất CSV ↓
              </a>
              <button
                className="secondary"
                onClick={() => void action.run(load, "")}
              >
                Làm mới
              </button>
            </div>
          </div>
        )}
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Mã sinh viên</th>
                <th>Họ tên</th>
                <th>Lớp</th>
                {(Object.entries(names) as [keyof Weights, string][]).map(
                  ([k, n]) => (
                    <th key={k}>
                      {n}
                      <br />
                      {book?.weights[k]}%
                    </th>
                  ),
                )}
                <th>Tổng kết</th>
              </tr>
            </thead>
            <tbody>
              {book?.items
                .filter((r) =>
                  `${r.student_id} ${r.full_name}`
                    .toLowerCase()
                    .includes(search.toLowerCase()),
                )
                .map((r) => (
                  <tr key={r.student_id}>
                    <td>{r.student_id}</td>
                    <td>{r.full_name}</td>
                    <td>{r.class_name}</td>
                    {(Object.keys(names) as (keyof Weights)[]).map((k) => (
                      <td key={k}>{r[`${k}_score`] ?? "—"}</td>
                    ))}
                    <td>
                      <strong style={{ color: "var(--primary)" }}>
                        {r.total_score ?? "—"}
                      </strong>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        {!book?.items.length && (
          <div className="empty">
            {teacher
              ? "Chưa có sinh viên trong khóa."
              : "Giảng viên chưa công bố bảng điểm."}
          </div>
        )}
        <p className="section-note">
          Điểm thi được quy đổi từ số bài AC theo cấu hình đề thi. Điểm tổng kết
          chỉ có khi các thành phần có trọng số dương đã đủ điểm.
          {teacher &&
            " Khi mở CSV trong Excel, import cột mã sinh viên dưới dạng Text để giữ số 0 đầu."}
        </p>
      </section>
    </div>
  );
}
