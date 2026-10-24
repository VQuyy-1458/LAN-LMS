"use client";

import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

import { useRouter } from "next/navigation";

import {
  getCurrentUser,
  login,
} from "@/lib/auth";

import { ApiError } from "@/lib/api";

function HeaderLogoIcon() {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M2.5 8.5L12 4L21.5 8.5L12 13L2.5 8.5Z"
        stroke="white"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M6.5 10.5V14.8C6.5 16.3 9 18 12 18C15 18 17.5 16.3 17.5 14.8V10.5"
        stroke="white"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function GraduationCapIcon() {
  return (
    <svg
      width="42"
      height="42"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M2.5 8.5L12 4L21.5 8.5L12 13L2.5 8.5Z"
        fill="#CC0D00"
      />
      <path
        d="M6.5 10.4V14.8C6.5 16.4 9 18 12 18C15 18 17.5 16.4 17.5 14.8V10.4L12 13L6.5 10.4Z"
        fill="#CC0D00"
      />
      <path
        d="M21.5 8.5V14"
        stroke="#CC0D00"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg
      width="21"
      height="21"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle
        cx="12"
        cy="8"
        r="4"
        stroke="#94A3B8"
        strokeWidth="1.8"
      />
      <path
        d="M4.5 20C5.2 15.8 8 14 12 14C16 14 18.8 15.8 19.5 20"
        stroke="#94A3B8"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg
      width="21"
      height="21"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <rect
        x="5"
        y="10"
        width="14"
        height="10"
        rx="2"
        stroke="#94A3B8"
        strokeWidth="1.8"
      />
      <path
        d="M8 10V7.5C8 5.3 9.8 3.5 12 3.5C14.2 3.5 16 5.3 16 7.5V10"
        stroke="#94A3B8"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();

  const [username, setUsername] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState("");

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  useEffect(() => {
    async function checkSession() {
      try {
        const user =
          await getCurrentUser();

        redirectUser(user);
      } catch {
        // Chưa đăng nhập thì ở lại trang login
      }
    }

    void checkSession();
  }, []);

  function redirectUser(user: {
    role: "teacher" | "student";
    must_change_password: boolean;
  }) {
    if (user.must_change_password) {
      router.replace("/change-password");
      return;
    }

    if (user.role === "teacher") {
      router.replace("/teacher/dashboard");
      return;
    }

    router.replace("/student/dashboard");
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");

    if (username.trim() === "") {
      setError("Vui lòng nhập mã sinh viên.");
      return;
    }

    if (password === "") {
      setError("Vui lòng nhập mật khẩu.");
      return;
    }

    setIsSubmitting(true);

    try {
      await login({
        username: username.trim(),
        password,
      });

      const user =
        await getCurrentUser();

      redirectUser(user);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Không thể kết nối tới máy chủ.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#F7F9FC]">
      {/* HEADER */}
      <header className="flex h-[84px] shrink-0 items-center border-b border-[#E5EAF1] bg-white px-[58px]">
        <div className="flex items-center gap-4">
          <div className="flex h-[44px] w-[44px] items-center justify-center rounded-[10px] bg-[#CC0D00] shadow-sm">
            <HeaderLogoIcon />
          </div>

          <span className="text-[20px] font-bold text-[#1E293B]">
            Hệ thống LAN LMS
          </span>
        </div>
      </header>

      {/* MAIN */}
      <main className="flex flex-1 items-center justify-center px-4 py-[52px]">
        <section className="w-full max-w-[470px] rounded-[20px] bg-white px-[40px] pb-[40px] pt-[40px] shadow-[0_16px_42px_rgba(15,23,42,0.08)]">
          {/* ICON */}
          <div className="mb-[44px] flex justify-center">
            <div className="flex h-[78px] w-[78px] items-center justify-center rounded-[18px] bg-[#FFF1F1]">
              <GraduationCapIcon />
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            {/* MÃ SINH VIÊN */}
            <div className="mb-[26px]">
              <label
                htmlFor="username"
                className="mb-[11px] block text-[16px] font-bold text-[#334155]"
              >
                Mã sinh viên
              </label>

              <div className="flex h-[58px] items-center rounded-[12px] border border-[#DCE3EC] bg-white px-[18px] transition focus-within:border-[#CC0D00]">
                <UserIcon />

                <input
                  id="username"
                  name="username"
                  value={username}
                  onChange={(event) =>
                    setUsername(event.target.value)
                  }
                  autoComplete="username"
                  placeholder="Nhập mã sinh viên"
                  className="ml-3 min-w-0 flex-1 bg-transparent text-[16px] text-[#334155] outline-none placeholder:text-[#9EACC0]"
                />
              </div>
            </div>

            {/* MẬT KHẨU */}
            <div>
              <label
                htmlFor="password"
                className="mb-[11px] block text-[16px] font-bold text-[#334155]"
              >
                Mật khẩu
              </label>

              <div className="flex h-[58px] items-center rounded-[12px] border border-[#DCE3EC] bg-white px-[18px] transition focus-within:border-[#CC0D00]">
                <LockIcon />

                <input
                  id="password"
                  name="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  type="password"
                  autoComplete="current-password"
                  placeholder="Nhập mật khẩu"
                  className="ml-3 min-w-0 flex-1 bg-transparent text-[16px] text-[#334155] outline-none placeholder:text-[#9EACC0]"
                />
              </div>
            </div>

            {/* ERROR */}
            {error ? (
              <div className="mt-[18px] rounded-[10px] border border-red-100 bg-red-50 px-4 py-3 text-[13px] text-[#CC0D00]">
                {error}
              </div>
            ) : null}

            {/* BUTTON */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="mt-[28px] h-[64px] w-full cursor-pointer rounded-[13px] bg-[#CC0D00] text-[20px] font-extrabold text-white shadow-[0_13px_25px_rgba(204,13,0,0.20)] transition hover:bg-[#B90C00] disabled:cursor-wait disabled:opacity-75"
            >
              {isSubmitting
                ? "Đang đăng nhập..."
                : "Đăng nhập"}
            </button>

            {/* DIVIDER */}
            <div className="mt-[40px] border-t border-[#E9EEF4]" />

            {/* SUPPORT */}
            <div className="pt-[28px] text-center">
              <p className="text-[13px] leading-[1.75] text-[#8190A5]">
                Cần hỗ trợ đăng nhập? Liên hệ{" "}
                <span className="font-semibold text-[#CC0D00]">
                  Phòng Công nghệ
                  <br />
                  Thông tin
                </span>{" "}
                hoặc Hotline{" "}
                <span className="font-bold text-[#475569]">
                  1900 6868
                </span>
              </p>
            </div>
          </form>
        </section>
      </main>

      {/* FOOTER */}
      <footer className="flex h-[62px] shrink-0 items-center justify-center border-t border-[#E5EAF1] bg-white">
        <p className="text-[12px] text-[#A0AEC0]">
          © 2024 LAN LMS - Hệ thống quản lý học tập trong mạng LAN.
        </p>
      </footer>
    </div>
  );
}