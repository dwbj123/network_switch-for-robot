# network_switch-for-robot
针对树莓派机器人，自动根据网络环境进行异构网络切换，包括wifi、4G/5G等
#环境配置
首先需要安装必要的依赖：
``bash
sudo apt update
sudo apt install python3-dbus network-manager -y
pip install dbus-python
