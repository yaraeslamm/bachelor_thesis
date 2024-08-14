import time
from andr_controller import AndrController

EYES_LEFT_VALUES = [80, 80, 128, 0, 0, 0, 0, 0, 0, 0, 0, 128, 175, 128]
HEAD_LEFT_VALUES = [80, 128, 128, 0, 0, 0, 0, 0, 0, 0, 0, 128, 175, 80]
SMILE_VALUES = [45, 128, 128, 107, 0, 0, 89, 191, 0, 132, 43, 128, 229, 128]

pause = 0.04
steps = 10

controller = AndrController('COM5', steps, pause) # 'COM5'

controller.send_values(EYES_LEFT_VALUES)
time.sleep(steps * pause)
controller.move_to(HEAD_LEFT_VALUES)
time.sleep(steps * pause)
controller.move_to(SMILE_VALUES)
time.sleep(steps * pause)
controller.move_to(controller.startup_values)






