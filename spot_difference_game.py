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




# ----------------------------- GUI Class -----------------------------


