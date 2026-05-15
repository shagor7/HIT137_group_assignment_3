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

class DifferenceGenerator:
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
        max_size = max(36, min(width, height) // 8)

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

class SpotDifferenceApp:
    """Main Tkinter application class."""

    DISPLAY_MAX_WIDTH = 520
    DISPLAY_MAX_HEIGHT = 520
    MAX_MISTAKES = 3

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("HIT137 Assignment 3 - Spot the Difference")
        self.root.geometry("1160x760")
        self.root.minsize(980, 650)

        self.generator = DifferenceGenerator()

        self.original_image = None
        self.modified_image = None
        self.regions = []

        self.original_display = None
        self.modified_display = None
        self.original_photo = None
        self.modified_photo = None

        self.scale = 1.0
        self.display_w = 0
        self.display_h = 0

        self.mistakes = 0
        self.total_score = 0
        self.clicks_locked = True

        self._build_interface()

    def _build_interface(self):
        """Creates the Tkinter layout."""
        title = tk.Label(
            self.root,
            text="Spot the Difference Game",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=10)

        controls = tk.Frame(self.root)
        controls.pack(pady=5)

        self.load_button = tk.Button(
            controls,
            text="Load Image",
            width=16,
            command=self.load_image,
            font=("Arial", 11, "bold")
        )
        self.load_button.grid(row=0, column=0, padx=8)

        self.reveal_button = tk.Button(
            controls,
            text="Reveal Differences",
            width=18,
            command=self.reveal_differences,
            state=tk.DISABLED,
            font=("Arial", 11, "bold")
        )
        self.reveal_button.grid(row=0, column=1, padx=8)

        self.info_label = tk.Label(
            controls,
            text="Load a JPG, PNG, or BMP image to start.",
            font=("Arial", 11)
        )
        self.info_label.grid(row=0, column=2, padx=12)

        score_frame = tk.Frame(self.root)
        score_frame.pack(pady=8)

        self.remaining_label = tk.Label(score_frame, text="Remaining: 0", font=("Arial", 13, "bold"))
        self.remaining_label.grid(row=0, column=0, padx=18)

        self.mistakes_label = tk.Label(score_frame, text="Mistakes: 0 / 3", font=("Arial", 13, "bold"))
        self.mistakes_label.grid(row=0, column=1, padx=18)

        self.score_label = tk.Label(score_frame, text="Score: 0", font=("Arial", 13, "bold"))
        self.score_label.grid(row=0, column=2, padx=18)

        image_frame = tk.Frame(self.root)
        image_frame.pack(expand=True, fill=tk.BOTH, padx=15, pady=10)

        left_frame = tk.Frame(image_frame)
        left_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=8)

        right_frame = tk.Frame(image_frame)
        right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=8)

        tk.Label(left_frame, text="Original Image", font=("Arial", 14, "bold")).pack(pady=5)
        tk.Label(right_frame, text="Modified Image - Click Here", font=("Arial", 14, "bold")).pack(pady=5)

        self.original_canvas = tk.Canvas(left_frame, width=self.DISPLAY_MAX_WIDTH, height=self.DISPLAY_MAX_HEIGHT, bg="#eeeeee")
        self.original_canvas.pack(expand=True)

        self.modified_canvas = tk.Canvas(right_frame, width=self.DISPLAY_MAX_WIDTH, height=self.DISPLAY_MAX_HEIGHT, bg="#eeeeee")
        self.modified_canvas.pack(expand=True)
        self.modified_canvas.bind("<Button-1>", self.handle_click)

    def load_image(self):
        """Opens a file dialog and loads a new image."""
        file_path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("BMP files", "*.bmp"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        image = cv2.imread(file_path)
        if image is None:
            messagebox.showerror("Loading Error", "Could not load the selected image.")
            return

        try:
            self.original_image = image
            self.modified_image, self.regions = self.generator.generate(self.original_image)
        except ValueError as error:
            messagebox.showerror("Image Error", str(error))
            return

        self.mistakes = 0
        self.clicks_locked = False
        self.reveal_button.config(state=tk.NORMAL)
        self.info_label.config(text="Find all 5 differences. Only click on the modified image.")
        self.update_status()
        self.refresh_canvases()

    def calculate_display_size(self, image: np.ndarray):
        """Calculates scaled display size while preserving aspect ratio."""
        height, width = image.shape[:2]
        self.scale = min(self.DISPLAY_MAX_WIDTH / width, self.DISPLAY_MAX_HEIGHT / height, 1.0)
        self.display_w = int(width * self.scale)
        self.display_h = int(height * self.scale)

    def prepare_display_image(self, image: np.ndarray, reveal_unfound: bool = False):
        """Prepares an image for Tkinter display and draws feedback circles."""
        display_image = image.copy()

        for region in self.regions:
            if region.found:
                self.draw_region_circle(display_image, region, (0, 0, 255))  # red in BGR
            elif region.revealed:
                self.draw_region_circle(display_image, region, (255, 0, 0))  # blue in BGR

        resized = cv2.resize(display_image, (self.display_w, self.display_h), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb)
        return ImageTk.PhotoImage(pil_image)

    def draw_region_circle(self, image: np.ndarray, region: DifferenceRegion, colour):
        """Draws a circle around a difference region on the full-size image."""
        cv2.circle(image, region.center, region.radius, colour, 3)

    def refresh_canvases(self, reveal_unfound: bool = False):
        """Redraws both image canvases."""
        if self.original_image is None or self.modified_image is None:
            return

        self.calculate_display_size(self.original_image)

        self.original_photo = self.prepare_display_image(self.original_image, reveal_unfound)
        self.modified_photo = self.prepare_display_image(self.modified_image, reveal_unfound)

        self.original_canvas.delete("all")
        self.modified_canvas.delete("all")

        x_offset = (self.DISPLAY_MAX_WIDTH - self.display_w) // 2
        y_offset = (self.DISPLAY_MAX_HEIGHT - self.display_h) // 2

        self.original_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.original_photo)
        self.modified_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.modified_photo)

    def handle_click(self, event):
        """Handles mouse clicks on the modified image."""
        if self.clicks_locked or self.modified_image is None:
            return

        x_offset = (self.DISPLAY_MAX_WIDTH - self.display_w) // 2
        y_offset = (self.DISPLAY_MAX_HEIGHT - self.display_h) // 2

        if not (x_offset <= event.x <= x_offset + self.display_w and y_offset <= event.y <= y_offset + self.display_h):
            return

        original_x = int((event.x - x_offset) / self.scale)
        original_y = int((event.y - y_offset) / self.scale)

        clicked_region = None
        for region in self.regions:
            if not region.found and region.contains_click(original_x, original_y):
                clicked_region = region
                break

        if clicked_region:
            clicked_region.found = True
            self.total_score += 1
            self.info_label.config(text=f"Correct! Found: {clicked_region.alteration_type}")
            self.refresh_canvases()
            self.check_completion()
        else:
            self.mistakes += 1
            self.info_label.config(text="Wrong click. Try carefully.")
            if self.mistakes >= self.MAX_MISTAKES:
                self.clicks_locked = True
                self.info_label.config(text="Game locked: 3 mistakes reached. Load a new image or reveal differences.")
                self.update_status()
                messagebox.showwarning(
                    "Too Many Mistakes",
                    "You have made 3 mistakes. No further guesses are allowed for this image."
                )
                return

        self.update_status()

    def check_completion(self):
        """Checks if all five differences have been found."""
        if all(region.found for region in self.regions):
            self.clicks_locked = True
            self.reveal_button.config(state=tk.DISABLED)
            self.info_label.config(text="Congratulations! You found all 5 differences. Load another image to continue.")
            messagebox.showinfo("Completed", "Well done! You found all 5 differences.")

    def reveal_differences(self):
        """Marks all unfound differences in blue and ends the current round."""
        if self.original_image is None:
            return

        self.clicks_locked = True
        self.reveal_button.config(state=tk.DISABLED)

        for region in self.regions:
            if not region.found:
                region.revealed = True

        self.info_label.config(text="Unfound differences revealed in blue. Load a new image to restart.")
        self.update_status()
        self.refresh_canvases(reveal_unfound=True)

    def update_status(self):
        """Updates remaining, mistake, and score labels."""
        remaining = sum(1 for region in self.regions if not region.found and not region.revealed)
        self.remaining_label.config(text=f"Remaining: {remaining}")
        self.mistakes_label.config(text=f"Mistakes: {self.mistakes} / {self.MAX_MISTAKES}")
        self.score_label.config(text=f"Score: {self.total_score}")


def main():
    root = tk.Tk()
    app = SpotDifferenceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
