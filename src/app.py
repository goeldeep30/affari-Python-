from flask import Flask
from flask_restful import Resource, Api
from tasks import Task, TaskStatus, TaskRes
from flask_jwt import JWT
from authenticate import authenticate, identity
from user import UserRegisterRes

import json

app = Flask(__name__)
app.secret_key = "mySecret"
api = Api(app)

jwt = JWT(app, authenticate, identity)


class HomeRes(Resource):
    def get(self):
        return {'message':'Welcome to Affari'},200


api.add_resource(HomeRes, '/')
api.add_resource(TaskRes, '/tasks')
api.add_resource(UserRegisterRes,'/register')

if __name__ == "__main__":
    app.run(debug=True)
