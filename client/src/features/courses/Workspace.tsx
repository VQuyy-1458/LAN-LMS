"use client";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { request, type Course, type Page, type Event } from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import Feedback from "@/components/Feedback";
import StudentsPanel from "./StudentsPanel";
import MaterialsPanel from "./MaterialsPanel";
import AssignmentsPanel from "./AssignmentsPanel";
import CalendarPanel from "./CalendarPanel";
import AttendancePanel from "./AttendancePanel";
import ExamsPanel from "./ExamsPanel";
import GradebookPanel from "./GradebookPanel";
type Tab =
  | "overview"
  | "students"
  | "materials"
  | "calendar"
  | "attendance"
  | "assignments"
  | "exams"
  | "grades";
const tabs: [Tab, string][] = [
  ["overview", "Tổng quan"],
  ["students", "Sinh viên"],
  ["materials", "Tài liệu"],
  ["calendar", "Lịch & Thông báo"],
  ["attendance", "Điểm danh"],
  ["assignments", "Bài tập"],
  ["exams", "Thi lập trình"],
  ["grades", "Bảng điểm"],
];
function CourseForm({
  course,
  save,
  busy,
}: {
  course?: Course;
  save: (body: unknown, form: HTMLFormElement) => void;
  busy: boolean;
}) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const f = new FormData(e.currentTarget);
        save(
          {
            course_code: f.get("course_code"),
            name: f.get("name"),
            semester: f.get("semester"),
            academic_year: f.get("academic_year"),
            description: f.get("description"),
            start_date: f.get("start_date") || null,
            end_date: f.get("end_date") || null,
          },
          e.currentTarget,
        );
      }}
    >
      <div className="form-grid">
        <label>
          Mã khóa học
          <input
            name="course_code"
            required
            defaultValue={course?.course_code}
            maxLength={128}
          />
        </label>
        <label>
          Tên khóa học
          <input
            name="name"
            required
            defaultValue={course?.name}
            maxLength={200}
          />
        </label>
        <label>
          Học kỳ
          <input
            name="semester"
            required
            defaultValue={course?.semester || "1"}
          />
        </label>
        <label>
          Năm học
          <input
            name="academic_year"
            required
            defaultValue={course?.academic_year || "2026-2027"}
          />
        </label>
        <label>
          Bắt đầu
          <input
            type="date"
            name="start_date"
            defaultValue={course?.start_date || ""}
          />
        </label>
        <label>
          Kết thúc
          <input
            type="date"
            name="end_date"
            defaultValue={course?.end_date || ""}
          />
        </label>
        <label className="full">
          Mô tả
          <textarea
            name="description"
            defaultValue={course?.description}
            maxLength={10000}
          />
        </label>
      </div>
      <div className="actions">
        <button disabled={busy}>
          {course ? "Lưu thông tin" : "Tạo khóa học"}
        </button>
      </div>
    </form>
  );
}
export default function Workspace({
  teacher = false,
  initialTab = "overview",
}: {
  teacher?: boolean;
  initialTab?: Tab;
}) {
  const [courses, setCourses] = useState<Course[]>([]),
    [selected, setSelected] = useState(0),
    [tab, setTab] = useState<Tab>(initialTab),
    [search, setSearch] = useState(""),
    [attendance, setAttendance] = useState(0),
    [token, setToken] = useState(""),
    [loaded, setLoaded] = useState(false);
  const action = useAction();
  const [attendanceLesson, setAttendanceLesson] = useState<Event | undefined>();
  const load = useCallback(async () => {
    const r = await apiRequest<Page<Course>>("/api/courses?page_size=100");
    setCourses(r.items);
    setLoaded(true);
  }, []);
  useEffect(() => {
    load().catch(action.setError);
    const q = new URLSearchParams(window.location.search);
    if (q.get("course")) setSelected(Number(q.get("course")));
    if (q.get("attendance")) {
      const id = Number(q.get("attendance"));
      setAttendance(id);
      setToken(q.get("token") || "");
      setTab("attendance");
      apiRequest<{ course_id: number }>(`/api/attendance-sessions/${id}`)
        .then((r) => setSelected(r.course_id))
        .catch(action.setError);
    }
  }, [load, action.setError]);
  const course = courses.find((c) => c.id === selected),
    filtered = courses.filter((c) =>
      `${c.course_code} ${c.name}`.toLowerCase().includes(search.toLowerCase()),
    );
  const choose = (id: number) => {
    setSelected(id);
    setAttendance(0);
    setToken("");
    setAttendanceLesson(undefined);
    window.history.replaceState(
      null,
      "",
      `${window.location.pathname}${id ? `?course=${id}` : ""}`,
    );
  };
  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            {teacher ? "COURSE MANAGEMENT" : "MY COURSES"}
          </div>
          <h1>
            {course
              ? course.name
              : initialTab === "overview"
                ? "Khóa học"
                : tabs.find(([k]) => k === initialTab)?.[1]}
          </h1>
          <p>
            {course
              ? `${course.course_code} · Học kỳ ${course.semester} · ${course.academic_year}`
              : teacher
                ? "Quản lý nội dung học tập và hoạt động của lớp."
                : "Tài liệu, bài tập và hoạt động trong các khóa học của bạn."}
          </p>
        </div>
        {selected > 0 && (
          <button className="secondary" onClick={() => choose(0)}>
            ← Danh sách khóa
          </button>
        )}
      </div>
      <Feedback error={action.error} message={action.message} />
      {!course && (
        <>
          {teacher && (
            <section className="panel">
              <details>
                <summary>Tạo khóa học mới</summary>
                <CourseForm
                  busy={action.busy}
                  save={(body, form) =>
                    void action.run(async () => {
                      const c = await request<Course>(
                        "/api/courses",
                        "POST",
                        body,
                      );
                      form.reset();
                      await load();
                      choose(c.id);
                      setTab("overview");
                    }, "Đã tạo khóa học.")
                  }
                />
              </details>
            </section>
          )}
          <div className="toolbar">
            <input
              placeholder="Tìm tên hoặc mã khóa học…"
              aria-label="Tìm khóa học"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <span className="muted">{courses.length} khóa học</span>
          </div>
          {!loaded ? (
            <div className="loading">Đang tải khóa học…</div>
          ) : filtered.length ? (
            <div className="grid-3">
              {filtered.map((c) => (
                <button
                  className="panel course-card"
                  style={{ textAlign: "left" }}
                  key={c.id}
                  onClick={() => choose(c.id)}
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
                      <span>Mở khóa học</span>
                      <span>→</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="empty">
              {search
                ? "Không có khóa học phù hợp."
                : "Chưa có khóa học trong danh sách."}
            </div>
          )}
        </>
      )}
      {course && (
        <>
          <nav className="tabs" aria-label="Nội dung khóa học">
            {tabs
              .filter(([k]) => teacher || k !== "students")
              .map(([k, n]) => (
                <button
                  key={k}
                  className={tab === k ? "active" : ""}
                  onClick={() => setTab(k)}
                >
                  {n}
                </button>
              ))}
          </nav>
          <div key={course.id}>
            {tab === "overview" && (
              <section className="panel">
                <div className="panel-title">
                  <h2>Thông tin khóa học</h2>
                  <span className="badge">{course.course_code}</span>
                </div>
                <p className="statement">
                  {course.description || "Chưa có mô tả khóa học."}
                </p>
                <p className="section-note">
                  Thời gian: {course.start_date || "Chưa đặt"} →{" "}
                  {course.end_date || "Chưa đặt"}
                </p>
                {teacher && (
                  <details style={{ marginTop: 24 }}>
                    <summary>Sửa thông tin khóa học</summary>
                    <CourseForm
                      key={JSON.stringify(course)}
                      course={course}
                      busy={action.busy}
                      save={(body) =>
                        void action.run(async () => {
                          await request(
                            `/api/courses/${course.id}`,
                            "PATCH",
                            body,
                          );
                          await load();
                        })
                      }
                    />
                  </details>
                )}
                <div className="grid-3" style={{ marginTop: 24 }}>
                  {tabs
                    .filter(([k]) => !["overview", "students"].includes(k))
                    .map(([k, n]) => (
                      <button
                        className="button-link"
                        key={k}
                        onClick={() => setTab(k)}
                      >
                        {n} →
                      </button>
                    ))}
                </div>
              </section>
            )}
            {tab === "students" && teacher && (
              <StudentsPanel courseId={course.id} />
            )}
            {tab === "materials" && (
              <MaterialsPanel courseId={course.id} teacher={teacher} />
            )}
            {tab === "calendar" && (
              <CalendarPanel
                courseId={course.id}
                teacher={teacher}
                onAttendance={(event) => {
                  setAttendanceLesson(event);
                  setTab("attendance");
                }}
              />
            )}
            {tab === "attendance" && (
              <div className="stack">
                {teacher && (
                  <CalendarPanel
                    courseId={course.id}
                    teacher={teacher}
                    onAttendance={(event) => setAttendanceLesson(event)}
                  />
                )}
                <AttendancePanel
                  key={attendanceLesson?.id || "attendance"}
                  courseId={course.id}
                  teacher={teacher}
                  lesson={attendanceLesson}
                  initialSession={attendance}
                  initialToken={token}
                />
              </div>
            )}
            {tab === "assignments" && (
              <AssignmentsPanel courseId={course.id} teacher={teacher} />
            )}
            {tab === "exams" && (
              <ExamsPanel courseId={course.id} teacher={teacher} />
            )}
            {tab === "grades" && (
              <GradebookPanel courseId={course.id} teacher={teacher} />
            )}
          </div>
        </>
      )}
    </div>
  );
}
