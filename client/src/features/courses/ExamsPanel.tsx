"use client";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { date, request, statusLabel, type Page, type Exam } from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import Feedback from "@/components/Feedback";
import ExamEditor, { ExamForm } from "./ExamEditor";
import ExamPlayer from "./ExamPlayer";
import { availableExamComponents } from "@/lib/examCreation";
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
  const [loaded, setLoaded] = useState(false);
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
    setLoaded(true);
    setJudge(await apiRequest(`/api/courses/${courseId}/judge-status`));
  }, [courseId]);
  useEffect(() => {
    load().catch(action.setError);
    const timer = setInterval(() => load().catch(() => {}), 10000);
    return () => clearInterval(timer);
  }, [load, action.setError]);
  const chosen = rows.find((r) => r.id === selected);
  const availableComponents = availableExamComponents(rows);
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      <section className="exam-service-bar" aria-live="polite">
        <div>
          <strong>
            {judge?.ready ? "Bộ chấm đang hoạt động" : "Bộ chấm chưa sẵn sàng"}
          </strong>
          <p className="section-note">
            {judge?.ready
              ? `${judge.workers} worker · ${judge.pending_jobs} bài trong hàng đợi`
              : "Bài nộp vẫn được lưu an toàn và chờ chấm. Vui lòng liên hệ giảng viên nếu cần hỗ trợ."}
          </p>
        </div>
        {chosen && (
          <button className="secondary" onClick={() => setSelected(0)}>
            ← Danh sách kỳ thi
          </button>
        )}
      </section>
      {teacher && loaded && !chosen && availableComponents.length > 0 && (
        <section className="panel">
          <details>
            <summary>Tạo kỳ thi giữa kỳ / cuối kỳ</summary>
            <p className="section-note">
              Mỗi khóa học có một đề giữa kỳ và một đề cuối kỳ. Chỉ tạo được
              thành phần chưa có; các đề đã có nằm trong danh sách bên dưới.
            </p>
            <ExamForm
              availableComponents={availableComponents}
              busy={action.busy}
              save={(body) =>
                void action.run(async () => {
                  let e: Exam;
                  try {
                    e = await request<Exam>(
                      `/api/courses/${courseId}/coding-exams`,
                      "POST",
                      body,
                    );
                  } catch (error) {
                    await load();
                    throw error;
                  }
                  setSelected(e.id);
                  await load();
                }, "Đã tạo đề nháp. Thêm đủ bài và test trước khi lên lịch mở thi.")
              }
            />
          </details>
        </section>
      )}
      {teacher && loaded && !chosen && availableComponents.length === 0 && (
        <section className="panel">
          <h2>Khóa học đã có đủ hai kỳ thi</h2>
          <p className="section-note">
            Mỗi khóa học có một đề giữa kỳ và một đề cuối kỳ. Chọn một đề bên
            dưới để xem nội dung, quản lý lịch thi và theo dõi bài nộp.
          </p>
        </section>
      )}
      {!loaded && <p role="status">Đang tải danh sách kỳ thi…</p>}
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
      {loaded && !rows.length && (
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
