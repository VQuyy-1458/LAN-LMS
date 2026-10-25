"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiRequest } from "@/lib/api";
import {
  date,
  key,
  request,
  statusLabel,
  type Exam,
  type Page,
  type Problem,
  type ExamSession,
  type Submission,
} from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import Feedback from "@/components/Feedback";
import { useRealtime } from "@/components/Realtime";
const template: Record<string, string> = {
  c: "#include <stdio.h>\n\nint main(void) {\n    // Viết bài làm tại đây\n    return 0;\n}\n",
  cpp: "#include <iostream>\nusing namespace std;\n\nint main() {\n    // Viết bài làm tại đây\n    return 0;\n}\n",
  java: "import java.util.*;\n\npublic class Main {\n    public static void main(String[] args) {\n        // Viết bài làm tại đây\n    }\n}\n",
};
function Solver({
  problem: p,
  session,
  refreshSession,
  canSubmit,
}: {
  problem: Problem;
  session: ExamSession;
  refreshSession: () => Promise<void>;
  canSubmit: boolean;
}) {
  const [source, setSource] = useState(""),
    [language, setLanguage] = useState(p.languages[0]),
    [rows, setRows] = useState<Submission[]>([]),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0),
    [detail, setDetail] = useState<Submission | null>(null),
    [loaded, setLoaded] = useState(false);
  const action = useAction(),
    pending = useRef<{ body: string; key: string } | null>(null),
    { revision } = useRealtime();
  const storageKey = `lan-lms-draft-${session.id}-${p.id}`;
  const languageList = p.languages.join(",");
  useEffect(() => {
    const languages = languageList.split(",");
    try {
      const draft = JSON.parse(localStorage.getItem(storageKey) || "null");
      if (
        draft &&
        typeof draft.source === "string" &&
        languages.includes(draft.language)
      ) {
        setSource(draft.source);
        setLanguage(draft.language);
      } else {
        setSource(template[languages[0]]);
        setLanguage(languages[0]);
      }
    } catch {
      setSource(template[languages[0]]);
    }
    setLoaded(true);
  }, [storageKey, languageList]);
  useEffect(() => {
    if (loaded)
      try {
        localStorage.setItem(storageKey, JSON.stringify({ source, language }));
      } catch {
        /* Browser may disallow persistent local drafts; server submissions still work. */
      }
  }, [source, language, storageKey, loaded]);
  const load = useCallback(async () => {
    const r = await apiRequest<Page<Submission>>(
      `/api/problems/${p.id}/submissions?page=${page}&page_size=20`,
    );
    setRows(r.items);
    setTotal(r.total);
  }, [p.id, page]);
  useEffect(() => {
    load().catch(action.setError);
  }, [load, revision, action.setError]);
  useEffect(() => {
    const timer = setInterval(() => {
      void load().catch(() => {});
    }, 3000);
    return () => clearInterval(timer);
  }, [load]);
  const detailId = detail?.id;
  const detailStatus = rows.find((r) => r.id === detailId)?.status;
  useEffect(() => {
    if (detailId)
      apiRequest<Submission>(`/api/submissions/${detailId}`)
        .then(setDetail)
        .catch(action.setError);
  }, [detailId, detailStatus, revision, action.setError]);
  const accepted = rows.some((s) => s.verdict_code === "AC");
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      <div className="code-layout">
        <section className="panel">
          <div className="panel-title">
            <h2>{p.title}</h2>
            {accepted && <span className="badge AC">Đã AC</span>}
          </div>
          <p className="section-note">
            Thời gian: {p.time_limit_ms} ms · Bộ nhớ: {p.memory_limit_mib} MiB
          </p>
          <p className="section-note">
            {p.io_mode === "file"
              ? `Đọc ${p.input_filename}, ghi ${p.output_filename}`
              : "Đọc stdin, ghi stdout"}{" "}
            ·{" "}
            {p.comparator === "exact"
              ? "So sánh chính xác"
              : "Chuẩn hóa đầu/cuối và xuống dòng"}
          </p>
          <hr
            style={{
              border: 0,
              borderTop: "1px solid var(--border)",
              margin: "20px 0",
            }}
          />
          <div className="statement">{p.statement}</div>
        </section>
        <section className="panel">
          <h2>Bài làm của bạn</h2>
          <div className="code-toolbar">
            <label>
              Ngôn ngữ
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                {p.languages.map((l) => (
                  <option key={l} value={l}>
                    {{ c: "C17", cpp: "C++17", java: "Java 17" }[l]}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="secondary"
              onClick={() => {
                if (
                  !source.trim() ||
                  confirm("Thay nội dung hiện tại bằng khung mã mẫu?")
                )
                  setSource(template[language]);
              }}
            >
              Chèn khung mã
            </button>
          </div>
          <label>
            <span className="muted">Source code</span>
            <textarea
              spellCheck={false}
              className="code-editor"
              aria-label="Source code"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Tab") {
                  e.preventDefault();
                  const t = e.currentTarget,
                    start = t.selectionStart,
                    end = t.selectionEnd;
                  setSource(
                    source.slice(0, start) + "    " + source.slice(end),
                  );
                  requestAnimationFrame(() => {
                    t.selectionStart = t.selectionEnd = start + 4;
                  });
                }
              }}
            />
          </label>
          <label style={{ marginTop: 12 }}>
            Hoặc tải source lên
            <input
              type="file"
              accept=".c,.cpp,.java"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                void action.run(async () => {
                  if (file.size > 256 * 1024)
                    throw new Error("Source tối đa 256 KiB.");
                  setSource(await file.text());
                }, "Đã đọc source. Kiểm tra lại ngôn ngữ trước khi gửi.");
              }}
            />
          </label>
          {language === "java" && (
            <p className="section-note">
              Java: dùng public class Main, không khai báo package.
            </p>
          )}
          <div className="actions">
            <button
              disabled={action.busy || !canSubmit || !source.trim()}
              onClick={() =>
                void action.run(async () => {
                  if (new TextEncoder().encode(source).length > 256 * 1024)
                    throw new Error("Source tối đa 256 KiB UTF-8.");
                  const body = JSON.stringify({
                    exam_session_id: session.id,
                    language,
                    source_code: source,
                  });
                  if (pending.current?.body !== body)
                    pending.current = { body, key: key() };
                  const r = await apiRequest<Submission>(
                    `/api/problems/${p.id}/submissions`,
                    {
                      method: "POST",
                      body,
                      headers: { "Idempotency-Key": pending.current.key },
                    },
                  );
                  pending.current = null;
                  setDetail(r);
                  await load();
                  await refreshSession();
                }, "Đã nhận bài. Kết quả sẽ tự cập nhật khi chấm xong.")
              }
            >
              {action.busy ? "Đang gửi…" : "Gửi bài chấm"}
            </button>
            <span className="section-note">
              {canSubmit
                ? "Bản nháp được giữ trên trình duyệt này."
                : "Phiên thi đã kết thúc; không nhận thêm bài."}
            </span>
          </div>
        </section>
      </div>
      <section className="panel">
        <div className="panel-title">
          <h2>Lịch sử nộp bài</h2>
          <span className="badge">{total} lần nộp · tự cập nhật</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Mã bài nộp</th>
                <th>Thời gian</th>
                <th>Ngôn ngữ</th>
                <th>Kết quả</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>#{r.id}</td>
                  <td>{date(r.received_at)}</td>
                  <td>{r.language}</td>
                  <td>
                    <span className={`badge ${r.verdict_code}`}>
                      {statusLabel[r.verdict_code]}
                    </span>
                  </td>
                  <td>
                    <button
                      className="secondary"
                      onClick={() =>
                        void action.run(
                          async () =>
                            setDetail(
                              await apiRequest<Submission>(
                                `/api/submissions/${r.id}`,
                              ),
                            ),
                          "",
                        )
                      }
                    >
                      Chi tiết
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!rows.length && <div className="empty">Bạn chưa gửi bài này.</div>}
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
        <p className="section-note">
          AC: đúng toàn bộ test · WA: sai kết quả · RTE: lỗi chạy · TLE: quá
          thời gian · MLE: quá bộ nhớ · CE: lỗi biên dịch. Chỉ AC được tính là
          một bài giải đúng.
        </p>
        {detail && (
          <div className="details-box">
            <div className="panel-title">
              <h3>Bài nộp #{detail.id}</h3>
              <button className="ghost" onClick={() => setDetail(null)}>
                Đóng
              </button>
            </div>
            <span
              className={`badge ${(rows.find((r) => r.id === detail.id) || detail).verdict_code}`}
            >
              {
                statusLabel[
                  (rows.find((r) => r.id === detail.id) || detail).verdict_code
                ]
              }
            </span>
            {detail.compile_message && (
              <pre className="source-output" style={{ marginTop: 12 }}>
                {detail.compile_message}
              </pre>
            )}
            {detail.source_code && (
              <pre className="source-output" style={{ marginTop: 12 }}>
                {detail.source_code}
              </pre>
            )}
            <p className="section-note">
              Kết quả chỉ gồm tổng bài; không công khai test ẩn.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
export default function ExamPlayer({ exam }: { exam: Exam }) {
  const [session, setSession] = useState<ExamSession | null>(null),
    [problems, setProblems] = useState<Problem[]>([]),
    [pid, setPid] = useState(0),
    [now, setNow] = useState(() => Date.now()),
    [offset, setOffset] = useState(0);
  const action = useAction(),
    { revision } = useRealtime();
  const refresh = useCallback(async () => {
    const s = await apiRequest<ExamSession | null>(
      `/api/coding-exams/${exam.id}/my-session`,
    );
    setSession(s);
    if (s) setOffset(new Date(s.server_time).getTime() - Date.now());
    if (exam.status !== "upcoming") {
      const p = await apiRequest<Page<Problem>>(
        `/api/coding-exams/${exam.id}/problems?page_size=100`,
      );
      setProblems(p.items);
      setPid((v) => v || p.items[0]?.id || 0);
    }
  }, [exam.id, exam.status]);
  useEffect(() => {
    refresh().catch(action.setError);
  }, [refresh, revision, action.setError]);
  useEffect(() => {
    const timer = setInterval(() => {
      void refresh().catch(() => {});
    }, 3000);
    return () => clearInterval(timer);
  }, [refresh]);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  const remaining = session
      ? Math.max(
          0,
          Math.floor(
            (new Date(session.ends_at).getTime() - now - offset) / 1000,
          ),
        )
      : 0,
    canSubmit =
      !!session &&
      session.status === "active" &&
      remaining > 0 &&
      exam.status === "open";
  useEffect(() => {
    if (session?.status === "active" && remaining === 0)
      void request(`/api/exam-sessions/${session.id}/finish`, "POST")
        .then(() => refresh())
        .catch(() => {});
  }, [session?.id, session?.status, remaining, refresh]);
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      <section className="panel">
        <div className="panel-title">
          <div>
            <h2>{exam.title}</h2>
            <p className="section-note">
              {date(exam.starts_at)} → {date(exam.ends_at)}
            </p>
          </div>
          <span className={`badge ${exam.status}`}>
            {statusLabel[exam.status]}
          </span>
        </div>
        <p className="section-note">
          Điểm theo số bài AC:{" "}
          {exam.score_ladder.map((n, i) => `${i} bài = ${n}`).join(" · ")}
        </p>
        {session ? (
          <>
            <div
              className="welcome-stats"
              style={{ background: "#f7f9fc", marginTop: 18 }}
            >
              <div>
                <strong>
                  {session.accepted_count}/{session.problem_count}
                </strong>
                <span>Bài đã AC</span>
              </div>
              <div>
                <strong>{session.total_score}/10</strong>
                <span>Điểm thi hiện tại</span>
              </div>
              <div>
                <strong>
                  {canSubmit
                    ? `${Math.floor(remaining / 3600)
                        .toString()
                        .padStart(2, "0")}:${Math.floor((remaining % 3600) / 60)
                        .toString()
                        .padStart(
                          2,
                          "0",
                        )}:${(remaining % 60).toString().padStart(2, "0")}`
                    : statusLabel[session.status]}
                </strong>
                <span>
                  {canSubmit ? "Thời gian còn lại" : "Trạng thái phiên"}
                </span>
              </div>
            </div>
            {canSubmit && (
              <div className="actions">
                <button
                  className="secondary"
                  disabled={action.busy}
                  onClick={() => {
                    if (
                      confirm(
                        "Kết thúc phiên thi? Bạn sẽ không gửi thêm bài được.",
                      )
                    )
                      void action.run(async () => {
                        await request(
                          `/api/exam-sessions/${session.id}/finish`,
                          "POST",
                        );
                        await refresh();
                      }, "Đã kết thúc phiên thi. Các bài đang chấm vẫn được xử lý.");
                  }}
                >
                  Kết thúc phiên thi
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="actions">
            <button
              disabled={exam.status !== "open" || action.busy}
              onClick={() =>
                void action.run(async () => {
                  setSession(
                    await request<ExamSession>(
                      `/api/coding-exams/${exam.id}/sessions/start`,
                      "POST",
                    ),
                  );
                  await refresh();
                }, "Đã bắt đầu phiên thi.")
              }
            >
              Bắt đầu làm bài
            </button>
            <span className="section-note">Giờ thi do máy chủ quyết định.</span>
          </div>
        )}
      </section>
      {session && (
        <>
          <nav className="tabs" aria-label="Danh sách bài thi">
            {problems.map((p, i) => (
              <button
                key={p.id}
                className={p.id === pid ? "active" : ""}
                onClick={() => setPid(p.id)}
              >
                Bài {i + 1} · {p.title}
              </button>
            ))}
          </nav>
          {problems.find((p) => p.id === pid) && (
            <Solver
              key={`${session.id}-${pid}`}
              problem={problems.find((p) => p.id === pid)!}
              session={session}
              refreshSession={refresh}
              canSubmit={canSubmit}
            />
          )}
        </>
      )}
    </div>
  );
}
