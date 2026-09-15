"""GeoTIFF metadata extraction — uses rasterio + pyproj when available."""
from __future__ import annotations
import io
import logging
from app.models.schemas import GeoMetadata

logger = logging.getLogger(__name__)

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False
    logger.info("rasterio not available — GeoTIFF metadata extraction disabled")


async def extract_geo_metadata(file_bytes: bytes, filename: str = "") -> GeoMetadata:
    """Extract geospatial metadata from a GeoTIFF file.
    For non-GeoTIFF files, returns empty metadata. Never invents coordinates."""

    # Only attempt if it looks like a TIFF
    is_tiff = filename.lower().endswith(('.tif', '.tiff', '.geotiff'))
    if not is_tiff:
        return GeoMetadata()

    if not HAS_RASTERIO:
        logger.warning("rasterio not installed — cannot extract GeoTIFF metadata")
        return GeoMetadata()

    try:
        with rasterio.open(io.BytesIO(file_bytes)) as dataset:
            crs_str = str(dataset.crs) if dataset.crs else None
            bounds = list(dataset.bounds) if dataset.bounds else None
            res = list(dataset.res) if dataset.res else None

            transform_list = None
            if dataset.transform:
                t = dataset.transform
                transform_list = [t.a, t.b, t.c, t.d, t.e, t.f]

            return GeoMetadata(
                crs=crs_str,
                bounds=bounds,
                resolution=res,
                width=dataset.width,
                height=dataset.height,
                band_count=dataset.count,
                transform=transform_list,
            )
    except Exception as e:
        logger.warning(f"Failed to extract GeoTIFF metadata: {e}")
        return GeoMetadata()
