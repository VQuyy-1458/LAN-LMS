import type { Exam } from "@/lib/lms";

export type ExamComponent = "midterm" | "final";
export function availableExamComponents(
  exams: Pick<Exam, "grade_component">[],
): ExamComponent[] {
  return (["midterm", "final"] as const).filter(
    (component) => !exams.some((exam) => exam.grade_component === component),
  );
}
