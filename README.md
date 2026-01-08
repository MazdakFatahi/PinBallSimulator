# 🎮 Pinball Game Simulator (Python)

This repository contains a **simple 2D pinball game simulator** written in Python.  
It is designed for experimentation, simulation, and research purposes (control, perception, reinforcement learning, neuromorphic vision, etc.).


## 📁 Repository Structure

```
pinball-game/
├── PinBallGameEnvironment.py   # Main game environment class
├── game.py                     # Example script to run the game
└── README.md                   # This file
```

---

## ⚙️ Requirements

- Python **3.7+**
- `numpy`
- `pygame`

---

## 📦 Install Dependencies

It is **strongly recommended** to use a virtual environment.

### Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

**Ubuntu / Debian (if venv is missing):**

```bash
sudo apt install python3-venv
```

### Install required Python packages

```bash
pip install numpy pygame
```

---

## ▶️ Example: 

```bash
python game.py
```

---

## 🧠 Main Class: `GameEnvironment`

The core logic of the simulator is implemented in:

```
PinBallGameEnvironment.py
```

### Importing the environment

```python
import PinBallGameEnvironment as env
```

or

```python
from PinBallGameEnvironment import GameEnvironment
```

---

## 🚀 Initialization Example

```python
# Counters and logs
all_times = []
cnt_left = 0
cnt_right = 0
cnt_left_success_hit, cnt_right_success_hit = 0, 0
total_cnt_left = 0
total_cnt_right = 0
total_cnt_left_success_hit, total_cnt_right_success_hit = 0, 0

# Geometry and camera
bottom_area_height = 250
upper_area_height = 150
camera_fov = (256, 256)

height = bottom_area_height + camera_fov[1] + upper_area_height
width = 256

# Game parameters
num_episodes = 5
max_ball_speed = 1_000
flipper_rotation_speed_frac = 1

# Initialize the game environment
game = env.GameEnvironment(
    bottom_area_height=bottom_area_height,
    height=height,
    width=width,
    show_fov=True,
    camera_height=camera_fov[0],
    ball_radius=12,
    bumpers_radius=[15, 12, 12],
    num_leds=10,
    save_speed_log=False,
    num_episodes=num_episodes,
    max_ball_speed=max_ball_speed,
    flipper_rotation_speed_frac=flipper_rotation_speed_frac
)
```

---

## 🧩 Parameter Explanation

### 📐 Environment Geometry

| Parameter | Description |
|----------|-------------|
| `width` | Width of the game window (pixels) |
| `height` | Total height of the game window |
| `bottom_area_height` | Height of the lower (flippers) area |
| `upper_area_height` | Height of the upper static area |

### 📷 Camera / Field of View

| Parameter | Description |
|----------|-------------|
| `show_fov` | Displays the camera field of view |
| `camera_height` | Height of the camera region |
| `camera_fov` | Field of view resolution `(width, height)` |

### ⚽ Ball & Physics

| Parameter | Description |
|----------|-------------|
| `ball_radius` | Radius of the pinball |
| `max_ball_speed` | Maximum allowed ball speed |
| `flipper_rotation_speed_frac` | Flipper rotation speed multiplier |

### 🔴 Obstacles & Elements

| Parameter | Description |
|----------|-------------|
| `bumpers_radius` | List of bumper radii |
| `num_leds` | Number of LEDs in the environment |

### 🎮 Simulation Control

| Parameter | Description |
|----------|-------------|
| `num_episodes` | Number of episodes (games) |
| `save_speed_log` | Save ball speed history |


