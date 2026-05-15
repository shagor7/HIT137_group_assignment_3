"""
HIT137 Assignment 3 - Spot the Difference Game
Author: Replace with your group members' names
Description:
    Desktop application using Tkinter and OpenCV.
    Loads an image, creates a modified clone with exactly 5 random non-overlapping
    differences, and lets the player find them by clicking the modified image.

Requirements covered:
    - OOP design with multiple classes
    - Tkinter GUI
    - OpenCV image processing
    - JPG, PNG, BMP loading
    - Side-by-side original and modified images
    - 5 non-overlapping randomized differences
    - At least 3 alteration types
    - Click detection, scoring, mistakes, lockout, and reveal feature
"""

import random
import tkinter as tk
from tkinter import filedialog, messagebox
from dataclasses import dataclass
from abc import ABC, abstractmethod

import cv2
import numpy as np
from PIL import Image, ImageTk


# ----------------------------- Data Classes -----------------------------

@dataclass
class DifferenceRegion:
    """Stores the position and status of a generated difference."""
    x: int
    y: int
    w: int
    h: int
    alteration_type: str
    found: bool = False
    revealed: bool = False

    @property
    def center(self):
        return self.x + self.w // 2, self.y + self.h // 2

    @property
    def radius(self):
        return max(self.w, self.h) // 2 + 8

    def contains_click(self, click_x: int, click_y: int, tolerance: int = 15) -> bool:
        """Checks whether a click is close enough to this difference region."""
        return (
            self.x - tolerance <= click_x <= self.x + self.w + tolerance
            and self.y - tolerance <= click_y <= self.y + self.h + tolerance
        )

    def overlaps(self, other: "DifferenceRegion", padding: int = 20) -> bool:
        """Checks whether this region overlaps another region, including padding."""
        return not (
            self.x + self.w + padding < other.x
            or other.x + other.w + padding < self.x
            or self.y + self.h + padding < other.y
            or other.y + other.h + padding < self.y
        )



# -------------------------- Alteration Classes --------------------------
class ImageAlteration(ABC):
    """Abstract base class for all OpenCV alteration types."""

    name = "Base Alteration"

    @abstractmethod
    def apply(self, image: np.ndarray, region: DifferenceRegion) -> None:
        """Apply an alteration to the selected region."""
        pass


class ColourShiftAlteration(ImageAlteration):
    """Subtly changes colour values inside a rectangular region."""

    name = "Colour Shift"

    def apply(self, image: np.ndarray, region: DifferenceRegion) -> None:
        roi = image[region.y:region.y + region.h, region.x:region.x + region.w]
        shift = np.array([random.randint(-18, 18), random.randint(-18, 18), random.randint(-18, 18)])
        altered = np.clip(roi.astype(np.int16) + shift, 0, 255).astype(np.uint8)
        image[region.y:region.y + region.h, region.x:region.x + region.w] = altered


class BlurAlteration(ImageAlteration):
    """Applies a slight blur to a small region."""

    name = "Blur"

    def apply(self, image: np.ndarray, region: DifferenceRegion) -> None:
        roi = image[region.y:region.y + region.h, region.x:region.x + region.w]
        blurred = cv2.GaussianBlur(roi, (9, 9), 0)
        image[region.y:region.y + region.h, region.x:region.x + region.w] = blurred


class BrightnessAlteration(ImageAlteration):
    """Slightly changes brightness in a region."""

    name = "Brightness Change"

    def apply(self, image: np.ndarray, region: DifferenceRegion) -> None:
        roi = image[region.y:region.y + region.h, region.x:region.x + region.w]
        factor = random.choice([0.78, 1.22])
        altered = np.clip(roi.astype(np.float32) * factor, 0, 255).astype(np.uint8)
        image[region.y:region.y + region.h, region.x:region.x + region.w] = altered


class SmallShapeAlteration(ImageAlteration):
    """Adds a small subtle filled circle using a nearby average colour."""

    name = "Small Shape"

    def apply(self, image: np.ndarray, region: DifferenceRegion) -> None:
        roi = image[region.y:region.y + region.h, region.x:region.x + region.w]
        avg_colour = np.mean(roi.reshape(-1, 3), axis=0)
        colour = np.clip(avg_colour + random.randint(-35, 35), 0, 255).astype(int).tolist()
        center = region.center
        radius = max(4, min(region.w, region.h) // 3)
        cv2.circle(image, center, radius, colour, -1)


# ------------------------- Difference Generator -------------------------
"""Creates exactly five random, non-overlapping differences using OpenCV."""

    TOTAL_DIFFERENCES = 5

    def __init__(self):
        self.alterations = [
            ColourShiftAlteration(),
            BlurAlteration(),
            BrightnessAlteration(),
            SmallShapeAlteration(),
        ]

    def generate(self, original_image: np.ndarray):
        """Returns a modified image and a list of generated difference regions."""
        modified_image = original_image.copy()
        height, width = original_image.shape[:2]
        regions = []

        min_size = max(24, min(width, height) // 16)
        max_size = max(36, min(width, height) // 14)

        attempts = 0
        while len(regions) < self.TOTAL_DIFFERENCES and attempts < 1000:
            attempts += 1

            region_w = random.randint(min_size, max_size)
            region_h = random.randint(min_size, max_size)

            if width <= region_w + 20 or height <= region_h + 20:
                raise ValueError("Image is too small. Please choose a larger image.")

            x = random.randint(10, width - region_w - 10)
            y = random.randint(10, height - region_h - 10)

            alteration = random.choice(self.alterations)
            new_region = DifferenceRegion(x, y, region_w, region_h, alteration.name)

            if all(not new_region.overlaps(existing) for existing in regions):
                alteration.apply(modified_image, new_region)
                regions.append(new_region)

        if len(regions) != self.TOTAL_DIFFERENCES:
            raise ValueError("Could not create 5 non-overlapping differences. Try a larger image.")

        return modified_image, regions



# ----------------------------- GUI Class -----------------------------


