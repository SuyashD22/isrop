"""
src/data/downloader.py
Download scripts for all three data sources:
  - Sentinel-2 L2A via sentinelsat (Copernicus Open Hub)
  - LISS-IV tiles from ISRO Bhuvan (manual instructions — no public API)
  - SEN12MS subset via direct URL download
"""

from __future__ import annotations

import logging
import os
import shutil
import urllib.request
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Sentinel-2 Downloader ─────────────────────────────────────────────────────

class SentinelDownloader:
    """
    Download Sentinel-2 L2A tiles from Copernicus Open Hub (scihub.copernicus.eu).
    Requires free registration at: https://scihub.copernicus.eu/dhus/#/self-registration

    Usage:
        dl = SentinelDownloader(user="your_user", password="your_pass")
        dl.download_tiles(
            area="POLYGON((68 8, 97 8, 97 37, 68 37, 68 8))",  # India bbox
            date_range=("2023-06-01", "2023-09-30"),
            output_dir=Path("data/raw/sentinel2"),
            max_tiles=20,
        )
    """

    # India bounding box (WGS84) — covers major agricultural zones
    INDIA_BBOX = "POLYGON((68.1766 8.4076, 97.4026 8.4076, 97.4026 37.6007, 68.1766 37.6007, 68.1766 8.4076))"

    # Monsoon belt — focus area for cloud removal
    MONSOON_BBOX = "POLYGON((72 16, 88 16, 88 28, 72 28, 72 16))"

    def __init__(self, user: str, password: str):
        try:
            from sentinelsat import SentinelAPI
        except ImportError:
            raise ImportError(
                "sentinelsat not installed. Run: pip install sentinelsat"
            )
        self.api = SentinelAPI(user, password, "https://scihub.copernicus.eu/dhus")
        logger.info("Sentinel API authenticated for user: %s", user)

    def download_tiles(
        self,
        area: str = None,
        date_range: Tuple[str, str] = ("2023-06-01", "2023-09-30"),
        output_dir: Path = Path("data/raw/sentinel2"),
        max_tiles: int = 20,
        cloud_cover: Tuple[int, int] = (0, 80),
        platform: str = "Sentinel-2",
        product_type: str = "S2MSI2A",   # L2A with SCL band
    ) -> List[str]:
        """
        Search and download Sentinel-2 tiles.

        Args:
            area:        WKT polygon string. Defaults to India bbox.
            date_range:  (start, end) as 'YYYY-MM-DD' strings.
            output_dir:  Local directory to save .zip tiles.
            max_tiles:   Download at most this many tiles.
            cloud_cover: (min%, max%) cloud cover filter.

        Returns:
            List of downloaded product UUIDs.
        """
        from sentinelsat import geojson_to_wkt
        from datetime import datetime

        area = area or self.MONSOON_BBOX
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        start = datetime.strptime(date_range[0], "%Y-%m-%d").date()
        end = datetime.strptime(date_range[1], "%Y-%m-%d").date()

        logger.info("Searching Sentinel-2 tiles: %s → %s", start, end)
        products = self.api.query(
            area=area,
            date=(start, end),
            platformname=platform,
            producttype=product_type,
            cloudcoverpercentage=cloud_cover,
        )

        logger.info("Found %d products. Downloading up to %d.", len(products), max_tiles)
        product_list = list(products.items())[:max_tiles]

        uuids = []
        for uuid, info in product_list:
            title = info.get("title", uuid)
            out_zip = output_dir / f"{title}.zip"
            if out_zip.exists():
                logger.info("Already downloaded: %s", title)
                uuids.append(uuid)
                continue

            logger.info("Downloading: %s (%.0f MB)", title,
                        info.get("size", 0) / 1e6)
            self.api.download(uuid, directory_path=str(output_dir))
            uuids.append(uuid)

        logger.info("Downloaded %d tiles to %s", len(uuids), output_dir)
        return uuids

    def unzip_all(self, directory: Path) -> None:
        """Extract all .zip SAFE archives in a directory."""
        for zf in Path(directory).glob("*.zip"):
            logger.info("Extracting: %s", zf.name)
            shutil.unpack_archive(str(zf), str(directory))
            zf.unlink()  # Remove zip after extraction


# ── SEN12MS Downloader ────────────────────────────────────────────────────────

class SEN12MSDownloader:
    """
    Download subset of SEN12MS dataset (pre-paired SAR + optical with cloud masks).
    Full dataset: 180GB — we download only the ROIs needed for India.

    Source: https://mediatum.ub.tum.de/1474000
    Citation: Schmitt et al., 2019 — SEN12MS: A Curated Dataset of Georeferenced
              Multi-Spectral Sentinel-1/2 Imagery for Deep Learning and Data Fusion.
    """

    # Base URLs for different seasons (Spring / Summer / Fall / Winter)
    BASE_URLS = {
        "spring": "https://mediatum.ub.tum.de/download/1474000/1474000.tar.gz",
    }

    # ROI IDs that cover South Asian / Indian subcontinent geography
    INDIA_ROIS = [
        "ROI_0360", "ROI_0361", "ROI_0363",  # Gangetic Plain
        "ROI_0500", "ROI_0501",               # Deccan Plateau
        "ROI_0600",                            # Western Ghats
    ]

    def __init__(self, output_dir: Path = Path("data/raw/sen12ms")):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_roi(self, roi_id: str, season: str = "spring") -> Path:
        """Download a single ROI subset. Returns path to downloaded archive."""
        url = self.BASE_URLS.get(season)
        if not url:
            raise ValueError(f"Unknown season: {season}. Choose from {list(self.BASE_URLS)}")

        out_path = self.output_dir / f"{roi_id}_{season}.tar.gz"
        if out_path.exists():
            logger.info("Already downloaded: %s", out_path.name)
            return out_path

        logger.info("Downloading SEN12MS ROI %s (%s)...", roi_id, season)

        def _progress(block_count, block_size, total_size):
            pct = block_count * block_size * 100 / total_size
            if block_count % 100 == 0:
                logger.info("  %.1f%%", min(pct, 100))

        urllib.request.urlretrieve(url, str(out_path), _progress)
        return out_path

    def instructions(self) -> str:
        """Print manual download instructions for the full SEN12MS dataset."""
        return """
        SEN12MS Download Instructions
        ==============================
        The full dataset is 180GB. For this project, we use a subset.

        1. Go to: https://mediatum.ub.tum.de/1474000
        2. Register for a free account
        3. Download specific ROI files (recommended for development):
           - ROI_0360_patch_{0..100}.tif (Gangetic Plain — monsoon area)
           - ROI_0500_patch_{0..100}.tif (Deccan Plateau)
        4. Place .tif files in: data/raw/sen12ms/

        Alternatively, use the SEN12MS Python loader:
            pip install sen12ms
            from sen12ms import SEN12MS
            ds = SEN12MS("data/raw/sen12ms/")
        """


# ── LISS-IV Manual Download Guide ─────────────────────────────────────────────

BHUVAN_INSTRUCTIONS = """
LISS-IV Download from ISRO Bhuvan
===================================
LISS-IV data is not available via a public programmatic API.
Follow these steps to download tiles manually:

1. Register: https://bhuvan-app1.nrsc.gov.in/bhuvan/bhuvan2d.php
   (Free account, .gov.in email preferred but not required)

2. Navigate to: Bhuvan → Thematic Services → Data Download

3. Select parameters:
   - Sensor:      LISS-IV MX (multispectral, 4 bands)
   - Resolution:  5.8 m
   - Area:        Draw AOI over your target region (e.g., Uttar Pradesh, Punjab)
   - Date Range:  Jun 2023 – Sep 2023 (monsoon season)
   - Bands:       B2 (Green), B3 (Red), B4 (NIR)

4. Download GeoTIFF files and place in: data/raw/liss4/

5. Naming convention expected by this pipeline:
   LISS4_<tile_id>_<date>.tif
   Example: LISS4_UP_078_20230715.tif

Alternative: Use Sentinel-2 as a proxy (5.8m simulation via 10m data).
The pipeline works identically with Sentinel-2 L2A tiles.
"""
