import Link from 'next/link';
import { ArrowRight, Satellite, Zap, Globe2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function Home() {
  return (
    <div className="flex-1 flex flex-col">
      {/* Hero Section */}
      <section className="relative flex-1 flex flex-col items-center justify-center py-20 lg:py-32 overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 bg-hero-radial -z-10" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-space-400/20 blur-[100px] rounded-full -z-10 pointer-events-none" />
        
        <div className="container mx-auto px-4 text-center">
          <div className="inline-flex items-center space-x-2 bg-space-50 border border-space-100 text-space-700 px-4 py-1.5 rounded-full text-sm font-semibold mb-8 animate-fade-in shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-space-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-space-500"></span>
            </span>
            <span>BAH 2026 • Problem Statement 2 Prototype</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-gray-900 mb-6 max-w-4xl mx-auto animate-slide-up">
            See through the clouds with <br className="hidden md:block" />
            <span className="text-gradient-isro">Generative AI</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto leading-relaxed animate-slide-up" style={{ animationDelay: '100ms' }}>
            Multi-temporal conditioned diffusion models for high-fidelity cloud removal in LISS-IV and Sentinel-2 satellite imagery. 
            Preserving spectral indices for agricultural monitoring.
          </p>
          
          <div className="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-6 animate-slide-up" style={{ animationDelay: '200ms' }}>
            <Link href="/demo">
              <Button size="lg" className="w-full sm:w-auto shadow-glow-blue group">
                Try the Demo
                <ArrowRight className="ml-2 group-hover:translate-x-1 transition-transform" size={20} />
              </Button>
            </Link>
            <Link href="/about">
              <Button variant="outline" size="lg" className="w-full sm:w-auto bg-white/50 backdrop-blur-sm">
                Read Methodology
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="bg-gray-50 py-24 border-t border-gray-200">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Why LISSclear?</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Our approach differs from standard inpainting by incorporating domain-specific satellite priors.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:border-space-200 transition-colors">
              <div className="w-12 h-12 bg-space-100 text-space-600 rounded-xl flex items-center justify-center mb-6">
                <Globe2 size={24} />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Multi-temporal Context</h3>
              <p className="text-gray-600 leading-relaxed">
                Conditions the generative model on cloud-free reference frames from different dates, ensuring accurate reconstruction of persistent structures like roads and buildings.
              </p>
            </div>
            
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:border-earth-200 transition-colors">
              <div className="w-12 h-12 bg-earth-100 text-earth-600 rounded-xl flex items-center justify-center mb-6">
                <Satellite size={24} />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Spectral Fidelity</h3>
              <p className="text-gray-600 leading-relaxed">
                Trained with Spectral Angle Mapper (SAM) loss to preserve relative band ratios, ensuring that derived products like NDVI remain mathematically valid for agriculture.
              </p>
            </div>
            
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:border-amber-200 transition-colors">
              <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center mb-6">
                <Zap size={24} />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Automated Masking</h3>
              <p className="text-gray-600 leading-relaxed">
                Includes an integrated cloud segmentation pipeline that dynamically selects between SCL, NDSI, or brightness thresholds based on available sensor bands.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
