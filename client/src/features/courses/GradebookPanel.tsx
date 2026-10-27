"use client";
import {useCourseReadonly} from "@/components/CourseAccess";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { request } from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import { useRealtime } from "@/components/Realtime";
import ScoreCell from "@/components/ScoreCell";
import ConfirmAction from "@/components/ConfirmAction";
import {useListPage} from "@/components/Pagination";
import Feedback from "@/components/Feedback";
type Weights = {
  attendance: number;
  homework: number;
  midterm: number;
  final: number;
};
type Grade = {
  student_id: string;
  full_name: string;
  class_name: string;
  attendance_score: number | null;
  homework_score: number | null;
  midterm_score: number | null;
  final_score: number | null;
  total_score: number | null;
};
type Book = { weights: Weights; published: boolean; items: Grade[] };
const names: Record<keyof Weights, string> = {
  attendance: "Chuyên cần",
  homework: "Bài tập",
  midterm: "Giữa kỳ",
  final: "Cuối kỳ",
};
export default function GradebookPanel({
  courseId,
  teacher,
}: {
  courseId: number;
  teacher: boolean;
}) {
  const [book, setBook] = useState<Book | null>(null),
    [weights, setWeights] = useState<Weights>({
      attendance: 10,
      homework: 10,
      midterm: 10,
      final: 70,
    }),
    [search, setSearch] = useState("");
  const readonly=useCourseReadonly();
  const action = useAction();
  const { revision } = useRealtime();
  const load = useCallback(async () => {
    const r = await apiRequest<Book>(`/api/courses/${courseId}/gradebook`);
    setBook(r);

  }, [courseId]);
  useEffect(() => {
    load().catch(action.setError);
  }, [load, revision, action.setError]);
  useEffect(() => {
    const timer = setInterval(() => void load().catch(() => {}), 5000);
    return () => clearInterval(timer);
  }, [load]);
  const visibleRows=(book?.items||[]).filter(r=>`${r.student_id} ${r.full_name}`.toLowerCase().includes(search.toLowerCase()));
  const pagination=useListPage(visibleRows.length);
  const total = Object.values(weights).reduce((a, b) => a + b, 0);
  return (
    <div className="stack">
      <Feedback error={action.error} message={action.message} />
      {teacher && !readonly && (
        <section className="panel">
          <details onToggle={e=>{if(e.currentTarget.open&&book)setWeights(book.weights)}}>
            <summary>Cấu hình trọng số</summary>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void action.run(async () => {
                  await request(
                    `/api/courses/${courseId}/grade-components`,
                    "PATCH",
                    weights,
                  );
                  await load();
                }, "Đã cập nhật trọng số và điểm tổng kết.");
              }}
            >
              <div className="form-grid">
                {(Object.keys(names) as (keyof Weights)[]).map((k) => (
                  <label key={k}>
                    {names[k]} (%)
                    <input
                      type="number"
                      min={0}
                      max={100}
                      step="0.01"
                      required
                      value={weights[k]}
                      onChange={(e) =>
                        setWeights((v) => ({
                          ...v,
                          [k]: Number(e.target.value),
                        }))
                      }
                    />
                  </label>
                ))}
              </div>
              <div className="actions">
                <button
                  disabled={action.busy || Math.abs(total - 100) > 0.000001}
                >
                  Lưu trọng số
                </button>
                <span className="badge">Tổng {total}% / 100%</span>
              </div>
            </form>
          </details>
        </section>
      )}
      {teacher && !readonly && <section className="panel"><h2>Nhập điểm CSV</h2><p className="section-note">Dùng bảng điểm xuất bên dưới làm mẫu. Cần student_id và các cột điểm muốn nhập; ô trống giữ nguyên. Chấp nhận bảng điểm chưa đủ đầu điểm.</p><form onSubmit={e=>{e.preventDefault();const form=e.currentTarget;void action.run(async()=>{await apiRequest(`/api/courses/${courseId}/gradebook/import-csv`,{method:"POST",body:new FormData(form)});form.reset();await load()},"Đã nhập điểm CSV.")}}><label>File CSV<input type="file" name="file" accept=".csv" required/></label><button disabled={action.busy}>Nhập điểm</button></form></section>}
      <section className="panel">
        <div className="panel-title">
          <div>
            <h2>
              {teacher ? "Bảng điểm khóa học" : "Kết quả học tập của tôi"}
            </h2>
            <p className="section-note">
              Thang điểm 10 · Điểm trống là chưa đủ dữ liệu. {teacher && !readonly && "Sửa trực tiếp từng ô, nhấn Enter hoặc chuyển ô để lưu."}
            </p>
          </div>
          <span className="badge">
            {book?.published ? "Đã xác nhận tổng kết" : "Điểm cập nhật trực tiếp"}
          </span>
        </div>
        {teacher && (
          <div className="toolbar">
            <input
              aria-label="Tìm sinh viên"
              placeholder="Tìm mã hoặc họ tên…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <div className="actions" style={{ marginTop: 0 }}>
              {!readonly&&<ConfirmAction label="Chốt tổng kết khóa học" message="Sau khi chốt, toàn bộ khóa học chỉ được xem và xuất dữ liệu. Bạn chắc chắn muốn tổng kết?" run={async()=>{await request(`/api/courses/${courseId}/gradebook/publish`,"POST",{published:true});await load();window.dispatchEvent(new Event("course-finalized"))}} disabled={action.busy||!book}/>}
              <a
                className="button-link"
                href={`/api/courses/${courseId}/gradebook/export-csv`}
              >
                Xuất CSV ↓
              </a>
              <button
                className="secondary"
                onClick={() => void action.run(load, "")}
              >
                Làm mới
              </button>
            </div>
          </div>
        )}
        {!teacher && !book?.published && (
          <p className="section-note">
            Điểm thi tự cập nhật khi bạn kết thúc phiên và các bài đã chấm xong.
            Các đầu điểm cập nhật trực tiếp khi giảng viên lưu.
          </p>
        )}
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Mã sinh viên</th>
                <th>Họ tên</th>
                <th>Lớp</th>
                {(Object.entries(names) as [keyof Weights, string][]).map(
                  ([k, n]) => (
                    <th key={k}>
                      {n}
                      <br />
                      {book?.weights[k]}%
                    </th>
                  ),
                )}
                <th>Tổng kết</th>
              </tr>
            </thead>
            <tbody>
              {visibleRows.slice(pagination.start,pagination.end)
                .map((r) => (
                  <tr key={r.student_id}>
                    <td>{r.student_id}</td>
                    <td>{r.full_name}</td>
                    <td>{r.class_name}</td>
                    {(Object.keys(names) as (keyof Weights)[]).map((k) => (
                      <td key={k}>{teacher && !readonly ? <ScoreCell key={`${r.student_id}-${k}-${r[`${k}_score`]}`} value={r[`${k}_score`]} label={`${r.student_id} ${names[k]}`} save={async score=>{await request(`/api/courses/${courseId}/grades`,"PATCH",{items:[{student_id:r.student_id,component:k,score}]});await load()}}/> : r[`${k}_score`] ?? "—"}</td>
                    ))}
                    <td>
                      <strong style={{ color: "var(--primary)" }}>
                        {r.total_score ?? "—"}
                      </strong>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        {pagination.controls}
        {!book?.items.length && (
          <div className="empty">
            {teacher
              ? "Chưa có sinh viên trong khóa."
              : "Chưa có dữ liệu điểm."}
          </div>
        )}
        <p className="section-note">
          Điểm thi được quy đổi từ số bài AC theo cấu hình đề thi. Điểm tổng kết
          chỉ có khi các thành phần có trọng số dương đã đủ điểm.
          {teacher &&
            " Khi mở CSV trong Excel, import cột mã sinh viên dưới dạng Text để giữ số 0 đầu."}
        </p>
      </section>
    </div>
  );
}
