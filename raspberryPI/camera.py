
# using picamera2 class to taking the picture 
# using cv2 to showing the picture 
import cv2
import time 

import os
import subprocess
from datetime import datetime



def capture_image(folder="cam_pic"):
    os.makedirs(folder, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = os.path.join(folder, f"image_{ts}.jpg")
    # subprocess.run(["rpicam-still", "-o", img_path], check=True)
    subprocess.run(["rpicam-still", "-n", "-t", "1",
                    "--width", "640", "--height", "480",
                    "--quality", "70", "-o",  img_path], check=True)
    return img_path 


if __name__ == "__main__":
    image = capture_image()
    print("Image capture success")
    print("Image shape: ", image.shape)

    # # show image, wait a key pass and close all image window
    # cv2.imshow("test capture", image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()



    # take picture rpicam-still -o Desktop/image.jpg

