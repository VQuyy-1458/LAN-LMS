"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiRequest } from "@/lib/api";
type Course = { id: number; name: string; course_code: string };
type Material = { id: number; title: string; original_filename: string };
type Assignment = { id: number; title: string; due_at: string };
type Submission = {
  id: number;
  student_id: string;
  original_filename: string;
  score: number | null;
};
type Preview = {
  preview_id: string;
  can_confirm: boolean;
  valid_rows: number;
  errors: { row: number; message: string }[];
};
export default function Workspace({ teacher = false }: { teacher?: boolean }) {
  const [courses, setCourses] = useState<Course[]>([]),
    [selected, setSelected] = useState(""),
    [materials, setMaterials] = useState<Material[]>([]),
    [assignments, setAssignments] = useState<Assignment[]>([]),
    [submissions, setSubmissions] = useState<Record<number, Submission[]>>({}),
    [preview, setPreview] = useState<Preview | null>(null),
    [message, setMessage] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const pendingKeys=useRef<Record<number,{file:File;key:string}>>({});
  async function loadCourses() {
    const result = await apiRequest<{ items: Course[] }>(
      "/api/courses?page_size=100",
    );
    setCourses(result.items);
  }
  async function loadContent(id: string) {
    if (!id) return;
    const [m, a] = await Promise.all([
      apiRequest<{ items: Material[] }>(
        `/api/courses/${id}/materials?page_size=100`,
      ),
      apiRequest<{ items: Assignment[] }>(
        `/api/courses/${id}/assignments?page_size=100`,
      ),
    ]);
    setMaterials(m.items);
    setAssignments(a.items);
    setSubmissions({});
  }
  useEffect(() => {
    loadCourses().catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    setPreview(null);
    loadContent(selected).catch((e) => setError(e.message));
  }, [selected]);
  async function act(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Có lỗi xảy ra");
    } finally {
      setBusy(false);
    }
  }
  function form(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    return new FormData(e.currentTarget);
  }
  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-bold">Khóa học, tài liệu và bài tập</h1>
      {error && (
        <p role="alert" className="rounded bg-red-50 p-3">
          {error}
        </p>
      )}
      {message && <p role="status">{message}</p>}
      {teacher && (
        <details>
          <summary>Tạo khóa học</summary>
          <form
            className="space-y-2"
            onSubmit={(e) => {
              const data = form(e);
              void act(async () => {
                const c = await apiRequest<Course>("/api/courses", {
                  method: "POST",
                  body: JSON.stringify({
                    course_code: data.get("code"),
                    name: data.get("name"),
                    description: data.get("description"),
                  }),
                });
                await loadCourses();
                setSelected(String(c.id));
                setMessage("Đã tạo khóa học");
              });
            }}
          >
            <input name="code" placeholder="Mã khóa học" required />
            <input name="name" placeholder="Tên khóa học" required />
            <input name="description" placeholder="Mô tả" />
            <button disabled={busy}>Tạo khóa học</button>
          </form>
        </details>
      )}
      <label>
        Chọn khóa học{" "}
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">Chọn…</option>
          {courses.map((c) => (
            <option key={c.id} value={c.id}>
              {c.course_code} — {c.name}
            </option>
          ))}
        </select>
      </label>
      {!courses.length && <p>Chưa có khóa học được cấp quyền.</p>}
      {selected && (
        <>
          {teacher && (
            <section>
              <h2>Nhập sinh viên CSV</h2>
              <p>
                Các cột: student_id, full_name, date_of_birth (DDMMYYYY),
                class_name, email.
              </p>
              <form
                onSubmit={(e) => {
                  const data = form(e);
                  void act(async () => {
                    setPreview(
                      await apiRequest<Preview>(
                        `/api/courses/${selected}/students/import-preview`,
                        { method: "POST", body: data },
                      ),
                    );
                  });
                }}
              >
                <input type="file" name="file" accept=".csv" required />
                <button disabled={busy}>Xem trước CSV</button>
              </form>
              {preview && (
                <div>
                  <p>{preview.valid_rows} dòng hợp lệ</p>
                  {preview.errors.map((v, i) => (
                    <p key={i}>
                      Dòng {v.row}: {v.message}
                    </p>
                  ))}
                  <button
                    disabled={busy || !preview.can_confirm}
                    onClick={() =>
                      void act(async () => {
                        await apiRequest(
                          `/api/courses/${selected}/students/import-confirm`,
                          {
                            method: "POST",
                            headers: {
                              "Idempotency-Key": `csv-${preview.preview_id}`,
                            },
                            body: JSON.stringify({
                              preview_id: preview.preview_id,
                            }),
                          },
                        );
                        setPreview(null);
                        setMessage(
                          "Đã nhập sinh viên. Tài khoản mới phải đổi mật khẩu.",
                        );
                      })
                    }
                  >
                    Xác nhận import
                  </button>
                </div>
              )}
            </section>
          )}
          <section>
            <h2>Tài liệu</h2>
            {teacher && (
              <form
                onSubmit={(e) => {
                  const data = form(e);
                  void act(async () => {
                    await apiRequest(`/api/courses/${selected}/materials`, {
                      method: "POST",
                      body: data,
                    });
                    await loadContent(selected);
                    setMessage("Đã đăng tài liệu");
                  });
                }}
              >
                <input name="title" placeholder="Tên tài liệu" required />
                <input type="file" name="file" required />
                <button disabled={busy}>Đăng tài liệu</button>
              </form>
            )}
            {materials.length ? (
              materials.map((m) => (
                <p key={m.id}>
                  <a href={`/api/materials/${m.id}/download`}>
                    {m.title} — {m.original_filename}
                  </a>
                </p>
              ))
            ) : (
              <p>Chưa có tài liệu.</p>
            )}
          </section>
          <section>
            <h2>Bài tập file</h2>
            {teacher && (
              <form
                onSubmit={(e) => {
                  const data = form(e);
                  void act(async () => {
                    await apiRequest(`/api/courses/${selected}/assignments`, {
                      method: "POST",
                      body: JSON.stringify({
                        title: data.get("title"),
                        description: data.get("description"),
                        due_at: new Date(String(data.get("due"))).toISOString(),
                        allow_resubmit: true,
                      }),
                    });
                    await loadContent(selected);
                  });
                }}
              >
                <input name="title" placeholder="Tên bài tập" required />
                <input name="description" placeholder="Đề bài" />
                <label>
                  Hạn nộp <input type="datetime-local" name="due" required />
                </label>
                <button disabled={busy}>Tạo bài tập</button>
              </form>
            )}
            {assignments.map((a) => (
              <article className="my-4 rounded border p-4" key={a.id}>
                <h3>{a.title}</h3>
                <p>Hạn nộp: {new Date(a.due_at).toLocaleString("vi-VN")}</p>
                {!teacher && (
                  <form
                    onSubmit={(e) => {
                      const data = form(e);
                      const file=data.get("file") as File;
                      const prior=pendingKeys.current[a.id];
                      const key=prior?.file===file?prior.key:Array.from(crypto.getRandomValues(new Uint8Array(16)),b=>b.toString(16).padStart(2,"0")).join("");
                      pendingKeys.current[a.id]={file,key};
                      void act(async () => {
                        await apiRequest(
                          `/api/assignments/${a.id}/submissions`,
                          {
                            method: "POST",
                            headers: { "Idempotency-Key": key },
                            body: data,
                          },
                        );
                        delete pendingKeys.current[a.id];
                        setMessage("Đã nộp bài");
                      });
                    }}
                  >
                    <input type="file" name="file" required />
                    <button disabled={busy}>Nộp file</button>
                  </form>
                )}
                <button
                  onClick={() =>
                    void act(async () => {
                      const result = await apiRequest<{ items: Submission[] }>(
                        `/api/assignments/${a.id}/submissions?page_size=100`,
                      );
                      setSubmissions((s) => ({ ...s, [a.id]: result.items }));
                    })
                  }
                >
                  Xem lịch sử bài nộp
                </button>
                {submissions[a.id]?.map((s) => (
                  <div key={s.id}>
                    <a href={`/api/assignment-submissions/${s.id}/download`}>
                      {s.student_id}: {s.original_filename}
                    </a>
                    <span> — điểm: {s.score ?? "Chưa công bố"}</span>
                    {teacher && (
                      <form
                        onSubmit={(e) => {
                          const data = form(e);
                          void act(async () => {
                            await apiRequest(
                              `/api/assignment-submissions/${s.id}/grade`,
                              {
                                method: "PATCH",
                                body: JSON.stringify({
                                  score: Number(data.get("score")),
                                  feedback: data.get("feedback"),
                                }),
                              },
                            );
                            setMessage(
                              "Đã chấm bài; công bố điểm đã được thu hồi",
                            );
                          });
                        }}
                      >
                        <input
                          name="score"
                          type="number"
                          min="0"
                          max="10"
                          step="0.01"
                          required
                          aria-label="Điểm"
                        />
                        <input name="feedback" placeholder="Nhận xét" />
                        <button disabled={busy}>Lưu điểm</button>
                      </form>
                    )}
                  </div>
                ))}
              </article>
            ))}
          </section>
        </>
      )}
    </section>
  );
}
