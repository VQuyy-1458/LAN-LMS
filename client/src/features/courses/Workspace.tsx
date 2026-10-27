"use client";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { request, allPages, type Course, type Event } from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import CourseAccess from "@/components/CourseAccess";
import PaginatedList from "@/components/Pagination";
import ConfirmAction from "@/components/ConfirmAction";
import Feedback from "@/components/Feedback";
import CourseOverview from "./CourseOverview";
import CourseTransfer from "./CourseTransfer";
import StudentsPanel from "./StudentsPanel";
import MaterialsPanel from "./MaterialsPanel";
import AssignmentsPanel from "./AssignmentsPanel";
import CalendarPanel from "./CalendarPanel";
import AttendancePanel from "./AttendancePanel";
import ExamsPanel from "./ExamsPanel";
import GradebookPanel from "./GradebookPanel";
import { courseLocation, courseHref } from "@/lib/courseNavigation";
type Tab =
  | "overview"
  | "students"
  | "materials"
  | "calendar"
  | "attendance"
  | "assignments"
  | "exams"
  | "grades";
function CourseForm({
  course,
  save,
  busy,
}: {
  course?: Course;
  save: (body: unknown, form: HTMLFormElement) => void;
  busy: boolean;
}) {
  const [startYear,setStartYear]=useState(Number(course?.academic_year.slice(0,4)||new Date().getFullYear()));
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
            academic_year: `${f.get("year_start")}-${f.get("year_end")}`,
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
          <select name="semester" defaultValue={course?.semester||"1"}><option value="1">Kỳ 1</option><option value="2">Kỳ 2</option><option value="summer">Kỳ hè</option></select>
        </label>
        <label>Năm bắt đầu<select name="year_start" value={startYear} onChange={e=>setStartYear(Number(e.target.value))}>{Array.from({length:16},(_,i)=>2020+i).map(y=><option key={y} value={y}>{y}</option>)}</select></label>
        <label>Năm kết thúc<select name="year_end" value={startYear+1} onChange={()=>{}}><option value={startYear+1}>{startYear+1}</option></select><small>Năm học gồm hai năm liên tiếp.</small></label>
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
  const [semesterFilter,setSemesterFilter]=useState(""),[yearFilter,setYearFilter]=useState("");
  const action = useAction();
  const [attendanceLesson, setAttendanceLesson] = useState<Event | undefined>();
  const load = useCallback(async () => {
    setCourses(await allPages<Course>("/api/courses"));
    setLoaded(true);
  }, []);
  useEffect(() => {
    load().catch(action.setError);
    const syncLocation = () => {
      const q = new URLSearchParams(window.location.search);
      const location = courseLocation(
        window.location.search,
        teacher,
        initialTab,
      );
      setSelected(location.courseId);
      setTab(location.tab);
      setAttendanceLesson(undefined);
      setAttendance(0);
      setToken("");
      if (q.get("attendance")) {
        const id = Number(q.get("attendance"));
        setAttendance(id);
        setToken(q.get("token") || "");
        setTab("attendance");
        apiRequest<{ course_id: number }>(`/api/attendance-sessions/${id}`)
          .then((r) => setSelected(r.course_id))
          .catch(action.setError);
      }
    };
    syncLocation();
    window.addEventListener("popstate", syncLocation);
    window.addEventListener("course-finalized",load);
    return () => window.removeEventListener("popstate", syncLocation);
  }, [load, action.setError, teacher, initialTab]);
  useEffect(() => {
    if (!selected || !loaded || courses.some((c) => c.id === selected)) return;
    let live = true;
    apiRequest<Course>(`/api/courses/${selected}`)
      .then((c) => {
        if (live)
          setCourses((rows) =>
            rows.some((r) => r.id === c.id) ? rows : [...rows, c],
          );
      })
      .catch(action.setError);
    return () => {
      live = false;
    };
  }, [selected, loaded, courses, action.setError]);
  const course = courses.find((c) => c.id === selected),
    filtered = courses.filter((c) =>
      `${c.course_code} ${c.name}`.toLowerCase().includes(search.toLowerCase()) && (!semesterFilter||c.semester===semesterFilter) && (!yearFilter||c.academic_year===yearFilter),
    );
  const choose = (id: number) => {
    setSelected(id);
    setAttendance(0);
    setToken("");
    setAttendanceLesson(undefined);
    setTab("overview");
    window.history.pushState(null, "", courseHref(teacher, id));
    window.dispatchEvent(new Event("course-navigation"));
  };
  const selectTab = (value: Tab) => {
    setTab(value);
    window.history.pushState(null, "", courseHref(teacher, selected, value));
    window.dispatchEvent(new Event("course-navigation"));
  };
  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            {teacher ? "QUẢN LÝ KHÓA HỌC" : "KHÓA HỌC"}
          </div>
          <h1>{course ? course.name : "Khóa học"}</h1>
          <p>
            {course
              ? `${course.course_code} · ${course.semester==="summer"?"Kỳ hè":"Học kỳ "+course.semester} · ${course.academic_year}`
              : teacher
                ? "Chọn khóa học để quản lý sinh viên, lịch học, điểm danh và kỳ thi."
                : "Chọn khóa học để xem tài liệu, quét QR điểm danh và làm bài thi."}
          </p>
        </div>
        {selected > 0 && (
          <button className="secondary" onClick={() => choose(0)}>
            ← Danh sách khóa
          </button>
        )}
      </div>
      <Feedback error={action.error} message={action.message} />
      {!course && !selected && (
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
          {teacher && (
            <CourseTransfer
              imported={async (id) => {
                await load();
                choose(id);
              }}
            />
          )}
          <div className="toolbar">
            <input
              placeholder="Tìm tên hoặc mã khóa học…"
              aria-label="Tìm khóa học"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select aria-label="Lọc học kỳ" value={semesterFilter} onChange={e=>setSemesterFilter(e.target.value)}><option value="">Tất cả học kỳ</option><option value="1">Kỳ 1</option><option value="2">Kỳ 2</option><option value="summer">Kỳ hè</option></select>
            <select aria-label="Lọc năm học" value={yearFilter} onChange={e=>setYearFilter(e.target.value)}><option value="">Tất cả năm học</option>{Array.from(new Set(courses.map(c=>c.academic_year))).sort().map(y=><option key={y}>{y}</option>)}</select>
            <span className="muted">{filtered.length} khóa học</span>
          </div>
          {!loaded ? (
            <div className="loading">Đang tải khóa học…</div>
          ) : filtered.length ? (
            <PaginatedList className="grid-3" key={`${search}-${semesterFilter}-${yearFilter}`}>
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
                      {c.semester==="summer"?"Kỳ hè":"Học kỳ "+c.semester} · {c.academic_year}
                    </p>
                    <div className="course-footer">
                      <span>Mở khóa học</span>
                      <span>→</span>
                    </div>
                  </div>
                </button>
              ))}
            </PaginatedList>
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
        <CourseAccess readonly={course.status==="finalized"}>
          {course.status==="finalized"&&<p className="alert">Khóa học đã tổng kết. Bạn chỉ có thể xem và xuất dữ liệu.</p>}
          {teacher && tab === "overview" && (
            <CourseTransfer courseId={course.id} />
          )}
          <div key={course.id}>
            {tab === "overview" && (
              <>
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
                  {teacher && course.status!=="finalized" && (
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
                  {teacher&&course.status!=="finalized"&&<div className="actions"><ConfirmAction label="Xóa khóa học" message="Bạn có chắc chắn muốn xóa khóa học này? Khóa học sẽ bị ẩn khỏi giảng viên và sinh viên." run={async()=>{await request(`/api/courses/${course.id}`,"DELETE");choose(0);await load()}}/></div>}
                  <p className="section-note" style={{ marginTop: 24 }}>
                    Chọn chức năng trong nhánh Khóa học ở thanh điều hướng bên trái.
                  </p>
                </section>
                <CourseOverview
                  courseId={course.id}
                  teacher={teacher}
                  open={selectTab}
                />
              </>
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
                  selectTab("attendance");
                }}
              />
            )}
            {tab === "attendance" && (
              <div className="stack">
                {teacher && (
                  <div className="panel">
                    <h2>Điểm danh theo buổi học</h2>
                    <p className="section-note">
                      Tạo hoặc chọn buổi học trong Lịch & Thông báo, sau đó tạo
                      mã QR. Chọn đúng buổi học để tạo mã và theo dõi danh sách
                      điểm danh.
                    </p>
                    <button
                      className="secondary"
                      onClick={() => selectTab("calendar")}
                    >
                      Mở lịch học →
                    </button>
                  </div>
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
        </CourseAccess>
      )}
      {selected > 0 && !course && !action.error && (
        <p role="status">Đang tải khóa học…</p>
      )}
    </div>
  );
}
