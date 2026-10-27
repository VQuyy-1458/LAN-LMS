"use client";
import {useCourseReadonly} from "@/components/CourseAccess";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import {
  allPages,
  date,
  key,
  localInput,
  localISO,
  request,
  statusLabel,
  type Exam,
  type Problem,
  type ExamSession,
  type Submission,
} from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import PaginatedList,{useListPage} from "@/components/Pagination";
import Feedback from "@/components/Feedback";
import { examComponentLabel, type ExamComponent } from "@/lib/examCreation";
export function ExamForm({
  exam,
  save,
  busy,
  availableComponents = ["practice", "midterm", "final"],
}: {
  exam?: Exam;
  save: (body: unknown) => void;
  busy: boolean;
  availableComponents?: ExamComponent[];
}) {
  const [defaults] = useState(() => ({
    start: localInput(
      exam?.starts_at || new Date(Date.now() + 3600000).toISOString(),
    ),
    end: localInput(
      exam?.ends_at || new Date(Date.now() + 10800000).toISOString(),
    ),
  }));
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const f = new FormData(e.currentTarget);
        save({
          title: f.get("title"),
          starts_at: localISO(String(f.get("starts_at"))),
          ends_at: localISO(String(f.get("ends_at"))),
          grade_component: f.get("grade_component"),
          score_ladder: String(f.get("score_ladder"))
            .split(",")
            .map((x) => Number(x.trim())),
        });
      }}
    >
      <div className="form-grid">
        <label>
          Tên kỳ thi
          <input
            name="title"
            defaultValue={exam?.title}
            required
            maxLength={200}
          />
        </label>
        {
          <label>
            Thành phần điểm
            <select
              name="grade_component"
              required
              defaultValue={exam?.grade_component || availableComponents[0]}
            >
              {availableComponents.map((component) => (
                <option key={component} value={component}>
                  {examComponentLabel[component]}
                </option>
              ))}
            </select>
          </label>
        }
        <label>
          Bắt đầu
          <input
            type="datetime-local"
            name="starts_at"
            defaultValue={defaults.start}
            required
          />
        </label>
        <label>
          Kết thúc
          <input
            type="datetime-local"
            name="ends_at"
            defaultValue={defaults.end}
            required
          />
        </label>
        <label className="full">
          Bảng quy đổi số bài AC → điểm
          <input
            name="score_ladder"
            defaultValue={exam?.score_ladder.join(", ") || "0, 5, 7, 8, 9, 10"}
            required
          />
          <small>
            Các mức điểm ứng với 0, 1, 2… bài AC. Ví dụ trên yêu cầu đề có 5
            bài; bảng phải tăng dần từ 0 tới 10.
          </small>
        </label>
      </div>
      <div className="actions">
        <button disabled={busy}>
          {exam ? "Lưu kỳ thi" : "Tạo đề thi nháp"}
        </button>
      </div>
    </form>
  );
}
function ProblemForm({
  problem,
  save,
  busy,
}: {
  problem?: Problem;
  save: (body: unknown) => void;
  busy: boolean;
}) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const f = new FormData(e.currentTarget);
        save({
          title: f.get("title"),
          statement: f.get("statement"),
          languages: f.getAll("languages"),
          io_mode: f.get("io_mode"),
          input_filename: f.get("input_filename") || null,
          output_filename: f.get("output_filename") || null,
          time_limit_ms: Number(f.get("time_limit_ms")),
          memory_limit_mib: Number(f.get("memory_limit_mib")),
          max_score: Number(f.get("max_score")),
          comparator: f.get("comparator"),
        });
      }}
    >
      <div className="form-grid">
        <label className="full">
          Tên bài
          <input
            name="title"
            defaultValue={problem?.title}
            required
            maxLength={200}
          />
        </label>
        <label className="full">
          Đề bài và ví dụ input/output
          <textarea
            name="statement"
            defaultValue={problem?.statement}
            required
            maxLength={50000}
            rows={8}
          />
        </label>
        <label>
          Thời gian (ms)
          <input
            name="time_limit_ms"
            type="number"
            defaultValue={problem?.time_limit_ms || 2000}
            min={100}
            max={10000}
            required
          />
        </label>
        <label>
          Bộ nhớ (MiB)
          <input
            name="memory_limit_mib"
            type="number"
            defaultValue={problem?.memory_limit_mib || 256}
            min={64}
            max={1024}
            required
          />
        </label>
        <label>
          Chế độ I/O
          <select name="io_mode" defaultValue={problem?.io_mode || "stdio"}>
            <option value="stdio">Standard input/output</option>
            <option value="file">File input/output</option>
          </select>
        </label>
        <label>
          So sánh output
          <select
            name="comparator"
            defaultValue={problem?.comparator || "normalized"}
          >
            <option value="normalized">
              Bỏ trắng cuối dòng và chuẩn hóa xuống dòng
            </option>
            <option value="exact">Khớp chính xác</option>
          </select>
        </label>
        <label>
          Tên file input (file mode)
          <input
            name="input_filename"
            defaultValue={problem?.input_filename || "input.txt"}
          />
        </label>
        <label>
          Tên file output (file mode)
          <input
            name="output_filename"
            defaultValue={problem?.output_filename || "output.txt"}
          />
        </label>
        <label>
          Tổng trọng số test
          <input
            type="number"
            name="max_score"
            min="0.01"
            max={10000}
            step="0.01"
            required
            defaultValue={problem?.max_score || 100}
          />
          <small>
            Chỉ AC mới tính bài giải đúng, không cộng điểm test lẻ vào điểm thi.
          </small>
        </label>
        <div>
          <label>Ngôn ngữ cho phép</label>
          <div className="actions">
            {["c", "cpp", "java"].map((l) => (
              <label className="check-label" key={l}>
                <input
                  name="languages"
                  type="checkbox"
                  value={l}
                  defaultChecked={
                    problem ? problem.languages.includes(l) : true
                  }
                />
                {{ c: "C17", cpp: "C++17", java: "Java 17" }[l]}
              </label>
            ))}
          </div>
        </div>
      </div>
      <div className="actions">
        <button disabled={busy}>
          {problem ? "Lưu cấu hình bài" : "Thêm bài"}
        </button>
      </div>
    </form>
  );
}
type Test = { id: number; points: number; is_hidden: boolean; ordinal: number };
function TestEditor({
  problemId,
  editable: requestedEditable,
}: {
  problemId: number;
  editable: boolean;
}) {
  const readonly=useCourseReadonly();
  const editable=requestedEditable&&!readonly;
  const [rows, setRows] = useState<Test[]>([]);
  const [zipKey, setZipKey] = useState(key);
  const action = useAction();
  const testsPage=useListPage(rows.length);
  const load=useCallback(async()=>setRows(await allPages<Test>(`/api/problems/${problemId}/test-cases`)),[problemId]);
  useEffect(() => {
    load().catch(action.setError);
  }, [load, action.setError]);
  return (
    <div className="details-box">
      <h3>
        Test case · {rows.length} test · tổng{" "}
        {rows.reduce((s, r) => s + r.points, 0)} trọng số
      </h3>
      <Feedback error={action.error} message={action.message} />
      {editable && <form onSubmit={event=>{event.preventDefault();const form=event.currentTarget;const values=new FormData(form),body=new FormData();
        body.set("input_file",new File([String(values.get("input")??"")],"input.in",{type:"text/plain"}));
        body.set("expected_output_file",new File([String(values.get("output")??"")],"output.out",{type:"text/plain"}));
        body.set("points",String(values.get("points")));body.set("ordinal",String(rows.length+1));body.set("is_hidden",values.has("hidden")?"true":"false");
        void action.run(async()=>{await apiRequest(`/api/problems/${problemId}/test-cases`,{method:"POST",body});form.reset();await load()},"Đã thêm testcase.");
      }}><h4>Thêm testcase bằng nội dung</h4><div className="form-grid"><label>Input<textarea name="input" rows={4}/></label><label>Output mong đợi<textarea name="output" rows={4}/></label><label>Trọng số test<input name="points" type="number" min={0} max={10000} step="0.01" defaultValue={100} required/></label><label className="check-label"><input name="hidden" type="checkbox" defaultChecked/>Test ẩn</label></div><button disabled={action.busy||readonly}>Lưu testcase</button><p className="section-note">Có thể để input/output rỗng nếu đề yêu cầu. Tổng trọng số tất cả test phải bằng điểm tối đa câu hỏi trước khi mở thi.</p></form>}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Thứ tự</th>
              <th>Trọng số</th>
              <th>Loại</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.slice(testsPage.start,testsPage.end).map((r) => (
              <tr key={r.id}>
                <td>{r.ordinal}</td>
                <td>{r.points}</td>
                <td>{r.is_hidden ? "Ẩn" : "Ví dụ"}</td>
                <td>
                  <a href={`/api/test-cases/${r.id}/file?kind=input`}>Input</a>
                  {" · "}
                  <a href={`/api/test-cases/${r.id}/file?kind=output`}>
                    Output
                  </a>{" "}
                  {editable && (
                    <button
                      className="danger"
                      disabled={action.busy||readonly}
                      onClick={() => {
                        if (confirm("Xóa test case này?"))
                          void action.run(async () => {
                            await request(`/api/test-cases/${r.id}`, "DELETE");
                            await load();
                          }, "Đã xóa test.");
                      }}
                    >
                      Xóa
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {testsPage.controls}
      {editable && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            const form = event.currentTarget;
            void action.run(async () => {
              await apiRequest(
                `/api/problems/${problemId}/test-cases/import-zip`,
                {
                  method: "POST",
                  body: new FormData(form),
                  headers: { "Idempotency-Key": zipKey },
                },
              );
              form.reset();
              setZipKey(key());
              await load();
            }, "Đã nhập bộ testcase và chia đều trọng số.");
          }}
        >
          <h4>Nhập nhanh bộ testcase (.zip)</h4>
          <p className="section-note">
            Dành cho bài chưa có test. ZIP chứa các cặp 01.in/01.out ở thư mục
            gốc; tên bắt đầu sample_ là ví dụ công khai. Tối đa 100 cặp, ZIP 20
            MiB. Các test chia đều trọng số.
          </p>
          <label>
            File ZIP
            <input
              type="file"
              name="file"
              accept=".zip"
              required
              onChange={() => setZipKey(key())}
            />
          </label>
          <button
            className="secondary"
            disabled={action.busy || rows.length > 0}
          >
            Nhập testcase ZIP
          </button>
        </form>
      )}
      {editable && (
        <form
          style={{ marginTop: 18 }}
          onSubmit={(e) => {
            e.preventDefault();
            const form = e.currentTarget,
              f = new FormData(form);
            if (!f.has("is_hidden")) f.set("is_hidden", "false");
            else f.set("is_hidden", "true");
            void action.run(async () => {
              await apiRequest(`/api/problems/${problemId}/test-cases`, {
                method: "POST",
                body: f,
              });
              form.reset();
              await load();
            }, "Đã thêm test.");
          }}
        >
          <div className="form-grid">
            <label>
              Input (.in/.txt)
              <input
                name="input_file"
                type="file"
                accept=".in,.txt,.out"
                required
              />
            </label>
            <label>
              Expected output (.out/.txt)
              <input
                name="expected_output_file"
                type="file"
                accept=".in,.txt,.out"
                required
              />
            </label>
            <label>
              Trọng số
              <input
                name="points"
                type="number"
                min={0}
                max={10000}
                step="0.01"
                defaultValue={100}
                required
              />
            </label>
            <label>
              Thứ tự
              <input
                name="ordinal"
                type="number"
                min={0}
                defaultValue={rows.length + 1}
                required
              />
            </label>
            <label className="check-label">
              <input name="is_hidden" type="checkbox" defaultChecked />
              Test ẩn
            </label>
          </div>
          <p className="section-note">
            Tối đa 1 MiB/file, 100 test/bài. Tổng trọng số phải khớp cấu hình
            bài trước khi mở thi. Nội dung test không trả về sinh viên.
          </p>
          <div className="actions">
            <button disabled={action.busy||readonly}>Thêm test case</button>
          </div>
        </form>
      )}
    </div>
  );
}
export default function ExamEditor({
  exam,
  onChange,
}: {
  exam: Exam;
  onChange: () => Promise<void>;
}) {
  const [problems, setProblems] = useState<Problem[]>([]),
    [sessions, setSessions] = useState<ExamSession[]>([]),
    [selectedProblem, setSelectedProblem] = useState(0),
    [submissions, setSubmissions] = useState<Submission[]>([]),
    [source, setSource] = useState<Submission | null>(null);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  const action = useAction();
  const readonly=useCourseReadonly();
  const editable = !readonly &&
    ["draft", "upcoming"].includes(exam.status) &&
    new Date(exam.starts_at).getTime() > now;
  const load = useCallback(async () => {
    const [p, s] = await Promise.all([
      allPages<Problem>(`/api/coding-exams/${exam.id}/problems`),
      allPages<ExamSession>(`/api/coding-exams/${exam.id}/sessions`),
    ]);
    setProblems(p);
    setSessions(s);
  }, [exam.id]);
  const sessionsPage=useListPage(sessions.length),submissionsPage=useListPage(submissions.length);
  const loadSubs=useCallback(async()=>{if(selectedProblem)setSubmissions(await allPages<Submission>(`/api/problems/${selectedProblem}/submissions`))},[selectedProblem]);
  useEffect(() => {
    load().catch(action.setError);
    const t = setInterval(() => load().catch(() => {}), 5000);
    return () => clearInterval(t);
  }, [load, action.setError]);
  useEffect(() => {
    loadSubs().catch(action.setError);
    const t = setInterval(() => loadSubs().catch(() => {}), 5000);
    return () => clearInterval(t);
  }, [loadSubs, action.setError]);
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      <section className="panel">
        <div className="panel-title">
          <div>
            <h2>{exam.title}</h2>
            <p className="section-note">
              {date(exam.starts_at)} → {date(exam.ends_at)} ·{" "}
              {exam.problem_count} bài
            </p>
          </div>
          <span className={`badge ${exam.status}`}>
            {statusLabel[exam.status]}
          </span>
        </div>
        <p className="section-note">
          Bảng điểm theo số bài AC:{" "}
          {exam.score_ladder.map((n, i) => `${i} bài = ${n}`).join(" · ")}
        </p>
        <div className="actions">
          {editable && (
            <button
              disabled={action.busy||readonly}
              onClick={() =>
                void action.run(async () => {
                  await request(`/api/coding-exams/${exam.id}`, "PATCH", {
                    status: "scheduled",
                  });
                  await onChange();
                }, "Đã kiểm tra bộ đề và lên lịch mở thi.")
              }
            >
              Kiểm tra đề & Lên lịch mở
            </button>
          )}
          {["upcoming", "open"].includes(exam.status) && (
            <button
              className="danger"
              disabled={action.busy||readonly}
              onClick={() => {
                if (
                  confirm(
                    "Đóng kỳ thi ngay? Sinh viên sẽ không gửi thêm bài được.",
                  )
                )
                  void action.run(async () => {
                    await request(`/api/coding-exams/${exam.id}`, "PATCH", {
                      status: "closed",
                    });
                    await onChange();
                  }, "Đã đóng kỳ thi.");
              }}
            >
              Đóng kỳ thi
            </button>
          )}
        </div>
        <div className="actions">
          <label>
            Loại bài thi
            <select
              aria-label="Loại bài thi"
              value={exam.grade_component}
              disabled={action.busy||readonly}
              onChange={(event) => {
                const grade_component = event.target.value;
                void action.run(async () => {
                  await request(`/api/coding-exams/${exam.id}`, "PATCH", {
                    grade_component,
                  });
                  await onChange();
                }, "Đã cập nhật loại bài thi và tính lại điểm thành phần.");
              }}
            >
              {["practice", "midterm", "final"].map((value) => (
                <option key={value} value={value}>
                  {examComponentLabel[value]}
                </option>
              ))}
            </select>
          </label>
        </div>
        {editable && (
          <details style={{ marginTop: 18 }}>
            <summary>Chỉnh sửa thông tin kỳ thi</summary>
            <ExamForm
              exam={exam}
              busy={action.busy}
              save={(body) =>
                void action.run(async () => {
                  await request(`/api/coding-exams/${exam.id}`, "PATCH", body);
                  await onChange();
                })
              }
            />
          </details>
        )}
      </section>
      {editable && (
        <section className="panel">
          <details open>
            <summary>
              Thêm bài lập trình ({problems.length}/{exam.problem_count})
            </summary>
            <ProblemForm
              busy={action.busy}
              save={(body) =>
                void action.run(async () => {
                  await request(
                    `/api/coding-exams/${exam.id}/problems`,
                    "POST",
                    body,
                  );
                  await load();
                }, "Đã thêm bài. Tiếp theo hãy thêm test case.")
              }
            />
          </details>
        </section>
      )}
      <PaginatedList>{problems.map((p, i) => (
        <section className="panel" key={p.id}>
          <h2>
            Bài {i + 1}. {p.title}
          </h2>
          {editable && (
            <div className="actions">
              <button
                className="danger"
                disabled={action.busy||readonly}
                onClick={() => {
                  if (confirm("Xóa bài này và các test trước khi thi?"))
                    void action.run(async () => {
                      await request(`/api/problems/${p.id}`, "DELETE");
                      await load();
                    }, "Đã xóa bài khỏi đề.");
                }}
              >
                Xóa bài khỏi đề
              </button>
            </div>
          )}
          <p className="section-note">
            {p.time_limit_ms} ms · {p.memory_limit_mib} MiB ·{" "}
            {p.io_mode === "file"
              ? `${p.input_filename} → ${p.output_filename}`
              : "stdin / stdout"}
          </p>
          <details style={{ marginTop: 15 }}>
            <summary>
              {editable ? "Xem / Sửa nội dung bài" : "Xem nội dung"}
            </summary>
            {editable ? (
              <ProblemForm
                problem={p}
                busy={action.busy}
                save={(body) =>
                  void action.run(async () => {
                    await request(`/api/problems/${p.id}`, "PATCH", body);
                    await load();
                  })
                }
              />
            ) : (
              <p className="statement">{p.statement}</p>
            )}
          </details>
          <details open style={{ marginTop: 15 }}>
            <summary>Quản lý test case</summary>
            <TestEditor problemId={p.id} editable={editable} />
          </details>
        </section>
      ))}</PaginatedList>
      <section className="panel">
        <div className="panel-title">
          <h2>Theo dõi phiên thi</h2>
          <a className="button-link" href={`/api/coding-exams/${exam.id}/export-csv`}>Xuất điểm thi CSV ↓</a>
          <span className="badge">
            {sessions.length} phiên · cập nhật mỗi 5 giây
          </span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Sinh viên</th>
                <th>Trạng thái</th>
                <th>Kết nối</th>
                <th>AC / Tổng bài</th>
                <th>Điểm</th>
                <th>Chờ chấm</th>
                <th>IP / Nhật ký</th>
              </tr>
            </thead>
            <tbody>
              {sessions.slice(sessionsPage.start,sessionsPage.end).map((s) => (
                <tr key={s.id}>
                  <td>
                    {s.student_id}
                    <p className="section-note">{s.full_name}</p>
                  </td>
                  <td>{statusLabel[s.status]}</td>
                  <td>
                    <span className={`badge ${s.connection_status}`}>
                      {s.connection_status === "connected"
                        ? "Đang kết nối"
                        : "Mất kết nối"}
                    </span>
                    <p className="section-note">{date(s.last_seen_at)}</p>
                  </td>
                  <td>
                    {s.accepted_count}/{s.problem_count}
                  </td>
                  <td>{s.total_score}/10</td>
                  <td>{s.pending_count}</td>
                  <td>
                    <p>{s.started_ip || "—"}</p>
                    <SessionEvents session={s} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!sessions.length && (
          <div className="empty">Chưa có sinh viên bắt đầu phiên thi.</div>
        )}
        {sessionsPage.controls}
      </section>
      <section className="panel">
        <h2>Lịch sử chấm của lớp</h2>
        <select
          aria-label="Bài cần xem lịch sử"
          value={selectedProblem || ""}
          onChange={(e) => setSelectedProblem(Number(e.target.value))}
          style={{ marginTop: 15 }}
        >
          <option value="">Chọn bài lập trình</option>
          {problems.map((p) => (
            <option key={p.id} value={p.id}>
              {p.title}
            </option>
          ))}
        </select>
        <div className="table-wrap" style={{ marginTop: 15 }}>
          <table>
            <thead>
              <tr>
                <th>Mã</th>
                <th>Sinh viên</th>
                <th>Ngôn ngữ</th>
                <th>Thời gian</th>
                <th>Kết quả</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {submissions.slice(submissionsPage.start,submissionsPage.end).map((s) => (
                <tr key={s.id}>
                  <td>#{s.id}</td>
                  <td>{s.student_id}</td>
                  <td>{s.language}</td>
                  <td>{date(s.received_at)}</td>
                  <td>
                    <span className={`badge ${s.verdict_code}`}>
                      {statusLabel[s.verdict_code]}
                    </span>
                  </td>
                  <td>
                    <button
                      className="secondary"
                      onClick={() =>
                        void action.run(
                          async () =>
                            setSource(
                              await apiRequest<Submission>(
                                `/api/submissions/${s.id}`,
                              ),
                            ),
                          "",
                        )
                      }
                    >
                      Xem source
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {source && (
          <div className="details-box">
            <div className="panel-title">
              <h3>
                Source #{source.id} · {source.student_id}
              </h3>
              <button className="ghost" onClick={() => setSource(null)}>
                Đóng
              </button>
            </div>
            <pre className="source-output">{source.source_code}</pre>
            {source.compile_message && (
              <pre className="source-output">{source.compile_message}</pre>
            )}
          </div>
        )}
        {submissionsPage.controls}
      </section>
    </div>
  );
}

function SessionEvents({ session }: { session: ExamSession }) {
  const [events, setEvents] = useState<
    { id: number; event_type: string; ip_address: string; created_at: string }[]
  >([]);
  const action = useAction();
  return (
    <details
      onToggle={(event) => {
        if (event.currentTarget.open)
          void action.run(async () => {
            setEvents(await allPages<{id:number;event_type:string;ip_address:string;created_at:string}>(`/api/exam-sessions/${session.id}/events`));
          });
      }}
    >
      <summary>{session.focus_event_count} sự kiện rời màn hình</summary>
      <Feedback error={action.error} message="" />
      <p className="section-note">
        Nhật ký phân trang 10 mục; nhật ký trình duyệt chỉ hỗ trợ giám sát, không
        khẳng định gian lận.
      </p>
      <PaginatedList>{events.map((event) => (
        <p key={event.id}>
          {date(event.created_at)} ·{" "}
          {
            (
              {
                tab_hidden: "Rời tab",
                window_blur: "Mất tiêu điểm",
                fullscreen_exit: "Thoát toàn màn hình",
              } as Record<string, string>
            )[event.event_type]
          }{" "}
          · {event.ip_address}
        </p>
      ))}</PaginatedList>
    </details>
  );
}
