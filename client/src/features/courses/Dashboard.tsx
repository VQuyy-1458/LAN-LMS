"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiRequest } from "@/lib/api";
import { date, type Course, type Event, type Exam } from "@/lib/lms";
import Feedback from "@/components/Feedback";
import { useRealtime } from "@/components/Realtime";
type Assignment = {
  id: number;
  course_id: number;
  title: string;
  due_at: string;
  submitted?: boolean;
};
type DashboardData = {
  full_name: string;
  courses: Course[];
  stats: Record<string, number>;
  events: Event[];
  exams: Exam[];
  assignments: Assignment[];
};
type CalendarEntry = {
  key: string;
  title: string;
  at: string;
  course_id: number;
  kind: string;
};
const dayKey = (d: Date) =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Ho_Chi_Minh",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(d);
export default function Dashboard({ teacher = false }: { teacher?: boolean }) {
  const [data, setData] = useState<DashboardData | null>(null),
    [error, setError] = useState(""),
    [search, setSearch] = useState(""),
    [term, setTerm] = useState("all");
  const [month, setMonth] = useState(
      () => new Date(new Date().getFullYear(), new Date().getMonth(), 1),
    ),
    [chosen, setChosen] = useState(() => dayKey(new Date()));
  const { revision } = useRealtime(),
    role = teacher ? "teacher" : "student";
  const load = useCallback(
    () =>
      apiRequest<DashboardData>("/api/dashboard")
        .then((r) => {
          setData(r);
          setError("");
        })
        .catch((e) => setError(e.message)),
    [],
  );
  useEffect(() => {
    void load();
  }, [load, revision]);
  const entries = useMemo<CalendarEntry[]>(
    () =>
      data
        ? [
            ...data.events.map((e) => ({
              key: `e${e.id}`,
              title: e.title,
              at: e.starts_at,
              course_id: e.course_id,
              kind: e.event_type === "announcement" ? "Thông báo" : "Lịch học",
            })),
            ...data.exams.map((e) => ({
              key: `x${e.id}`,
              title: e.title,
              at: e.starts_at,
              course_id: e.course_id,
              kind: "Thi lập trình",
            })),
            ...data.assignments.map((a) => ({
              key: `a${a.id}`,
              title: a.title,
              at: a.due_at,
              course_id: a.course_id,
              kind: "Hạn nộp bài",
            })),
          ].sort((a, b) => a.at.localeCompare(b.at))
        : [],
    [data],
  );
  const selectedEvents = entries.filter(
      (e) => dayKey(new Date(e.at)) === chosen,
    ),
    days = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate(),
    offset = (month.getDay() + 6) % 7;
  const terms = [
    ...new Set(data?.courses.map((c) => `${c.semester}|${c.academic_year}`)),
  ];
  const courses =
    data?.courses.filter(
      (c) =>
        (term === "all" || `${c.semester}|${c.academic_year}` === term) &&
        `${c.name} ${c.course_code}`
          .toLowerCase()
          .includes(search.toLowerCase()),
    ) ?? [];
  if (!data)
    return (
      <>
        <Feedback error={error} />
        <div className="loading">
          Đang tải không gian học tập…
          {error && <button onClick={load}>Thử lại</button>}
        </div>
      </>
    );
  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            {teacher ? "TEACHING SPACE" : "MY LEARNING"}
          </div>
          <h1>{teacher ? "Không gian giảng dạy" : "Không gian học tập"}</h1>
          <p>
            {date(new Date().toISOString(), {
              dateStyle: "full",
              timeStyle: undefined,
            })}
          </p>
        </div>
        <Link className="button-link" href={`/${role}/courses`}>
          Xem khóa học →
        </Link>
      </div>
      <Feedback error={error} />
      <section className="welcome">
        <div>
          <h2>Chào mừng {data.full_name} quay lại!</h2>
          <p>
            {teacher
              ? "Sẵn sàng cho một buổi học hiệu quả."
              : "Mỗi ngày một bước tiến trên hành trình học tập."}
          </p>
          <span className="badge" style={{ marginTop: 14 }}>
            Học tập trong mạng LAN
          </span>
        </div>
        <div className="welcome-stats">
          <div>
            <strong>{data.stats.courses}</strong>
            <span>Khóa học {teacher ? "phụ trách" : "tham gia"}</span>
          </div>
          <div>
            <strong>
              {teacher ? data.stats.students : data.stats.submitted}
            </strong>
            <span>{teacher ? "Sinh viên" : "Bài tập đã nộp"}</span>
          </div>
          <div>
            <strong>
              {teacher ? data.stats.awaiting_grades : data.stats.upcoming_exams}
            </strong>
            <span>{teacher ? "Bài cần chấm" : "Kỳ thi đang / sắp mở"}</span>
          </div>
        </div>
      </section>
      <div className="grid-2">
        <section className="panel">
          <div className="calendar-head">
            <h2>
              Tháng {month.getMonth() + 1}/{month.getFullYear()}
            </h2>
            <div>
              <button
                className="ghost"
                aria-label="Tháng trước"
                onClick={() =>
                  setMonth(
                    new Date(month.getFullYear(), month.getMonth() - 1, 1),
                  )
                }
              >
                ‹
              </button>
              <button
                className="ghost"
                aria-label="Tháng sau"
                onClick={() =>
                  setMonth(
                    new Date(month.getFullYear(), month.getMonth() + 1, 1),
                  )
                }
              >
                ›
              </button>
            </div>
          </div>
          <div className="calendar-grid">
            {["T2", "T3", "T4", "T5", "T6", "T7", "CN"].map((d) => (
              <span key={d}>{d}</span>
            ))}
            {Array.from({ length: offset }, (_, i) => (
              <span key={`empty${i}`} />
            ))}
            {Array.from({ length: days }, (_, i) => {
              const d = new Date(
                  month.getFullYear(),
                  month.getMonth(),
                  i + 1,
                  12,
                ),
                key = dayKey(d);
              return (
                <button
                  key={i}
                  onClick={() => setChosen(key)}
                  className={[
                    chosen === key ? "chosen" : "",
                    key === dayKey(new Date()) ? "today" : "",
                    entries.some((e) => dayKey(new Date(e.at)) === key)
                      ? "has-events"
                      : "",
                  ].join(" ")}
                >
                  {i + 1}
                </button>
              );
            })}
          </div>
          <p className="calendar-legend">
            ● Có hoạt động · Chọn ngày để xem lịch
          </p>
        </section>
        <section className="panel">
          <div className="panel-header">
            Lịch ngày {chosen.split("-").reverse().join("/")}
          </div>
          {selectedEvents.length ? (
            selectedEvents.map((e) => (
              <Link href={`/${role}/courses?course=${e.course_id}`} key={e.key}>
                <div className="event-item">
                  <span className="badge">{e.kind}</span>
                  <h3 style={{ marginTop: 5 }}>{e.title}</h3>
                  <small>
                    {date(e.at)} ·{" "}
                    {
                      data.courses.find((c) => c.id === e.course_id)
                        ?.course_code
                    }
                  </small>
                </div>
              </Link>
            ))
          ) : (
            <div className="empty">
              <span className="empty-symbol">▤</span>Chưa có hoạt động vào ngày
              này.
              <p className="section-note">
                Chọn ngày có dấu chấm để xem lịch và hạn nộp.
              </p>
            </div>
          )}
        </section>
      </div>
      <section>
        <div className="panel-title">
          <h2>{teacher ? "Khóa học phụ trách" : "Khóa học của tôi"}</h2>
          <span className="muted">{courses.length} khóa học</span>
        </div>
        <div className="toolbar">
          <input
            aria-label="Tìm khóa học"
            placeholder="Tìm tên hoặc mã khóa học…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            aria-label="Học kỳ"
            style={{ maxWidth: 260 }}
            value={term}
            onChange={(e) => setTerm(e.target.value)}
          >
            <option value="all">Tất cả học kỳ</option>
            {terms.map((t) => (
              <option key={t} value={t}>
                Học kỳ {t.split("|")[0]} · {t.split("|")[1]}
              </option>
            ))}
          </select>
        </div>
        {courses.length ? (
          <div className="grid-3">
            {courses.map((c) => (
              <Link
                className="panel course-card"
                href={`/${role}/courses?course=${c.id}`}
                key={c.id}
              >
                <div className="course-cover">
                  <small>{c.course_code}</small>
                  <h3>{c.name}</h3>
                </div>
                <div className="course-body">
                  <p>
                    Học kỳ {c.semester} · {c.academic_year}
                  </p>
                  <div className="course-footer">
                    <span>Vào khóa học</span>
                    <span>→</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="empty">
            {search
              ? "Không tìm thấy khóa học phù hợp."
              : "Chưa có khóa học. Danh sách sẽ xuất hiện khi có đăng ký."}
          </div>
        )}
      </section>
    </div>
  );
}
