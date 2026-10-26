"use client";
import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import { apiRequest } from "@/lib/api";
import { date, request, type Page, type Event } from "@/lib/lms";
import AttendanceScanner from "@/components/AttendanceScanner";
import { parseAttendanceQr } from "@/lib/attendanceQr";
import { useAction } from "@/lib/useAction";
import Feedback from "@/components/Feedback";
type Attendance = {
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
  const [rows, setRows] = useState<Attendance[]>([]),
    [created, setCreated] = useState<Created | null>(null),
    [selected, setSelected] = useState<number>(initialSession || 0),
    [records, setRecords] = useState<Record[]>([]),
    [token, setToken] = useState(initialToken || ""),
    [recordPage, setRecordPage] = useState(1),
    [recordTotal, setRecordTotal] = useState(0);
  const action = useAction();
  const load = useCallback(async () => {
    setRows(
      (
        await apiRequest<Page<Attendance>>(
          `/api/courses/${courseId}/attendance-sessions?page_size=100`,
        )
      ).items,
    );
  }, [courseId]);
  const loadRecords = useCallback(async () => {
    if (teacher && selected) {
      const r = await apiRequest<Page<Record>>(
        `/api/attendance-sessions/${selected}/roster?page=${recordPage}&page_size=50`,
      );
      setRecords(r.items);
      setRecordTotal(r.total);
    }
  }, [selected, teacher, recordPage]);
  useEffect(() => {
    load().catch(action.setError);
    const timer = setInterval(() => load().catch(() => {}), 15000);
    return () => clearInterval(timer);
  }, [load, action.setError]);
  useEffect(() => {
    loadRecords().catch(action.setError);
    if (!teacher || !selected) return;
    const timer = setInterval(() => loadRecords().catch(() => {}), 5000);
    return () => clearInterval(timer);
  }, [loadRecords, action.setError, teacher, selected]);
  useEffect(() => {
    if (lesson)
      document
        .getElementById("attendance-create")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [lesson]);
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      {teacher ? (
        <section className="panel" id="attendance-create">
          <h2>Tạo QR điểm danh{lesson ? ` · ${lesson.title}` : ""}</h2>
          {lesson && (
            <p className="section-note">
              Lịch học: {date(lesson.starts_at)} → {date(lesson.ends_at)}
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
                    title: f.get("title"),
                    duration_seconds: Number(f.get("duration_seconds")),
                    event_id: lesson?.id,
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
                <input
                  name="title"
                  defaultValue={lesson?.title || "Điểm danh buổi học"}
                  readOnly={!!lesson}
                  maxLength={200}
                  required
                />
              </label>
              <label>
                Thời hạn mã (giây)
                <input
                  name="duration_seconds"
                  type="number"
                  min={60}
                  max={3600}
                  defaultValue={300}
                  required
                />
              </label>
            </div>
            <div className="actions">
              <button disabled={action.busy}>Mở phiên điểm danh</button>
            </div>
          </form>
          {created && created.id === selected && (
            <div className="details-box" style={{ textAlign: "center" }}>
              <h3>{created.title}</h3>
              <div className="qr">
                <Image
                  src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(created.qr_svg)}`}
                  alt="QR điểm danh"
                  width={220}
                  height={220}
                  unoptimized
                />
              </div>
              <p className="section-note">
                Sinh viên mở mục Điểm danh trong khóa học để quét QR này.
              </p>
              <p className="token">{created.token}</p>
              <p className="section-note">
                Phiên #{created.id} · Hết hạn {date(created.expires_at)}. Mã chỉ
                hiển thị khi vừa tạo phiên.
              </p>
            </div>
          )}
        </section>
      ) : (
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
                if (session.course_id !== courseId)
                  throw new Error(
                    "QR thuộc khóa học khác. Hãy mở đúng khóa học rồi quét lại.",
                  );
                setSelected(qr.sessionId);
                setToken(qr.token);
                const result = await request<Record>(
                  `/api/attendance-sessions/${qr.sessionId}/check-in`,
                  "POST",
                  { token: qr.token },
                );
                await load();
                if (result.status !== "present" && result.status !== "late")
                  throw new Error(
                    "Giảng viên đã ghi nhận bạn vắng. Vui lòng liên hệ giảng viên để điều chỉnh.",
                  );
              }, "Điểm danh bằng QR thành công.");
            }}
          />
          <p className="section-note">
            Có thể nhập mã khi không sử dụng được camera. Nếu mở từ QR, mã đã
            được điền sẵn.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void action.run(async () => {
                const result = await request<Record>(
                  `/api/attendance-sessions/${selected}/check-in`,
                  "POST",
                  { token },
                );
                await load();
                if (result.status !== "present" && result.status !== "late")
                  throw new Error(
                    "Giảng viên đã ghi nhận bạn vắng. Vui lòng liên hệ giảng viên để điều chỉnh.",
                  );
              }, "Điểm danh thành công.");
            }}
          >
            <div className="form-grid" style={{ marginTop: 15 }}>
              <label>
                Phiên điểm danh
                <select
                  required
                  value={selected || ""}
                  onChange={(e) => setSelected(Number(e.target.value))}
                >
                  <option value="">Chọn buổi học</option>
                  {rows.map((r) => (
                    <option key={r.id} value={r.id}>
                      #{r.id} · {r.title} ·{" "}
                      {r.status === "open" ? "Đang mở" : "Đã đóng"}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Mã điểm danh
                <input
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  required
                  autoComplete="off"
                  maxLength={200}
                />
              </label>
            </div>
            <div className="actions">
              <button disabled={action.busy || !selected}>
                Xác nhận điểm danh
              </button>
            </div>
          </form>
        </section>
      )}
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
              {rows.map((r) => (
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
        {!rows.length && <div className="empty">Chưa có phiên điểm danh.</div>}
      </section>
      {teacher && selected > 0 && (
        <section className="panel">
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
                {records.map((r) => (
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
                      <div
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
                      </div>
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
              disabled={recordPage * 50 >= recordTotal}
              onClick={() => setRecordPage((x) => x + 1)}
            >
              Sau
            </button>
          </div>
          <details style={{ marginTop: 20 }}>
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
          </details>
        </section>
      )}
    </div>
  );
}
