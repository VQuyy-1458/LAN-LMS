import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";
const source = await readFile(
  new URL("../src/lib/examCreation.ts", import.meta.url),
  "utf8",
);
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext },
}).outputText;
const { availableExamComponents } = await import(
  "data:text/javascript;base64," + Buffer.from(compiled).toString("base64")
);
test("teacher can create only missing exam components", () => {
  assert.deepEqual(availableExamComponents([]), ["midterm", "final"]);
  assert.deepEqual(availableExamComponents([{ grade_component: "midterm" }]), [
    "final",
  ]);
  assert.deepEqual(availableExamComponents([{ grade_component: "final" }]), [
    "midterm",
  ]);
});
test("both existing exams hide the create form, including drafts and ended exams", () => {
  assert.deepEqual(
    availableExamComponents([
      { grade_component: "midterm", status: "draft" },
      { grade_component: "final", status: "ended" },
    ]),
    [],
  );
});
