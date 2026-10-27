"use client";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { date } from "@/lib/lms";
import { useRealtime } from "@/components/Realtime";
type Overview = {
  students: number;
  materials: number;
  assignments: number;
  exams: number;
  submitted_assignments: number | null;
  awaiting_grades: number | null;
  upcoming: {
    id: number;
    title: string;
    starts_at: string;
    event_type: string;
  }[];
};
export default function CourseOverview({
  courseId,
  teacher,
  open,
}: {
  courseId: number;
  teacher: boolean;
  open: (
    tab: "students" | "materials" | "assignments" | "exams" | "calendar",
  ) => void;
}) {
  const [data, setData] = useState<Overview | null>(null),
    [error, setError] = useState("");
  const { revision } = useRealtime();
  const load = useCallback(async () => {
    setData(await apiRequest<Overview>(`/api/courses/${courseId}/overview`));
    setError("");
  }, [courseId]);
  useEffect(() => {
    void load().catch((error) => setError(error.message));
  }, [load, revision]);
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <p role="status">Đang tải tổng quan khóa học…</p>;
  return (
    <div className="stack" style={{ marginTop: 20 }}>
      <div className="grid-3">
        <button
          className="panel overview-card"
          onClick={() => open("materials")}
        >
          <span className="section-note">HỌC LIỆU</span>
          <strong>{data.materials}</strong>
          <span>Tài liệu và file thực hành →</span>
        </button>
        <button
          className="panel overview-card"
          onClick={() => open("assignments")}
        >
          <span className="section-note">BÀI TẬP</span>
          <strong>
            {teacher
              ? data.awaiting_grades
              : `${data.submitted_assignments}/${data.assignments}`}
          </strong>
          <span>
            {teacher ? "Bài nộp đang chờ chấm →" : "Bài tập đã gửi →"}
          </span>
        </button>
        <button className="panel overview-card" onClick={() => open("exams")}>
          <span className="section-note">THI LẬP TRÌNH</span>
          <strong>{data.exams}</strong>
          <span>Đề luyện tập và kỳ thi →</span>
        </button>
      </div>
      <section className="panel">
        <div className="panel-title">
          <h2>Hoạt động sắp tới</h2>
          <button className="ghost" onClick={() => open("calendar")}>
            Xem lịch →
          </button>
        </div>
        {data.upcoming.length ? (
          data.upcoming.map((event) => (
            <div className="course-activity" key={event.id}>
              <span className="badge">
                {event.event_type === "exam" ? "Thi" : "Lịch học"}
              </span>
              <div>
                <strong>{event.title}</strong>
                <p className="section-note">{date(event.starts_at)}</p>
              </div>
            </div>
          ))
        ) : (
          <p className="section-note">
            Chưa có lịch sắp tới.{" "}
            {teacher
              ? "Thêm buổi học hoặc sự kiện trong Lịch & Thông báo."
              : "Theo dõi thông báo của giảng viên."}
          </p>
        )}
        <p className="section-note">
          {data.students} sinh viên đang tham gia khóa học.
        </p>
      </section>
    </div>
  );
}
