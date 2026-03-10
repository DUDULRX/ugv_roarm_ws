#include <memory>
#include <chrono>
#include <fstream>
#include <string>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <nav2_msgs/action/navigate_to_pose.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <nlohmann/json.hpp>

#include "roarm_msgs/srv/pick_place_cmd.hpp"

using namespace std::chrono_literals;
using NavigateToPose = nav2_msgs::action::NavigateToPose;
using json = nlohmann::json;

class NavToPoseClient : public rclcpp::Node
{
public:
    NavToPoseClient()
    : Node("navigate_to_pose_client")
    {
        client_ = rclcpp_action::create_client<NavigateToPose>(this, "navigate_to_pose");
        pick_place_client_ = this->create_client<roarm_msgs::srv::PickPlaceCmd>("/pick_place_cmd");

        step_ = 0;
        send_goal(1, 1);  // Initial navigation to pick_1
    }

private:
    rclcpp_action::Client<NavigateToPose>::SharedPtr client_;
    rclcpp::Client<roarm_msgs::srv::PickPlaceCmd>::SharedPtr pick_place_client_;
    int step_;  // State variables of control flow

    void send_goal(int cmd, int name)
    {
        if (!client_->wait_for_action_server(5s)) {
            RCLCPP_ERROR(get_logger(), "Navigation server unavailable!");
            return;
        }

        std::ifstream in("/home/ws/ugv_roarm_ws/saved_points.json");
        if (!in.is_open()) {
            RCLCPP_ERROR(get_logger(), "Unable to open JSON file!");
            return;
        }

        json point_data;
        in >> point_data;

        std::string key = (cmd == 1 ? "pick_" : "place_") + std::to_string(name);
        if (point_data.find(key) == point_data.end()) {
            RCLCPP_ERROR(get_logger(), "Target point not found in JSON: %s", key.c_str());
            return;
        }

        double x = point_data[key]["x"];
        double y = point_data[key]["y"];
        double yaw = point_data[key]["yaw"];

        tf2::Quaternion q;
        q.setRPY(0, 0, yaw);
        q.normalize();

        auto goal_msg = NavigateToPose::Goal();
        goal_msg.pose.header.frame_id = "map";
        goal_msg.pose.header.stamp = now();
        goal_msg.pose.pose.position.x = x;
        goal_msg.pose.pose.position.y = y;
        goal_msg.pose.pose.orientation.x = q.x();
        goal_msg.pose.pose.orientation.y = q.y();
        goal_msg.pose.pose.orientation.z = q.z();
        goal_msg.pose.pose.orientation.w = q.w();
        goal_msg.behavior_tree = "";

        RCLCPP_INFO(get_logger(), "Sending navigation goal: %s -> x=%.2f, y=%.2f, yaw=%.2f", key.c_str(), x, y, yaw);

        auto send_goal_options = rclcpp_action::Client<NavigateToPose>::SendGoalOptions();
        send_goal_options.feedback_callback =
            std::bind(&NavToPoseClient::feedback_callback, this, std::placeholders::_1, std::placeholders::_2);
        send_goal_options.result_callback =
            std::bind(&NavToPoseClient::result_callback, this, std::placeholders::_1);

        client_->async_send_goal(goal_msg, send_goal_options);
    }

    void feedback_callback(
        rclcpp_action::ClientGoalHandle<NavigateToPose>::SharedPtr,
        const std::shared_ptr<const NavigateToPose::Feedback> feedback)
    {
        RCLCPP_INFO(get_logger(), "Current remaining distance: %.2f meters", feedback->distance_remaining);
    }

    void result_callback(const rclcpp_action::ClientGoalHandle<NavigateToPose>::WrappedResult & result)
    {
        if (result.code != rclcpp_action::ResultCode::SUCCEEDED) {
            RCLCPP_ERROR(get_logger(), "Navigation failed or canceled!");
            rclcpp::shutdown();
            return;
        }

        if (step_ == 0) {
            RCLCPP_INFO(get_logger(), "Arrived at pick_1. Starting to pick up object 1...");
            step_++;
            call_pick_place_service(1, 1);
        } else if (step_ == 2) {
            RCLCPP_INFO(get_logger(), "Arrived at place_1. Preparing to place object 1...");
            step_++;
            call_pick_place_service(2, 1);
        }
    }

    void call_pick_place_service(int cmd, int target)
    {
        if (!pick_place_client_->wait_for_service(2s)) {
            RCLCPP_ERROR(get_logger(), "Timeout waiting for /pick_place_cmd service!");
            rclcpp::shutdown();
            return;
        }

        auto request = std::make_shared<roarm_msgs::srv::PickPlaceCmd::Request>();
        request->cmd = cmd;
        request->target = target;

        pick_place_client_->async_send_request(request,
            [this](rclcpp::Client<roarm_msgs::srv::PickPlaceCmd>::SharedFuture future) {
                auto response = future.get();
                if (!response->success) {
                    RCLCPP_WARN(this->get_logger(), "Pick/place execution failed!");
                    rclcpp::shutdown();
                    return;
                }

                if (step_ == 1) {
                    RCLCPP_INFO(this->get_logger(), "Object 1 picked up, heading to place_1...");
                    step_++;
                    send_goal(2, 1);
                } else if (step_ == 3) {
                    RCLCPP_INFO(this->get_logger(), "Object 1 placed, task completed!");
                    rclcpp::shutdown();
                }
            }
        );
    }
};

int main(int argc, char ** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<NavToPoseClient>());
    return 0;
}
