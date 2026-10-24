"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import CurrentUserPanel from "@/components/CurrentUserPanel";
export interface NavigationItem {
  label: string;
  href: string;
}

interface AppSidebarProps {
  items: NavigationItem[];
}

export default function AppSidebar({
  items,
}: AppSidebarProps) {
  const pathname = usePathname();

  return (
    <aside className="flex min-h-screen w-[230px] flex-col border-r border-gray-200 bg-white">
      <div className="border-b border-gray-100 px-5 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#CC0D00] font-bold text-white">
            L
          </div>

          <div>
            <p className="font-bold text-gray-900">
              LAN LMS
            </p>

            <p className="text-[10px] uppercase tracking-wide text-gray-400">
              Learning Portal
            </p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {items.map((item) => {
          const active =
            pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-lg px-4 py-2.5 text-sm font-medium transition ${
                active
                  ? "bg-red-50 text-[#CC0D00]"
                  : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-gray-100 p-4">
        <CurrentUserPanel />
      </div>
    </aside>
  );
}