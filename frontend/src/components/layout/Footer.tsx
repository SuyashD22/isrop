import { APP_NAME, ISRO_URL, BAH_URL } from "@/lib/constants";

export function Footer() {
  return (
    <footer className="w-full border-t border-[rgba(0,212,255,0.08)] bg-[rgba(5,10,20,0.95)] py-6 mt-auto">
      <div className="container mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Left */}
        <div className="flex items-center gap-3">
          <span className="terminal-label">{APP_NAME}</span>
          <span className="text-[rgba(226,232,244,0.2)] text-xs">—</span>
          <span className="terminal-label opacity-60">PS2 / BAH 2026 / ISRO</span>
        </div>

        {/* Right */}
        <div className="flex items-center gap-6 text-[12px] text-[rgba(226,232,244,0.35)]">
          <a
            href={BAH_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-[#00D4FF] transition-colors"
          >
            Build with AI for Humanity
          </a>
          <span className="text-[rgba(226,232,244,0.15)]">|</span>
          <a
            href={ISRO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-[#00D4FF] transition-colors"
          >
            ISRO
          </a>
        </div>
      </div>
    </footer>
  );
}
