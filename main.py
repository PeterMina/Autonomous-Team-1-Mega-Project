import time
from dronekit import connect, VehicleMode, LocationGlobalRelative, Command
from typing import Tuple
from pymavlink import mavutil
import math

class Navigator:
    def __init__(self):
        self.vehicle = connect('udpin:0.0.0.0:14551')
        self.target_system = 0
        self.target_component = 0
        self.sequence = 0
        self.obstacles = []

    def change_mode(self, mode: str):
        """
        Change the vehicle mode.

        Args:
            mode (str): The mode to change to.
        """
        try:
            mode_id = self.vehicle._mode_mapping[mode]
            self.vehicle._master.mav.set_mode_send(self.target_system, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, mode_id)
            time.sleep(2)
        except Exception as e:
            print(f'Error changing mode: {e}')


    def arm_and_takeoff(self, alt: int = 20) -> None:   
        """
        Arms the vehicle and takes off to the target altitude.
        """

        print('Basic pre-arm checks')

        while not self.vehicle.is_armable:
            print('Waiting for vehicle to initialise...')
            time.sleep(1)

        print('Arming motors')

        self.change_mode('GUIDED')

        self.vehicle.armed = True

        while not self.vehicle.armed:
            print('Waiting for arming...')
            time.sleep(1)

        try:
            self.vehicle._master.mav.command_long_send(self.target_system, self.target_component, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,0,0,0,0,0,0,0, alt)
        except Exception as e:
            print(e)
            print("Error while trying to takeoff")
            return
        
        while True:
            print(f'Altitude: {self.vehicle.location.global_relative_frame.alt}')
            if self.vehicle.location.global_relative_frame.alt >=  alt * 0.95:
                print('Reached target altitude')
                break
            time.sleep(1)

    def setting_bendy_ruler(self) -> None:
        self.vehicle.parameters['OA_TYPE'] = 1
        self.vehicle.parameters['OA_BR_LOOKAHEAD'] = 5
        self.vehicle.parameters['OA_MARGIN_MAX'] = 3

    def take_off_and_waypoints(self, alt: int = 20) -> None:
        self.vehicle.commands.clear()
        self.vehicle.commands.upload()
        take_off = Command(self.target_system, self.target_component,
                        self.sequence,
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 
                        0, 0, 0, 0, 0, 0, 0, 0, alt)

        self.vehicle.commands.add(take_off)
        with open('./waypoints_and_obstalces/waypoints.txt', 'r', encoding='utf8') as file:
            while True:
                line = file.readline()
                if not line:
                    break
                lat, long = list(map(float, line.split(' ')))
                self.vehicle.commands.add(Command(self.target_system, self.target_component,
                        self.sequence, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0,
                        0, 0, 0, 0, 0, lat, long, alt))
        self.vehicle.commands.upload()

    def setting_obstalces(self) -> None:
        with open('./waypoints_and_obstalces/obstacles.txt', 'r', encoding='utf8') as file:
            while True:
                line = file.readline()
                if not line:
                    break
                lat, long = list(map(float, line.split(' ')))
                self.obstacles.append((lat, long))
        # self.set_fence((self.obstacles))
        self.vehicle.parameters['FENCE_ENABLE'] = 1
        self.vehicle.parameters['FENCE_ACTION'] = 0
        self.vehicle.parameters['FENCE_RADIUS'] = 5
        self.vehicle.parameters['FENCE_ALT_MAX'] = 100

    # def send_fence_point(self, idx, lat, lon):
    #     msg = self.vehicle.message_factory.fence_point_encode(self.target_system,
    #         self.target_component,
    #         idx,
    #         lat,
    #         lon)
    #     self.vehicle.send_mavlink(msg)

    # def set_fence(self, fence_points):
    #     self.vehicle.parameters['FENCE_TOTAL'] = len(fence_points)
    #     for idx, point in enumerate(fence_points):
    #         self.send_fence_point(idx, point[0], point[1])
    #     print("Fence uploaded and enabled!")

if __name__ == '__main__':
    drone = Navigator()
    drone.arm_and_takeoff()
    drone.setting_obstalces()
    drone.setting_bendy_ruler()
    drone.vehicle.airspeed = 30
    drone.take_off_and_waypoints()
    drone.change_mode('AUTO')
    time.sleep(60*5)
