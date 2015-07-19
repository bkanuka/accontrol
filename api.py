import logging
logging.getLogger().setLevel(logging.DEBUG)

from flask import Flask, request
from flask_restful import reqparse, Resource, Api

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('temp', type=int)
parser.add_argument('power', type=str)

from pyac import AC
ac = AC()

class Main(Resource):
    def get(self):
        mode = ac.getMode()
        temp = ac.getTemp()

        r = {
                'power': bool(mode),
            }

        if mode == 'cool':
            r['target_temp'] = temp
        else:
            r['room_temp'] = temp

        if mode:
            r['mode'] = mode

            fan = ac.getFan()
            r['fan'] = fan
            
        return r

    def put(self):
        args = parser.parse_args()
        if args.get('power', False):
            if args['power'].lower() in ['off', 'false']:
                ac.powerOff()
                return True
            elif args['power'].lower() in ['on', 'true']:
                ac.powerOn()
            else:
                abort(400, 
                        message="Invalid power command: {}".format(args['power']))

        if args.get('temp', False):
            ac.setTemp(args['temp'])

        return True


api.add_resource(Main, '/')


class Temp(Resource):
    def get(self):
        r = ac.getTemp()
        return r
    
    def put(self):
        temp = int(request.form['temp'])
        ac.setTemp(temp)
        r = ac.getTemp()
        return r

api.add_resource(Temp, '/temp')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, use_reloader=False)

'''
class AC:
    def __init__(self, timeout=2, camera=0):
    def power(self):
    def getTemp(self):
    def getMode(self):
    def getPower(self):
    def getFan(self):
    def getTarget(self):
    def setTemp(self, target):
    def setMode(self, mode):
    def powerOn(self):
    def powerOff(self):
'''
