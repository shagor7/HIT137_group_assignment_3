# HIT137 Assignment 3 - Spot the Difference Game

## How to run

1. Install Python 3.
2. Install required packages:

```bash
pip install -r requirements.txt
```

On Ubuntu, if normal pip is blocked, use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python spot_difference_game.py
```

3. Run the program:

```bash
python spot_difference_game.py
```

## Files

- `spot_difference_game.py` - main assignment code
- `requirements.txt` - required packages
- `github_link.txt` - replace the placeholder with your public GitHub repository link

## Features implemented

- OOP structure using multiple classes
- Tkinter GUI
- Image loading using file dialog
- Supports JPG, PNG, and BMP
- Displays original and modified images side by side
- Generates exactly 5 random non-overlapping differences
- Uses OpenCV for all image manipulation
- Includes colour shift, blur, brightness change, and small shape alterations
- Click detection with tolerance
- Red circles for found differences on both images
- Remaining counter, mistake counter, and score
- Locks guesses after 3 mistakes
- Reveal button marks unfound differences in blue
