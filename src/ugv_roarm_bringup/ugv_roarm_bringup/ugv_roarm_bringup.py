import rclpy
from rclpy.node import Node
from std_msgs.msg import Header, Float32MultiArray
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu, MagneticField, JointState, BatteryState

import os
import time
import json
import threading
import subprocess
import netifaces

from serial import SerialException
import threading

from .base_ctrl import BaseController

def get_all_ips():
    ip_dict = {}
    interfaces = netifaces.interfaces()
    for iface in interfaces:
        if iface == 'lo':
            continue
        addrs = netifaces.ifaddresses(iface)
        inet = addrs.get(netifaces.AF_INET)
        if inet:
            ip_dict[iface] = inet[0]['addr']
    return ip_dict

# ROS node class for bringing up the UGV system and publishing sensor data
class ugv_roarm_bringup(Node):
    def __init__(self):
        super().__init__('ugv_roarm_bringup')
        # Publishers for IMU data, magnetic field data, odometry, and voltage
        # self.imu_data_raw_publisher_ = self.create_publisher(Imu, "imu/data_raw", 100)
        self.imu_data_raw_publisher_ = self.create_publisher(Imu, "imu/raw", 20)
        self.imu_mag_publisher_ = self.create_publisher(MagneticField, "imu/mag", 100)
        self.odom_publisher_ = self.create_publisher(Float32MultiArray, "odom/odom_raw", 100)
        self.voltage_publisher_ = self.create_publisher(BatteryState, "ugv/voltage", 20)
        # Subscribe to velocity commands (cmd_vel topic)
        self.cmd_vel_sub_ = self.create_subscription(Twist, "cmd_vel", self.cmd_vel_callback, 10)
        self.zero_vel_count = 0
        self.zero_vel_limit = 5
        # Subscribe to joint states (joint_states topic)
        self.joint_states_sub = self.create_subscription(JointState, 'joint_states', self.joint_states_callback, 10)
        # Subscribe to LED control data (ugv/led_ctrl topic)
        self.led_ctrl_sub = self.create_subscription(Float32MultiArray, 'ugv/led_ctrl', self.led_ctrl_callback, 10)
        # Subscribe to voltage data (voltage topic)
        self.voltage_sub = self.create_subscription(BatteryState, 'ugv/voltage', self.voltage_callback, 20)
        
        self.declare_parameter('serial_port', '/dev/ttyAMA0')
        self.declare_parameter('baud_rate', 115200)
        serial_port_name = self.get_parameter('serial_port').value
        baud_rate = self.get_parameter('baud_rate').value
        
        self.roarm_type = os.environ['ROARM_MODEL']
        self.last_roarm_sent_data = None

        # Initialize the base controller with the UART port and baud rate
        self.base_controller = BaseController(serial_port_name, 115200)

        control_data = json.dumps({"T":301,"mode":0}) + "\n"
        self.base_controller.send_command(control_data.encode())   

        request_data = json.dumps({"T":131,"cmd":1}) + "\n"
        self.base_controller.send_command(request_data.encode())         

        # Timer to periodically execute the feedback loop
        self.feedback_thread = threading.Thread(target=self.feedback_loop_thread, daemon=True)
        self.feedback_thread.start()
        self.ip_thread = threading.Thread(target=self.ip_thread_func, daemon=True)
        self.ip_thread.start()

        self.set_ugv_version()

    def set_ugv_version(self):
        model = os.getenv("UGV_MODEL", "ugv_rover")
        ugv_main = 2

        if model == "ugv_rover":
            ugv_main = 2
        elif model == "ugv_beast":
            ugv_main = 3
        elif model == "rasp_rover":
            ugv_main = 1
        else:
            ugv_main = 2

        switch_dict = {
            "roarm_m2": 1,
            "roarm_m3": 3,
        }
        data = switch_dict[self.roarm_type]

        version_data = json.dumps({"T":900,"main":ugv_main,"module":data}) + "\n"
        self.base_controller.send_command(version_data.encode())  

    def feedback_loop_thread(self):
        rate = self.create_rate(20)
        while rclpy.ok():
            try:
                data = self.base_controller.feedback_data()
                if data and data["T"] == 1001:
                    self.publish_imu_data_raw()
                    self.publish_imu_mag()
                    self.publish_odom_raw()
                    self.publish_voltage()

            except Exception as e:
                self.get_logger().error(f"[feedback_loop_thread] error: {e}")
            rate.sleep()

    def ip_thread_func(self):
        last_wlan_ip = None
        last_eth_ip = None

        rate = self.create_rate(20)

        while rclpy.ok():
            ip_map = get_all_ips()
            wlan_ip = ip_map.get("wlan0", "N/A")
            eth_ip = ip_map.get("eth0", "N/A")

            if wlan_ip != last_wlan_ip:
                last_wlan_ip = wlan_ip
                data = json.dumps({'T': '3', 'lineNum': 1, 'Text': f"W:{wlan_ip}"}) + "\n"
                self.base_controller.send_command(data.encode())

            if eth_ip != last_eth_ip:
                last_eth_ip = eth_ip
                data = json.dumps({'T': '3', 'lineNum': 0, 'Text': f"E:{eth_ip}"}) + "\n"
                self.base_controller.send_command(data.encode())

            rate.sleep()

    # Publish IMU data to the ROS topic "imu/data_raw"
    def publish_imu_data_raw(self):
        msg = Imu()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()  # Get the current timestamp
        msg.header.frame_id = "base_link"
        imu_raw_data = self.base_controller.base_data

        # Populate the linear acceleration and angular velocity fields degree/s  m/s^2 
        msg.linear_acceleration.x = 9.8 * float(imu_raw_data["ax"]) / 8192
        msg.linear_acceleration.y = 9.8 * float(imu_raw_data["ay"]) / 8192
        msg.linear_acceleration.z = 9.8 * float(imu_raw_data["az"]) / 8192
        
        msg.angular_velocity.x = 3.1415926 * float(imu_raw_data["gx"]) / (16.4 * 180)
        msg.angular_velocity.y = 3.1415926 * float(imu_raw_data["gy"]) / (16.4 * 180)
        msg.angular_velocity.z = 3.1415926 * float(imu_raw_data["gz"]) / (16.4 * 180)
              
        self.imu_data_raw_publisher_.publish(msg)  # Publish the IMU data
        
    # Publish magnetic field data to the ROS topic "imu/mag"
    def publish_imu_mag(self):
        msg = MagneticField()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()  # Get the current timestamp
        msg.header.frame_id = "base_link"
        imu_raw_data = self.base_controller.base_data

        # Populate the magnetic field data μT
        msg.magnetic_field.x = float(imu_raw_data["mx"]) * 0.15
        msg.magnetic_field.y = float(imu_raw_data["my"]) * 0.15
        msg.magnetic_field.z = float(imu_raw_data["mz"]) * 0.15
              
        self.imu_mag_publisher_.publish(msg)  # Publish the magnetic field data

    # Publish odometry data to the ROS topic "odom/odom_raw" m
    def publish_odom_raw(self):
        odom_raw_data = self.base_controller.base_data
        array = [odom_raw_data["odl"]/100, odom_raw_data["odr"]/100,odom_raw_data["L"], odom_raw_data["R"]]
        msg = Float32MultiArray(data=array)
        self.odom_publisher_.publish(msg)  # Publish the odometry data

    # Publish voltage data to the ROS topic "voltage" v
    def publish_voltage(self):
        voltage_data = self.base_controller.base_data
        msg = BatteryState()
        msg.voltage = float(voltage_data["v"]/100)
        msg.percentage = float(voltage_data["v"]/1260)
        msg.present = True
        self.voltage_publisher_.publish(msg)  # Publish the voltage data

    # Callback for processing velocity commands m/s
    def cmd_vel_callback(self, msg):
        linear_velocity = msg.linear.x
        angular_velocity = msg.angular.z

        if linear_velocity == 0.0 and angular_velocity == 0.0:
            self.zero_vel_count += 1
            if self.zero_vel_count > self.zero_vel_limit:
                return  
        else:
            self.zero_vel_count = 0  

        # Apply minimum threshold to angular velocity if linear velocity is zero
        if linear_velocity == 0.0:
            if 0 < angular_velocity < 0.2:
                angular_velocity = 0.2
            elif -0.2 < angular_velocity < 0:
                angular_velocity = -0.2

        # Send the velocity data to the UGV as a JSON string
        data = json.dumps({'T': '13', 'X': linear_velocity, 'Z': angular_velocity}) + "\n"
        self.base_controller.send_command(data.encode())

    # Callback for processing joint state updates radian
    def handle_m2_joint_states(self,name,position):
        base = position[name.index('base_link_to_link1')]
        shoulder = position[name.index('link1_to_link2')]
        elbow =  position[name.index('link2_to_link3')]
        hand =  3.1415926 - position[name.index('link3_to_gripper_link')]
                
        data = json.dumps({
            'T': 102, 
            'base': base, 
            'shoulder': shoulder, 
            'elbow': elbow, 
            'hand': hand, 
            'spd': 1000,
            'acc': 50
        }) + "\n"
         
        return data
    
    def handle_m3_joint_states(self,name,position):
        base = position[name.index('base_link_to_link1')]
        shoulder = position[name.index('link1_to_link2')]
        elbow =  position[name.index('link2_to_link3')]
        wrist =  position[name.index('link3_to_link4')]
        roll = position[name.index('link4_to_link5')] 
        hand =  3.1415926 - position[name.index('link5_to_gripper_link')]
                
        data = json.dumps({
            'T': 102, 
            'base': base, 
            'shoulder': shoulder, 
            'elbow': elbow, 
            'wrist': wrist, 
            'roll': roll, 
            'hand': hand, 
            'spd': 1000,
            'acc': 50
        }) + "\n"
        
        return data

    def joint_states_callback(self, msg):
        header = {
            'stamp': {
                'sec': msg.header.stamp.sec,
                'nanosec': msg.header.stamp.nanosec,
            },
            'frame_id': msg.header.frame_id,
        }
        
        name = msg.name
        position = msg.position
        velocity = msg.velocity
        effort = msg.effort

        switch_dict = {
            "roarm_m2": self.handle_m2_joint_states,
            "roarm_m3": self.handle_m3_joint_states,
        }
        data = switch_dict[self.roarm_type](name,position)  

        if data == self.last_roarm_sent_data:
            return  

        self.last_roarm_sent_data = data

        try:
            self.base_controller.send_command(data.encode())
            print(data)
            # self.base_controller.ser.write(data.encode())

        except SerialException as e:
            self.get_logger().error(f"{e}")
        return

    # Callback for processing LED control commands 0-255
    def led_ctrl_callback(self, msg):
        IO4 = msg.data[0]
        IO5 = msg.data[1]

        IO4 = max(0, min(IO4, 255))
        IO5 = max(0, min(IO5, 255))     
                
        # Send LED control data as a JSON string to the UGV
        led_ctrl_data = json.dumps({
            'T': 132, 
            "IO4": IO4,
            "IO5": IO5,
        }) + "\n"
           
        self.base_controller.send_command(led_ctrl_data.encode())

    # Callback for processing voltage data
    def voltage_callback(self, msg):
        voltage_value = msg.voltage

        # If voltage drops below a threshold, play a low battery warning sound
        if 0.1 < voltage_value < 9:
            try:
                subprocess.run(['spd-say', 'low battery'], check=True)
                data = json.dumps({'T': '3', 'lineNum': 2, 'Text': f"V:{voltage_value}"}) + "\n"
                self.base_controller.send_command(data.encode())
            except Exception as e:
                self.get_logger().error(f"Failed to say low battery warning: {e}")
            time.sleep(5)
            
# Main function to initialize the ROS node and start spinning
def main(args=None):
    rclpy.init(args=args)  # Initialize ROS
    node = ugv_roarm_bringup()  # Create the UGV roarm bringup node
    rclpy.spin(node)  # Keep the node running
    #node.destroy_node()  # (optional) Shutdown the node
    rclpy.shutdown()  # Shutdown ROS

if __name__ == '__main__':
    main()
