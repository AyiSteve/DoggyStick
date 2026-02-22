from inference_sdk import InferenceHTTPClient
import base64

import os 
from pprint import pprint


from typing import List, Dict, Any

class PedestrianLightDetector:
    def __init__(
            self,
            api_key: str,
            workspace_name: str,
            workflow_id: str,
            api_url: str = "https://serverless.roboflow.com",
            min_confidence: float =0.40,
    ):
        self.client  = InferenceHTTPClient(
                api_url=api_url,
                api_key=api_key)
        self.workspace_name = workspace_name
        self.workflow_id = workflow_id
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
        "Return : pedestrain light, red light, unknown"
        result = self.client.run_workflow(
            workspace_name=self.workspace_name,
            workflow_id=self.workflow_id,
            images={"image": img_path},
            use_cache=True
        )
        item = result[0] if isinstance(result, list) and result else result


        # remove the huge visualization field if present 
        if not isinstance(item,dict):
            return "unknown"
        item.pop("visualization", None)

        predictions = self.extract_predictions(item)
        if not predictions:
            return "unknown"
        
        # pick the highest confidence prediction 
        best = max(predictions, key=lambda p : p.get("confidence",0))
        conf = float(best.get("confidence", 0))
        raw_class = str(best.get("class", "")).lower()

        if conf < self.min_confidence:
            return "unknown"
        
        # needs to convert the name of the class and return pedestrian light/ red light 
        if "pedestrian" in raw_class:
            return "pedestrian light"
        else: 
            return "red light"
def main():
    API_KEY = "33kWcCWTIdNOSMB0eTvR"
    detector = PedestrianLightDetector(
        api_key=API_KEY,
        workspace_name="object-detection-phsdt",
        workflow_id="detect-count-and-visualize-2",
        min_confidence=0.40
    )

    img_path = "raspberryPI/object_det_test_picture/test2.png"
    label = detector.classify_image(img_path)
    print(label)


if __name__ == "__main__":
    main()





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