"use client";

import Link from "next/link";
import {
  LayoutDashboard,
  FolderKanban,
  CircleDot,
  PlayCircle,
  BarChart3,
  Video,
} from "lucide-react";

const items = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Projects",
    href: "/projects",
    icon: FolderKanban,
  },
  {
    name: "Recorder",
    href: "/recorder",
    icon: Video,
  },
  {
    name: "Tests",
    href: "/tests",
    icon: CircleDot,
  },
  {
    name: "Runs",
    href: "/runs",
    icon: PlayCircle,
  },
  {
    name: "Reports",
    href: "/reports",
    icon: BarChart3,
  },
];

export default function Sidebar() {
  return (
    <aside className="fixed bottom-0 left-0 top-16 w-60 border-r border-white/10 bg-[#0b0f15] p-4">
      <nav className="space-y-2">
        {items.map((item) => {
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm text-gray-400 transition hover:bg-white/5 hover:text-white"
            >
              <Icon size={18} />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}