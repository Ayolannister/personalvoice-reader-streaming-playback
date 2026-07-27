"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Library, Mic2, Settings, BookPlus } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Library", icon: Library },
  { href: "/voices", label: "Voices", icon: Mic2 },
  { href: "/upload", label: "Add", icon: BookPlus },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-30 flex border-t border-ink-hairline bg-ink-surface pb-[env(safe-area-inset-bottom)]">
      {links.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px]",
              active ? "text-lamp-400" : "text-paper-muted"
            )}
          >
            <Icon size={20} strokeWidth={1.75} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
