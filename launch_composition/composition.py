from ament_index_python.packages import get_package_prefix, get_package_share_directory
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict
from jinja2 import Template, Environment, FileSystemLoader


def get_package_include_directory(package_name: str) -> Path:
    return Path(get_package_prefix(package_name)).joinpath("include")


def get_package_include_header_files(package_name: str) -> List[str]:
    ret: List[str] = []
    hpp_files = (
        get_package_include_directory(package_name)
        .joinpath(package_name)
        .glob("**/*.hpp")
    )
    for include_file in hpp_files:
        ret.append(
            str(include_file.relative_to(get_package_include_directory(package_name)))
        )
    h_files = (
        get_package_include_directory(package_name)
        .joinpath(package_name)
        .glob("**/*.h")
    )
    for include_file in h_files:
        ret.append(
            str(include_file.relative_to(get_package_include_directory(package_name)))
        )
    return ret


def get_package_launch_directory(package_name: str) -> Path:
    return Path(get_package_share_directory(package_name), "launch")


def get_component_containers(tree: ET):
    assert tree.getroot().tag == "launch"

    def get_include_files(tree: ET) -> List[str]:
        include_files: List[str] = []
        for child in tree:
            assert child.tag == "composable_node"
            include_files = include_files + get_package_include_header_files(
                child.attrib["pkg"]
            )
        include_files = list(set(include_files))
        return include_files

    def get_executor_type(tree: ET) -> str:
        assert tree.attrib["pkg"] == "rclcpp_components"
        assert (
            tree.attrib["exec"] == "component_container_mt"
            or tree.attrib["exec"] == "component_container"
        )
        if tree.attrib["exec"] == "component_container_mt":
            return "rclcpp::executors::MultiThreadedExecutor"
        if tree.attrib["exec"] == "component_container":
            return "rclcpp::executors::SingleThreadedExecutor"

    def get_node_name_and_classname(tree: ET) -> List[Dict[str, str]]:
        ret: List[Dict[str, str]] = []
        for child in tree:
            assert child.tag == "composable_node"
            # print(child.attrib)
            ret.append(
                {"name": child.attrib["name"], "class_name": child.attrib["plugin"]}
            )
        return ret

    for child in tree.getroot():
        if child.tag == "node_container":
            code = generate_cpp_code(
                get_include_files(child),
                get_executor_type(child),
                get_node_name_and_classname(child),
            )
            print(
                "================================ Generated C++ code start. ================================"
            )
            print(code)
            print(
                "================================ Generated C++ code end. ================================"
            )


def generate_cpp_code(
    header_files: List[str],
    executor_type: str,
    node_names_and_classnames: List[Dict[str, str]],
) -> str:
    env = Environment(loader=FileSystemLoader("./", encoding="utf8"))
    template = env.get_template("ros2_node_template.jinja")
    return template.render(
        {
            "header_files": header_files,
            "executor_type": executor_type,
            "node_list": node_names_and_classnames,
        }
    )


def composition(package_name: str, launch_filename: str):
    launch_filepath = get_package_launch_directory(package_name).joinpath(
        launch_filename
    )
    print("Loading launch file >>> ", launch_filepath)
    tree = ET.parse(launch_filepath)
    get_component_containers(tree)


if __name__ == "__main__":
    composition("perception_bringup", "sensor_bringup.launch.xml")
    # composition("perception_bringup", "perception_bringup.launch.xml")
