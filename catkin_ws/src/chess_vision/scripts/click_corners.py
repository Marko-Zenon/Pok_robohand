import cv2
import os
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FILE_RELATIVE = "../data/current_photo/board2.jpg"
OUTPUT_FOLDER_RELATIVE = "../data/cells"

IMAGE_FILE = os.path.join(SCRIPT_DIR, IMAGE_FILE_RELATIVE)
OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, OUTPUT_FOLDER_RELATIVE)

points = []

def click_event(event, x, y, flags, params):
    # Left click handling
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Click {len(points)+1}/4: [{x}, {y}]")
        points.append([x, y])

        # Draws a point
        cv2.circle(img, (x, y), 4, (0, 0, 255), -1)
        cv2.imshow("Click Corners", img)

        if len(points) == 4:
            print(f"src_points = np.float32({points})")

img = cv2.imread(IMAGE_FILE)

if img is None:
    print(f"Could`nt find {IMAGE_FILE}")
else:
    print("Click in order 4 inside corners of a board:")
    print("1)Upper-left")
    print("2)Upper-right")
    print("3)Lower-right")
    print("4)Lower-left")

    cv2.imshow("Click Corners", img)
    cv2.setMouseCallback("Click Corners", click_event)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()