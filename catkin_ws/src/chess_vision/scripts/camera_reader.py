#!/usr/bin/env python3
import rospy
import cv2
import os
import sys
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from std_srvs.srv import Trigger, TriggerResponse

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from split_board import ChessSplitter
except ImportError:
    print("Split_board not found")
    sys.exit(1)

class ChessCameraReader:
    def __init__(self):
        rospy.init_node('chess_camera_reader', anonymous=True)
        self.bridge = CvBridge()

        # Dirs
        self.board_path = os.path.normpath(os.path.join(current_dir, "../data/current_photo/board2.jpg"))
        self.cells_dir = os.path.normpath(os.path.join(current_dir, "../data/cells"))

        if not os.path.exists(os.path.dirname(self.board_path)):
            os.makedirs(os.path.dirname(self.board_path))

        self.splitter = ChessSplitter(self.cells_dir)
        
        self.latest_image = None

        # Camera subscriber
        rospy.Subscriber("/usb_cam/image_raw", Image, self.image_callback)
        
        # Waits for robots call
        self.service = rospy.Service('trigger_chess_capture', Trigger, self.handle_capture_request)
        
        print(f"Camera Node started. Waiting for robot`s move...")

    def image_callback(self, data):
        """Updates last frame in memory"""
        try:
            self.latest_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except Exception as e:
            pass

    def handle_capture_request(self, req):
        """Called by robot when it finished a move"""
        if self.latest_image is None:
            return TriggerResponse(success=False, message="No image received yet")

        try:
            print("Got a new imge, processing...")

            cv_image = cv2.resize(self.latest_image, (640, 480))

            cv2.imwrite(self.board_path, cv_image)

            self.splitter.process_image(cv_image)

            print("Image is sliced")
            return TriggerResponse(success=True, message="Success")

        except Exception as e:
            print(f"Error: {e}")
            return TriggerResponse(success=False, message=str(e))

if __name__ == '__main__':
    try:
        ChessCameraReader()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass