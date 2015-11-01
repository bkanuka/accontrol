#!/usr/bin/env python

import sys
import time
import requests
from w1thermsensor import W1ThermSensor
from datetime import datetime

print "running"

def get_room_temp():
    room_sensor = W1ThermSensor()
    room_temp = room_sensor.get_temperature()
    return room_temp

def set_room_temp(temp):
    idx = 17
    baseurl = "http://ha.home.bkanuka.com/json.htm"
    params = {"type":"command",
            "param": "udevice",
            "idx": idx,
            "nvalue": 0,
            "svalue": temp}
    r = requests.get(baseurl, params=params)
    return r.json()


def set_setpoint(temp):
    idx = 18
    baseurl = "http://ha.home.bkanuka.com/json.htm"
    params = {"type":"command",
            "param": "setsetpoint",
            "idx": idx,
            "setpoint": temp}
    r = requests.get(baseurl, params=params)
    return r.json()

def get_setpoint():
    idx = 18
    baseurl = "http://ha.home.bkanuka.com/json.htm"
    params = {"type":"devices",
            "rid": idx}
    r = requests.get(baseurl, params=params).json()
    result = r['result'][0]
    setpoint = float(result['SetPoint'])
    last_update = datetime.strptime(result['LastUpdate'], "%Y-%m-%d %H:%M:%S")
    return (setpoint, last_update)
    
def set_ac_temp(temp):
    baseurl = "http://accontrol.home.bkanuka.com"
    params = {"temp": temp}
    r = requests.get(baseurl, params=params).json()
    return r

if __name__ == "__main__":
    print "running __main__"
    setpoint, lastupdate = get_setpoint()

    while True:
        temp = get_room_temp()
        r = set_room_temp(temp)
        print temp
        print r

        for i in range(6):
            s, l = get_setpoint()
            if l > lastupdate:
                print "setpoint updated"
                lastupdate = l
                r = set_ac_temp(int(s))
                print r
            time.sleep(10)
