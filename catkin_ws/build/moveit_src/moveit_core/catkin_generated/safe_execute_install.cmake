execute_process(COMMAND "/home/yarema/catkin_ws/build/moveit_src/moveit_core/catkin_generated/python_distutils_install.sh" RESULT_VARIABLE res)

if(NOT res EQUAL 0)
  message(FATAL_ERROR "execute_process(/home/yarema/catkin_ws/build/moveit_src/moveit_core/catkin_generated/python_distutils_install.sh) returned error code ")
endif()
