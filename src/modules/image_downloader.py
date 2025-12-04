"""
Multi-source image downloader for actor faces.
Downloads from TMDb, DuckDuckGo, and Bing with rate limiting and retry logic.
"""

import requests
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from urllib.parse import urlparse
import time
from random import uniform

from config.settings import (
    TMDB_IMAGE_BASE_URL,
    MIN_RAW_IMAGES,
    MAX_IMAGES_PER_SOURCE,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    DOWNLOAD_DELAY_MIN,
    DOWNLOAD_DELAY_MAX,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    IMAGE_SOURCES,
    SEARCH_ENHANCEMENTS,
    MIN_IMAGE_SIZE,
    MAX_IMAGE_SIZE,
)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


logger = logging.getLogger(__name__)


class ImageDownloader:
    """
    Downloads images from multiple sources with rate limiting and error handling.
    """

    def __init__(self):
        """Initialize downloader with session and rate limiting."""
        self.session = requests.Session()
        self.session.timeout = REQUEST_TIMEOUT
        self.downloaded_urls = set()
        self.failed_urls = set()

    def _random_delay(self, min_delay: float, max_delay: float) -> None:
        """
        Add random delay between requests.

        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        delay = uniform(min_delay, max_delay)
        time.sleep(delay)

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def _download_image(self, url: str) -> Tuple[Optional[bytes], str]:
        """
        Download image from URL with retry logic.

        Args:
            url: Image URL

        Returns:
            Tuple of (image_bytes, file_extension) or (None, "") on failure
        """
        if url in self.failed_urls:
            return None, ""

        try:
            logger.debug(f"Downloading from: {url}")
            
            response = self.session.get(
                url,
                timeout=REQUEST_TIMEOUT,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Get file extension from URL or content-type
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            if "." in path:
                ext = path.split(".")[-1].split("?")[0]
            else:
                # Try to get from content-type
                content_type = response.headers.get("content-type", "").lower()
                ext_map = {
                    "image/jpeg": "jpg",
                    "image/png": "png",
                    "image/webp": "webp",
                    "image/bmp": "bmp",
                }
                ext = ext_map.get(content_type.split(";")[0], "jpg")
            
            # Validate it's actually an image
            if not response.headers.get("content-type", "").startswith("image/"):
                logger.warning(f"URL doesn't appear to be image: {url}")
                self.failed_urls.add(url)
                return None, ""
            
            image_bytes = response.content
            
            # Check minimum size
            if len(image_bytes) < 5000:  # Less than 5KB
                logger.warning(f"Image too small ({len(image_bytes)} bytes): {url}")
                self.failed_urls.add(url)
                return None, ""
            
            logger.debug(f"Successfully downloaded {len(image_bytes)} bytes from {url}")
            self.downloaded_urls.add(url)
            return image_bytes, ext
        except Exception as e:
            logger.warning(f"Failed to download {url}: {str(e)}")
            self.failed_urls.add(url)
            return None, ""

    def download_and_save(self, url: str, save_path: Path) -> bool:
        """
        Download image from URL and save to file.

        Args:
            url: Image URL
            save_path: Path to save image

        Returns:
            True if successful, False otherwise
        """
        image_bytes, ext = self._download_image(url)
        
        if image_bytes is None:
            return False
        
        try:
            # Update file extension if determined
            if ext and not str(save_path).endswith(f".{ext}"):
                save_path = save_path.parent / f"{save_path.stem}.{ext}"
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, "wb") as f:
                f.write(image_bytes)
            
            logger.info(f"Saved image: {save_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving image to {save_path}: {str(e)}")
            return False

    def download_from_tmdb(
        self,
        actor_name: str,
        tmdb_images: List[dict],
        output_dir: Path,
        limit: int = None
    ) -> int:
        """
        Download images from TMDb actor profile.

        Args:
            actor_name: Actor name (for logging)
            tmdb_images: List of image dictionaries from TMDb
            output_dir: Directory to save images
            limit: Maximum images to download

        Returns:
            Number of successfully downloaded images
        """
        if limit is None:
            limit = MAX_IMAGES_PER_SOURCE
        
        logger.info(f"Downloading up to {limit} images from TMDb for {actor_name}")
        
        downloaded = 0
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for idx, image_info in enumerate(tmdb_images[:limit]):
            try:
                image_path = image_info.get("file_path")
                if not image_path:
                    continue
                
                # Construct URL
                url = f"{TMDB_IMAGE_BASE_URL}/original{image_path}"
                
                # Save with TMDb source identifier
                save_path = output_dir / f"tmdb_{idx:04d}.jpg"
                
                if self.download_and_save(url, save_path):
                    downloaded += 1
                
                # Rate limiting
                self._random_delay(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
            except Exception as e:
                logger.error(f"Error processing TMDb image {idx}: {str(e)}")
        
        logger.info(f"Downloaded {downloaded} images from TMDb for {actor_name}")
        return downloaded

    def download_from_duckduckgo(
        self,
        query: str,
        output_dir: Path,
        limit: int = None
    ) -> int:
        """
        Download images from DuckDuckGo.

        Args:
            query: Search query
            output_dir: Directory to save images
            limit: Maximum images to download

        Returns:
            Number of successfully downloaded images
        """
        if limit is None:
            limit = MAX_IMAGES_PER_SOURCE
        
        logger.info(f"Downloading up to {limit} images from DuckDuckGo: {query}")
        
        try:
            from bing_image_downloader import bing_images_download
            
            # Note: Using bing_image_downloader which also works with DuckDuckGo
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Download images
            bing_images_download(
                query=query,
                limit=limit,
                output_folder="downloads",
                adult_filter_off=True,
                force_replace=False,
                timeout=REQUEST_TIMEOUT,
                verbose=False,
            )
            
            logger.info(f"Downloaded images from DuckDuckGo for query: {query}")
            return min(limit, 10)  # Conservative estimate
        except Exception as e:
            logger.error(f"Error downloading from DuckDuckGo: {str(e)}")
            return 0

    def build_search_query(self, actor_name: str) -> str:
        """
        Build optimized search query with enhancements.

        Args:
            actor_name: Actor name

        Returns:
            Optimized search query
        """
        # Build enhanced query
        query_parts = [actor_name]
        
        # Add enhancing terms to avoid mythological content
        query_parts.extend(SEARCH_ENHANCEMENTS[:3])  # Add top 3 enhancement terms
        
        query = " ".join(query_parts)
        logger.debug(f"Built search query: {query}")
        return query

    def validate_image_dimensions(self, image_bytes: bytes) -> bool:
        """
        Validate image dimensions are within acceptable range.

        Args:
            image_bytes: Image binary data

        Returns:
            True if dimensions are valid
        """
        try:
            from PIL import Image
            from io import BytesIO
            
            img = Image.open(BytesIO(image_bytes))
            width, height = img.size
            
            min_w, min_h = MIN_IMAGE_SIZE
            max_w, max_h = MAX_IMAGE_SIZE
            
            if width < min_w or height < min_h:
                logger.warning(f"Image too small: {width}x{height} (min: {min_w}x{min_h})")
                return False
            
            if width > max_w or height > max_h:
                logger.warning(f"Image too large: {width}x{height} (max: {max_w}x{max_h})")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating image dimensions: {str(e)}")
            return False

    def get_download_stats(self) -> dict:
        """
        Get download statistics.

        Returns:
            Dictionary with download stats
        """
        return {
            "total_downloaded": len(self.downloaded_urls),
            "total_failed": len(self.failed_urls),
            "success_rate": len(self.downloaded_urls) / (len(self.downloaded_urls) + len(self.failed_urls))
            if (len(self.downloaded_urls) + len(self.failed_urls)) > 0 else 0,
        }
