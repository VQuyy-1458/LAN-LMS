export function parseAttendanceQr(text: string) {
  // Read the payload locally; never navigate to an arbitrary scanned URL.
  const url = new URL(text, "https://lan-lms.invalid");
  const session = url.searchParams.get("attendance");
  const token = url.searchParams.get("token");
  if (
    !["http:", "https:"].includes(url.protocol) ||
    url.pathname !== "/student/courses" ||
    url.searchParams.getAll("attendance").length !== 1 ||
    url.searchParams.getAll("token").length !== 1 ||
    !/^[1-9]\d*$/.test(session || "") ||
    !Number.isSafeInteger(Number(session)) ||
    !token ||
    !/^[A-Za-z0-9_-]{1,200}$/.test(token)
  ) {
    throw new Error("Đây không phải mã QR điểm danh LAN-LMS hợp lệ.");
  }
  return { sessionId: Number(session), token };
}
