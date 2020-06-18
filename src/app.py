from flask import Flask
from flask_restful import Resource, Api
from tasks import TaskRes
from flask_jwt import JWT
from authenticate import authenticate, identity
from user import UserRegisterRes
from db import db

app = Flask(__name__)
app.secret_key = "mySecret"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
api = Api(app)
db.init_app(app)

jwt = JWT(app, authenticate, identity)


class HomeRes(Resource):
    def get(self):
        return {'message': 'Welcome to Affari'}, 200


api.add_resource(HomeRes, '/')
api.add_resource(TaskRes, '/tasks')
api.add_resource(UserRegisterRes, '/register')

if __name__ == "__main__":
    app.run(debug=True)
