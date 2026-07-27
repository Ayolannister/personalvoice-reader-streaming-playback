"use client";

import { useVoices } from "@/hooks/use-voices";

function SettingsRow({ label, description, control }: { label: string; description?: string; control: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 py-4">
      <div>
        <p className="text-sm text-paper">{label}</p>
        {description && <p className="mt-0.5 text-xs text-paper-muted">{description}</p>}
      </div>
      {control}
    </div>
  );
}

export default function SettingsPage() {
  const { data: voices } = useVoices();
  const readyVoices = voices?.filter((v) => v.status === "ready") ?? [];
  const defaultVoice = readyVoices.find((v) => v.isDefault);

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 md:px-8">
      <h1 className="mb-6 font-display text-2xl text-paper">Settings</h1>

      <section className="mb-8">
        <h2 className="mb-1 font-display text-base text-paper">Playback</h2>
        <div className="divide-y divide-ink-hairline rounded-card border border-ink-hairline px-4">
          <SettingsRow
            label="Default voice"
            description="Used for newly added books unless you choose another"
            control={
              readyVoices.length === 0 ? (
                <span className="text-xs text-paper-faint">No trained voices yet</span>
              ) : (
                <select
                  className="rounded-lg border border-ink-hairline bg-ink-surface px-3 py-1.5 text-sm text-paper"
                  defaultValue={defaultVoice?.id}
                >
                  {readyVoices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name}
                    </option>
                  ))}
                </select>
              )
            }
          />
          <SettingsRow
            label="Default playback speed"
            control={
              <select
                className="rounded-lg border border-ink-hairline bg-ink-surface px-3 py-1.5 text-sm text-paper"
                defaultValue="1.0x"
              >
                {["0.75x", "1.0x", "1.25x", "1.5x", "2.0x", "3.0x"].map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            }
          />
          <SettingsRow
            label="Default sleep timer"
            control={
              <select className="rounded-lg border border-ink-hairline bg-ink-surface px-3 py-1.5 text-sm text-paper">
                <option>Off</option>
                <option>15 min</option>
                <option>30 min</option>
                <option>45 min</option>
                <option>End of chapter</option>
              </select>
            }
          />
        </div>
      </section>

      <section className="mb-8">
        <h2 className="mb-1 font-display text-base text-paper">Appearance</h2>
        <div className="divide-y divide-ink-hairline rounded-card border border-ink-hairline px-4">
          <SettingsRow
            label="Theme"
            description="Dark is the default; light mode ships in a later milestone"
            control={
              <select className="rounded-lg border border-ink-hairline bg-ink-surface px-3 py-1.5 text-sm text-paper" disabled>
                <option>Dark</option>
              </select>
            }
          />
        </div>
      </section>

      <section>
        <h2 className="mb-1 font-display text-base text-paper">Storage</h2>
        <div className="divide-y divide-ink-hairline rounded-card border border-ink-hairline px-4">
          <SettingsRow
            label="Cached audio"
            description="Generated chapter audio, stored so it never needs regenerating"
            control={<span className="font-mono text-xs text-paper-muted">1.2 GB</span>}
          />
          <SettingsRow
            label="Clear cache"
            description="Removes generated audio only — books and voices stay"
            control={
              <button className="rounded-full border border-ink-hairline px-3 py-1.5 text-xs text-paper-muted hover:border-danger-400/50 hover:text-danger-400">
                Clear
              </button>
            }
          />
        </div>
      </section>
    </div>
  );
}
