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
test("multiple practice and midterms remain available; only final is unique", () => {
  assert.deepEqual(availableExamComponents([]), [
    "practice",
    "midterm",
    "final",
  ]);
  assert.deepEqual(availableExamComponents([{ grade_component: "midterm" }]), [
    "practice",
    "midterm",
    "final",
  ]);
  assert.deepEqual(availableExamComponents([{ grade_component: "final" }]), [
    "practice",
    "midterm",
  ]);
  assert.deepEqual(
    availableExamComponents([
      { grade_component: "midterm" },
      { grade_component: "final" },
    ]),
    ["practice", "midterm"],
  );
});
