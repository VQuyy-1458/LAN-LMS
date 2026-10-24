import { apiRequest } from "@/lib/api";

import type {
  AuthUser,
  CsrfResponse,
  LoginRequest,
  LoginResponse,
} from "@/types/api";

export function login(
  data: LoginRequest,
): Promise<LoginResponse> {
  return apiRequest<LoginResponse>(
    "/api/auth/login",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

export function getCurrentUser():
  Promise<AuthUser> {
  return apiRequest<AuthUser>(
    "/api/auth/me",
  );
}

export function getCsrfToken():
  Promise<CsrfResponse> {
  return apiRequest<CsrfResponse>(
    "/api/auth/csrf",
  );
}