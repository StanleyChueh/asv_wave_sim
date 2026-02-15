import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
import sys, select, termios, tty

msg = """
Control Your WAM-V!
---------------------------
Moving around:
    w
a   s   d

w/s : Forward/Backward
a/d : Pivot Steering (New!)
space : STOP

CTRL-C to quit
"""

class WAMVTeleop(Node):
    def __init__(self):
        super().__init__('wamv_teleop')
        # Thrust Publishers
        self.left_thrust_pub = self.create_publisher(Float64, '/wamv/thrusters/left/thrust', 10)
        self.right_thrust_pub = self.create_publisher(Float64, '/wamv/thrusters/right/thrust', 10)
        # Position (Steering) Publishers
        self.left_pos_pub = self.create_publisher(Float64, '/wamv/thrusters/left/pos', 10)
        self.right_pos_pub = self.create_publisher(Float64, '/wamv/thrusters/right/pos', 10)

    def publish_cmd(self, left_t, right_t, left_p, right_p):
        # Publish Thrusts
        self.left_thrust_pub.publish(Float64(data=float(left_t)))
        self.right_thrust_pub.publish(Float64(data=float(right_t)))
        # Publish Angles (Radians)
        self.left_pos_pub.publish(Float64(data=float(left_p)))
        self.right_pos_pub.publish(Float64(data=float(right_p)))

# Bindings: (Left Thrust, Right Thrust, Left Angle, Right Angle)
moveBindings = {
    'w': (500.0, 500.0, 0.0, 0.0),   # Forward
    's': (-300.0, -300.0, 0.0, 0.0), # Backward
    'a': (300.0, 300.0, -0.5, -0.5), # Turn Left
    'd': (300.0, 300.0, 0.5, 0.5),   # Turn Right
    ' ': (0.0, 0.0, 0.0, 0.0),       # Stop
}

def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    select.select([sys.stdin], [], [], 0.1)
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def main():
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init()
    node = WAMVTeleop()
    print(msg)

    try:
        while True:
            key = get_key(settings)
            if key in moveBindings.keys():
                # FIX 1: Unpack all 4 values
                lt, rt, lp, rp = moveBindings[key]
                # FIX 2: Call the correct function name
                node.publish_cmd(lt, rt, lp, rp)
                print(f"Thrust: {lt} | Angle: {lp}      ", end='\r')
            elif key == '\x03': # CTRL-C
                break
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Stop the boat on exit
        node.publish_cmd(0.0, 0.0, 0.0, 0.0)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()