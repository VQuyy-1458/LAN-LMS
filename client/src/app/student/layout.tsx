import type { ReactNode } from "react";

import AppSidebar from "@/components/AppSidebar";

const studentNavigation = [
  {
    label: "Trang chủ",
    href: "/student/dashboard",
  },
  {
    label: "Khóa học của tôi",
    href: "/student/courses",
  },
  {
    label: "Lịch học & Thi",
    href: "/student/exams",
  },
  {
    label: "Bảng điểm & Kết quả",
    href: "/student/grades",
  },
];

export default function StudentLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <div className="flex min-h-screen bg-[#F7F8FB]">
      <AppSidebar
        items={studentNavigation}
      />

      <main className="min-w-0 flex-1 p-6">
        {children}
      </main>
    </div>
  );
}