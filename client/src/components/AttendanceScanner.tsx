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
        "Trình duyệt chưa cho phép quét trực tiếp. Bạn có thể chụp ảnh mã QR để điểm danh.",
      );
      return;
    }
    const version = generation.current;
    setActive(true);
    try {
      const { BrowserQRCodeReader } = await import("@zxing/browser");
      if (version !== generation.current || !video.current) return;
      const reader = new BrowserQRCodeReader();
      const handle = await reader.decodeFromConstraints(
        { video: { facingMode: { ideal: "environment" } }, audio: false },
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
        Hướng camera vào mã QR của giảng viên. Sau khi đọc được mã, hệ thống tự
        ghi nhận điểm danh.
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
          onClick={() => {
            if (
              window.isSecureContext &&
              typeof navigator.mediaDevices?.getUserMedia === "function"
            )
              void start();
            else photoInput.current?.click();
          }}
        >
          Bật camera quét QR
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
      {active && (
        <button type="button" className="secondary" onClick={stop}>
          Tắt camera
        </button>
      )}
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
      {error && (
        <p className="alert error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
