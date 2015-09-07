import sys
from flask import Flask, request
from flask_restful import reqparse, Resource, Api, abort

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('temp', type=int)
parser.add_argument('power', type=str)
parser.add_argument('mode', type=str)

if len(sys.argv) > 1 and sys.argv[1] == '--debug':
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

from pyac import AC
ac = AC()

class Main(Resource):
    def get(self):
        args = parser.parse_args()

        if args.get('power', False):
            if args['power'].lower() in ['off', 'false']:
                ac.powerOff()
            elif args['power'].lower() in ['on', 'true']:
                ac.powerOn()
            else:
                abort(400, 
                        message="Invalid power command: {}".format(args['power']))

        if args.get('temp', False):
            ac.setTemp(args['temp'])

        if args.get('mode', False):
            if args['mode'].lower() in ['fan', 'cool', 'dry']:
                ac.setMode(args['mode'])
            else:
                abort(400, 
                        message="Invalid mode command: {}".format(args['mode']))

        r = ac.getStatus()
        return r

    def put(self):
        args = parser.parse_args()
        if args.get('power', False):
            if args['power'].lower() in ['off', 'false']:
                ac.powerOff()
                return True
            elif args['power'].lower() in ['on', 'true']:
                ac.powerOn()
                return True
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
        args = parser.parse_args()
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
