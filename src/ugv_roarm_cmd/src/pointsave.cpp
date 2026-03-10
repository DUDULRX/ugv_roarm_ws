#include <rclcpp/rclcpp.hpp>
#include <tf2_ros/transform_listener.h>
#include <tf2_ros/buffer.h>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <ugv_msgs/msg/point_save.hpp>
#include <fstream>
#include <nlohmann/json.hpp>
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
#include <tf2/LinearMath/Matrix3x3.h>

using std::placeholders::_1;
using json = nlohmann::json;

class PointSaver : public rclcpp::Node
{
public:
    PointSaver() : Node("point_saver_node"), tf_buffer_(get_clock()), tf_listener_(tf_buffer_)
    {
        sub_ = this->create_subscription<ugv_msgs::msg::PointSave>(
            "save_point_cmd", 10, std::bind(&PointSaver::point_callback, this, _1));
        json_path_ = declare_parameter("save_file", "saved_points.json");
        load_json();
    }

private:
    rclcpp::Subscription<ugv_msgs::msg::PointSave>::SharedPtr sub_;
    tf2_ros::Buffer tf_buffer_;
    tf2_ros::TransformListener tf_listener_;
    json point_data_;
    std::string json_path_;

    void point_callback(const ugv_msgs::msg::PointSave::SharedPtr msg)
    {
        geometry_msgs::msg::TransformStamped tf;
        try {
            tf = tf_buffer_.lookupTransform("map", "base_footprint", tf2::TimePointZero);
        } catch (tf2::TransformException &ex) {
            RCLCPP_WARN(get_logger(), "unable to get TF: %s", ex.what());
            return;
        }

        double x = tf.transform.translation.x;
        double y = tf.transform.translation.y;

        tf2::Quaternion q(
            tf.transform.rotation.x,
            tf.transform.rotation.y,
            tf.transform.rotation.z,
            tf.transform.rotation.w);
        double roll, pitch, yaw;
        tf2::Matrix3x3(q).getRPY(roll, pitch, yaw);

        std::string key;
        if (msg->cmd == 1) key = "pick_" + std::to_string(msg->name);
        else if (msg->cmd == 2) key = "place_" + std::to_string(msg->name);
        else {
            RCLCPP_WARN(get_logger(), "unknow cmd: %d", msg->cmd);
            return;
        }

        point_data_[key] = {
            {"x", x},
            {"y", y},
            {"yaw", yaw}
        };

        save_json();
        RCLCPP_INFO(get_logger(), "point save [%s]: x=%.2f, y=%.2f, yaw=%.2f", key.c_str(), x, y, yaw);
    }

    void load_json()
    {
        std::ifstream in(json_path_);
        if (in) {
            in >> point_data_;
        }
    }

    void save_json()
    {
        std::ofstream out(json_path_);
        out << point_data_.dump(4);  
    }
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<PointSaver>());
    rclcpp::shutdown();
    return 0;
}
