"use client";
import { useState } from "react";
export function useAction() {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  async function run(fn: () => Promise<void>, success = "Đã lưu thay đổi.") {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await fn();
      setMessage(success);
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không thể hoàn tất thao tác");
      return false;
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, message, run, setError };
}
