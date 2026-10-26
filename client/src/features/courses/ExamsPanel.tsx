"use client";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { date, request, statusLabel, type Page, type Exam } from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import Feedback from "@/components/Feedback";
import ExamEditor, { ExamForm } from "./ExamEditor";
import ExamPlayer from "./ExamPlayer";
export default function ExamsPanel({
  courseId,
  teacher,
}: {
  courseId: number;
  teacher: boolean;
}) {
  const [rows, setRows] = useState<Exam[]>([]),
    [selected, setSelected] = useState(0);
  const action = useAction();
  const [judge, setJudge] = useState<{
    ready: boolean;
    workers: number;
    pending_jobs: number;
  } | null>(null);
  const load = useCallback(async () => {
    const r = await apiRequest<Page<Exam>>(
      `/api/courses/${courseId}/coding-exams?page_size=100`,
    );
    setRows(r.items);
    setJudge(await apiRequest(`/api/courses/${courseId}/judge-status`));
  }, [courseId]);
  useEffect(() => {
    load().catch(action.setError);
    const timer = setInterval(() => load().catch(() => {}), 10000);
    return () => clearInterval(timer);
  }, [load, action.setError]);
  const chosen = rows.find((r) => r.id === selected);
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      <section className="panel judge-status" aria-live="polite">
        <div>
          <h2>
            {judge?.ready ? "Bộ chấm đang hoạt động" : "Bộ chấm chưa sẵn sàng"}
          </h2>
          <p className="section-note">
            {judge?.ready
              ? `${judge.workers} worker · ${judge.pending_jobs} bài trong hàng đợi`
              : "Docker Engine hoặc worker chưa hoạt động. Bài nộp được lưu và chờ bộ chấm; chưa thể trả kết quả."}
          </p>
        </div>
        <p className="section-note">
          Nộp qua HTTP → hàng đợi trên máy chủ → chấm test trong Docker → cập
          nhật kết quả qua WebSocket.
        </p>
      </section>
      {chosen && (
        <div className="panel-title">
          <h2>{chosen.title}</h2>
          <button className="secondary" onClick={() => setSelected(0)}>
            ← Danh sách kỳ thi
          </button>
        </div>
      )}
      {teacher && !chosen && (
        <section className="panel">
          <details>
            <summary>Tạo kỳ thi giữa kỳ / cuối kỳ</summary>
            <ExamForm
              busy={action.busy}
              save={(body) =>
                void action.run(async () => {
                  const e = await request<Exam>(
                    `/api/courses/${courseId}/coding-exams`,
                    "POST",
                    body,
                  );
                  setSelected(e.id);
                  await load();
                }, "Đã tạo đề nháp. Thêm đủ bài và test trước khi lên lịch mở thi.")
              }
            />
          </details>
        </section>
      )}
      {!chosen && (
        <div className="grid-2">
          {rows.map((e) => (
            <button
              key={e.id}
              className="panel"
              style={{
                textAlign: "left",
                color: "var(--text-primary)",
                borderColor:
                  e.id === selected ? "var(--primary)" : "var(--border)",
              }}
              onClick={() => setSelected(e.id)}
            >
              <div className="panel-title">
                <span className="badge">
                  {e.grade_component === "midterm" ? "Giữa kỳ" : "Cuối kỳ"}
                </span>
                <span className={`badge ${e.status}`}>
                  {statusLabel[e.status]}
                </span>
              </div>
              <h2>{e.title}</h2>
              <p className="section-note">
                {date(e.starts_at)} · {e.problem_count} bài
              </p>
            </button>
          ))}
        </div>
      )}
      {!rows.length && (
        <div className="empty">
          {teacher
            ? "Chưa có kỳ thi. Tạo đề nháp để bắt đầu."
            : "Chưa có kỳ thi được công bố trong khóa học."}
        </div>
      )}
      {chosen &&
        (teacher ? (
          <ExamEditor key={chosen.id} exam={chosen} onChange={load} />
        ) : (
          <ExamPlayer key={chosen.id} exam={chosen} />
        ))}
    </div>
  );
}
