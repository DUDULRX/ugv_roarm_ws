#include <iostream>
#include <cmath>
#include <iomanip>
#include <sstream> 
#include <cstdlib> 
#include <vector>
#include "roarm_moveit_cmd/solver.hpp"
#include <algorithm>

#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <tf2_ros/transform_listener.h>
#include <tf2_ros/buffer.h>
#include <tf2/utils.h>

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <geometry_msgs/msg/pose.hpp>
#include <geometry_msgs/msg/quaternion.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <std_msgs/msg/float32.hpp>
#include <trajectory_msgs/msg/joint_trajectory.hpp>
#include <trajectory_msgs/msg/joint_trajectory_point.hpp>

#include "roarm_msgs/srv/get_pose_cmd.hpp"
#include "roarm_msgs/srv/move_joint_cmd.hpp"
#include "roarm_msgs/srv/move_line_cmd.hpp"
#include "roarm_msgs/srv/pick_place_cmd.hpp"

std::string get_roarm_model() {
  const char* env_val = std::getenv("ROARM_MODEL");
  if (env_val == nullptr) {
      std::cerr << "no ROARM_MODEL!" << std::endl;
      return "";  
  }
  return std::string(env_val); 
}

std::string model = get_roarm_model();

class GripperPublisherNode : public rclcpp::Node
{
public:
  GripperPublisherNode()
  : Node("gripper_publisher_node")
  {
    gripper_pub_ = this->create_publisher<std_msgs::msg::Float32>("/gripper_cmd", 10);
  }

  void publishGripperCmd(float value)
  {
    std_msgs::msg::Float32 msg;
    msg.data = value;
    gripper_pub_->publish(msg);
    RCLCPP_INFO(this->get_logger(), "Published gripper command: %f", value);
  }

private:
  rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr gripper_pub_;
};

class HandPublisherNode : public rclcpp::Node
{
public:
  struct TrajPoint {
    std::vector<double> joints;
    double duration;
    double max_speed;
  };

  HandPublisherNode()
  : Node("hand_publisher_node")
  {
    hand_pub_ = this->create_publisher<trajectory_msgs::msg::JointTrajectory>(
        "/hand_controller/joint_trajectory", 10);
    if (model == "roarm_m2") {
      last_point_ = {0.0, 0.0, 0.0};
    }else if (model == "roarm_m3") {
      last_point_ = {0.0, 0.0, 0.0, 0.0, 0.0};
    }
  }

  // 允许指定时间和最大速度
  void addPoint(const std::vector<double> &joint_positions,
                double duration = 1.5, double max_speed = 0.5)
  {
    traj_points_.push_back({joint_positions, duration, max_speed});
    RCLCPP_INFO(this->get_logger(), "Added point #%zu (t=%.2fs, v=%.2fm/s)",
                traj_points_.size(), duration, max_speed);
  }

  void clearPoints()
  {
    traj_points_.clear();
  }

  void publishTrajectory()
  {
    if (traj_points_.empty()) {
      RCLCPP_WARN(this->get_logger(), "No points to publish!");
      return;
    }

    // 自动补起点
    if (traj_points_.size() == 1) {
      RCLCPP_INFO(this->get_logger(),
                  "Only one point, adding last_point as start.");
      traj_points_.insert(traj_points_.begin(), {last_point_, 0.0, traj_points_[0].max_speed});
    }

    trajectory_msgs::msg::JointTrajectory traj;

    traj.header.stamp = this->get_clock()->now();
    if (model == "roarm_m2") {
      traj.joint_names = {
          "base_link_to_link1",
          "link1_to_link2",
          "link2_to_link3",
      };
    }else if (model == "roarm_m3") {
      traj.joint_names = {
          "base_link_to_link1",
          "link1_to_link2",
          "link2_to_link3",
          "link3_to_link4",
          "link4_to_link5"
      };
    }

    double t_cumulative = 0.0;

    for (size_t seg = 0; seg < traj_points_.size() - 1; ++seg) {
      const auto &p0 = traj_points_[seg];
      const auto &p1 = traj_points_[seg + 1];

      // 计算段距离
      double dist = 0.0;
      for (size_t j = 0; j < p0.joints.size(); ++j)
        dist += std::pow(p1.joints[j] - p0.joints[j], 2);
      dist = std::sqrt(dist);

      if (dist < 1e-6) continue;

      // 计算时间（优先使用指定duration，否则由速度计算）
      double dt = p1.duration > 0.0 ? p1.duration : dist / p1.max_speed;

      int steps = std::max(5, static_cast<int>(dt * 10)); // 10Hz取样
      for (int i = 0; i <= steps; ++i) {
        double t = dt * i / steps;
        double tau = t / dt;
        double s = 10*std::pow(tau,3) - 15*std::pow(tau,4) + 6*std::pow(tau,5);

        trajectory_msgs::msg::JointTrajectoryPoint p;
        p.positions.resize(p0.joints.size());
        p.velocities.resize(p0.joints.size());

        for (size_t j = 0; j < p0.joints.size(); ++j) {
          p.positions[j] = p0.joints[j] + s * (p1.joints[j] - p0.joints[j]);
          double ds_dt = (30*std::pow(tau,2) - 60*std::pow(tau,3) + 30*std::pow(tau,4)) / dt;
          p.velocities[j] = ds_dt * (p1.joints[j] - p0.joints[j]);
        }

        p.time_from_start = rclcpp::Duration::from_seconds(t_cumulative + t);
        traj.points.push_back(p);
      }

      t_cumulative += dt;
    }

    last_point_ = traj_points_.back().joints;
    hand_pub_->publish(traj);
    RCLCPP_INFO(this->get_logger(),
                "Published trajectory with %zu samples, total %.2fs",
                traj.points.size(), t_cumulative);
    clearPoints();
  }

private:
  rclcpp::Publisher<trajectory_msgs::msg::JointTrajectory>::SharedPtr hand_pub_;
  std::vector<TrajPoint> traj_points_;
  std::vector<double> last_point_;
};


class TargetPoseSubscription : public rclcpp::Node
{
  public:
  TargetPoseSubscription() : Node("pick_place_cmd")
  {
      tf_buffer_ = std::make_shared<tf2_ros::Buffer>(this->get_clock());
      tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);
  }
  geometry_msgs::msg::Pose update_target1_pose() 
  {
      try
      {
          geometry_msgs::msg::TransformStamped transformStamped1;
          transformStamped1 = tf_buffer_->lookupTransform(base_frame, target1_frame, tf2::TimePointZero);
 
          geometry_msgs::msg::TransformStamped transformStamped2;
          transformStamped2 = tf_buffer_->lookupTransform(cam_frame, target1_frame, tf2::TimePointZero);

          target1_pose.position.x = transformStamped1.transform.translation.x;
          target1_pose.position.y = transformStamped1.transform.translation.y;
          target1_pose.position.z = transformStamped1.transform.translation.z;
          target1_pose.orientation = transformStamped2.transform.rotation;
      }
      catch (tf2::TransformException &ex)
      {
          RCLCPP_WARN(this->get_logger(), "Could not transform %s to %s: %s", base_frame.c_str(), target1_frame.c_str(), ex.what());
      }
      return target1_pose;
  }
  geometry_msgs::msg::Pose update_target2_pose() 
  {
      try
      {
          geometry_msgs::msg::TransformStamped transformStamped1;
          transformStamped1 = tf_buffer_->lookupTransform(base_frame, target2_frame, tf2::TimePointZero);
 
          geometry_msgs::msg::TransformStamped transformStamped2;
          transformStamped2 = tf_buffer_->lookupTransform(cam_frame, target2_frame, tf2::TimePointZero);

          target1_pose.position.x = transformStamped1.transform.translation.x;
          target1_pose.position.y = transformStamped1.transform.translation.y;
          target1_pose.position.z = transformStamped1.transform.translation.z;
          target1_pose.orientation = transformStamped2.transform.rotation;
      }
      catch (tf2::TransformException &ex)
      {
          RCLCPP_WARN(this->get_logger(), "Could not transform %s to %s: %s", base_frame.c_str(), target2_frame.c_str(), ex.what());
      }
      return target2_pose;
  }

private:
  std::string base_frame = "ugv_roarm_base_link";
  std::string cam_frame = "camera_link";
  std::string target1_frame = "object_1"; 
  std::string target2_frame = "object_2"; 
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
  std::shared_ptr<tf2_ros::Buffer> tf_buffer_;
  
  geometry_msgs::msg::Pose target1_pose;  
  geometry_msgs::msg::Pose target2_pose;  

};  

double limitYaw(double yaw)
{
    double v = yaw;

    while (v > M_PI)  v -= 2 * M_PI;
    while (v < -M_PI) v += 2 * M_PI;

    if (fabs(fabs(v) - M_PI) < 0.3)
    {
        v = 0.0;
    }
    return v;
}

void pick_place_cmd_service(const std::shared_ptr<roarm_msgs::srv::PickPlaceCmd::Request> request,
  std::shared_ptr<roarm_msgs::srv::PickPlaceCmd::Response> response,
  std::shared_ptr<TargetPoseSubscription> node,
  std::shared_ptr<GripperPublisherNode> gripper_node,
  std::shared_ptr<HandPublisherNode> hand_node)
{
auto logger = node->get_logger();
bool success = false;
double roll, pitch, yaw;

geometry_msgs::msg::Pose target_pose;
std::array<double, 5> pose;
std::vector<double> target;
std::vector<double> temp_target;
std::string model = get_roarm_model();

moveit::planning_interface::MoveGroupInterface move_group(node, "hand");
moveit::planning_interface::MoveGroupInterface::Plan plan;

if(request->cmd==1){
  //move to observe 
  if (model == "roarm_m2") {
    target = {0.0, 0.0, 2.618};
  } else if (model == "roarm_m3") {
    target = {0.0, 0.0, 1.5708, 1.5708, 0.0};
  }

  hand_node->addPoint(target);
  hand_node->publishTrajectory();  
  sleep(1.5);  

  //open gripper
  gripper_node->publishGripperCmd(1.5f);
  sleep(3);

  //move to target
  switch (request->target)
  {
  case 1:
    target_pose = node->update_target1_pose();
    break;

  case 2:
    target_pose = node->update_target2_pose();

  default:
    break;
  }

  pose[0]= 1000*target_pose.position.x;
  pose[1]= 1000*target_pose.position.y+30;
  pose[2]= 1000*target_pose.position.z-87.459+30;

  if (model == "roarm_m2") {
    temp_target = roarm_m2::computeJointRadbyPos(pose[0],pose[1],pose[2],0.0);
    RCLCPP_INFO(logger, "BASE_point_RAD: %f, SHOULDER_point_RAD: %f, ELBOW_point_RAD: %f", temp_target[0], temp_target[1], temp_target[2]);
    RCLCPP_INFO(logger, "x: %f, y: %f, z: %f", pose[0],pose[1],pose[2]);
    bool valid = true;
    for (auto v : temp_target) {
        if (std::isnan(v)) {
            valid = false;
            break;
        }
    }   
    if (valid) {
      hand_node->addPoint(temp_target);

      pose[2]= pose[2]-60;
      target = roarm_m2::computeJointRadbyPos(pose[0],pose[1],pose[2],0.0);

      for (auto v : target) {
          if (std::isnan(v)) {
              valid = false;
              break;
          }
      }   
      RCLCPP_INFO(logger, "BASE_point_RAD: %f, SHOULDER_point_RAD: %f, ELBOW_point_RAD: %f", target[0], target[1], target[2]);
      RCLCPP_INFO(logger, "x: %f, y: %f, z: %f", pose[0],pose[1],pose[2]);
      if (valid) {
        //move to target z
        hand_node->addPoint(target,3.0,0.1);
        hand_node->publishTrajectory();  
        sleep(5);  

        //close gripper
        // gripper_node->publishGripperCmd(0.0f);
        gripper_node->publishGripperCmd(request->gripper);
        sleep(3);  

        hand_node->addPoint(temp_target);

        //move to observe 
        target = {0.0, 0.0, 2.618};
        hand_node->addPoint(target);
        
        target = {0.0, -0.7, 2.618};
        hand_node->addPoint(target);
        
        hand_node->publishTrajectory();  

        response->success = true;
        response->message = "MoveJointCmd executed successfully";
      }else{
        response->success = false;
        response->message = "MoveJointCmd executed failed";
      } 

    }
  } else if (model == "roarm_m3") {
    tf2::Quaternion q(target_pose.orientation.x, target_pose.orientation.y, target_pose.orientation.z, target_pose.orientation.w);
    tf2::Matrix3x3 mat(q);
    double roll, pitch, yaw;
    mat.getRPY(roll, pitch, yaw);
    RCLCPP_INFO(logger, "roll: %f", roll);
    RCLCPP_INFO(logger, "pitch: %f", pitch);
    RCLCPP_INFO(logger, "yaw: %f", yaw);
    // yaw = std::atan2(pose[1], pose[0]);
    pose[3]= limitYaw(pitch);
    pose[4]= 1.571;
    temp_target = roarm_m3::computeJointRadbyPos(pose[0],pose[1],pose[2],pose[3],pose[4]);
    RCLCPP_INFO(logger, "BASE_JOINT_RAD: %f, SHOULDER_JOINT_RAD: %f, ELBOW_JOINT_RAD: %f, WRIST_JOINT_RAD: %f, ROLL_JOINT_RAD: %f", temp_target[0], temp_target[1], temp_target[2], temp_target[3], temp_target[4]);
    RCLCPP_INFO(logger, "x: %f, y: %f, z: %f, roll: %f, pitch: %f", pose[0],pose[1],pose[2],pose[3],pose[4]);
    bool valid = true;
    for (auto v : temp_target) {
        if (std::isnan(v)) {
            valid = false;
            break;
        }
    }   

    if (valid) {
      //move to target z+0.03
      hand_node->addPoint(temp_target);

      pose[2]= pose[2]-60;
      target = roarm_m3::computeJointRadbyPos(pose[0],pose[1],pose[2],pose[3],pose[4]);

      for (auto v : target) {
          if (std::isnan(v)) {
              valid = false;
              break;
          }
      }   
      RCLCPP_INFO(logger, "BASE_JOINT_RAD: %f, SHOULDER_JOINT_RAD: %f, ELBOW_JOINT_RAD: %f, WRIST_JOINT_RAD: %f, ROLL_JOINT_RAD: %f", target[0], target[1], target[2], target[3], target[4]);
      RCLCPP_INFO(logger, "x: %f, y: %f, z: %f, roll: %f, pitch: %f", pose[0],pose[1],pose[2],pose[3],pose[4]);
      if (valid) {
        //move to target z
        hand_node->addPoint(target);
        hand_node->publishTrajectory();  
        sleep(5);  

        //close gripper
        // gripper_node->publishGripperCmd(0.0f);
        gripper_node->publishGripperCmd(request->gripper);
        sleep(3);  

        hand_node->addPoint(temp_target,3.0,0.1);

        //move to observe 
        target = {0.0, 0.0, 1.5708, 1.5708, 0.0};
        hand_node->addPoint(target);
        
        target = {0.0, 0, 2.618, -1.0472, 0.0};
        hand_node->addPoint(target);

        hand_node->publishTrajectory();  

        response->success = true;
        response->message = "MoveJointCmd executed successfully";
      }else{
        response->success = false;
        response->message = "MoveJointCmd executed failed";
      } 
    }else{
        response->success = false;
        response->message = "MoveJointCmd executed failed";
      }  
  } 
 
}else if(request->cmd==2){
  //move to observe
  if (model == "roarm_m2") {
    target = {0.0, 0.0, 2.618};
  } else if (model == "roarm_m3") {
    target = {0.0, 0.0, 1.5708, 1.5708, 0.0};
  }

  hand_node->addPoint(target);
  hand_node->publishTrajectory();  
  sleep(3);  

  //open gripper
  gripper_node->publishGripperCmd(1.5f);
  sleep(3);

  //move to reset
  if (model == "roarm_m2") {
    target = {0.0, -0.7, 2.618};
  } else if (model == "roarm_m3") {
    target = {0.0, 0, 2.618, -1.0472, 0.0};
  }

  hand_node->addPoint(target);
  hand_node->publishTrajectory();  
  sleep(1.5);  

  //close gripper
  gripper_node->publishGripperCmd(0.0f);

  response->success = true;
  response->message = "MoveJointCmd executed successfully";
}else if(request->cmd==0){
  //move to observe
  if (model == "roarm_m2") {
    target = {0.0, 0.0, 2.618};
  } else if (model == "roarm_m3") {
    target = {0.0, 0.0, 1.5708, 1.5708, 0.0};
  }
  hand_node->addPoint(target);

  hand_node->publishTrajectory();  

  //open gripper
  gripper_node->publishGripperCmd(1.5f);

  response->success = true;
  response->message = "MoveJointCmd executed successfully";
}
}

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<TargetPoseSubscription>();
    auto gripper_node = std::make_shared<GripperPublisherNode>();
    auto hand_node = std::make_shared<HandPublisherNode>();
    auto pick_place_cmd_server = node->create_service<roarm_msgs::srv::PickPlaceCmd>("pick_place_cmd", 
                    std::bind(&pick_place_cmd_service, std::placeholders::_1, std::placeholders::_2, node, gripper_node, hand_node));

    RCLCPP_INFO(node->get_logger(), "pick place task is ready to receive requests.");
    // rclcpp::spin(node);  
    rclcpp::executors::MultiThreadedExecutor executor;
    executor.add_node(node);
    executor.add_node(gripper_node);
    executor.add_node(hand_node);
    executor.spin();
    rclcpp::shutdown(); 

    return 0;
}
