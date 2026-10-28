"use client";
import { useEffect, useState } from "react";
import { key, request } from "@/lib/lms";

type Event = { event_key: string; event_type: string };
export default function ExamFocus({ sessionId }: { sessionId: number }) {
  const [warning, setWarning] = useState("");
  const [fullscreen, setFullscreen] = useState(false);
  useEffect(() => {
    const storageKey = `lan-lms-focus-${sessionId}`;
    let queue: Event[] = [];
    try {
      queue = JSON.parse(localStorage.getItem(storageKey) || "[]");
    } catch {
      /* optional storage */
    }
    let sending = false;
    const save = () => {
      try {
        localStorage.setItem(storageKey, JSON.stringify(queue));
      } catch {
        /* optional storage */
      }
    };
    const flush = async () => {
      if (sending) return;
      sending = true;
      try {
        while (queue.length) {
          await request(
            `/api/exam-sessions/${sessionId}/events`,
            "POST",
            queue[0],
          );
          queue.shift();
          save();
        }
      } catch {
        /* Retain unsent events on this browser and retry after reconnection. */
      } finally {
        sending = false;
      }
    };
    const last: Record<string, number> = {};
    const record = (event_type: string) => {
      if (Date.now() - (last[event_type] || 0) < 1500) return;
      last[event_type] = Date.now();
      setWarning(
        "Bạn vừa rời màn hình thi. Sự kiện được ghi nhận để giảng viên xem; hãy tiếp tục làm bài tại đây.",
      );
      if (queue.length < 1000) {
        queue.push({ event_key: key(), event_type });
        save();
      }
      void flush();
    };
    const visibility = () => {
      if (document.hidden) record("tab_hidden");
    };
    const blur = () => record("window_blur");
    let wasFullscreen = !!document.fullscreenElement;
    setFullscreen(wasFullscreen);
    const change = () => {
      const current = !!document.fullscreenElement;
      setFullscreen(current);
      if (wasFullscreen && !current) record("fullscreen_exit");
      wasFullscreen = current;
    };
    document.addEventListener("visibilitychange", visibility);
    document.addEventListener("fullscreenchange", change);
    window.addEventListener("blur", blur);
    window.addEventListener("online", flush);
    const leaving=(event:BeforeUnloadEvent)=>{event.preventDefault();event.returnValue=""};
    window.addEventListener("beforeunload",leaving);
    const timer = setInterval(() => void flush(), 5000);
    void flush();
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", visibility);
      document.removeEventListener("fullscreenchange", change);
      window.removeEventListener("blur", blur);
      window.removeEventListener("online", flush);
      window.removeEventListener("beforeunload",leaving);
    };
  }, [sessionId]);
  return (
    <section className="panel" aria-label="Giám sát phiên thi">
      <p>
        Trong thời gian thi, vui lòng giữ toàn màn hình. Rời tab, mất tiêu điểm
        và thoát toàn màn hình được ghi nhật ký; phiên thi vẫn tiếp tục.
      </p>
      {!fullscreen && (
        <button
          className="secondary"
          onClick={() => {
            if (!document.documentElement.requestFullscreen) {
              setWarning(
                "Trình duyệt này không hỗ trợ toàn màn hình. Bạn vẫn có thể làm bài; vui lòng giữ tab thi.",
              );
              return;
            }
            void document.documentElement
              .requestFullscreen()
              .catch(() =>
                setWarning(
                  "Không bật được toàn màn hình. Hãy cho phép toàn màn hình hoặc tiếp tục giữ tab thi.",
                ),
              );
          }}
        >
          Bật toàn màn hình
        </button>
      )}
      {warning && (
        <p role="status" className="section-note">
          {warning}
        </p>
      )}
    </section>
  );
}
