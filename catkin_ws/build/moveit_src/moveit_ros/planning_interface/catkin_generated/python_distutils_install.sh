#!/bin/sh

if [ -n "$DESTDIR" ] ; then
    case $DESTDIR in
        /*) # ok
            ;;
        *)
            /bin/echo "DESTDIR argument must be absolute... "
            /bin/echo "otherwise python's distutils will bork things."
            exit 1
    esac
fi

echo_and_run() { echo "+ $@" ; "$@" ; }

echo_and_run cd "/home/yarema/catkin_ws/src/moveit_src/moveit_ros/planning_interface"

# ensure that Python install destination exists
echo_and_run mkdir -p "$DESTDIR/home/yarema/catkin_ws/install/lib/python3/dist-packages"

# Note that PYTHONPATH is pulled from the environment to support installing
# into one location when some dependencies were installed in another
# location, #123.
echo_and_run /usr/bin/env \
    PYTHONPATH="/home/yarema/catkin_ws/install/lib/python3/dist-packages:/home/yarema/catkin_ws/build/lib/python3/dist-packages:$PYTHONPATH" \
    CATKIN_BINARY_DIR="/home/yarema/catkin_ws/build" \
    "/usr/bin/python3" \
    "/home/yarema/catkin_ws/src/moveit_src/moveit_ros/planning_interface/setup.py" \
    egg_info --egg-base /home/yarema/catkin_ws/build/moveit_src/moveit_ros/planning_interface \
    build --build-base "/home/yarema/catkin_ws/build/moveit_src/moveit_ros/planning_interface" \
    install \
    --root="${DESTDIR-/}" \
    --install-layout=deb --prefix="/home/yarema/catkin_ws/install" --install-scripts="/home/yarema/catkin_ws/install/bin"
