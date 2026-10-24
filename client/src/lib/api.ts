import type {
  ApiErrorResponse,
} from "@/types/api";

export class ApiError extends Error {
  status: number;
  code?: string;
  requestId?: string;
  errors?: unknown;

  constructor(
    message: string,
    status: number,
    payload?: ApiErrorResponse,
  ) {
    super(message);

    this.name = "ApiError";
    this.status = status;
    this.code = payload?.code;
    this.requestId = payload?.request_id;
    this.errors = payload?.errors;
  }
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(path, {
    ...init,

    credentials: "same-origin",

    headers: {
      Accept: "application/json",

      ...(init.body
        ? {
            "Content-Type": "application/json",
          }
        : {}),

      ...init.headers,
    },
  });

  if (!response.ok) {
    let payload:
      | ApiErrorResponse
      | undefined;

    try {
      payload =
        (await response.json()) as ApiErrorResponse;
    } catch {
      payload = undefined;
    }

    throw new ApiError(
      payload?.detail ??
        "Không thể hoàn thành yêu cầu.",
      response.status,
      payload,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}