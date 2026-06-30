import { APP_NAME, ISRO_URL, BAH_URL } from '@/lib/constants';

export function Footer() {
  return (
    <footer className="w-full border-t border-gray-200 bg-gray-50 py-8 mt-auto">
      <div className="container mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-gray-700">{APP_NAME}</span>
          <span className="text-gray-400 text-sm">
            © {new Date().getFullYear()} — Problem Statement 2
          </span>
        </div>
        
        <div className="flex items-center space-x-6 text-sm text-gray-500">
          <a href={BAH_URL} target="_blank" rel="noopener noreferrer" className="hover:text-space-600 transition-colors">
            Build with AI for Humanity
          </a>
          <span>•</span>
          <a href={ISRO_URL} target="_blank" rel="noopener noreferrer" className="hover:text-space-600 transition-colors">
            Indian Space Research Organisation
          </a>
        </div>
      </div>
    </footer>
  );
}
