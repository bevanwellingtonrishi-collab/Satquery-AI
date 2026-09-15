"""Image utilities — local processing, no AI required."""
from __future__ import annotations
import base64
import io
from PIL import Image
import numpy as np

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


MAX_DIMENSION = 1600  # Max dimension for API-bound images
THUMB_SIZE = (400, 400)


def resize_image(image_bytes: bytes, max_dim: int = MAX_DIMENSION) -> bytes:
    """Resize image if any dimension exceeds max_dim."""
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode == "RGBA":
        img = img.convert("RGB")

    w, h = img.size
    if max(w, h) <= max_dim:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    ratio = max_dim / max(w, h)
    new_size = (int(w * ratio), int(h * ratio))
    img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def create_thumbnail(image_bytes: bytes) -> bytes:
    """Create a small thumbnail."""
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode == "RGBA":
        img = img.convert("RGB")
    img.thumbnail(THUMB_SIZE, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def image_to_base64(image_bytes: bytes) -> str:
    """Convert image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")


def base64_to_image(b64: str) -> bytes:
    """Decode base64 string to image bytes."""
    return base64.b64decode(b64)


def get_image_info(image_bytes: bytes) -> dict:
    """Get basic image info — dimensions, format, size."""
    img = Image.open(io.BytesIO(image_bytes))
    return {
        "width": img.size[0],
        "height": img.size[1],
        "format": img.format or "UNKNOWN",
        "mode": img.mode,
        "size_bytes": len(image_bytes),
    }


def generate_difference_heatmap(before_bytes: bytes, after_bytes: bytes) -> str:
    """
    Generate a pixel-difference heatmap between two images.
    Returns base64-encoded PNG.
    This is a VISUAL AID — NOT a scientifically validated change detection.
    """
    before_img = Image.open(io.BytesIO(before_bytes)).convert("RGB")
    after_img = Image.open(io.BytesIO(after_bytes)).convert("RGB")

    # Resize to common dimensions
    common_size = (
        min(before_img.width, after_img.width, 800),
        min(before_img.height, after_img.height, 800),
    )
    before_img = before_img.resize(common_size, Image.LANCZOS)
    after_img = after_img.resize(common_size, Image.LANCZOS)

    before_arr = np.array(before_img, dtype=np.float32)
    after_arr = np.array(after_img, dtype=np.float32)

    # Calculate absolute difference
    diff = np.abs(before_arr - after_arr)
    diff_gray = np.mean(diff, axis=2).astype(np.uint8)

    # Normalize to 0-255
    if diff_gray.max() > 0:
        diff_gray = ((diff_gray / diff_gray.max()) * 255).astype(np.uint8)

    if HAS_CV2:
        # Apply colormap for visualization
        heatmap = cv2.applyColorMap(diff_gray, cv2.COLORMAP_JET)
        heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        heatmap_img = Image.fromarray(heatmap_rgb)
    else:
        # Fallback: create a simple red-channel heatmap without OpenCV
        heatmap_arr = np.zeros((*diff_gray.shape, 3), dtype=np.uint8)
        heatmap_arr[:, :, 0] = diff_gray  # Red channel
        heatmap_arr[:, :, 1] = (diff_gray * 0.2).astype(np.uint8)  # Slight green
        heatmap_img = Image.fromarray(heatmap_arr)

    # Blend with the after image for context
    after_resized = after_img.resize(common_size, Image.LANCZOS)
    blended = Image.blend(after_resized, heatmap_img, alpha=0.5)

    buf = io.BytesIO()
    blended.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def compute_change_magnitude(before_bytes: bytes, after_bytes: bytes) -> float:
    """Compute overall change magnitude between two images (0-1)."""
    before_img = Image.open(io.BytesIO(before_bytes)).convert("RGB")
    after_img = Image.open(io.BytesIO(after_bytes)).convert("RGB")

    common_size = (256, 256)
    before_arr = np.array(before_img.resize(common_size, Image.LANCZOS), dtype=np.float32)
    after_arr = np.array(after_img.resize(common_size, Image.LANCZOS), dtype=np.float32)

    diff = np.abs(before_arr - after_arr)
    magnitude = float(np.mean(diff) / 255.0)
    return min(magnitude * 3.0, 1.0)  # Scale up for perceptual relevance


def _generate_placeholder_image(scene_id: str) -> bytes:
    """Generate a colored placeholder satellite-style image for demo scenes."""
    color_map = {
        "urban": (40, 60, 80),
        "urban_2023": (45, 65, 75),
        "urban_2026": (55, 50, 70),
        "flood_before": (50, 70, 45),
        "flood_after": (35, 55, 80),
        "forest": (25, 75, 35),
        "agriculture": (70, 80, 40),
        "coastal": (40, 70, 90),
    }
    base_color = color_map.get(scene_id, (50, 60, 70))

    # Create 800x600 image with noise pattern for satellite look
    w, h = 800, 600
    arr = np.zeros((h, w, 3), dtype=np.uint8)

    # Base color with noise
    for c in range(3):
        channel = np.full((h, w), base_color[c], dtype=np.float32)
        noise = np.random.normal(0, 20, (h, w)).astype(np.float32)
        channel = np.clip(channel + noise, 0, 255).astype(np.uint8)
        arr[:, :, c] = channel

    # Add some "feature" rectangles to look like buildings/fields
    rng = np.random.RandomState(hash(scene_id) % 2**31)
    for _ in range(rng.randint(8, 25)):
        x1 = rng.randint(0, w - 60)
        y1 = rng.randint(0, h - 50)
        bw = rng.randint(15, 55)
        bh = rng.randint(12, 45)
        brightness = rng.randint(-40, 40)
        for c in range(3):
            val = np.clip(arr[y1:y1+bh, x1:x1+bw, c].astype(np.int16) + brightness, 0, 255)
            arr[y1:y1+bh, x1:x1+bw, c] = val.astype(np.uint8)

    # Add line features (roads)
    for _ in range(rng.randint(2, 5)):
        y_pos = rng.randint(50, h - 50)
        thickness = rng.randint(2, 5)
        arr[y_pos:y_pos+thickness, :, :] = np.clip(
            arr[y_pos:y_pos+thickness, :, :].astype(np.int16) + 50, 0, 255
        ).astype(np.uint8)

    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
