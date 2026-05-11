from xarm.wrapper import XArmAPI
import time

# connection
arm = XArmAPI('192.168.1.242') 
time.sleep(1)

if arm.has_err_warn:
    print(f"Errors found: {arm.get_err_warn_code()}")
    arm.clean_error() 
    arm.clean_warn()
    time.sleep(1)

arm.motion_enable(False) 
time.sleep(0.5)
arm.motion_enable(True)
time.sleep(1) 

# Mode 0 = Position Mode
arm.set_mode(0) 
arm.set_state(0) 
time.sleep(1)

# Safe zone
target_angle = [0.1, -17.7, -64, 83.1, 0]
print(f'Move to {target_angle}...')

# Move status
ret = arm.set_servo_angle(
    angle=target_angle, 
    speed=20,
    mvacc=100,
    is_wait=True,
    is_radian=False 
)

if ret == 0:
    print('Move is done')
else:
    print(f'Error in moving: {ret}')

arm.disconnect()