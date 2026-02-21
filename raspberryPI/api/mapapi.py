import googlemaps
from geopy.distance import geodesic
import math
import polyline
import requests

gmaps = googlemaps.Client(key="AIzaSyDipGnBuSsmfubof6qHdRn-dKliz9MVzrA")

# This library connect with the google map api and ask for path from current to destination.
# Two type of path that can be explained: transit and walk
class MapNavigator:
    def __init__(self, current):
        self.currentLocation = current
        self.destination = None
        self.path = []

        self.directionsTransit = None
        self.directionsWalk = None
        self.WalkPath = None
        self.TransitPath = None

    def updateDestination(self, intendedDestination):
        self.destination = intendedDestination

    def updateCurrentLocation(self, current):
        self.currentLocation = current

    def updateDirection(self):
        print(self.currentLocation)
        if self.currentLocation is None or self.destination is None:
            print("MapNavigator: missing origin or destination")
            return
        self.directionsWalk = gmaps.directions(
            origin = self.currentLocation,
            destination = self.destination,
            mode = "walking"
        )

        #self.directionsTransit = gmaps.directions(
        #     origin = self.currentLocation,
        #     destination = self.destination,
        #     mode = "transit"
        # )

        steps = self.directionsWalk[0]["legs"][0]["steps"]
        self.WalkPath = []

        for step in steps:
            decoded = polyline.decode(step["polyline"]["points"])
            for point in decoded:
                self.WalkPath.append(point)

        print(steps)
        #steps = self.directionsTransit[0]["legs"][0]["steps"]
        #self.TransitPath = []
        #for step in steps:
            # start = step["start_location"]
            # end = step["end_location"]
            # self.TransitPath.append((start["lat"], start["lng"]))
            # self.TransitPath.append((end["lat"], end["lng"]))
       

    def getDistanceWalk(self):

        leg = self.directionsWalk[0]["legs"][0]
        distance = leg["distance"]["text"]
        duration = leg["duration"]["text"]

        return distance, duration
    
    def getDistanceTransit(self):

        leg = self.directionsTransit[0]["legs"][0]
        distance = leg["distance"]["text"]
        duration = leg["duration"]["text"]

        return distance, duration
    
    def getCurrentPathWalk(self, n):
        return self.WalkPath[n]
    
    def getCurrentPathTransit(self, n):
        return self.TransitPath[n]
    
    # Return the meters between two point
    def distance(self, p1, p2, radius = 6371000):
        lat1 = math.radians(p1[0])
        lat2 = math.radians(p2[0])
        long1 = math.radians(p1[1])
        long2 = math.radians(p2[1])
        x = (long2-long1)*math.cos(((lat2+lat1))/2)
        y = lat2-lat1
        return math.sqrt(x*x + y*y) * radius

    def bearing(self, p1, p2):
        # Convert to radians frin degrees
        lat1 = math.radians(p1[0])
        lat2 = math.radians(p2[0])
        long1 = math.radians(p1[1])
        long2 = math.radians(p2[1])

        # Differences between two point
        dlon = long2 - long1

        initial_bearing = math.atan2(math.sin(dlon)*math.cos(lat2), math.cos(lat1)*math.sin(lat2)-math.sin(lat1)*math.cos(lat2)*math.cos(dlon))
        bearing = (math.degrees(initial_bearing) + 360) % 360
        return bearing


    def recalculateRoute(self):
        """
        Recalculate walking route from current GPS to existing destination.
        """
        self.updateCurrentLocation(self.currentLocation)
        self.updateDirection()

        return self.WalkPath
    
    def text_search(self, query):
        if (query == None):
            return []
        lat, lng = self.currentLocation
        print(self.currentLocation)
        url = "https://places.googleapis.com/v1/places:searchText"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": "AIzaSyDipGnBuSsmfubof6qHdRn-dKliz9MVzrA",
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location"
        }

        body = {
            "textQuery": query,
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lng
                    },
                    "radius": 5000
                }
            }
        }

        response = requests.post(url, headers=headers, json=body)

        if response.status_code == 200:
            return response.json().get("places", [])
        else:
            print("Error:", response.text)
            return []
        
#import googlemaps

#API_KEY = "YOUR_API_KEY_HERE"
#gmaps = googlemaps.Client(key=API_KEY)

#directions = gmaps.directions(
#    origin=(47.653785, -122.308408),
#    destination="Seattle Public Library",
#    mode="walking"
#)

#steps = directions[0]["legs"][0]["steps"]

#print("directions")
#for i, step in enumerate(steps):
#    instruction = step["html_instructions"]
#    distance = step["distance"]["text"]
#    duration = step["duration"]["text"]
#    print(f"{i+1}. {instruction} ({distance}, {duration})")