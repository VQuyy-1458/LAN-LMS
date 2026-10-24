export type UserRole =
  | "teacher"
  | "student";

export interface AuthUser {
  user_id: number;
  username: string;
  role: UserRole;
  must_change_password: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  user: AuthUser;
}

export interface CsrfResponse {
  csrf_token: string;
}

export interface ApiErrorResponse {
  detail?: string;
  code?: string;
  request_id?: string;
  errors?: unknown;
}