export const courseTabs = [
  "overview",
  "students",
  "materials",
  "calendar",
  "attendance",
  "assignments",
  "exams",
  "grades",
] as const;
export type CourseTab = (typeof courseTabs)[number];
export function courseLocation(
  query: string,
  teacher: boolean,
  fallback: CourseTab = "overview",
) {
  const params = new URLSearchParams(query);
  const raw = params.get("course") || "";
  const courseId =
    /^[1-9]\d*$/.test(raw) && Number.isSafeInteger(Number(raw))
      ? Number(raw)
      : 0;
  const value = params.get("tab");
  const tab = courseTabs.includes(value as CourseTab)
    ? (value as CourseTab)
    : fallback;
  return {
    courseId,
    tab: !teacher && tab === "students" ? ("overview" as const) : tab,
  };
}
export function courseHref(
  teacher: boolean,
  id = 0,
  tab: CourseTab = "overview",
) {
  const path = `/${teacher ? "teacher" : "student"}/courses`;
  if (!id) return path;
  const params = new URLSearchParams({ course: String(id), tab });
  return `${path}?${params}`;
}
