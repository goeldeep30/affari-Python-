from flask_restful import Resource, reqparse
from src.db import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))

    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __str__(self):
        return f"User(id='{self.id}')"

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    def create_update_user(self):
        db.session.add(self)
        db.session.commit()

    def delete_user(self):
        db.session.delete(self)
        db.session.commit()


class UserRegisterRes(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str, required=True,
                        help='Username Required')
    parser.add_argument('password', type=str, required=True,
                        help='Password Required')

    def get(self):
        usrs = []
        for user in User.query.all():
            usrs.append(
                {'id': user.id,
                 'username': user.username,
                 'password': user.password}
            )
        return {'Users': usrs}, 200

    def post(self):
        data = UserRegisterRes.parser.parse_args()
        if User.find_by_username(data['username']):
            return {'message': 'User already exists'}, 400

        User(id=None, **data).create_update_user()
        return {'message': 'User created successfully'}, 200

    def put(self):
        data = UserRegisterRes.parser.parse_args()
        usr = User.find_by_username(data['username'])
        if usr:
            usr.username = data['username']
            usr.password = data['password']
            usr.create_update_user()
            return {'message': 'user updated successfully'}, 200

        User(id=None, **data).create_update_user()
        return {'message': 'User Created Successfully'}, 200

    def delete(self):
        data = UserRegisterRes.parser.parse_args()
        usr = User.find_by_username(data['username'])
        if usr:
            usr.delete_user()
            return {'message': 'User deleted successfully'}, 200

        return {'message': 'User not found'}, 404
