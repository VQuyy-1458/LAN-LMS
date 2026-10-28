"use client";
import { useState } from "react";
import Link from "next/link";
export type ScheduleEntry = {
  key: string;
  title: string;
  at: string;
  kind: string;
  href: string;
  course?: string;
};
const vietnamDay = (date: Date) =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Ho_Chi_Minh",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
export default function WeeklySchedule({
  entries,
}: {
  entries: ScheduleEntry[];
}) {
  const [offset, setOffset] = useState(0);
  const today = vietnamDay(new Date());
  const start = new Date(`${today}T12:00:00+07:00`);
  start.setUTCDate(
    start.getUTCDate() - ((start.getUTCDay() + 6) % 7) + offset * 7,
  );
  const days = Array.from({ length: 7 }, (_, i) => {
    const day = new Date(start);
    day.setUTCDate(day.getUTCDate() + i);
    return day.toISOString().slice(0, 10);
  });
  return (
    <section className="panel">
      <div className="panel-title">
        <div>
          <h2>Lịch trong tuần</h2>
          <p className="section-note">
            {days[0].split("-").reverse().join("/")} -{" "}
            {days[6].split("-").reverse().join("/")}
          </p>
        </div>
        <div className="actions">
          <button
            className="secondary"
            aria-label="Tuần trước"
            onClick={() => setOffset((value) => value - 1)}
          >
            ←
          </button>
          <button className="secondary" onClick={() => setOffset(0)}>
            Tuần này
          </button>
          <button
            className="secondary"
            aria-label="Tuần sau"
            onClick={() => setOffset((value) => value + 1)}
          >
            →
          </button>
        </div>
      </div>
      <div className="weekly-grid">
        {days.map((day, i) => (
          <div
            className={`weekly-day ${day === today ? "is-today" : ""}`}
            key={day}
          >
            <h3>
              {
                [
                  "Thứ hai",
                  "Thứ ba",
                  "Thứ tư",
                  "Thứ năm",
                  "Thứ sáu",
                  "Thứ bảy",
                  "Chủ nhật",
                ][i]
              }
              <small>
                {day.slice(8)}/{day.slice(5, 7)}
              </small>
            </h3>
            {entries
              .filter((entry) => vietnamDay(new Date(entry.at)) === day)
              .map((entry) => (
                <Link
                  className="weekly-event"
                  href={entry.href}
                  key={entry.key}
                >
                  <span className="badge">{entry.kind}</span>
                  <strong>{entry.title}</strong>
                  <span>
                    {new Intl.DateTimeFormat("vi-VN", {
                      timeZone: "Asia/Ho_Chi_Minh",
                      hour: "2-digit",
                      minute: "2-digit",
                    }).format(new Date(entry.at))}
                  </span>
                  {entry.course && <small>{entry.course}</small>}
                </Link>
              ))}
          </div>
        ))}
      </div>
    </section>
  );
}
