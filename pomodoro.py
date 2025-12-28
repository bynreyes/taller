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
Lapse = namedtuple('Lapse', 'duration message name')

# constantes
WORK, SHORT_TIME, LONG_TIME, DISPLAY = (40*60, 5*60, 20*60, 10)

# set vakues
work_duration = Lapse(WORK, 'its work time', 'work')
break_duration = Lapse(SHORT_TIME, 'its break time', 'break')
long_break_duration = Lapse(LONG_TIME, 'mid time', 'long break')
short_cycle = [work_duration, break_duration]
long_cycle = [work_duration, long_break_duration]


def pomodoro():
    c = 0
    while True:
        c += 1
        lap = long_cycle if c % 4 == 0 else short_cycle
        print(c)
        for lapse in lap:
            notification.notify(
                title = f"pomodoro sesion {lapse.name}",
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