import numpy as np
from SimpleCV import *
import tempfile
import glob
import sys
import time
from lirc import Lirc

from configobj import ConfigObj
from validate import Validator

import logging

def img_to_base64(self):
    with tempfile.NamedTemporaryFile(suffix='.png') as f:
        self.save(f.name, cleanTemp=True)
        data = open(f.name, 'rb').read().encode('base64')
    return data

def img_repr_html_(self):
    return '<img src="data:image/png;base64,{0}">'.format(self.to_base64())

def img_getFloatArray(self):
    return ((self.getGrayNumpy().astype(float) / 255) * 2) - 1
 
def img_autocrop(self, threshold=None):
    if not threshold:
        threshold = self.meanColor()[0]
    bin_img = self.threshold(threshold).invert()
    blobs = bin_img.findBlobs(1)

    try:
        tx, ty = np.amin(blobs.topLeftCorners(), axis=0)
        bx, by = np.amax(blobs.bottomRightCorners(), axis=0)
    except AttributeError:
        return self

    return self.crop(tx, ty, bx-tx, by-ty)
 
SimpleCV.Image.to_base64 = img_to_base64
SimpleCV.Image._repr_html_ = img_repr_html_
SimpleCV.Image.getFloatArray = img_getFloatArray
SimpleCV.Image.autocrop = img_autocrop

def autothreshold(img, offset=0):
    return img.threshold(np.mean(img.meanColor()) + offset)

"""
timeout = 4
lirc_conf = lirc_ac.conf
focus_time = 0.9

screen = 0, 230, 640, 250
digit0 = 165, 90, 60, 67
digit1 = 220, 90, 60, 67
mode_cool = 130, 160, 90, 90
mode_dry = 260, 160, 90, 90
mode_fan = 390, 160, 90, 90
fan_power = 525, 0, 115, 55
"""

class AC:
    def __init__(self):

        self.conf = ConfigObj('ac.conf', configspec='ac.schema')
        validator = Validator()
        valid = self.conf.validate(validator)

        if valid != True:
            raise ValueError('Invalid config file')

        self.timeout = self.conf['timeout']
        self.lastwake = 0

        logging.debug("Initializing Camera")
        self.camera = Camera()
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            url = '0.0.0.0:8080'
            self.stream = JpegStreamer(url)
            logging.debug('Streaming camera on: {}'.format(url))

        self.remote = Lirc(self.conf['lirc_conf'])
        self.getImg()

    def send(self, command):
        command = command.upper()
        if command in self.remote.codes['AC']:
            logging.debug("Sending: {}".format(command))

            self.remote.send_once('AC', command)

            self.lastwake = time.time()
            time.sleep(0.2)
            if command == 'POWER':
                time.sleep(0.5)

        else:
            logging.error("Unknown command: {}".format(command))
            logging.error("Known commands: {}".format(self.remote.codes['AC']))

    def wake(self):
        logging.debug("Waking screen")
        self.send('fan_high')
        brightness = self._getBrightness()
        if brightness < 100:
            self.wake()

    def _getBrightness(self):
        img = self.camera.getImage().toRGB()
        img = img.crop(*self.conf['screen'])
        img = img.splitChannels()[1]
        mean = img.meanColor()[0]
        logging.debug("Mean Color: {}".format(mean))
        return mean

    def getImg(self):
        if time.time() - self.lastwake > self.timeout:
            self.wake()

        logging.debug("Getting Image")
        img = self.camera.getImage().toRGB()
        img = img.crop(*self.conf['screen'])
        img = img.splitChannels()[1]
        mean = img.meanColor()[0]
        logging.debug("Mean Color: {}".format(mean))
        while mean > 220:
            img = self.camera.getImage().toRGB()
            img = img.crop(*self.conf['screen'])
            img = img.splitChannels()[1]
            mean = img.meanColor()[0]
            logging.debug("Mean Color: {}".format(mean))
            time.sleep(0.1)

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            stream_img = img.copy()
            drawinglayer = DrawingLayer((stream_img.width, stream_img.height))

            drawinglayer.rectangle(*self._rec('screen'))
            drawinglayer.rectangle(*self._rec('digit0', Color.BLUE))
            drawinglayer.rectangle(*self._rec('digit1', Color.RED))
            drawinglayer.rectangle(*self._rec('mode_cool'))
            drawinglayer.rectangle(*self._rec('mode_dry'))
            drawinglayer.rectangle(*self._rec('mode_fan'))
            drawinglayer.rectangle(*self._rec('fan_power'))

            stream_img.addDrawingLayer(drawinglayer)
            stream_img.applyLayers()

            stream_img.save(self.stream)
            stream_img.save('debug/capture.png')

        return img

    def _rec(self, name, color=Color.DEFAULT):
        x, y, w, h = self.conf[name]
        return ((x,y), (w,h), color)

    def getTemp(self):
        img = self.getImg()

        area_digit0 = img.crop(*self.conf['digit0'])
        area_digit1 = img.crop(*self.conf['digit1'])
        temp = self._match_digit(area_digit0) * 10 + self._match_digit(area_digit1)

        logging.debug("Temp: {}".format(temp))
        while temp > 40:
            logging.warning('Tempurature in F')
            self.send('f_c')
            temp = self.getTemp()

        return temp

    def _match_digit(self, img):
        img = autothreshold(img, -15)
        img = img.autocrop()
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            img.save('debug/digit_autocrop.png')
        img = img.getFloatArray()

        d = 0
        d_coor = 0
        for f in glob.glob('templates/[0-9].png'):
            n = int(f[10:11])

            temp = Image(f)
            temp = temp.autocrop()
            temp = temp.resize(*img.shape)
            temp = temp.getFloatArray()

            c = ((img * temp) + 1) / 2

            c_sum = c.sum()

            Image(c * 255).save('debug/c_{}.png'.format(n))
            if c_sum > d_coor:
                d_coor = c_sum
                d = n
        return d

    def getMode(self):
        img = self.getImg()

        modes = {"cool": self.conf['mode_cool'],
                "dry": self.conf['mode_dry'], 
                "fan": self.conf['mode_fan']}

        s = 0.17
        mode = False

        for m, bb in modes.items():
            area = img.crop(*bb)
            area = autothreshold(area, - 20)
            area = area.invert()
            area_float = area.getGrayNumpy().astype(float) / 255
            area_sum = area_float.sum()
            area_percent = area_sum/float(area.area())

            logging.debug("Percent {}: {}".format(m, area_percent))

            if area_percent > s:
                s = area_percent
                mode = m

        return mode

    def getPower(self):
        logging.debug("Getting power status")
        if self.getMode():
            logging.debug("Power: ON")
            return True
        else:
            logging.debug("Power: OFF")
            return False

    def getFan(self):
        img = self.getImg()

        fan = img.crop(*self.conf['fan_power'])
        fan = autothreshold(fan - 20)
        fan = fan.invert()
        fan.save('debug/fan.png')
        fan = fan.getGrayNumpy().astype(int).sum()
        self.fanraw = fan

        if fan < 300000:
            fan = 1
        elif fan > 500000:
            fan = 3
        else:
            fan = 2

        return fan

    def getTarget(self):
        self.send('up')
        self.send('down')
        return self.getTemp()

    def setTemp(self, target):
        self.setMode('cool')
        current = self.getTemp()
        logging.info('Current setting: {}'.format(current))

        if target < current:
            for i in range(current - target):
                self.send('down')
        elif target > current:
            for i in range(target - current):
                self.send('up')

        current = self.getTemp()
        if current != target:
            self.setTemp(target)

    def setMode(self, mode):
        self.powerOn()
        self.send(mode)

    def powerOn(self):
        while not self.getPower():
            logging.info('Powering ON')
            self.send('power')

    def powerOff(self):
        while self.getPower():
            logging.info('Powering OFF')
            self.send('power')
