import type { ApiErrorResponse } from "@/types/api";
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public payload?: ApiErrorResponse,
  ) {
    super(message);
    this.name = "ApiError";
  }
  get code() {
    return this.payload?.code;
  }
  get requestId() {
    return this.payload?.request_id;
  }
}
export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !(init.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  if (
    !["GET", "HEAD", "OPTIONS"].includes(
      (init.method ?? "GET").toUpperCase(),
    ) &&
    path !== "/api/auth/login"
  ) {
    const csrf = await fetch("/api/auth/csrf", {
      credentials: "same-origin",
      cache: "no-store",
    });
    if (!csrf.ok) {
      const payload = await csrf.json().catch(() => undefined);
      throw new ApiError(
        payload?.detail ?? "Phiên đăng nhập đã hết",
        csrf.status,
        payload,
      );
    }
    headers.set("X-CSRF-Token", (await csrf.json()).csrf_token);
  }
  const response = await fetch(path, {
    ...init,
    headers,
    credentials: "same-origin",
    cache: "no-store",
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => undefined);
    throw new ApiError(
      payload?.detail ?? "Không thể hoàn thành yêu cầu",
      response.status,
      payload,
    );
  }
  return response.status === 204
    ? (undefined as T)
    : ((await response.json()) as T);
}
