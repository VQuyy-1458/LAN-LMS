import { apiRequest } from "./api";
export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};
export type Course = {
  id: number;
  course_code: string;
  name: string;
  description: string;
  semester: string;
  academic_year: string;
  start_date: string | null;
  end_date: string | null;
};
export type Event = {
  id: number;
  course_id: number;
  title: string;
  description: string;
  event_type: string;
  starts_at: string;
  ends_at: string;
};
export type Exam = {
  id: number;
  course_id: number;
  title: string;
  grade_component: string;
  starts_at: string;
  ends_at: string;
  status: string;
  score_ladder: number[];
  problem_count: number;
  server_time: string;
};
export type Problem = {
  id: number;
  exam_id: number;
  title: string;
  statement: string;
  languages: string[];
  io_mode: string;
  input_filename: string | null;
  output_filename: string | null;
  time_limit_ms: number;
  memory_limit_mib: number;
  max_score: number;
  comparator: string;
};
export type ExamSession = {
  id: number;
  exam_id: number;
  student_id: string;
  full_name: string;
  status: string;
  ends_at: string;
  last_seen_at: string | null;
  connection_status: string;
  accepted_count: number;
  problem_count: number;
  total_score: number;
  pending_count: number;
  server_time: string;
};
export type Submission = {
  id: number;
  problem_id: number;
  student_id: string;
  language: string;
  status: string;
  verdict_code: string;
  score: number | null;
  received_at: string;
  compile_message: string;
  source_code?: string;
};
export const request = <T>(path: string, method: string, body?: unknown) =>
  apiRequest<T>(path, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
export const key = () =>
  Array.from(crypto.getRandomValues(new Uint8Array(16)), (x) =>
    x.toString(16).padStart(2, "0"),
  ).join("");
export function date(
  value: string | null,
  options?: Intl.DateTimeFormatOptions,
) {
  return value
    ? new Intl.DateTimeFormat("vi-VN", {
        timeZone: "Asia/Ho_Chi_Minh",
        dateStyle: "short",
        timeStyle: "short",
        ...options,
      }).format(new Date(value))
    : "—";
}
export const localISO = (value: string) => new Date(value).toISOString();
export function localInput(iso: string) {
  const d = new Date(iso);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
}
export const statusLabel: Record<string, string> = {
  draft: "Đang soạn",
  upcoming: "Sắp diễn ra",
  open: "Đang mở",
  ended: "Đã kết thúc",
  closed: "Đã đóng",
  active: "Đang thi",
  finished: "Đã nộp",
  expired: "Hết giờ",
  PENDING: "Đang chờ",
  COMPILING: "Đang biên dịch",
  RUNNING: "Đang chấm",
  AC: "AC",
  WA: "WA",
  CE: "CE",
  RTE: "RTE",
  TLE: "TLE",
  MLE: "MLE",
  SE: "Lỗi hệ thống",
};
