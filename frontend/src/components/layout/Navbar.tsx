"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { APP_NAME, BAH_URL } from "@/lib/constants";

export function Navbar() {
  const path = usePathname();
  const active = (href: string) => path === href;

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-[rgba(0,212,255,0.1)] bg-[rgba(5,10,20,0.9)] backdrop-blur-xl">
      <div className="container mx-auto px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative w-8 h-8 flex items-center justify-center">
            {/* Satellite icon */}
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none" className="text-[#00D4FF]">
              <rect x="12" y="3" width="4" height="6" rx="1" fill="currentColor" opacity="0.9"/>
              <rect x="12" y="19" width="4" height="6" rx="1" fill="currentColor" opacity="0.9"/>
              <rect x="3" y="12" width="6" height="4" rx="1" fill="currentColor" opacity="0.9"/>
              <rect x="19" y="12" width="6" height="4" rx="1" fill="currentColor" opacity="0.9"/>
              <rect x="10" y="10" width="8" height="8" rx="2" fill="currentColor"/>
              <circle cx="14" cy="14" r="2" fill="#050a14"/>
            </svg>
            {/* Glow */}
            <div className="absolute inset-0 bg-[#00D4FF] blur-md opacity-20 rounded-full group-hover:opacity-35 transition-opacity" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-bold text-[15px] tracking-tight text-white">
              {APP_NAME}
            </span>
            <span className="terminal-label text-[10px]">v1.0</span>
          </div>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-6">
          <Link
            href="/demo"
            className={`text-[13px] font-medium tracking-wide transition-colors ${
              active("/demo")
                ? "text-[#00D4FF]"
                : "text-[rgba(226,232,244,0.55)] hover:text-[rgba(226,232,244,0.9)]"
            }`}
          >
            Demo
          </Link>
          <Link
            href="/about"
            className={`text-[13px] font-medium tracking-wide transition-colors ${
              active("/about")
                ? "text-[#00D4FF]"
                : "text-[rgba(226,232,244,0.55)] hover:text-[rgba(226,232,244,0.9)]"
            }`}
          >
            Methodology
          </Link>
        </div>
      </div>
    </nav>
  );
}
