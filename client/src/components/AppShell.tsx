"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import AuthGuard from "./AuthGuard";
import LogoutButton from "./LogoutButton";
import CurrentUserPanel from "./CurrentUserPanel";
import Realtime, { Connection } from "./Realtime";
const teacherNav = [
  ["Tổng quan", "dashboard"],
  ["Khóa học", "courses"],
];
const studentNav = [
  ["Tổng quan", "dashboard"],
  ["Khóa học của tôi", "courses"],
];
export default function AppShell({
  teacher = false,
  children,
}: {
  teacher?: boolean;
  children: ReactNode;
}) {
  const path = usePathname(),
    role = teacher ? "teacher" : "student";
  return (
    <AuthGuard role={role}>
      <Realtime>
        <div className="utility-bar">
          <span>LAN-LMS · Không gian học tập và thi lập trình</span>
          <span>{teacher ? "Cổng giảng viên" : "Cổng sinh viên"}</span>
        </div>
        <header className="site-header">
          <Link className="brand" href={`/${role}/dashboard`}>
            <span className="brand-mark">L</span>
            <span>
              <strong>LAN-LMS</strong>
              <small>HỌC TẬP · THỰC HÀNH · ĐÁNH GIÁ</small>
            </span>
          </Link>
          <div className="header-account">
            <Connection />
            <CurrentUserPanel />
            <LogoutButton />
          </div>
        </header>
        <div className="app-frame">
          <aside className="app-nav">
            <div className="nav-caption">KHÔNG GIAN CỦA BẠN</div>
            {(teacher ? teacherNav : studentNav).map(([label, href], i) => (
              <Link
                key={href}
                href={`/${role}/${href}`}
                className={path.startsWith(`/${role}/${href}`) ? "active" : ""}
              >
                <span className="nav-number">
                  {String(i + 1).padStart(2, "0")}
                </span>
                {label}
              </Link>
            ))}
            <div className="nav-note">
              Chọn khóa học để bắt đầu.
              <br />
              <small>
                Lịch học, điểm danh, bài tập, kỳ thi và bảng điểm nằm trong từng
                khóa học.
              </small>
            </div>
          </aside>
          <main className="main-content">{children}</main>
        </div>
      </Realtime>
    </AuthGuard>
  );
}
