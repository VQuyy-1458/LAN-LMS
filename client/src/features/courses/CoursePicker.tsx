"use client";
import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import type { Course, Page } from "@/lib/lms";
export default function CoursePicker({
  value,
  onChange,
}: {
  value: number;
  onChange: (id: number) => void;
}) {
  const [courses, setCourses] = useState<Course[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    let live = true;
    apiRequest<Page<Course>>("/api/courses?page_size=100")
      .then((r) => {
        if (live) setCourses(r.items);
      })
      .catch((e) => setError(e.message));
    return () => {
      live = false;
    };
  }, []);
  return (
    <div className="course-picker">
      <label>
        Khóa học
        <select
          value={value || ""}
          onChange={(e) => onChange(Number(e.target.value))}
        >
          <option value="">Chọn khóa học</option>
          {courses.map((c) => (
            <option key={c.id} value={c.id}>
              {c.course_code} — {c.name}
            </option>
          ))}
        </select>
      </label>
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
