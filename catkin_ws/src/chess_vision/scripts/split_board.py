import cv2
import numpy as np
import os

class ChessSplitter:
    def __init__(self, output_folder):
        self.output_folder = output_folder

        self.src_points = np.float32([[122, 22], [538, 34], [526, 447], [115, 434]])        
        self.side = 640
        self.dst_points = np.float32([[0, 0], [self.side, 0], [self.side, self.side], [0, self.side]])
        self.M = cv2.getPerspectiveTransform(self.src_points, self.dst_points)

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def process_image(self, img):
        img = cv2.resize(img, (640, 480))

        warped = cv2.warpPerspective(img, self.M, (self.side, self.side))

        step = self.side // 8
        ranks = ['1', '2', '3', '4', '5', '6', '7', '8']
        files = ['h', 'g', 'f', 'e', 'd', 'c', 'b', 'a'] 
        
        for r in range(8):
            for c in range(8):
                piece = warped[r*step:(r+1)*step, c*step:(c+1)*step]
                filename = os.path.join(self.output_folder, f"{files[c]}{ranks[r]}.jpg")
                cv2.imwrite(filename, piece)