import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const shell = await readFile(
  new URL("../src/components/AppShell.tsx", import.meta.url),
  "utf8",
);
const page = await readFile(
  new URL("../src/app/(public)/change-password/page.tsx", import.meta.url),
  "utf8",
);

test("teacher and student shell exposes the shared password page", () => {
  assert.match(shell, /href="\/change-password"/);
  assert.match(shell, />\s*Đổi mật khẩu\s*</);
});

test("password page returns either role to its own dashboard", () => {
  assert.match(page, /`\/\$\{user\.role\}\/dashboard`/);
  assert.match(page, /user\?\.must_change_password/);
});
