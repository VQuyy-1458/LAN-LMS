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
  const load = useCallback(async () => {
    const r = await apiRequest<Page<Exam>>(
      `/api/courses/${courseId}/coding-exams?page_size=100`,
    );
    setRows(r.items);
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
      {teacher && (
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
