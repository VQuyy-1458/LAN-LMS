"use client";
import { useEffect, useRef, useState } from "react";
import type { IScannerControls } from "@zxing/browser";

export default function AttendanceScanner({
  onScan,
  disabled,
}: {
  onScan: (text: string) => void;
  disabled: boolean;
}) {
  const video = useRef<HTMLVideoElement>(null);
  const photoInput = useRef<HTMLInputElement>(null);
  const galleryInput = useRef<HTMLInputElement>(null);
  const controls = useRef<IScannerControls | null>(null);
  const generation = useRef(0);
  const [active, setActive] = useState(false),
    [error, setError] = useState("");
  function stop() {
    generation.current++;
    controls.current?.stop();
    controls.current = null;
    setActive(false);
  }
  useEffect(
    () => () => {
      generation.current++;
      controls.current?.stop();
    },
    [],
  );
  async function start() {
    stop();
    setError("");
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setError(
        "Quét liên tục cần HTTPS hoặc localhost. Với LAN HTTP, dùng nút Chụp QR để điểm danh ở trên; không cần cài chứng chỉ.",
      );
      return;
    }
    const version = generation.current;
    setActive(true);
    try {
      const { BrowserQRCodeReader } = await import("@zxing/browser");
      if (version !== generation.current || !video.current) return;
      const reader = new BrowserQRCodeReader();
      const handle = await reader.decodeFromVideoDevice(
        undefined,
        video.current,
        (result, _, scanner) => {
          if (version !== generation.current) {
            scanner.stop();
            return;
          }
          if (result) {
            scanner.stop();
            stop();
            onScan(result.getText());
          }
        },
      );
      if (version !== generation.current) handle.stop();
      else controls.current = handle;
    } catch (e) {
      if (version === generation.current) {
        stop();
        setError(
          e instanceof Error && e.name === "NotAllowedError"
            ? "Bạn chưa cho phép camera. Hãy cấp quyền camera trong trình duyệt hoặc chọn ảnh QR."
            : "Không mở được camera. Kiểm tra thiết bị, quyền truy cập hoặc chọn ảnh QR.",
        );
      }
    }
  }
  async function readImage(file?: File) {
    if (!file) return;
    stop();
    setError("");
    if (file.size > 10 * 1024 * 1024) {
      setError("Chọn ảnh nhỏ hơn 10 MB.");
      return;
    }
    const version = generation.current;
    const url = URL.createObjectURL(file);
    try {
      const { BrowserQRCodeReader } = await import("@zxing/browser");
      const result = await new BrowserQRCodeReader().decodeFromImageUrl(url);
      if (version === generation.current) onScan(result.getText());
    } catch {
      if (version === generation.current)
        setError(
          "Không đọc được QR trong ảnh. Hãy chụp rõ toàn bộ mã rồi thử lại.",
        );
    } finally {
      URL.revokeObjectURL(url);
    }
  }
  return (
    <div className="details-box">
      <h3>Quét QR điểm danh</h3>
      <p className="section-note">
        Bấm Chụp QR để mở camera điện thoại, chụp rõ mã giảng viên đang hiển thị
        rồi dùng ảnh đó. Hệ thống tự đọc mã và cập nhật Có mặt, không cần nhập
        mã hay xác nhận thêm trên web.
      </p>
      <video
        ref={video}
        playsInline
        muted
        aria-label="Camera quét QR"
        hidden={!active}
        style={{
          width: "100%",
          maxWidth: 480,
          borderRadius: 12,
          marginTop: 12,
        }}
      />
      <div className="actions">
        <button
          type="button"
          disabled={disabled || active}
          onClick={() => photoInput.current?.click()}
        >
          Chụp QR để điểm danh
        </button>
        <button
          type="button"
          className="secondary"
          disabled={disabled || active}
          onClick={() => galleryInput.current?.click()}
        >
          Chọn ảnh QR có sẵn
        </button>
      </div>
      <p className="section-note">
        Dùng được trên LAN HTTP, không cần cài chứng chỉ. Tùy điện thoại, chọn
        Camera nếu hiện bảng lựa chọn; trên máy tính có thể chọn ảnh QR.
      </p>
      <input
        ref={photoInput}
        type="file"
        accept="image/*"
        capture="environment"
        hidden
        disabled={disabled || active}
        onChange={(e) => {
          const file = e.target.files?.[0];
          e.target.value = "";
          void readImage(file);
        }}
      />
      <input
        ref={galleryInput}
        type="file"
        accept="image/*"
        hidden
        disabled={disabled || active}
        onChange={(e) => {
          const file = e.target.files?.[0];
          e.target.value = "";
          void readImage(file);
        }}
      />
      <details style={{ marginTop: 16 }}>
        <summary>Quét liên tục bằng camera trong web (HTTPS)</summary>
        <div className="actions">
          <button
            type="button"
            disabled={disabled || active}
            onClick={() => void start()}
          >
            Mở camera quét liên tục
          </button>
          {active && (
            <button type="button" className="secondary" onClick={stop}>
              Tắt camera
            </button>
          )}
        </div>
      </details>
      {error && (
        <p className="alert error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
