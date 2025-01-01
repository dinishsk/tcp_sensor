import rclpy
from rclpy.node import Node
from example_interfaces.msg import UInt16, Int16
from rcl_interfaces.msg import ParameterDescriptor
from sensor_interfaces.srv import Start, Stop
import socket


class Sensor(Node):
    def __init__(self):
        super().__init__("sensor")
        self.get_logger().info("Node Created")
        self.int_bit_size = 16
        self.started = False
        self.param_desc = ParameterDescriptor(description = "Interval time for the sensor message to be received")
        self.declare_parameter("interval",1000,self.param_desc)
        self.interval = self.get_parameter(name="interval").value
        self.volatge_publisher = self.create_publisher(UInt16,"supply_voltage",10)
        self.env_temp_publisher = self.create_publisher(Int16, "env_temp", 10)
        self.yaw_publisher = self.create_publisher(Int16, "yaw", 10)
        self.pitch_publisher = self.create_publisher(Int16, "pitch", 10)
        self.roll_publisher = self.create_publisher(Int16, "roll", 10)
        self.start_service = self.create_service(Start, "start", self.start_callback)
        self.stop_service = self.create_service(Stop, "stop", self.stop_callback)
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.get_logger().info("Trying to Connect to TCP Server")
            self.s.connect(("",2000))
            self.timer = self.create_timer(0.1, self.callback)
        except:
            self.get_logger().error("Could not connect to server")
        else:
            self.get_logger().info("Connected to the TCP Server")

        self.start_msg_send(self.interval)
    
    def hex_le_to_decimal(self, value, signed = False):
        hex = "0x" + value[2:4] + value[0:2]
        integer = int(hex, 16)
        if signed == True and integer >= (2**(self.int_bit_size - 1)):
            integer =  integer - (2**self.int_bit_size)   
        return integer 

    def decimal_to_hex_le(self,value):
        hex_value = hex(value & (2**self.int_bit_size - 1))[2:].upper()
        hex_corrected = ("0" * (self.int_bit_size//4 - len(hex_value))) + hex_value
        l = []
        for i in range(0, len(hex_corrected), 2):
            l.insert(0, (hex_corrected[i:i+2]))
        return "".join(l)

    def encode_data(self,start, cmd_id, values):
        data = ""
        for i in values:
            data = data + self.decimal_to_hex_le(i)
        end = "0D0A"
        return start+cmd_id+data+end
    
    def start_encode(self,value):
        return self.encode_data("#", "03", [value])
    
    def stop_encode(self):
        return self.encode_data("#", "09", [])
    
    def decode_data(self, value):
        if (value.startswith("$") and value.endswith("0D0A")):
            if(value[1:3]=="11"):
                value = value[3:-4]
                l = []
                l.append(self.hex_le_to_decimal(value[0:4]))
                for i in range(4,len(value),4):
                    l.append(self.hex_le_to_decimal(value[i:i+4], True))
                return l
        return "Invalid Data"

    def start_msg_send(self,interval):
        if not self.s:
            self.get_logger().warn("Trying to send the start command for the unconnected server")
            return
        try:
            self.get_logger().info("Sending the Start Mesg")
            self.s.sendall(self.start_encode(interval).encode())
            self.started = True
        except Exception as e:
            print(e)
            self.get_logger().error("Exception in sending start message")
    
    def start_callback(self,req,res):
        if not req.interval:
            self.interval = req.interval 
        if self.started:
            self.get_logger().warn("Trying to send the start msg that was already started")
            res.result = "Failed"
            return res
        self.start_msg_send(self.interval)
        res.result = "Success"
        return res
    
    def stop_callback(self, req, res):
        if not self.started:
            self.get_logger().warn("Trying to stop without starting")
            res.result = "Failed"
            return res
        self.s.sendall(self.stop_encode().encode())
        self.get_logger().info("Successfully Stopped")
        res.result = "Success"
        return res
    
    def callback(self):
        try:
            received = self.s.recv(27).decode().strip()
            values = self.decode_data(received)
            if values == "Invalid Data":
                self.get_logger().error("Invalid Data")
            self.volatge_publisher.publish(UInt16(data = values[0]))
            self.env_temp_publisher.publish(Int16(data = values[1]))
            self.yaw_publisher.publish(Int16(data = values[2]))
            self.pitch_publisher.publish(Int16(data = values[3]))
            self.roll_publisher.publish(Int16(data = values[4]))
        except Exception as e:
            print(e)
            self.get_logger().error("Failed to Receive and process data")
        else:
            self.get_logger().info("Successfully received and processed Data")

def main(args=None):
    rclpy.init(args=args)
    node = Sensor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__=="__main__":
    main()
