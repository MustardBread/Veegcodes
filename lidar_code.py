import os
import ydlidar
import time
import sys
from matplotlib.patches import Arc
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

RMAX = 32.0
MUUR = False  # Start met MUUR op False

# Create a plot
fig = plt.figure()
fig.canvas.setWindowTitle('YDLidar LIDAR Monitor')
lidar_polar = plt.subplot(polar=True)
lidar_polar.autoscale_view(True, True, True)
lidar_polar.set_rmax(RMAX)
lidar_polar.grid(True)

# Manually set the correct port
port = "/dev/ttyUSB1"  

# Initialize the LiDAR
laser = ydlidar.CYdLidar()
laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 512000)  
laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TOF)
laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
laser.setlidaropt(ydlidar.LidarPropScanFrequency, 10.0)
laser.setlidaropt(ydlidar.LidarPropSampleRate, 9)
laser.setlidaropt(ydlidar.LidarPropSingleChannel, False)

scan = ydlidar.LaserScan()

# Initialize the LiDAR
ret = laser.initialize()
if not ret:
    print("Failed to initialize the LiDAR!")
    sys.exit(1)

# Turn on the LiDAR
ret = laser.turnOn()
if not ret:
    print("Failed to turn on the LiDAR!")
    sys.exit(1)

# Define a threshold for detecting the "wall" (MUUR)
threshold_distance = 0.5  # meters, change this value as needed

# Define the angle ranges for filtering
# For angles between 0° and 180° (0 rad to pi rad)
min_angle_1 = np.deg2rad(0)    # 0 degrees in radians
max_angle_1 = np.deg2rad(180)  # 180 degrees in radians

# For angles between 180° and 360° (pi rad to 2*pi rad)
min_angle_2 = np.deg2rad(180)  # 180 degrees in radians
max_angle_2 = np.deg2rad(360)  # 360 degrees in radians

def animate(num):
    global MUUR  # Declare MUUR as global to modify it inside the function
    r = laser.doProcessSimple(scan)
    if not r:
        print("Failed to retrieve scan data!")
        return

    angle = []
    ran = []
    intensity = []
    
    # Loop through all points and check if any range is below the threshold and angle is in the specified range
    MUUR = False  # Reset MUUR to False at the start of each frame
    for point in scan.points:
        # Correct negative angles to be positive (0 to 360 degrees)
        if point.angle < 0:
            point.angle += 2 * np.pi  # Add 2*pi to the negative angles to bring them into the 0-2pi range

        # Print the corrected angle for debugging purposes
        print(f"Corrected Angle: {point.angle} radians, {np.rad2deg(point.angle)} degrees")
        
        # Filter the points based on angle range
        if min_angle_1 <= point.angle < max_angle_1:  # Angles between 0° and 180° (0 rad to pi rad)
            angle.append(point.angle)
            ran.append(point.range)
            intensity.append(point.intensity)

            # Check if the point is below the threshold distance
            if point.range < threshold_distance:
                MUUR = True
        
        elif min_angle_2 <= point.angle < max_angle_2:  # Angles between 180° and 360° (pi rad to 2*pi rad)
            angle.append(point.angle)
            ran.append(point.range)
            intensity.append(point.intensity)

            # Check if the point is below the threshold distance
            if point.range < threshold_distance:
                MUUR = True

    lidar_polar.cla()  # Clears the current axes
    lidar_polar.set_rmax(RMAX)
    lidar_polar.set_title("YDLidar LIDAR Monitor")
    lidar_polar.scatter(angle, ran, c=intensity, cmap='hsv', alpha=0.95)

    # Print the MUUR status for debugging
    print("MUUR status:", MUUR)

# Start the animation
ani = animation.FuncAnimation(fig, animate, interval=50)
plt.show()

# Turn off the LiDAR and disconnect
laser.turnOff()
laser.disconnecting()
plt.close()