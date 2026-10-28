"use client";
import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser, login } from "@/lib/auth";
import type { AuthUser } from "@/types/api";
export default function Login() {
  const [username, setUsername] = useState(""),
    [password, setPassword] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const router = useRouter();
  function destination(user: AuthUser) {
    if (user.must_change_password) return "/change-password";
    const next = new URLSearchParams(window.location.search).get("next");
    return next && next.startsWith(`/${user.role}/`)
      ? next
      : `/${user.role}/dashboard`;
  }
  useEffect(() => {
    let live = true;
    getCurrentUser()
      .then((user) => {
        if (live) {
          const next = new URLSearchParams(window.location.search).get("next");
          router.replace(
            user.must_change_password
              ? "/change-password"
              : next && next.startsWith(`/${user.role}/`)
                ? next
                : `/${user.role}/dashboard`,
          );
        }
      })
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [router]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await login({ username: username.trim(), password });
      router.replace(destination(r.user));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không thể đăng nhập");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div
      style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}
    >
      <div className="utility-bar">
        <span>HỆ THỐNG HỌC TẬP VÀ THI LẬP TRÌNH TRONG MẠNG LAN</span>
      </div>
      <header className="site-header">
        <Link className="brand" href="/">
          <span className="brand-mark">L</span>
          <span>
            <strong>LAN-LMS</strong>
            <small>HỌC TẬP · THỰC HÀNH · ĐÁNH GIÁ</small>
          </span>
        </Link>
        <Link className="muted" href="/">← Về trang chủ</Link>
      </header>
      <main
        style={{
          flex: 1,
          display: "grid",
          placeItems: "center",
          padding: "40px 18px",
        }}
      >
        <section
          className="panel"
          style={{ width: "100%", maxWidth: 440, padding: 36 }}
        >
          <div className="eyebrow">ĐĂNG NHẬP HỆ THỐNG</div>
          <h1>Đăng nhập</h1>
          <p className="muted" style={{ margin: "8px 0 26px" }}>
            Truy cập khóa học, bài tập và kỳ thi của bạn.
          </p>
          {error && (
            <div className="alert error" role="alert">
              {error}
            </div>
          )}
          <form onSubmit={submit}>
            <label>
              Tên đăng nhập / Mã sinh viên
              <input
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                maxLength={128}
                style={{ marginBottom: 20 }}
              />
            </label>
            <label>
              Mật khẩu
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                maxLength={128}
              />
            </label>
            <button
              disabled={busy}
              style={{ width: "100%", marginTop: 25, padding: 12 }}
            >
              {busy ? "Đang đăng nhập…" : "Đăng nhập →"}
            </button>
          </form>
          <div
            style={{
              borderTop: "1px solid var(--border)",
              marginTop: 25,
              paddingTop: 20,
            }}
          >
            <p className="section-note">
              Sinh viên dùng tài khoản giảng viên cung cấp. Lần đầu đăng nhập
              cần đổi mật khẩu. Nếu cần hỗ trợ, liên hệ giảng viên phụ trách
              khóa học.
            </p>
          </div>
        </section>
      </main>
      <footer
        style={{
          textAlign: "center",
          padding: 20,
          color: "var(--text-secondary)",
          fontSize: 11,
        }}
      >
        LAN-LMS · Học tập và thực hành trong mạng LAN
      </footer>
    </div>
  );
}
