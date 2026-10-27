"use client";
import { useCallback, useEffect, useState } from "react";
import {
  allPages,
  date,
  localInput,
  localISO,
  request,
  type Event,
} from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import WeeklySchedule from "@/components/WeeklySchedule";
import PaginatedList from "@/components/Pagination";
import {useCourseReadonly} from "@/components/CourseAccess";
import Feedback from "@/components/Feedback";
import {useRealtime} from "@/components/Realtime";
function EventForm({
  event,
  save,
  busy,
}: {
  event?: Event;
  save: (body: unknown, form: HTMLFormElement) => void;
  busy: boolean;
}) {
  const [defaults] = useState(() => ({
    start: localInput(event?.starts_at || new Date().toISOString()),
    end: localInput(
      event?.ends_at || new Date(Date.now() + 3600000).toISOString(),
    ),
  }));
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const f = new FormData(e.currentTarget);
        save(
          {
            title: f.get("title"),
            description: f.get("description"),
            event_type: f.get("event_type"),
            starts_at: localISO(String(f.get("starts_at"))),
            ends_at: localISO(String(f.get("ends_at"))),
          },
          e.currentTarget,
        );
      }}
    >
      <div className="form-grid">
        <label>
          Tên hoạt động
          <input
            name="title"
            defaultValue={event?.title}
            required
            maxLength={200}
          />
        </label>
        <label>
          Loại
          <select
            name="event_type"
            defaultValue={event?.event_type || "lesson"}
          >
            <option value="lesson">Lịch học</option>
            <option value="announcement">Thông báo</option>
          </select>
        </label>
        <label>
          Bắt đầu
          <input
            type="datetime-local"
            name="starts_at"
            required
            defaultValue={defaults.start}
          />
        </label>
        <label>
          Kết thúc
          <input
            type="datetime-local"
            name="ends_at"
            required
            defaultValue={defaults.end}
          />
        </label>
        <label className="full">
          Nội dung
          <textarea
            name="description"
            defaultValue={event?.description}
            maxLength={10000}
          />
        </label>
      </div>
      <div className="actions">
        <button disabled={busy}>
          {event ? "Lưu thay đổi" : "Tạo hoạt động"}
        </button>
      </div>
    </form>
  );
}
export default function CalendarPanel({
  courseId,
  teacher,
  onAttendance,
}: {
  courseId: number;
  teacher: boolean;
  onAttendance?: (event: Event) => void;
}) {
  const [rows, setRows] = useState<Event[]>([]);
  const readonly=useCourseReadonly();
  const {revision}=useRealtime();
  const [filter,setFilter]=useState("all");
  const action = useAction();
  const load = useCallback(async () => {
    setRows(await allPages<Event>(`/api/courses/${courseId}/events`));
  }, [courseId]);
  useEffect(() => {
    load().catch(action.setError);
    const timer=setInterval(()=>void load().catch(()=>{}),15000);
    return()=>clearInterval(timer);
  }, [load, action.setError,revision]);
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      {teacher && !readonly && (
        <section className="panel">
          <details>
            <summary>Thêm lịch hoặc thông báo</summary>
            <EventForm
              busy={action.busy}
              save={(body, form) =>
                void action.run(async () => {
                  await request(
                    `/api/courses/${courseId}/events`,
                    "POST",
                    body,
                  );
                  form.reset();
                  await load();
                })
              }
            />
          </details>
        </section>
      )}
      <WeeklySchedule
        entries={rows.map((event) => ({
          key: String(event.id),
          title: event.title,
          at: event.starts_at,
          kind:
            event.event_type === "lesson"
              ? "Lịch học"
              : event.event_type === "exam"
                ? "Lịch thi"
                : "Sự kiện",
          href: `/${teacher ? "teacher" : "student"}/courses?course=${courseId}&tab=calendar`,
        }))}
      />
      <nav className="tabs" aria-label="Lọc lịch">{[["all","Tổng số"],["lesson","Lịch học"],["exam","Lịch thi"],["deadline","Hạn bài tập"]].map(([value,label])=><button key={value} className={filter===value?"active":""} onClick={()=>setFilter(value)}>{label} ({rows.filter(e=>value==="all"||e.event_type===value).length})</button>)}</nav>
      <PaginatedList key={filter}>
      {rows.filter(e=>filter==="all"||e.event_type===filter).map((e) => (
        <section className="panel" key={e.id}>
          <span className="badge">
            {
              {
                lesson: "Lịch học",
                exam: "Lịch thi",
                deadline: "Hạn nộp",
                announcement: "Thông báo",
              }[e.event_type]
            }
          </span>
          <h2 style={{ marginTop: 10 }}>{e.title}</h2>
          <p className="section-note">
            {date(e.starts_at)} → {date(e.ends_at)}
          </p>
          <p className="statement" style={{ marginTop: 14 }}>
            {e.description}
          </p>
          {teacher && !readonly && e.event_type === "lesson" && e.attendance_state!=="closed" && onAttendance && (
            <div className="actions">
              <button onClick={() => onAttendance(e)}>
                Tạo QR điểm danh buổi học này
              </button>
            </div>
          )}
          {teacher && !readonly && e.editable!==false && !e.attendance_state && (
            <details style={{ marginTop: 18 }}>
              <summary>Chỉnh sửa / Xóa</summary>
              <EventForm
                event={e}
                busy={action.busy}
                save={(body) =>
                  void action.run(async () => {
                    await request(`/api/events/${e.id}`, "PUT", body);
                    await load();
                  })
                }
              />
              <div className="actions">
                <button
                  className="danger"
                  disabled={action.busy}
                  onClick={() => {
                    if (confirm("Xóa hoạt động này khỏi lịch?"))
                      void action.run(async () => {
                        await request(`/api/events/${e.id}`, "DELETE");
                        await load();
                      }, "Đã xóa hoạt động.");
                  }}
                >
                  Xóa hoạt động
                </button>
              </div>
            </details>
          )}
        </section>
      ))}
      </PaginatedList>
      {!rows.length && (
        <div className="empty">Chưa có lịch hoặc thông báo.</div>
      )}
    </div>
  );
}
