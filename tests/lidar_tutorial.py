import os
import ydlidar

if __name__ == "__main__":
    ydlidar.os_init()
    laser = ydlidar.CYdLidar()
    
    # Stel de poort in op /dev/ttyUSB1
    port = "/dev/ttyUSB1"  # Specificeer hier de poort die je wilt gebruiken
    
    # Stel de LiDAR opties in
    laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
    laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 512000)
    laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TOF)
    laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
    laser.setlidaropt(ydlidar.LidarPropScanFrequency, 10.0)
    laser.setlidaropt(ydlidar.LidarPropSampleRate, 20)
    laser.setlidaropt(ydlidar.LidarPropSingleChannel, False)

    # Initialiseer de LiDAR
    ret = laser.initialize()
    if ret:
        ret = laser.turnOn()
        scan = ydlidar.LaserScan()
        while ret and ydlidar.os_isOk():
            r = laser.doProcessSimple(scan)
            if r:
                # Controleer of scan_time geldig is voordat je de frequentie berekent
                if scan.config.scan_time != 0:
                    print("Scan received[", scan.stamp, "]:", scan.points.size(), "ranges is [", 1.0 / scan.config.scan_time, "]Hz")
                else:
                    print("Scan received[", scan.stamp, "]: scan_time is 0, unable to calculate frequency.")
            else:
                print("Failed to get Lidar Data.")
        laser.turnOff()
    laser.disconnecting()
