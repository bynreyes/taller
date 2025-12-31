"""
pomodoro timer
by nreyes

for next:
- sound notification
- commands for interrup, set values, etc
"""
from collections import namedtuple
import time
from plyer import notification

# data structure
Lapse = namedtuple('Lapse', 'duration message name') # sound, gift,  ...
Cycle = namedtuple('Cycle', 'work pause name')

# constantes
# Options to keep in mind here are: @dataclass, namedtuple, enum type
# def set_values(*args):
#     ...
WORK, SHORT_TIME, LONG_TIME, DISPLAY, CYCLES = (40*60, 5*60, 20*60, 10, 4)

# set values
work_duration = Lapse(WORK, 'tlabaja, tienes que tlabaja!!', 'work time')
break_duration = Lapse(SHORT_TIME, '5 minutos de chisme', 'break')
long_break_duration = Lapse(LONG_TIME, 'descansa viejo', 'long break')
short_cycle = Cycle(work_duration, break_duration, 'short cycle')
long_cycle = Cycle(work_duration, long_break_duration, 'long cycle')

def pomodoro():
    step = 0
    while True:
        step += 1
        lap = long_cycle if step % CYCLES == 0 else short_cycle
        print(f'{step}  --> {lap.name}')
        for lapse in (lap.work, lap.pause):
            notification.notify(
                title = f"iniciando pomodoro sesion {lapse.name}",
                message=f"{lapse.message}" ,
                # displaying time
                timeout=DISPLAY 
                    )
            time.sleep(lapse.duration)
            
            
if __name__ == '__main__':
    try:
        pomodoro()
    except KeyboardInterrupt:
        print("\nPomodoro terminado por el usuario")