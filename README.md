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
