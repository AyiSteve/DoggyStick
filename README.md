# DoggyStick – Autonomous Navigation System for the Visually Impaired

DoggyStick is an autonomous navigation assistance system designed to help visually impaired users safely travel to a destination. The system integrates GPS navigation, obstacle detection, voice commands, and traffic light recognition to guide users along a walkable route.

The system runs on a **Raspberry Pi**, which handles navigation logic, sensor processing, and voice recognition, while an **STM32 microcontroller** controls the motors that drive the vehicle.

---

# Features

- Voice-based destination input
- GPS-based navigation using Google Maps API
- Obstacle detection using ultrasonic sensors
- Pedestrian traffic light detection using machine learning
- Bluetooth communication between Raspberry Pi and STM32
- Multithreaded sensor processing
- Web-based debugging dashboard

---

# System Architecture

The system consists of three main layers.

## 1. Sensor Layer

Collects information from the environment and the user.

Hardware used:

- **NEO-6M GPS Module** – Provides current location
- **Ultrasonic Sensors** – Detect nearby obstacles
- **INMP441 Microphone** – Captures voice commands
- **Raspberry Pi Camera** – Detects pedestrian traffic lights

---

## 2. Navigation Layer

Handles navigation logic and decision making.

### MapNavigator
Responsible for communication with the Google Maps API.

Functions include:

- `updateDestination()`
- `updateCurrentLocation()`
- `distance()`
- `bearing()`
- `updateDirection()`

The `updateDirection()` function requests a **walkable route** between the current location and destination and stores the route as a series of waypoints.

---

### Navigation

Implements the navigation logic and state machine.

Key responsibilities:

- Determine if the user is following the route
- Detect wrong direction movement
- Detect off-route conditions
- Determine steering angle

Navigation states include:

- `FOLLOW_ROUTE`
- `AVOID`
- `WRONG_DIRECTION`
- `OFF_ROUTE`
- `DESTINATION_REACHED`
- `EMStop`

---

### NavigationSupervisor

The **central controller** of the system.

Responsibilities:

- Collect sensor data
- Run navigation logic
- Send commands to the STM32
- Manage system threads

Multiple threads run simultaneously for:

- GPS updates
- Ultrasonic sensor readings
- Voice command processing
- Navigation updates
- Debug server

---

## 3. Motion Control Layer

Controls the physical movement of the vehicle.

Components:

- **STM32 Microcontroller**
- **Motor Driver**
- **DC Motors**

Movement commands are sent from the Raspberry Pi to the STM32 via **Bluetooth UART**.

Command format:
(num,time)
Example:
(3,10000000)
Where:

- `num` represents the command type
- `time` represents how long the action should run

Typical commands include:

- Move forward
- Stop
- Turn

The STM32 interprets these commands and drives the motor driver accordingly.

---

# Obstacle Avoidance

Three ultrasonic sensors are placed at the **front, left, and right** of the device.

The algorithm works as follows:

1. Check if an obstacle is directly in front.
2. Compare left and right distances.
3. Turn toward the side with more available space.
4. Resume route following when the path is clear.

---

# Traffic Light Detection

Traffic lights are detected using a **Roboflow object detection model**.

Steps:

1. Raspberry Pi captures an image using `rpicam-still`.
2. The image is sent to the Roboflow detection API.
3. The server returns detected objects and confidence scores.
4. If a **red light** is detected, the system triggers **EMStop**.

---

# Voice Command Input

The destination is provided using voice commands.

Process:

1. User presses a button connected to GPIO.
2. Audio recording starts using `arecord`.
3. Recording stops when the button is released.
4. Audio is converted to mono using `sox`.
5. Speech is converted to text using **VOSK**.
6. The recognized text is used to search destinations using the **Google Text Search API**.

---

# Debug Dashboard

A lightweight web server is included to monitor system variables.

The dashboard displays:

- Current GPS location
- Navigation state
- Target waypoint
- Distance to destination
- Ultrasonic sensor readings
- Current heading
- Turn angle

It also allows manual testing such as:

- Setting current location
- Updating destination
- Sending manual turn commands

Access the dashboard at:
http://localhost:8080/ui
---

# Hardware Components

| Component | Purpose |
|--------|--------|
| Raspberry Pi | Main processing unit |
| STM32 Microcontroller | Motor control |
| NEO-6M GPS | Location tracking |
| INMP441 Microphone | Voice input |
| Ultrasonic Sensors | Obstacle detection |
| Motor Driver | Controls motor power |
| DC Motors | Drive the wheels |
| Raspberry Pi Camera | Traffic light detection |
| Bluetooth Module | Communication between Pi and STM32 |

---

# Software Dependencies

Python libraries:
pynmea2
requests
gpiozero
opencv-python
vosk
System tools:
arecord
sox
rpicam-still
---

# Running the System

Start the navigation supervisor:
python navigationSupervisor.py
Open the debug dashboard:
http://:8080/ui
---

# Future Improvements

- Local object detection to reduce API latency
- Improved sensor fusion for better localization
- More accurate turning control
- Battery optimization
- Integration with wearable assistive devices

---

# License

This project is intended for educational and research purposes.
