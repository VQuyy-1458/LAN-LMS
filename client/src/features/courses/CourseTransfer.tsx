"use client";
import { useRef, useState } from "react";
import { apiRequest } from "@/lib/api";
import { key } from "@/lib/lms";
import { useAction } from "@/lib/useAction";
import Feedback from "@/components/Feedback";

export default function CourseTransfer({
  courseId,
  imported,
}: {
  courseId?: number;
  imported?: (id: number) => Promise<void>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<{
    name: string;
    course_code: string;
    counts: Record<string, number>;
  } | null>(null);
  const [code, setCode] = useState("");
  const attempt = useRef(key());
  const action = useAction();
  return (
    <section className="panel">
      <details>
        <summary>
          {courseId
            ? "Xuất toàn bộ dữ liệu khóa học"
            : "Nhập khóa học từ file ZIP"}
        </summary>
        <p className="section-note">
          Gói gồm nội dung, sinh viên, bài nộp, điểm và nhật ký thi. Có hồ sơ
          sinh viên và mã băm mật khẩu; chỉ lưu/chuyển cho người được phép quản
          lý lớp.
        </p>
        <Feedback error={action.error} message={action.message} />
        {courseId ? (
          <a
            className="button"
            href={`/api/courses/${courseId}/export-package`}
          >
            Tải gói khóa học (.zip)
          </a>
        ) : (
          <>
            <p className="section-note">
              Nhập thành khóa mới do bạn quản lý. Tài khoản trùng chỉ được dùng
              lại khi hồ sơ khớp; mật khẩu tài khoản có sẵn được giữ nguyên. Giờ
              thi/hạn nộp giữ nguyên; bài chờ chấm được tiếp tục. Sau khi chuyển
              máy, sinh viên đăng nhập lại; giảng viên tạo QR mới.
            </p>
            <label>
              Gói khóa học
              <input
                type="file"
                accept=".zip"
                onChange={(event) => {
                  setFile(event.target.files?.[0] || null);
                  setPreview(null);
                  attempt.current = key();
                }}
              />
            </label>
            <button
              className="secondary"
              disabled={!file || action.busy}
              onClick={() =>
                void action.run(async () => {
                  const body = new FormData();
                  body.set("file", file!);
                  const result = await apiRequest<{
                    name: string;
                    course_code: string;
                    counts: Record<string, number>;
                  }>("/api/courses/import-package/preview", {
                    method: "POST",
                    body,
                  });
                  setPreview(result);
                  setCode(result.course_code);
                })
              }
            >
              Kiểm tra gói
            </button>
            {preview && (
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  void action.run(async () => {
                    const body = new FormData();
                    body.set("file", file!);
                    body.set("course_code", code);
                    const result = await apiRequest<{ id: number }>(
                      "/api/courses/import-package",
                      {
                        method: "POST",
                        body,
                        headers: { "Idempotency-Key": attempt.current },
                      },
                    );
                    await imported?.(result.id);
                  }, "Đã nhập khóa học.");
                }}
              >
                <h3>{preview.name}</h3>
                <p>
                  {preview.counts.students} sinh viên ·{" "}
                  {preview.counts.coding_exams} đề thi ·{" "}
                  {preview.counts.assignment_submissions} bài nộp file ·{" "}
                  {preview.counts.code_submissions} bài nộp code
                </p>
                <label>
                  Mã khóa học trên máy này
                  <input
                    value={code}
                    required
                    maxLength={128}
                    onChange={(event) => {
                      setCode(event.target.value);
                      attempt.current = key();
                    }}
                  />
                </label>
                <p className="section-note">
                  Nếu mã khóa + học kỳ + năm học đã tồn tại, đổi mã để tạo bản
                  mới; không ghi đè dữ liệu cũ.
                </p>
                <button disabled={action.busy}>
                  Xác nhận nhập cả nội dung và dữ liệu lớp
                </button>
              </form>
            )}
          </>
        )}
      </details>
    </section>
  );
}
