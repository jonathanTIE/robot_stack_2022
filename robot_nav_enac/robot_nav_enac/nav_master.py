import numpy as np

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Pose, TransformStamped
from nav_msgs.msg import Odometry

from interfaces_enac.msg import _set_navigation
from interfaces_enac.msg import _obstacles

from robot_nav_enac.Stop import Stop
from robot_nav_enac.StraightPath import StraightPath
from robot_nav_enac.PurePursuit import PurePursuit
from robot_nav_enac.NavigationType import OdomData

SetNavigation = _set_navigation.SetNavigation
Obstacles = _obstacles.Obstacles

"""
Navtypes :
    0 : stop
    1 : StraigthPath (without planification, no basic obstacle stop yet)
    2 : PurePursuit (use astar planification and obstacle avoidance)
    3 : WallFollower (without planification, no basic obstacle stop yet)
    4 : WallStop (without planification, no basic obstacle stop yet)
"""

def z_euler_from_quaternions(qx, qy, qz, qw):
    t3 = +2.0 * (qw * qz + qx * qy)
    t4 = +1.0 - 2.0 * (qy * qy + qz * qz)
    return np.arctan2(t3, t4)


class Navigator(Node):
    def __init__(self):
        super().__init__('navigator')

        self.last_time_stamp = -1.0
        self.dt = 0.0
        self.robot_radius = 0.0885 #in meter
        #epaisseur roue : 0.022
        #distance max entre roues (de bout à bout ) : 0.199
        #diameter = 0.177
        
        self.target_position = OdomData(0, 0, 0) #TODO : set it to initial position from state machine on beggining
        self.cur_position = OdomData(0, 0, 0)
        self.cur_speed = OdomData(0,0,0)
        self.fixed_obstacle = [] #TODO : to fill on init
        self.dynamic_obstacle = [] 

        #instantiate nav types available
        self.stop = Stop()
        self.straight_path = StraightPath(self.get_logger().info)
        self.pure_pursuit = PurePursuit()
        #self.wall_follower = WallFollower()
        #self.wall_stop = WallStop()

        self.navigation_type = self.stop #default navigation_type by safety
        self.nav_type_int = 0 #used to detect if navigation_type has changed


        # subscribe to nav
        navigation_subscriber = self.create_subscription(
            SetNavigation, 'set_nav', self.on_nav_callback, 10)
        #subscribe to odom
        odom_subscriber = self.create_subscription(
            Odometry, 'odom', self.on_odom_callback, 10)
        #subscribe to obstacles
        obstacle_subscriber = self.create_subscription(
            Obstacles, 'obstacles', self.on_obstacle_callback, 10)
        #publish to velocity
        self.velocity_publisher = self.create_publisher(Twist, 'cmd_vel', 10)

    def on_obstacle_callback(self, msg):
        #TODO : maintain a list of dynamic obstacles and send it to PurePursuit astar planification on callback
        pass

    def on_nav_callback(self, msg):
        #switch nav type if changed
        if self.nav_type_int != msg.navigation_type:
            self.navigation_type = msg.navigation_type
            if self.navigation_type == 0:
                self.navigation_type = self.stop
            elif self.navigation_type == 1:
                self.navigation_type = self.straight_path
                #self.navigation_type.set_target = cur_position or reset button??
            #elif self.navigation_type == 2:
            #    self.navigation_type = self.pure_pursuit
            #elif self.navigation_type == 3:
            #    self.navigation_type = self.wall_follower
            #elif self.navigation_type == 4:
            #    self.navigation_type = self.wall_stop

        #extracting goal_pose from msg
        x = msg.pose.position.x
        y = msg.pose.position.y
        rotation = z_euler_from_quaternions(msg.pose.orientation.x,
        									msg.pose.orientation.y,
        									msg.pose.orientation.z,
        									msg.pose.orientation.w)

        #set target to the navigation_type selected
        self.target_position.updataOdomData(x,y, rotation)
        self.navigation_type.set_target(self.target_position)


    def on_odom_callback(self, msg):
		# Update position here

                        # TODO : uncomment when TF is working
                        # x = msg.transform.translation.x
                        # y = msg.transform.translation.y
                        # rotation = z_euler_from_quaternions(msg.transform.rotation.x,
                        #									msg.transform.rotation.y,
                        #									msg.transform.rotation.z,
                        #									msg.transform.rotation.w)
                        # self.current_position.updataOdomData(x, y, rotation)

        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        rotation = z_euler_from_quaternions(msg.pose.pose.orientation.x,
        									msg.pose.pose.orientation.y,
        									msg.pose.pose.orientation.z,
        									msg.pose.pose.orientation.w)

        self.cur_position.updataOdomData(x, y, rotation)
        self.cur_speed.updataOdomData(msg.twist.twist.linear.x, 0, msg.twist.twist.angular.z)

        dt = 0.0
        if self.last_time_stamp == -1.0:
            self.last_time_stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            dt = 0.05 #TODO : not zero in case it could create problem, need to check that
        else:
            timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            
            dt = timestamp - self.last_time_stamp
            self.last_time_stamp = timestamp
            
        self.navigation_type.update_odom(self.publish_nav, self.cur_position, self.cur_speed, dt) #TODO voir quel type de données mettre (OdomData ??)
        
    def publish_nav(self, linear_speed: float, angular_speed: float):
        msg = Twist()
        msg.linear.x = float(linear_speed)
        msg.angular.z = float(angular_speed)
        self.velocity_publisher.publish(msg)

	


def main():
    rclpy.init()
    node = Navigator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    rclpy.shutdown()


if __name__ == '__main__':
    main()

