#!/usr/bin/env python3
import cv2

# Print the OpenCV version
print(f"OpenCV Version: {cv2.__version__}")

# Optional: Print additional information about the OpenCV build
print(f"OpenCV Build Information:")
print(f"  - Configuration: {cv2.getBuildInformation().split('General configuration')[1].split('    ')[1]}")
print(f"  - Platform: {cv2.getBuildInformation().split('Platform')[1].split('    ')[1]}")

# Confirm that OpenCV has been successfully imported
print("OpenCV has been successfully imported and is ready to use.")

