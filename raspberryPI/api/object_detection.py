import base64
import os 
from pprint import pprint
import requests
import time
from typing import List, Dict, Any

class PedestrianLightDetector:
    def __init__(
            self,
            api_key: str ="3n6ywM5Jck752Comeagi",
            workspace_name: str = "pedestrian-traffic-light-3p4dd-zjeii/3",
            api_url: str = "https://serverless.roboflow.com",
            min_confidence: float =0.40,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.workspace_name = workspace_name
        self.min_confidence = min_confidence
    
    def extract_predictions(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        handles  Roboflow workflow result shapes and 
        returns a list of prediction dicts.
        """
        preds = item.get("predictions", [])

        # handle item["predictions"] is already a list of dicts
        if isinstance(preds, list):
            return [p for p in preds if isinstance(p, dict)]

        # handle item["predictions"] is a dict containing "predictions": [...]
        if isinstance(preds, dict):
            inner = preds.get("predictions", [])
            if isinstance(inner, list):
                return [p for p in inner if isinstance(p, dict)]

        return []
    
    def classify_image(self, img_path: str) -> str:
        url = f"https://detect.roboflow.com/{self.workspace_name}?api_key={self.api_key}"

        with open(img_path, "rb") as f:
            response = requests.post(url, files={"file": f})

        if response.status_code != 200:
            print("API Error:", response.text)
            return "unknown"

        result = response.json()

        predictions = result.get("predictions", [])
        if not predictions:
            return "unknown"

        best = max(predictions, key=lambda p: p.get("confidence", 0))
        conf = float(best.get("confidence", 0))
        raw_class = str(best.get("class", "")).lower()

        if conf < self.min_confidence:
            return "unknown"

        if "pedestrian" in raw_class:
            return "pedestrian light"
        else:
            return "red light"

# Test.... 2.292 second to communicate with server  
def main():
    detector = PedestrianLightDetector()
    t0 = time.perf_counter()
    img_path = "/home/steve/Desktop/DoggyStick/DoggyStick/raspberryPI/object_det_test_picture/test2.png"
    label = detector.classify_image(img_path)
    print(label)
    t1 = time.perf_counter()
    latency_s = t1-t0
    print(f"latency: {latency_s:.3f} s  ({latency_s*1000:.1f} ms)")

    




# provide from roboflow
# client = InferenceHTTPClient(
#     api_url="https://serverless.roboflow.com",
#     api_key="33kWcCWTIdNOSMB0eTvR"
# )

# img_path = "raspberryPI/object_det_test_picture/test6.png"

# with open(img_path, "rb") as f:
#     img_b64 = base64.b64encode(f.read()).decode("utf-8")
# result = client.run_workflow(
#     workspace_name="object-detection-phsdt",
#     workflow_id="detect-count-and-visualize-2",
#     images={
#         "image": img_path # Path to your image file
#     },
#     use_cache=True # Speeds up repeated requests
# )

# item = result[0] if isinstance(result, list) and result else result

# # remove the huge visualization field if present 
# if isinstance(item,dict):
#     item.pop("visualization", None)


# pprint({"predictions" : item.get("predictions",[])})