import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";
const source = await readFile(
  new URL("../src/lib/courseNavigation.ts", import.meta.url),
  "utf8",
);
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext },
}).outputText;
const { courseLocation, courseHref } = await import(
  "data:text/javascript;base64," + Buffer.from(compiled).toString("base64")
);
test("course functions retain course and tab after reload/back navigation", () => {
  const href = courseHref(true, 12, "attendance");
  assert.equal(href, "/teacher/courses?course=12&tab=attendance");
  assert.deepEqual(courseLocation(href.split("?")[1], true), {
    courseId: 12,
    tab: "attendance",
  });
  assert.equal(courseHref(false), "/student/courses");
  assert.deepEqual(courseLocation("?course=3&tab=exams", false), {
    courseId: 3,
    tab: "exams",
  });
});
test("invalid selection and teacher-only tabs never enable student functions", () => {
  assert.deepEqual(courseLocation("?course=-2&tab=students", false), {
    courseId: 0,
    tab: "overview",
  });
  assert.deepEqual(
    courseLocation("?course=9007199254740999&tab=unknown", true),
    { courseId: 0, tab: "overview" },
  );
});
