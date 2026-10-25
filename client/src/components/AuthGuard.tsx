"use client";
import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
export default function AuthGuard({
  role,
  children,
}: {
  role: "teacher" | "student";
  children: ReactNode;
}) {
  const router = useRouter();
  const [allowed, setAllowed] = useState(false);
  useEffect(() => {
    let live = true;
    getCurrentUser()
      .then((user) => {
        if (user.must_change_password) router.replace("/change-password");
        else if (user.role !== role) router.replace(`/${user.role}/dashboard`);
        else if (live) setAllowed(true);
      })
      .catch(() => router.replace("/login"));
    return () => {
      live = false;
    };
  }, [role, router]);
  return allowed ? (
    children
  ) : (
    <p role="status">Đang kiểm tra phiên đăng nhập…</p>
  );
}
