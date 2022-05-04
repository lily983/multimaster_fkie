# How to use it

## Set and connect two/multiple ROS master in one host. 
The two ROS master can publish/subscribe ROS topics to/from each other.

In this first console: (remeber to change the local host to your IP address)
    
```
cd catkin_ws
source devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311 
roscore --port 11311 >/dev/null 2>&1 &
rosrun fkie_master_discovery master_discovery >/dev/null 2>&1 &
rosrun fkie_master_sync master_sync >/dev/null 2>&1 
```
   
In the second console:

```
cd catkin_ws
source devel/setup.bash
export ROS_MASTER_URI=http://localhost:11312
roscore --port 11312 >/dev/null 2>&1 &
rosrun fkie_master_discovery master_discovery >/dev/null 2>&1 &
rosrun fkie_master_sync master_sync >/dev/null 2>&1 &
```
    
## Set and connect two/multiple ROS master in two/multiple hosts. These computers can publish/subscribe ROS topics to/from each other.
First set the local network between two computers. Recommended to use a switch to connect them toghther. 
Reference link: (https://websiteforstudents.com/how-to-edit-the-local-hosts-file-on-ubuntu-18-04-16-04/), (http://wiki.ros.org/ROS/NetworkSetup)

Edit IP address:
```
sudo nano /etc/hosts
```

Now setup multi-master between two computers. 
    
In computer 1: 
```
cd catkin_ws
source devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311 
roscore --port 11311 >/dev/null 2>&1 &
rosrun fkie_master_discovery master_discovery >/dev/null 2>&1 &
rosrun fkie_master_sync master_sync >/dev/null 2>&1 &
```
In computer 2: do the same thing as computer 1.
      
To check if multi-master is running or not, use "rostopic list" to check if there have ros topic /master_discovery/changes, /master_discovery/linkstats. Also use "rosservice call /master_discovery/list_masters" to check.
```
rostopic list 
rosservice call /master_discovery/list_masters
```

# This is a new version with daemon instance!
Whats new:

 * Remote access and control of launch and configuration files.
 * Easy remote editing of launch files.
 * Monitoring for ROS nodes and system resources on remote hosts.

> Old version is available on branch: `old_master` and is no longer supported!

# FKIE multimaster for ROS

The ROS stack of *fkie_multimaster* offers a complete solution for using ROS with multicores.
In addition, Node Manager with a daemon provide a GUI-based management environment that is very useful to manage ROS-launch configurations and control running nodes, also in a single-core system.

![multimaster overview](multimaster_overview.png)

## Packages have been renamed

The FKIE multimaster packages used to have an \_fkie suffix. In conformance with [REP-144](http://www.ros.org/reps/rep-0144.html), all packages have been renamed with an fkie\_ prefix, starting from version 1.0.0.
If you have built an older version from source, make sure to remove the build artifacts of the old versions from your build space.

## Install

The communication between the Node Manager GUI and the Daemon is based on Python [gRPC](https://grpc.io/). If you are using Ubuntu 18.10 or later, you can simply run `sudo apt install python-grpcio python-grpc-tools`. For Ubuntu 18.04 LTS, we provide a [PPA backport of the gRPC libraries](https://launchpad.net/~roehling/+archive/ubuntu/grpc). If your Ubuntu version is older than that, you need to install `grpcio-tools` from [PyPI](https://pypi.org/project/grpcio-tools/).

You can run the following commands to setup a build from source:

```
cd catkin_ws/src
git clone https://github.com/fkie/multimaster_fkie.git multimaster
rosdep update
rosdep install -i --as-root pip:false --reinstall --from-paths multimaster
```

Then build all packages:
```
catkin build fkie_multimaster
```

## Documentation

* [multimaster\_fkie](http://fkie.github.io/multimaster_fkie)
* [discovery](http://fkie.github.io/multimaster_fkie/master_discovery.html) -- `discovery using multicast or zeroconf`
* [synchronization](http://fkie.github.io/multimaster_fkie/master_sync.html) -- `master synchronization`
* [Node Manager GUI](http://fkie.github.io/multimaster_fkie/node_manager.html) -- `A GUI to manage the configuration on local and remote ROS masters`
* [Node Manager daemon](http://fkie.github.io/multimaster_fkie/node_manager_daemon.html) -- `Helper node allows an easy (auto)start of remote nodes and manage remote launch files`

For ROS interfaces and parameterization see the [ROS Wiki](http://www.ros.org/wiki/multimaster_fkie). For configuration details you can find example launch files in each package.

