"""
Image Gallery Management System

This module provides functionality for managing generated images with metadata,
search capabilities, and cleanup operations.
"""

from .models import ImageMetadata
from .image_gallery import ImageGallery

__all__ = ["ImageMetadata", "ImageGallery"]
