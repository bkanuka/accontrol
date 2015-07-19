from SimpleCV import *
import time
from configobj import ConfigObj
from validate import Validator
config = ConfigObj('ac.conf', configspec='ac.schema')
validator = Validator()
valid = config.validate(validator)

if valid != True:
    raise ValueError('Invalid config file')

url = '0.0.0.0:8080'
stream = JpegStreamer(url)
camera = Camera()

print 'Streaming camera on: {}'.format(url)

def rec(name, color=Color.DEFAULT):
    x, y, w, h = config[name]
    return ((x,y), (w,h), color)

def rec_shift(name, color=Color.DEFAULT):
    x, y, w, h = config[name]
    xs, ys, ws, hs = config['screen']
    return ((x+xs,y+ys), (w,h), color)

while True:
    try:
        config = ConfigObj('ac.conf', configspec='ac.schema')
        validator = Validator()
        valid = config.validate(validator)

        if valid != True:
            raise ValueError('Invalid config file')

        img = camera.getImage()

        drawinglayer = DrawingLayer((img.width, img.height))

        drawinglayer.rectangle(*rec('screen'))
        drawinglayer.rectangle(*rec_shift('digit0', Color.BLUE))
        drawinglayer.rectangle(*rec_shift('digit1', Color.RED))
        drawinglayer.rectangle(*rec_shift('mode_cool'))
        drawinglayer.rectangle(*rec_shift('mode_dry'))
        drawinglayer.rectangle(*rec_shift('mode_fan'))
        drawinglayer.rectangle(*rec_shift('fan_power'))

        img.addDrawingLayer(drawinglayer)
        img.applyLayers()

        img.save(stream)
        time.sleep(0.25)
    except KeyboardInterrupt:
        break


