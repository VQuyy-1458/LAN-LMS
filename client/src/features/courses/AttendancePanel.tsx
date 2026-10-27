"use client";
import {useCourseReadonly} from "@/components/CourseAccess";
import { useCallback, useEffect, useRef, useState } from "react";
import {useListPage} from "@/components/Pagination";
import Image from "next/image";
import Modal from "@/components/Modal";
import { apiRequest } from "@/lib/api";
import { allPages, date, request, type Event } from "@/lib/lms";
import AttendanceScanner from "@/components/AttendanceScanner";
import { parseAttendanceQr } from "@/lib/attendanceQr";
import { courseHref } from "@/lib/courseNavigation";
import { useRealtime } from "@/components/Realtime";
import { useAction } from "@/lib/useAction";
import Feedback from "@/components/Feedback";
type Attendance = {
  event_id?:number|null;
  id: number;
  title: string;
  status: string;
  expires_at: string;
  created_at: string;
  my_status?: string | null;
};
type Created = Attendance & { token: string; qr_svg: string };
type Record = {
  id: number | null;
  student_id: string;
  full_name: string;
  status: string;
  checked_in_at: string | null;
};
export default function AttendancePanel({
  courseId,
  teacher,
  initialSession,
  initialToken,
  lesson,
}: {
  courseId: number;
  teacher: boolean;
  initialSession?: number;
  initialToken?: string;
  lesson?: Event;
}) {
  const readonly=useCourseReadonly();
  const [rows, setRows] = useState<Attendance[]>([]),
    [created, setCreated] = useState<Created | null>(null),
    [selected, setSelected] = useState<number>(initialSession || 0),
    [records, setRecords] = useState<Record[]>([]),
    [recordPage, setRecordPage] = useState(1),
    [recordTotal, setRecordTotal] = useState(0);
  const historyPage=useListPage(rows.length);
  const [lessons, setLessons] = useState<Event[]>([]);
  const [lessonId, setLessonId] = useState(lesson?.id || 0);
  const chosenLesson = lesson || lessons.find((event) => event.id === lessonId);
  const action = useAction();
  const autoCheck = useRef("");
  const { revision } = useRealtime();
  const load = useCallback(async () => {
    setRows(await allPages<Attendance>(`/api/courses/${courseId}/attendance-sessions`));
  }, [courseId]);
  useEffect(() => {
    if (teacher)
      allPages<Event>(`/api/courses/${courseId}/events`)
        .then((events) =>
          setLessons(events.filter((event) => event.event_type === "lesson" && event.attendance_state!=="closed")),
        )
        .catch(action.setError);
  }, [teacher, courseId, action.setError,revision,rows]);
  const loadRecords = useCallback(async () => {
    if (teacher && selected) {
      const records = await allPages<Record>(`/api/attendance-sessions/${selected}/roster`);
      setRecords(records);
      setRecordTotal(records.length);
    }
  }, [selected, teacher]);
  useEffect(() => {
    load().catch(action.setError);
    const timer = setInterval(() => load().catch(() => {}), 15000);
    return () => clearInterval(timer);
  }, [load, action.setError, revision]);
  useEffect(() => {
    loadRecords().catch(action.setError);
    if (!teacher || !selected) return;
    const timer = setInterval(() => loadRecords().catch(() => {}), 5000);
    return () => clearInterval(timer);
  }, [loadRecords, action.setError, teacher, selected, revision]);
  useEffect(() => {
    if (teacher || !initialSession || !initialToken) return;
    const identity = `${initialSession}:${initialToken}`;
    if (autoCheck.current === identity) return;
    autoCheck.current = identity;
    void action.run(async () => {
      const result = await request<Record>(
        `/api/attendance-sessions/${initialSession}/check-in`,
        "POST",
        { token: initialToken },
      );
      await load();
      if (result.status !== "present" && result.status !== "late")
        throw new Error(
          "Giảng viên đã ghi nhận bạn vắng. Vui lòng liên hệ giảng viên để điều chỉnh.",
        );
      window.history.replaceState(
        null,
        "",
        courseHref(false, courseId, "attendance"),
      );
    }, "Điểm danh thành công. Giảng viên đã nhận được kết quả.");
  }, [teacher, initialSession, initialToken, courseId, load, action]);
  useEffect(() => {
    if (chosenLesson)
      document
        .getElementById("attendance-create")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [chosenLesson]);
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      {teacher && !readonly ? (
        <section className="panel" id="attendance-create">
          <h2>
            Tạo QR điểm danh{chosenLesson ? ` · ${chosenLesson.title}` : ""}
          </h2>
          {chosenLesson && (
            <p className="section-note">
              Lịch học: {date(chosenLesson.starts_at)} →{" "}
              {date(chosenLesson.ends_at)}
            </p>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              void action.run(async () => {
                const r = await request<Created>(
                  `/api/courses/${courseId}/attendance-sessions`,
                  "POST",
                  {
                    title: chosenLesson?.title,
                    duration_seconds: Number(f.get("duration_seconds")),
                    event_id: chosenLesson?.id,
                  },
                );
                setCreated(r);
                setSelected(r.id);
                setRecordPage(1);
                await load();
              }, "Đã mở phiên điểm danh.");
            }}
          >
            <div className="form-grid" style={{ marginTop: 15 }}>
              <label>
                Tên buổi học
                <select
                  aria-label="Buổi học để tạo QR"
                  required
                  value={chosenLesson?.id || ""}
                  onChange={(event) => setLessonId(Number(event.target.value))}
                  disabled={!!lesson}
                >
                  <option value="">Chọn buổi học trong lịch</option>
                  {lessons.map((event) => (
                    <option key={event.id} value={event.id}>
                      {date(event.starts_at)} · {event.title}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Thời hạn mã (giây)
                <input
                  name="duration_seconds"
                  type="number"
                  min={60}
                  max={3600}
                  defaultValue={3600}
                  required
                />
              </label>
            </div>
            <div className="actions">
              <button disabled={action.busy || !chosenLesson || rows.some(r=>r.event_id===chosenLesson.id&&r.status==="closed")}>
                Tạo mã QR điểm danh
              </button>
            </div>
          </form>

        </section>
      ) : !teacher ? (
        <section className="panel">
          <h2>Điểm danh buổi học</h2>
          <AttendanceScanner
            disabled={action.busy}
            onScan={(text) => {
              void action.run(async () => {
                const qr = parseAttendanceQr(text);
                const session = await apiRequest<
                  Attendance & { course_id: number }
                >(`/api/attendance-sessions/${qr.sessionId}`);
                const result = await request<Record>(
                  `/api/attendance-sessions/${qr.sessionId}/check-in`,
                  "POST",
                  { token: qr.token },
                );
                if (result.status !== "present" && result.status !== "late")
                  throw new Error(
                    "Giảng viên đã ghi nhận bạn vắng. Vui lòng liên hệ giảng viên để điều chỉnh.",
                  );
                if (session.course_id !== courseId) {
                  window.location.assign(
                    courseHref(false, session.course_id, "attendance"),
                  );
                  return;
                }
                await load();

              }, "Điểm danh thành công. Giảng viên đã nhận được kết quả.");
            }}
          />
          <p className="section-note">
            Quét mã giảng viên đang hiển thị. Hệ thống tự nhận buổi học và ghi
            nhận có mặt.
          </p>
        </section>
      ) : null}
      <section className="panel">
        <h2>Lịch sử điểm danh</h2>
        <div className="table-wrap" style={{ marginTop: 15 }}>
          <table>
            <thead>
              <tr>
                <th>Buổi học</th>
                <th>Thời gian</th>
                <th>Trạng thái</th>
                <th>{teacher ? "Thao tác" : "Kết quả của tôi"}</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(historyPage.start,historyPage.end).map((r) => (
                <tr key={r.id}>
                  <td>
                    #{r.id} · {r.title}
                  </td>
                  <td>
                    {date(r.created_at)}
                    <p className="section-note">Hết hạn {date(r.expires_at)}</p>
                  </td>
                  <td>
                    <span className={`badge ${r.status}`}>
                      {r.status === "open" ? "Đang mở" : "Đã đóng"}
                    </span>
                  </td>
                  <td>
                    {teacher ? (
                      <div className="actions" style={{ marginTop: 0 }}>
                        <button
                          className="secondary"
                          onClick={() => {
                            setSelected(r.id);
                            setRecordPage(1);
                          }}
                        >
                          Danh sách
                        </button>
                        {r.status === "open" && (
                          <button
                            className="secondary"
                            disabled={action.busy}
                            onClick={() =>
                              void action.run(async () => {
                                await request(
                                  `/api/attendance-sessions/${r.id}`,
                                  "PATCH",
                                  { status: "closed" },
                                );
                                await load();
                              }, "Đã đóng phiên.")
                            }
                          >
                            Đóng phiên
                          </button>
                        )}
                      </div>
                    ) : r.my_status === "present" ? (
                      "Đã điểm danh"
                    ) : r.my_status === "late" ? (
                      "Đến muộn"
                    ) : r.my_status === "absent" ? (
                      "Vắng"
                    ) : r.status === "open" ? (
                      "Chưa điểm danh"
                    ) : (
                      "Không có điểm danh"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {historyPage.controls}
        {!rows.length && <div className="empty">Chưa có phiên điểm danh.</div>}
      </section>
      {teacher && selected > 0 && (
        <Modal title={rows.find(r=>r.id===selected)?.title || "Điểm danh buổi học"} onClose={()=>setSelected(0)}>
        <Feedback error={action.error} message={action.message}/>
          {created && created.id === selected && (
            <div className="details-box" style={{ textAlign: "center" }}>
              <h3>{created.title}</h3>
              <div className="qr">
                <Image
                  src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(created.qr_svg)}`}
                  alt="QR điểm danh"
                  width={360}
                  height={360}
                  unoptimized
                />
              </div>
              <p className="section-note">
                Sinh viên mở mục Điểm danh trong khóa học để quét QR này.
              </p>

              <p className="section-note">
                Mã QR có hiệu lực đến {date(created.expires_at)}. Tạo lại mã cho
                cùng buổi học để tiếp tục điểm danh; danh sách đã ghi nhận được
                giữ nguyên.
              </p>
            </div>
          )}
        <p className="section-note">Đã có mặt: {records.filter(r=>["present","late"].includes(r.status)).length}/{recordTotal}. {rows.find(s=>s.id===selected)?.status==="open"?"Danh sách chỉ còn sinh viên chưa có mặt.":"Đã chốt. Danh sách chỉ được xem."}</p>
        <section>
          <div className="panel-title">
            <h2>Điểm danh phiên #{selected}</h2>
            <button
              className="secondary"
              onClick={() => void action.run(loadRecords, "")}
            >
              Làm mới
            </button>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Mã SV</th>
                  <th>Họ tên</th>
                  <th>Kết quả</th>
                  <th>Thời gian</th>
                </tr>
              </thead>
              <tbody>
                {records.filter(r=>rows.find(s=>s.id===selected)?.status!=="open" || !["present","late"].includes(r.status)).slice((recordPage-1)*10,recordPage*10).map((r) => (
                  <tr key={r.student_id}>
                    <td>{r.student_id}</td>
                    <td>{r.full_name}</td>
                    <td>
                      <p className="section-note">
                        {r.status === "present"
                          ? "Có mặt"
                          : r.status === "late"
                            ? "Đến muộn"
                            : r.status === "absent"
                              ? "Vắng"
                              : "Chưa điểm danh"}
                      </p>
                      {!readonly && rows.find(s=>s.id===selected)?.status==="open" && <div
                        className="actions"
                        role="group"
                        aria-label={`Điểm danh ${r.student_id}`}
                      >
                        {(
                          [
                            ["present", "Có mặt"],
                            ["late", "Đến muộn"],
                            ["absent", "Vắng"],
                          ] as const
                        ).map(([status, label]) => (
                          <button
                            key={status}
                            type="button"
                            className={r.status === status ? "" : "secondary"}
                            aria-pressed={r.status === status}
                            disabled={action.busy}
                            onClick={() =>
                              void action.run(async () => {
                                await request(
                                  `/api/attendance-sessions/${selected}/records`,
                                  "PATCH",
                                  {
                                    student_id: r.student_id,
                                    status,
                                    reason:
                                      "Giảng viên điểm danh thủ công tại lớp",
                                  },
                                );
                                await loadRecords();
                              }, `Đã ghi nhận ${r.full_name}: ${label.toLowerCase()}.`)
                            }
                          >
                            {label}
                          </button>
                        ))}
                      </div>}
                    </td>
                    <td>{date(r.checked_in_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="actions">
            <button
              className="secondary"
              disabled={recordPage === 1}
              onClick={() => setRecordPage((x) => x - 1)}
            >
              Trước
            </button>
            <span>Trang {recordPage}</span>
            <button
              className="secondary"
              disabled={recordPage * 10 >= records.filter(r=>rows.find(s=>s.id===selected)?.status!=="open" || !["present","late"].includes(r.status)).length}
              onClick={() => setRecordPage((x) => x + 1)}
            >
              Sau
            </button>
          </div>
          {!readonly && rows.find(s=>s.id===selected)?.status==="open" && <details style={{ marginTop: 20 }}>
            <summary>Điều chỉnh có lý do</summary>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                void action.run(async () => {
                  await request(
                    `/api/attendance-sessions/${selected}/records`,
                    "PATCH",
                    {
                      student_id: f.get("student_id"),
                      status: f.get("status"),
                      reason: f.get("reason"),
                    },
                  );
                  await loadRecords();
                }, "Đã cập nhật và lưu nhật ký điều chỉnh.");
              }}
            >
              <div className="form-grid">
                <label>
                  Mã sinh viên
                  <input name="student_id" required />
                </label>
                <label>
                  Trạng thái
                  <select name="status">
                    <option value="present">Có mặt</option>
                    <option value="absent">Vắng</option>
                    <option value="late">Đến muộn</option>
                  </select>
                </label>
                <label className="full">
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
          </details>}
          {!readonly && rows.find(r=>r.id===selected)?.status==="open" && <button className="danger" disabled={action.busy} onClick={()=>void action.run(async()=>{
            await request(`/api/attendance-sessions/${selected}`,"PATCH",{status:"closed"});
            await load(); await loadRecords();setCreated(null);
          },"Đã đóng phiên. Sinh viên chưa điểm danh được tính vắng.")}>Kết thúc phiên điểm danh</button>}
        </section>
        </Modal>
      )}
    </div>
  );
}
