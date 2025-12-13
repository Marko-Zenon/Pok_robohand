from xarm.wrapper import XArmAPI
import time

# 1. Підключення
arm = XArmAPI('192.168.1.242') 
time.sleep(1)

# 2. Очистка помилок (ОБОВ'ЯЗКОВО після хрускоту)
if arm.has_err_warn:
    print(f"Знайдено помилки: {arm.get_err_warn_code()}")
    arm.clean_error() 
    arm.clean_warn()
    time.sleep(1)

# 3. Перезавантаження моторів
arm.motion_enable(False) 
time.sleep(0.5)
arm.motion_enable(True)
time.sleep(1) 

# 4. ВСТАНОВЛЕННЯ ПРАВИЛЬНОГО РЕЖИМУ
# Mode 0 = Position Mode (Плавний рух з плануванням шляху)
arm.set_mode(0) 
arm.set_state(0) 
time.sleep(1)

# Координати (твоя безпечна позиція)
target_angle = [0.1, -17.7, -64, 83.1, 0]
print(f'Рух руки до {target_angle}...')

# 5. Рух (швидкість невелика для тесту)
ret = arm.set_servo_angle(
    angle=target_angle, 
    speed=20,        # Швидкість (градусів на секунду)
    mvacc=100,       # Прискорення (чим менше, тим плавніше старт)
    is_wait=True,    # Чекати поки доїде
    is_radian=False 
)

if ret == 0:
    print('✅ УСПІХ! Рух виконано плавно.')
else:
    print(f'❌ Помилка руху. Код: {ret}')

arm.disconnect()