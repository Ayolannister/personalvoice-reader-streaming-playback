"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Library, Mic2, Settings, BookPlus } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Library", icon: Library },
  { href: "/voices", label: "Voices", icon: Mic2 },
  { href: "/upload", label: "Add book", icon: BookPlus },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function NavRail() {
  const pathname = usePathname();

  return (
    <nav className="hidden md:flex w-56 shrink-0 flex-col border-r border-ink-hairline bg-ink-surface px-3 py-6">
      <Link href="/" className="px-3 mb-8 flex items-baseline gap-1.5">
        <span className="font-display text-lg font-medium text-paper">PersonalVoice</span>
        <span className="font-display text-lg italic text-lamp-400">Reader</span>
      </Link>

      <ul className="flex flex-col gap-1">
        {links.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <li key={href}>
              <Link
                href={href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                  active
                    ? "bg-ink-raised text-paper"
                    : "text-paper-muted hover:bg-ink-raised/60 hover:text-paper"
                )}
              >
                <Icon size={18} strokeWidth={1.75} className={active ? "text-lamp-400" : ""} />
                {label}
              </Link>
            </li>
          );
        })}
      </ul>

      <div className="mt-auto px-3 pt-6 text-xs text-paper-faint">
        Local-first · single user
      </div>
    </nav>
  );
}
