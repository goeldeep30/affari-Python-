from src.db import db
from flask_restful import Resource, reqparse
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                jwt_required, get_jwt_claims)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    team = db.relationship("Team")
    access_level = db.Column(db.Integer)

    def __init__(self, id, username, password, team_id, access_level):
        self.id = id
        self.username = username
        self.password = password
        self.team_id = team_id
        self.access_level = access_level

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

    def json(self):
        return {'id': self.id,
                'username': self.username,
                # 'password': self.password,
                'team_id': self.team_id,
                'access_level': self.access_level
                }

    def is_user_admin(self):
        """
        0 -> Admin
        """
        if self.access_level <= 0:
            return True
        return False


class UserRegisterRes(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str, required=True,
                        help='Username Required')
    parser.add_argument('password', type=str, required=True,
                        help='Password Required')
    parser.add_argument('team_id', type=int, required=True,
                        help='Team ID Required')
    parser.add_argument('access_level', type=int, required=True,
                        help='Access level Required')

    def get(self):
        usrs = []
        for user in User.query.all():
            usrs.append(
                user.json()
            )
        return {'Users': usrs}, 200

    def post(self):
        data = UserRegisterRes.parser.parse_args()
        if User.find_by_username(data['username']):
            return {'msg': 'User already exists'}, 400

        User(id=None, **data).create_update_user()
        return {'msg': 'User created successfully'}, 200

    def put(self):
        data = UserRegisterRes.parser.parse_args()
        usr = User.find_by_username(data['username'])
        if usr:
            for key, value in data.items():
                setattr(usr, key, value)
            usr.create_update_user()
            return {'msg': 'user updated successfully'}, 200

        User(id=None, **data).create_update_user()
        return {'msg': 'User Created Successfully'}, 200

    @jwt_required
    def delete(self):
        claims = get_jwt_claims()
        if not claims['admin']:
            print(claims)
            return {'msg': 'Admin rights needed'}, 401

        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True,
                            help='Username Required')
        data = parser.parse_args()
        usr = User.find_by_username(data['username'])
        if usr:
            usr.delete_user()
            return {'msg': 'User deleted successfully'}, 200

        return {'msg': 'Invalid user'}, 404


class UserLoginRes(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str, required=True,
                        help='Username Required')
    parser.add_argument('password', type=str, required=True,
                        help='Password Required')

    def post(self):
        data = UserLoginRes.parser.parse_args()
        usr = User.find_by_username(data['username'])
        if usr and usr.password == data['password']:
            access_token = create_access_token(identity=usr.id, fresh=True)
            refresh_token = create_refresh_token(usr.id)
            return{
                'access_token': access_token,
                'refresh_token': refresh_token,
                'username': usr.username
            }, 200
        return {'msg': 'Invalid credentials'}, 401
