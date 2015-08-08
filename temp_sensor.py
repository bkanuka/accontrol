from w1thermsensor import W1ThermSensor

sensor = W1ThermSensor()
temp = sensor.get_temperature()
print temp
