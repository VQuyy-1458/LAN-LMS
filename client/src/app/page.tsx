"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth";
import type { AuthUser } from "@/types/api";
import type { Course, Page } from "@/lib/lms";

export default function HomePage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1),
    [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(() => {});
  }, []);
  useEffect(() => {
    let live = true;
    apiRequest<Page<Course>>(`/api/public/courses?page=${page}&page_size=10`)
      .then((r) => {
        if (live) {
          setCourses(r.items);
          setTotal(r.total);
          setError("");
        }
      })
      .catch((e) => {
        if (live) setError(e.message);
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [page]);
  const visible = courses.filter((c) =>
    `${c.name} ${c.course_code}`.toLowerCase().includes(search.toLowerCase()),
  );
  return (
    <>
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
        <Link
          className="button-link"
          href={user ? `/${user.role}/dashboard` : "/login"}
        >
          {user ? "Vào không gian học tập →" : "Đăng nhập →"}
        </Link>
      </header>
      <main className="public-main stack">
        <section className="public-hero">
          <div className="eyebrow">CỔNG HỌC TẬP LAN-LMS</div>
          <h1>Học tập, thực hành và kết nối cùng lớp.</h1>
          <p>
            Xem các khóa học đang mở. Đăng nhập để truy cập tài liệu, làm bài
            tập, quét QR điểm danh và tham gia kỳ thi lập trình.
          </p>
          <div className="actions">
            <a className="button-link" href="#courses">
              Khám phá khóa học ↓
            </a>
          </div>
        </section>
        <section id="courses" className="stack">
          <div className="panel-title">
            <div>
              <h2>Khóa học</h2>
              <p className="section-note">
                {total} khóa học · Nội dung khóa học dành cho thành viên được
                cấp quyền.
              </p>
            </div>
          </div>
          <input
            aria-label="Tìm khóa học trên trang"
            placeholder="Tìm tên hoặc mã khóa học trong trang này…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {error && (
            <p className="alert error" role="alert">
              {error}
            </p>
          )}
          {loading ? (
            <p role="status">Đang tải khóa học…</p>
          ) : (
            <div className="grid-3">
              {visible.map((c) => {
                const next = `/${user?.role || "student"}/courses?course=${c.id}`;
                return (
                  <Link
                    className="panel course-card"
                    key={c.id}
                    href={
                      user ? next : `/login?next=${encodeURIComponent(next)}`
                    }
                  >
                    <div className="course-cover">
                      <small>{c.course_code}</small>
                      <h3>{c.name}</h3>
                    </div>
                    <div className="course-body">
                      <p>
                        Học kỳ {c.semester} · {c.academic_year}
                      </p>
                      <p>
                        {c.description ||
                          "Khám phá nội dung và hoạt động của khóa học."}
                      </p>
                      <div className="course-footer">
                        <span>
                          {user ? "Mở khóa học" : "Đăng nhập để vào học"}
                        </span>
                        <span>→</span>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
          {!loading && !error && !visible.length && (
            <div className="empty">Chưa có khóa học phù hợp.</div>
          )}
          <div className="actions">
            <button
              className="secondary"
              disabled={page === 1}
              onClick={() => {
                setLoading(true);
                setPage((p) => p - 1);
              }}
            >
              Trước
            </button>
            <span>Trang {page}</span>
            <button
              className="secondary"
              disabled={page * 10 >= total}
              onClick={() => {
                setLoading(true);
                setPage((p) => p + 1);
              }}
            >
              Sau
            </button>
          </div>
        </section>
        <footer className="section-note">
          LAN-LMS · Không gian học tập trong mạng nội bộ
        </footer>
      </main>
    </>
  );
}
