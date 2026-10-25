import type { ReactNode } from "react";

import AuthGuard from "@/components/AuthGuard";
import LogoutButton from "@/components/LogoutButton";

import AppSidebar from "@/components/AppSidebar";

const teacherNavigation = [
  {
    label: "Trang chủ",
    href: "/teacher/dashboard",
  },
  {
    label: "Khóa học",
    href: "/teacher/courses",
  },
  {
    label: "Sinh viên",
    href: "/teacher/students",
  },
  {
    label: "Điểm danh",
    href: "/teacher/attendance",
  },
  {
    label: "Kiểm tra & Thi",
    href: "/teacher/exams",
  },
  {
    label: "Bảng điểm",
    href: "/teacher/gradebook",
  },
];

export default function TeacherLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <AuthGuard role="teacher">
      <div className="flex min-h-screen bg-[#F7F8FB]">
        <AppSidebar items={teacherNavigation} />

        <main className="min-w-0 flex-1 p-6">
          <LogoutButton />
          {children}
        </main>
      </div>
    </AuthGuard>
  );
}
