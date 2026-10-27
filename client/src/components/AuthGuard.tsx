"use client";
import { useEffect, useState, type ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { apiRequest } from "@/lib/api";
import { scopedUrl } from "@/lib/sessionScope";
export default function AuthGuard({
  role,
  children,
}: {
  role: "teacher" | "student";
  children: ReactNode;
}) {
  const router = useRouter();
  const path = usePathname();
  const [allowed, setAllowed] = useState(false);
  useEffect(() => {
    let live = true;
    setAllowed(false);
    getCurrentUser()
      .then(async (user) => {
        if (user.must_change_password) router.replace("/change-password");
        else if (user.role !== role) router.replace(`/${user.role}/dashboard`);
        else if (live) {
          if (role === "student") {
            const active = await apiRequest<{exam_id:number}|null>("/api/my/active-exam");
            if (active && (path !== "/student/exam" || Number(new URLSearchParams(location.search).get("exam")) !== active.exam_id)) {
              setAllowed(false); router.replace(`/student/exam?exam=${active.exam_id}`); return;
            }
          }
          setAllowed(true);
        }
      })
      .catch(() => router.replace(`/login?next=${encodeURIComponent(window.location.pathname+window.location.search)}`));
    return () => {
      live = false;
    };
  }, [role, router, path]);
  useEffect(() => {
    const download = (event: MouseEvent) => {
      const anchor = (event.target as Element).closest?.("a");
      if (anchor && anchor.pathname.startsWith("/api/") && anchor.origin === location.origin)
        anchor.href = scopedUrl(anchor.href);
    };
    document.addEventListener("click", download, true);
    return () => document.removeEventListener("click", download, true);
  }, []);
  return allowed ? (
    children
  ) : (
    <p role="status">Đang kiểm tra phiên đăng nhập…</p>
  );
}
