import Link from "next/link";
import { BookOpen, Mic2, Sparkles, Headphones } from "lucide-react";

const steps = [
  { icon: BookOpen, title: "Add a book", body: "Upload an EPUB, PDF, or TXT you have the right to read." },
  { icon: Mic2, title: "Clone a voice", body: "Upload ~1 hour of audio from someone who's given consent." },
  { icon: Sparkles, title: "Generate as you go", body: "Chapters are generated on demand, then cached for reuse." },
  { icon: Headphones, title: "Listen and resume", body: "PersonalVoice Reader remembers exactly where you stopped." },
];

export default function OnboardingPage() {
  return (
    <div className="mx-auto flex min-h-[80vh] max-w-lg flex-col justify-center px-6 py-12 text-center">
      <h1 className="font-display text-3xl text-paper">
        Your books, read in <span className="italic text-lamp-400">a voice you chose</span>
      </h1>
      <p className="mt-3 text-sm text-paper-muted">
        A personal audiobook reader. No accounts, no marketplace, no sharing — everything stays
        on this device.
      </p>

      <div className="mt-10 flex flex-col gap-5 text-left">
        {steps.map(({ icon: Icon, title, body }, i) => (
          <div key={title} className="flex gap-4">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-ink-surface ring-1 ring-ink-hairline">
              <Icon size={16} className="text-lamp-400" />
            </div>
            <div>
              <p className="text-sm text-paper">
                <span className="font-mono text-xs text-paper-faint mr-2">{String(i + 1).padStart(2, "0")}</span>
                {title}
              </p>
              <p className="mt-0.5 text-xs text-paper-muted">{body}</p>
            </div>
          </div>
        ))}
      </div>

      <Link
        href="/upload"
        className="mt-10 rounded-full bg-lamp-400 py-3 text-sm font-medium text-ink hover:bg-lamp-200"
      >
        Add your first book
      </Link>
    </div>
  );
}
