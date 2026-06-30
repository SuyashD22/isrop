import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';

export default function AboutPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-4xl font-bold text-gray-900 tracking-tight mb-4">
        Methodology
      </h1>
      <p className="text-xl text-gray-600 mb-12">
        How LISSclear solves Problem Statement 2 using multi-temporal conditioned diffusion.
      </p>

      <div className="space-y-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl text-space-700">The Problem</CardTitle>
          </CardHeader>
          <CardContent className="prose prose-gray max-w-none">
            <p>
              Optical satellite imagery (like LISS-IV or Sentinel-2) is heavily affected by cloud cover, particularly over the Indian subcontinent during the monsoon season. This restricts downstream applications like agricultural monitoring, disaster management, and land-use classification.
            </p>
            <p>
              Standard image inpainting algorithms (like vanilla Stable Diffusion) can make images look visually pleasing, but they hallucinate features. They might draw a forest where there should be a farm, rendering the imagery scientifically useless.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-2xl text-space-700">The Solution: Multi-Temporal Diffusion</CardTitle>
          </CardHeader>
          <CardContent className="prose prose-gray max-w-none">
            <p>
              LISSclear implements a fundamentally different approach designed for earth observation data:
            </p>
            <ul className="list-disc pl-5 space-y-2 mt-4">
              <li>
                <strong>Temporal Conditioning:</strong> Instead of guessing what is under the clouds, the model is conditioned on a stack of clear-sky images of the same location from different dates. It learns to transfer persistent spatial features (roads, buildings, topography) from the past to the present.
              </li>
              <li>
                <strong>Spectral Fidelity (SAM Loss):</strong> Generative models often distort spectral ratios. We fine-tune the diffusion decoder using Spectral Angle Mapper (SAM) loss. This heavily penalises distortions in the angle between spectral bands, ensuring that critical indices like NDVI (Normalized Difference Vegetation Index) remain mathematically accurate after reconstruction.
              </li>
              <li>
                <strong>Robust Cloud Masking:</strong> An automated masking pipeline dynamically chooses the best masking algorithm (NDSI for LISS-IV, SCL for Sentinel-2, or brightness thresholding) based on the available metadata and spectral bands.
              </li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-2xl text-space-700">Evaluation Metrics</CardTitle>
          </CardHeader>
          <CardContent className="prose prose-gray max-w-none">
            <p>
              Visual aesthetics are secondary in remote sensing. We evaluate the model exclusively on the cloud-masked pixels (excluding clear regions to prevent score inflation) using strict quantitative metrics:
            </p>
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="p-3 font-semibold text-gray-900">Metric</th>
                    <th className="p-3 font-semibold text-gray-900">Description</th>
                    <th className="p-3 font-semibold text-gray-900">Target</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="p-3 font-medium">SSIM</td>
                    <td className="p-3 text-gray-600">Structural Similarity Index</td>
                    <td className="p-3 text-green-600 font-medium">&gt; 0.85</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-medium">PSNR</td>
                    <td className="p-3 text-gray-600">Peak Signal-to-Noise Ratio</td>
                    <td className="p-3 text-green-600 font-medium">&gt; 30 dB</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-medium">SAM</td>
                    <td className="p-3 text-gray-600">Spectral Angle Mapper</td>
                    <td className="p-3 text-green-600 font-medium">&lt; 0.10 rad</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-medium">NDVI MAE</td>
                    <td className="p-3 text-gray-600">NDVI Mean Absolute Error</td>
                    <td className="p-3 text-green-600 font-medium">&lt; 0.05</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
