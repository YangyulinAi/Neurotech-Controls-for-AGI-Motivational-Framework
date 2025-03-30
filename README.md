# Neurotech Controls for AGI Motivational Framework

This project is a prototype for a brain-computer interface (BCI) framework that links human emotional and cognitive states (such as valence and arousal measured from EEG, fNIRS, and heart rate data) with Artificial General Intelligence (AGI) motivational systems. The system enables real-time modulation of AI agents based on the user's brain activity.

## Overview

The project leverages neurocognitive and psychological models (e.g., OpenPsi, Dorner’s Psi Theory) to develop a robust mechanism for controlling AGI behavior. Through a sequence of experiments—including resting state and video-based emotion induction—the framework captures labeled brain data and uses it to modulate motivational parameters.

## Features

- **Sequential Video Playback and Rating Workflow**
  - **Stage 1:** Video playback (input disabled).
  - **Stage 2:** Valence rating (emotional pleasantness).
  - **Stage 3:** Arousal rating (activation level).
  - Automatic transitions between stages and videos.
- **LSL Integration**
  - Sends event markers via Lab Streaming Layer (LSL) for data logging.
- **High-Resolution Video Display**
  - Uses Render Texture and RawImage to display high-quality video while maintaining the aspect ratio.
- **Customizable UI Layout**
  - Easily adjust the hint text position and layout via the Unity Editor or code.

## Requirements

- Unity 2020.3 LTS (or later recommended)
- LSL4Unity package (included in the project)
- Compatible video file format (e.g., H.264 encoded MP4 files using baseline profile for best compatibility)
- EEG, fNIRS, or other neurotech data collection devices (for experimental usage)

## Installation

1. Clone or download the repository.
2. Open the project in Unity.
3. Place your video files in the `Assets/StreamingAssets/` folder.
4. In the Unity Editor, configure the UI components (e.g., RawImage, hintText) and assign them to the corresponding fields in the `EventController` script.
5. Build and run the project on your target platform.

## Usage

1. Launch the project. The system will start with video playback.
2. After the video finishes, the system transitions to the rating phase:
   - **Stage 2:** Rate Valence by pressing keys 1-5.
   - **Stage 3:** Rate Arousal by pressing keys 1-5.
3. Once the ratings are complete, the system automatically plays the next video.
4. LSL markers are sent during the rating process to record event data.
5. Detailed logs and experimental data are recorded using the integrated Logger and UdpSender modules.

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes with clear messages.
4. Submit a pull request for review.

## Contributors

- **Yangyulin Ai, PhD(c)**
- **Gabriel Axel Montes, PhD**

## License



