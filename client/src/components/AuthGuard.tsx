"use client";
import { useEffect, useState, type ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { apiRequest, ApiError } from "@/lib/api";
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
  const [allowedRole, setAllowedRole] = useState<typeof role | null>(null);
  const [activeExam, setActiveExam] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let live = true;
    const redirect = (url: string) => {
      if (!live) return;
      setAllowedRole(null);
      router.replace(url);
    };
    // Revalidate in the background. Clearing authorization on every route change
    // unmounts the whole shell, reconnects WebSocket and discards page state.
    getCurrentUser()
      .then(async (user) => {
        if (!live) return;
        if (user.must_change_password) redirect("/change-password");
        else if (user.role !== role) redirect(`/${user.role}/dashboard`);
        else if (live) {
          if (role === "student") {
            const active = await apiRequest<{exam_id:number}|null>("/api/my/active-exam");
            if (!live) return;
            setActiveExam(active?.exam_id ?? null);
            if (active && (path !== "/student/exam" || Number(new URLSearchParams(location.search).get("exam")) !== active.exam_id)) {
              redirect(`/student/exam?exam=${active.exam_id}`); return;
            }
          }
          setAllowedRole(role);
          setError("");
        }
      })
      .catch((cause: unknown) => {
        if (!live) return;
        if (cause instanceof ApiError && cause.status === 401)
          redirect(`/login?next=${encodeURIComponent(window.location.pathname+window.location.search)}`);
        else setError("Chưa thể kiểm tra kết nối. Bạn có thể thử lại.");
      });
    return () => {
      live = false;
    };
  }, [role, router, path, retry]);
  useEffect(() => {
    const download = (event: MouseEvent) => {
      const anchor = (event.target as Element).closest?.("a");
      if (anchor && anchor.pathname.startsWith("/api/") && anchor.origin === location.origin)
        anchor.href = scopedUrl(anchor.href);
    };
    document.addEventListener("click", download, true);
    return () => document.removeEventListener("click", download, true);
  }, []);
  const examLocked = role === "student" && activeExam !== null &&
    (path !== "/student/exam" || (typeof window !== "undefined" && Number(new URLSearchParams(window.location.search).get("exam")) !== activeExam));
  return <>
    {error && <div className="alert" role="alert">{error} <button className="secondary" onClick={() => setRetry((value) => value + 1)}>Thử lại</button></div>}
    {allowedRole === role && !examLocked ? children : !error && <p role="status">{examLocked ? "Đang chuyển về phòng thi…" : "Đang kiểm tra phiên đăng nhập…"}</p>}
  </>;
}
