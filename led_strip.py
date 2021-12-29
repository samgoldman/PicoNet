from component import Component
import pwmio

def clamp_value(value):
    return min(100, max(0, value))

class LedStrip(Component):
    def __init__(self, red_pin, green_pin, blue_pin):
        self.red_pwm = pwmio.PWMOut(red_pin)
        self.green_pwm = pwmio.PWMOut(green_pin)
        self.blue_pwm = pwmio.PWMOut(blue_pin)
    
    def set_red_percent(self, value):
        self.red_pwm.duty_cycle = clamp_value(value)

    def set_green_percent(self, value):
        self.green_pwm.duty_cycle = clamp_value(value)

    def set_red_percent(self, value):
        self.blue_pwm.duty_cycle = clamp_value(value)
