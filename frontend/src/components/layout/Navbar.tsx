import Link from 'next/link';
import { APP_NAME, BAH_URL } from '@/lib/constants';

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 w-full border-b border-gray-200/50 bg-white/80 backdrop-blur-md">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-space-gradient flex items-center justify-center text-white font-bold text-lg shadow-glow-blue">
            L
          </div>
          <span className="font-bold text-xl tracking-tight text-gray-900">
            {APP_NAME}
          </span>
        </Link>
        
        <div className="flex items-center space-x-8">
          <Link href="/demo" className="text-sm font-medium text-gray-600 hover:text-space-600 transition-colors">
            Demo
          </Link>
          <Link href="/about" className="text-sm font-medium text-gray-600 hover:text-space-600 transition-colors">
            Methodology
          </Link>
          <a 
            href={BAH_URL} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-xs font-semibold px-3 py-1.5 rounded-full bg-orange-50 text-orange-600 border border-orange-200 hover:bg-orange-100 transition-colors"
          >
            BAH 2026
          </a>
        </div>
      </div>
    </nav>
  );
}
