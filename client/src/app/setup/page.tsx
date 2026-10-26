"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";

type Connection = {
  origin: string | null;
  fingerprint: string | null;
  certificate_available: boolean;
};
export default function PhoneSetup() {
  const [connection, setConnection] = useState<Connection | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    apiRequest<Connection>("/api/public/connection")
      .then(setConnection)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <main className="public-main stack" style={{ maxWidth: 800 }}>
      <Link className="brand" href="/">
        LAN-LMS
      </Link>
      <section className="panel stack">
        <h1>Mở camera điểm danh trên điện thoại</h1>
        <p>
          Cài chứng chỉ LAN-LMS một lần trên điện thoại, sau đó dùng địa chỉ
          HTTPS của lớp. Kết nối cùng Wi-Fi/LAN với máy chủ.
        </p>
        {error && (
          <p role="alert" className="alert error">
            {error}
          </p>
        )}
        {connection?.certificate_available ? (
          <>
            <a className="button-link" href="/api/public/lan-certificate">
              1. Tải chứng chỉ LAN-LMS-CA.cer
            </a>
            <p className="section-note">
              Chỉ cài chứng chỉ do máy chủ của lớp cung cấp. Đối chiếu SHA-256
              dưới đây với cửa sổ CHAY_LAN trên máy chủ:
            </p>
            <code style={{ overflowWrap: "anywhere" }}>
              {connection.fingerprint}
            </code>
          </>
        ) : (
          <p>Máy chủ chưa bật HTTPS LAN. Chạy lại CHAY_LAN.cmd trên máy chủ.</p>
        )}
        <div className="details-box">
          <h2>2. Cài trên Android</h2>
          <p>
            Mở Cài đặt, tìm “Cài đặt chứng chỉ” hoặc “Chứng chỉ CA”, chọn cài
            chứng chỉ CA từ bộ nhớ và chọn file vừa tải. Xác nhận bằng mã khóa
            máy nếu được hỏi. Tên mục có thể khác theo hãng điện thoại.
          </p>
          <a
            className="button-link"
            href="https://support.google.com/pixelphone/answer/2844832"
          >
            Hướng dẫn của Google ↗
          </a>
        </div>
        <div className="details-box">
          <h2>2. Cài trên iPhone / iPad</h2>
          <p>
            Dùng Safari tải chứng chỉ. Vào Cài đặt → Đã tải về hồ sơ (hoặc Cài
            đặt chung → VPN & Quản lý thiết bị) để cài. Sau đó vào Cài đặt chung
            → Giới thiệu → Cài đặt tin cậy chứng nhận, bật tin cậy hoàn toàn cho
            “LAN-LMS Local CA”.
          </p>
          <a className="button-link" href="https://support.apple.com/102390">
            Hướng dẫn của Apple ↗
          </a>
        </div>
        {connection?.origin && (
          <a className="button-link" href={connection.origin}>
            3. Mở LAN-LMS qua HTTPS →
          </a>
        )}
        <p>
          Sau khi vào HTTPS: đăng nhập → chọn khóa học → Điểm danh → Mở camera
          quét QR → cho phép camera. Quét thành công sẽ tự cập nhật Có mặt.
        </p>
        <p className="section-note">
          Nếu chưa cài chứng chỉ, bạn vẫn có thể dùng Chụp / chọn ảnh QR. Không
          cần tắt tính năng bảo mật của trình duyệt. Khi không còn dùng lớp học,
          có thể gỡ chứng chỉ trong cài đặt điện thoại.
        </p>
      </section>
    </main>
  );
}
