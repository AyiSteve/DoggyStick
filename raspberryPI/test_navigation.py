from api.mapapi import MapNavigator


def main():
    print("=== LIVE MapNavigator Functionality Test ===")

    # Test coordinates
    start = (47.653785, -122.308408)   # UW
    destination = "Seattle Public Library"

    nav = MapNavigator(current=start)
    nav.updateDestination(destination)

    print(f"Start: {start}")
    print(f"Destination: {destination}")

    # CALL FUNCTION UNDER TEST
    print("\nCalling updateDirection() ...")
    nav.updateDirection()

    # Validate walking path
    print("\n--- Walking Path ---")
    assert nav.WalkPath is not None
    assert len(nav.WalkPath) > 0

    print(f"Number of walk waypoints: {len(nav.WalkPath)}")
    print("First 3 walk points:")
    for pt in nav.WalkPath[:3]:
        print(" ", pt)

    print("Last walk point:", nav.WalkPath[-1])

    # Validate transit path

    print("\n--- Transit Path ---")
    assert nav.TransitPath is not None
    assert len(nav.TransitPath) > 0

    print(f"Number of transit waypoints: {len(nav.TransitPath)}")
    print("First 3 transit points:")
    for pt in nav.TransitPath[:3]:
        print(" ", pt)

    print("Last transit point:", nav.TransitPath[-1])

    # Distance + duration
    walk_dist, walk_time = nav.getDistanceWalk()
    transit_dist, transit_time = nav.getDistanceTransit()

    print("\n--- Distance & Duration ---")
    print(f"Walking:  {walk_dist}, {walk_time}")
    print(f"Transit:  {transit_dist}, {transit_time}")

    # Distance + bearing sanity
    p1 = nav.WalkPath[0]
    p2 = nav.WalkPath[-1]

    dist_m = nav.distance(p1, p2)
    bearing = nav.bearing(p1, p2)

    print("\n--- Geometry Sanity ---")
    print(f"Geodesic distance: {dist_m:.2f} meters")
    print(f"Bearing: {bearing:.2f} degrees")

    assert dist_m > 0
    assert 0 <= bearing <= 360

    print("\nLIVE MapNavigator FUNCTIONALITY TEST PASSED")


# Entry Point
if __name__ == "__main__":
    main()