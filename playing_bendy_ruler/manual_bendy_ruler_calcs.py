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


    def arm_and_takeoff(self, alt: int = 0.95) -> None:   
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

    def get_new_velocity(self, distance: float,
                        direction: float, max_distance: float,
                        max_velocity: int = 30) -> Tuple[int, int, int]:
        vx, vy, vz = self.vehicle.velocity

        if distance < max_distance:
            repulsive_force = 1.0 / (distance + 1e-6) 
            repulsive_force_x = repulsive_force * math.cos(direction)
            repulsive_force_y = repulsive_force * math.sin(direction)
            new_x = vx - repulsive_force_x
            new_y = vy - repulsive_force_y

            speed = math.sqrt(math.pow(new_x, 2) * math.pow(new_y, 2) * math.pow(vz))
            if speed > max_velocity:
                scaling_factor = max_velocity / speed
                new_x *= scaling_factor
                new_y *= scaling_factor
                vz *= scaling_factor 
        else:
            new_x, new_y, vz = vx, vy, vz
        
        return new_x, new_y, vz

    def angle(self, log1: float, lat1: float, log2: float, lat2: float) -> float:
        log1 = math.radians(log1)
        log2 = math.radians(log2)
        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)

        delta_log = log2 - log1

        x = math.cos(lat2) * math.sin(delta_log)
        y  = math.cos(lat1) * math.sin(lat2) * math.cos(lat2) * math.cos(delta_log)

        i_angle = math.atan2(x, y)
        i_angle = math.degrees(i_angle)
        final_angle = (i_angle + 360) % 360

        return final_angle 

    def haver_distance(self, log1: float, lat1: float, log2: float, lat2: float) -> float:
        log1 = math.radians(log1)
        log2 = math.radians(log2)
        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)

        delta_log = log2 - log1
        delta_lat = lat2 - lat1

        a = math.pow(math.sin(delta_lat / 2), 2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(delta_log / 2), 2)
        c = 2 * math.atan(math.sqrt(a), math.sqrt(1 - a))
        earth_radius = 6371
        d = earth_radius * c # in km
        return d / 1000 # in m
