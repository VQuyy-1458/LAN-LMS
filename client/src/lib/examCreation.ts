import type { Exam } from "@/lib/lms";
export type ExamComponent = "practice" | "midterm" | "final";
export const examComponentLabel: Record<string, string> = {
  practice: "Test / Luyện tập",
  midterm: "Giữa kỳ",
  final: "Cuối kỳ",
};
export function availableExamComponents(
  exams: Pick<Exam, "grade_component">[],
): ExamComponent[] {
  return exams.some((exam) => exam.grade_component === "final")
    ? ["practice", "midterm"]
    : ["practice", "midterm", "final"];
}
