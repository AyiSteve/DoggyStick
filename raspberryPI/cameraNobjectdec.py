import time
from camera import capture_image
from api.object_detection import PedestrianLightDetector 
def capture_detection() -> dict:
    detector = PedestrianLightDetector()

    t0 = time.perf_counter()

    img_path = capture_image()   # always same file

    label = detector.classify_image(img_path)

    t1 = time.perf_counter()

    return {
        "label": label,
        "image_path": img_path,
        "latency_s": t1 - t0
    }
    
if __name__ == "__main__":
    out = capture_detection()
    print(out)

