"use client";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { apiRequest } from "@/lib/api";
import { date, key, localInput, localISO, request, type Page } from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import Feedback from "@/components/Feedback";
type Assignment = {
  id: number;
  title: string;
  description: string;
  due_at: string;
  allow_resubmit: boolean;
};
type FileSub = {
  id: number;
  student_id: string;
  original_filename: string;
  received_at: string;
  score: number | null;
  feedback: string | null;
};
function AssignmentForm({
  initial,
  save,
  busy,
}: {
  initial?: Assignment;
  save: (body: unknown, form: HTMLFormElement) => void;
  busy: boolean;
}) {
  const [defaultDue] = useState(() =>
    localInput(
      initial?.due_at || new Date(Date.now() + 86400000).toISOString(),
    ),
  );
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const f = new FormData(e.currentTarget);
        save(
          {
            title: f.get("title"),
            description: f.get("description"),
            due_at: localISO(String(f.get("due_at"))),
            allow_resubmit: f.get("allow_resubmit") === "on",
          },
          e.currentTarget,
        );
      }}
    >
      <div className="form-grid">
        <label>
          Tên bài tập
          <input
            name="title"
            defaultValue={initial?.title}
            required
            maxLength={200}
          />
        </label>
        <label>
          Hạn nộp
          <input
            name="due_at"
            type="datetime-local"
            defaultValue={defaultDue}
            required
          />
        </label>
        <label className="full">
          Nội dung bài tập
          <textarea
            name="description"
            defaultValue={initial?.description}
            maxLength={20000}
          />
        </label>
        <label className="check-label">
          <input
            type="checkbox"
            name="allow_resubmit"
            defaultChecked={initial?.allow_resubmit ?? true}
          />
          Cho phép nộp lại trước hạn
        </label>
      </div>
      <div className="actions">
        <button disabled={busy}>
          {initial ? "Lưu bài tập" : "Tạo bài tập"}
        </button>
      </div>
    </form>
  );
}
function AssignmentCard({
  assignment: a,
  teacher,
  reload,
}: {
  assignment: Assignment;
  teacher: boolean;
  reload: () => Promise<void>;
}) {
  const [rows, setRows] = useState<FileSub[]>([]),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0),
    [open, setOpen] = useState(false);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  const action = useAction(),
    retry = useRef<{ file: File; key: string } | null>(null);
  const load = useCallback(async () => {
    const r = await apiRequest<Page<FileSub>>(
      `/api/assignments/${a.id}/submissions?page=${page}&page_size=30`,
    );
    setRows(r.items);
    setTotal(r.total);
  }, [a.id, page]);
  useEffect(() => {
    if (open) load().catch(action.setError);
  }, [open, load, action.setError]);
  function upload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget,
      f = new FormData(form),
      file = f.get("file") as File;
    if (!retry.current) retry.current = { file, key: key() };
    const k = retry.current.key;
    void action.run(async () => {
      await apiRequest(`/api/assignments/${a.id}/submissions`, {
        method: "POST",
        body: f,
        headers: { "Idempotency-Key": k },
      });
      retry.current = null;
      form.reset();
      setOpen(true);
      await load();
    }, "Đã nhận bài nộp. Bạn có thể tải lại file để kiểm tra.");
  }
  return (
    <section className="panel">
      <div className="panel-title">
        <div>
          <h2>{a.title}</h2>
          <p className="section-note">
            Hạn nộp: {date(a.due_at)} ·{" "}
            {a.allow_resubmit ? "Được nộp lại" : "Chỉ nộp một lần"}
          </p>
        </div>
        <span className="badge">
          {new Date(a.due_at).getTime() < now ? "Đã hết hạn" : "Đang nhận bài"}
        </span>
      </div>
      <p className="statement">
        {a.description || "Giảng viên chưa thêm mô tả."}
      </p>
      <Feedback error={action.error} message={action.message} />
      {teacher ? (
        <details style={{ marginTop: 18 }}>
          <summary>Chỉnh sửa bài tập</summary>
          <AssignmentForm
            initial={a}
            busy={action.busy}
            save={(body) =>
              void action.run(async () => {
                await request(`/api/assignments/${a.id}`, "PATCH", body);
                await reload();
              })
            }
          />
        </details>
      ) : (
        <form onSubmit={upload} style={{ marginTop: 20 }}>
          <label>
            Chọn bài nộp
            <input
              name="file"
              type="file"
              accept=".pdf,.docx,.txt,.zip,.c,.cpp,.java"
              required
              onChange={() => {
                retry.current = null;
              }}
            />
          </label>
          <p className="section-note">
            Tối đa 20 MiB. Hệ thống lưu lịch sử các lần nộp hợp lệ.
          </p>
          <div className="actions">
            <button
              disabled={action.busy || new Date(a.due_at).getTime() < now}
            >
              Nộp bài tập
            </button>
          </div>
        </form>
      )}
      <div className="actions">
        <button className="secondary" onClick={() => setOpen((v) => !v)}>
          {open
            ? "Ẩn lịch sử"
            : teacher
              ? "Xem bài nộp của lớp"
              : "Xem lịch sử nộp"}
        </button>
      </div>
      {open && (
        <>
          <div className="table-wrap" style={{ marginTop: 16 }}>
            <table>
              <thead>
                <tr>
                  <th>Sinh viên</th>
                  <th>Bài nộp</th>
                  <th>Thời gian</th>
                  <th>Điểm / Nhận xét</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td>{r.student_id}</td>
                    <td>
                      <a
                        className="download"
                        href={`/api/assignment-submissions/${r.id}/download`}
                      >
                        {r.original_filename} ↓
                      </a>
                    </td>
                    <td>{date(r.received_at)}</td>
                    <td>
                      {teacher ? (
                        <form
                          onSubmit={(e) => {
                            e.preventDefault();
                            const f = new FormData(e.currentTarget);
                            void action.run(async () => {
                              await request(
                                `/api/assignment-submissions/${r.id}/grade`,
                                "PATCH",
                                {
                                  score: Number(f.get("score")),
                                  feedback: f.get("feedback"),
                                },
                              );
                              await load();
                            }, "Đã lưu điểm và thu hồi công bố bảng điểm.");
                          }}
                        >
                          <label>
                            Điểm (0–10)
                            <input
                              name="score"
                              type="number"
                              min="0"
                              max="10"
                              step="0.01"
                              defaultValue={r.score ?? ""}
                              required
                            />
                          </label>
                          <label>
                            Nhận xét
                            <input
                              name="feedback"
                              defaultValue={r.feedback ?? ""}
                              maxLength={4000}
                            />
                          </label>
                          <button
                            disabled={action.busy}
                            style={{ marginTop: 8 }}
                          >
                            Lưu điểm
                          </button>
                        </form>
                      ) : (
                        <>
                          <strong>{r.score ?? "Chưa công bố"}</strong>
                          <p className="section-note">{r.feedback}</p>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!rows.length && <div className="empty">Chưa có bài nộp.</div>}
          <div className="actions">
            <button
              className="secondary"
              disabled={page === 1}
              onClick={() => setPage((x) => x - 1)}
            >
              Trước
            </button>
            <span>Trang {page}</span>
            <button
              className="secondary"
              disabled={page * 30 >= total}
              onClick={() => setPage((x) => x + 1)}
            >
              Sau
            </button>
          </div>
        </>
      )}
    </section>
  );
}
export default function AssignmentsPanel({
  courseId,
  teacher,
}: {
  courseId: number;
  teacher: boolean;
}) {
  const [rows, setRows] = useState<Assignment[]>([]),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0);
  const action = useAction();
  const load = useCallback(async () => {
    const r = await apiRequest<Page<Assignment>>(
      `/api/courses/${courseId}/assignments?page=${page}&page_size=20`,
    );
    setRows(r.items);
    setTotal(r.total);
  }, [courseId, page]);
  useEffect(() => {
    load().catch(action.setError);
  }, [load, action.setError]);
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      {teacher && (
        <section className="panel">
          <details>
            <summary>Tạo bài tập mới</summary>
            <AssignmentForm
              busy={action.busy}
              save={(body, form) =>
                void action.run(async () => {
                  await request(
                    `/api/courses/${courseId}/assignments`,
                    "POST",
                    body,
                  );
                  form.reset();
                  await load();
                }, "Đã tạo bài tập.")
              }
            />
          </details>
        </section>
      )}
      {rows.map((a) => (
        <AssignmentCard
          key={a.id}
          assignment={a}
          teacher={teacher}
          reload={load}
        />
      ))}
      {!rows.length && (
        <div className="empty">Chưa có bài tập trong khóa học.</div>
      )}
      <div className="actions">
        <button
          className="secondary"
          disabled={page === 1}
          onClick={() => setPage((x) => x - 1)}
        >
          Trước
        </button>
        <span>Trang {page}</span>
        <button
          className="secondary"
          disabled={page * 20 >= total}
          onClick={() => setPage((x) => x + 1)}
        >
          Sau
        </button>
      </div>
    </div>
  );
}
