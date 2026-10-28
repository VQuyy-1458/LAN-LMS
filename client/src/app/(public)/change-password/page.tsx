"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth";
import type { AuthUser } from "@/types/api";

export default function ChangePassword() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(() => router.replace("/login"));
  }, [router]);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setError("");
    if (form.get("new") !== form.get("confirm")) {
      setError("Mật khẩu xác nhận không khớp");
      return;
    }
    setBusy(true);
    try {
      await apiRequest("/api/auth/change-password", {
        method: "POST",
        body: JSON.stringify({
          current_password: form.get("current"),
          new_password: form.get("new"),
        }),
      });
      router.replace("/login");
      router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể đổi mật khẩu");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="password-page">
      <section className="panel password-panel">
        <div className="page-heading">
          <div>
            <p className="eyebrow">BẢO MẬT TÀI KHOẢN</p>
            <h1>Đổi mật khẩu</h1>
            <p>
              {user?.must_change_password
                ? "Bạn cần đổi mật khẩu ban đầu trước khi sử dụng hệ thống."
                : "Cập nhật mật khẩu cho tài khoản của bạn."}{" "}
              Sau khi đổi thành công, bạn cần đăng nhập lại.
            </p>
          </div>
        </div>
        <form onSubmit={submit} className="stack">
          {[
            ["current", "Mật khẩu hiện tại"],
            ["new", "Mật khẩu mới"],
            ["confirm", "Xác nhận mật khẩu mới"],
          ].map(([name, label]) => (
            <label key={name}>
              {label}
              <input
                type="password"
                name={name}
                required
                minLength={name === "current" ? 1 : 8}
                maxLength={128}
                autoComplete={name === "current" ? "current-password" : "new-password"}
              />
            </label>
          ))}
          {error && <p className="alert error" role="alert">{error}</p>}
          <div className="actions">
            <button disabled={busy}>{busy ? "Đang đổi…" : "Đổi mật khẩu"}</button>
            {user && !user.must_change_password && (
              <Link className="button-link" href={`/${user.role}/dashboard`}>
                Quay lại
              </Link>
            )}
          </div>
        </form>
      </section>
    </main>
  );
}
