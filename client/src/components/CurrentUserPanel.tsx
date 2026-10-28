"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  getCurrentUser,
} from "@/lib/auth";

import type {
  AuthUser,
} from "@/types/api";

export default function CurrentUserPanel() {
  const [user, setUser] =
    useState<AuthUser | null>(null);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {
    async function loadUser() {
      try {
        const result =
          await getCurrentUser();

        setUser(result);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    void loadUser();
  }, []);

  if (loading) {
    return (
      <div className="space-y-2">
        <div className="h-3 w-24 animate-pulse rounded bg-gray-100" />
        <div className="h-2 w-16 animate-pulse rounded bg-gray-100" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-red-50 font-semibold uppercase text-[#CC0D00]">
        {user.username.charAt(0)}
      </div>

      <div className="min-w-0">
        <p className="truncate text-sm font-semibold text-gray-800">
          {user.username}
        </p>

        <p className="text-xs text-gray-400">
          {user.role ===
          "teacher"
            ? "Giảng viên"
            : "Sinh viên"}
        </p>
      </div>
    </div>
  );
}