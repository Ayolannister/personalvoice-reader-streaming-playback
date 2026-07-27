import { NavRail } from "@/components/layout/nav-rail";
import { MobileNav } from "@/components/layout/mobile-nav";
import { MiniPlayer } from "@/components/player/mini-player";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-ink">
      <NavRail />
      <div className="flex-1 flex flex-col min-w-0">
        <main className="flex-1 overflow-y-auto pb-24 md:pb-20">{children}</main>
      </div>
      <MiniPlayer />
      <MobileNav />
    </div>
  );
}
