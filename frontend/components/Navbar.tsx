"use client";

import Link from "next/link";
import { TestTube2, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { logout } from "../lib/auth";

export default function Navbar() {
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <header className="fixed left-0 right-0 top-0 z-50 border-b border-white/10 bg-[#07090d]/90 backdrop-blur-xl">
      <div className="flex h-16 items-center justify-between px-6">
        <Link
          href="/dashboard"
          className="flex items-center gap-3"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-500/15 text-purple-400">
            <TestTube2 size={20} />
          </div>

          <span className="text-lg font-bold">
            Test AI
          </span>
        </Link>

        <button
          onClick={handleLogout}
          className="flex items-center gap-2 rounded-lg border border-white/10 px-4 py-2 text-sm text-gray-300 hover:bg-white/5"
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </header>
  );
}