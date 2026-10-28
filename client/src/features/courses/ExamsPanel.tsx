"use client";
import {useCourseReadonly} from "@/components/CourseAccess";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { allPages, date, request, statusLabel, type Exam } from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import PaginatedList from "@/components/Pagination";
import ConfirmAction from "@/components/ConfirmAction";
import Feedback from "@/components/Feedback";
import ExamEditor, { ExamForm } from "./ExamEditor";
import ExamPlayer from "./ExamPlayer";
import {
  availableExamComponents,
  examComponentLabel,
} from "@/lib/examCreation";
export default function ExamsPanel({
  courseId,
  teacher,
}: {
  courseId: number;
  teacher: boolean;
}) {
  const [rows, setRows] = useState<Exam[]>([]),
    [selected, setSelected] = useState(0);
  const readonly=useCourseReadonly();
  const action = useAction();
  const [loaded, setLoaded] = useState(false);
  const [judge, setJudge] = useState<{
    ready: boolean;
    workers: number;
    pending_jobs: number;
  } | null>(null);
  const load = useCallback(async () => {
    const r = await allPages<Exam>(`/api/courses/${courseId}/coding-exams`);
    setRows(r);
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
      {teacher && !readonly && loaded && !chosen && availableComponents.length > 0 && (
        <section className="panel">
          <details>
            <summary>Tạo bài thi lập trình</summary>
            <p className="section-note">
              Tạo nhiều đề test và giữa kỳ. Điểm giữa kỳ là trung bình các đề
              giữa kỳ; mỗi khóa có một đề cuối kỳ.
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
      {!loaded && <p role="status">Đang tải danh sách kỳ thi…</p>}
      {!chosen && (
        <PaginatedList className="grid-2">
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
              disabled={!teacher&&e.can_open===false}
              onClick={() => setSelected(e.id)}
            >
              <div className="panel-title">
                <span className="badge">
                  {examComponentLabel[e.grade_component]}
                </span>
                <span className={`badge ${e.status}`}>
                  {statusLabel[e.status]}
                </span>
              </div>
              <h2>{e.title}</h2>
              <p className="section-note">
                {date(e.starts_at)} · {e.problem_count} bài {!teacher&&e.can_open===false&&"· Đã nộp / hết giờ — không mở lại"}
              </p>
            </button>
          ))}
        </PaginatedList>
      )}
      {loaded && !rows.length && (
        <div className="empty">
          {teacher
            ? "Chưa có kỳ thi. Tạo đề nháp để bắt đầu."
            : "Chưa có kỳ thi được công bố trong khóa học."}
        </div>
      )}
      {chosen && teacher && !readonly && <ConfirmAction label="Xóa kỳ thi" message={`Bạn có chắc chắn muốn xóa kỳ thi “${chosen.title}”? Đề sẽ không còn truy cập được và không tính vào điểm khóa học.`} run={async()=>{await request(`/api/coding-exams/${chosen.id}`,"DELETE");setSelected(0);await load()}}/>}
      {chosen &&
        (teacher ? (
          <ExamEditor key={chosen.id} exam={chosen} onChange={load} />
        ) : (
          <ExamPlayer key={chosen.id} exam={chosen} />
        ))}
    </div>
  );
}
