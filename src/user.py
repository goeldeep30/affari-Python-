from blacklist import BLACKLIST
from src.db import db
from datetime import timedelta
from src.utility import AccessLevel
from flask_restful import Resource, reqparse
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                fresh_jwt_required, get_jwt_claims,
                                get_jwt_identity, jwt_required,
                                get_raw_jwt, jwt_refresh_token_required)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    access_level = db.Column(db.Integer)
    task = db.relationship("Task", lazy='dynamic')
    # curr_projects = db.relationship("Project", secondary=proj_allocation,
    #                          backref='members', lazy='dynamic')

    # project = db.relationship("Project")

    def __init__(self, username: str, password: str,
                 access_level: int, id: int = None):
        self.id = id
        self.username = username
        self.password = password
        self.access_level = access_level

    def __str__(self):
        return f"{self.__dict__}"

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    def make_dev_user(self):
        self.access_level = AccessLevel.DEVELOPER
        db.session.add(self)
        db.session.commit()

    def block_dev_user_creation(func):
        def create_user(obj):
            if obj.access_level <= AccessLevel.DEVELOPER:
                obj.access_level = AccessLevel.ADMIN
            return func(obj)
            # BUG: If developer tries to update its user detais,
            # It won't have developer any more rights after that
        return create_user

    @block_dev_user_creation
    def create_update_user(self):
        db.session.add(self)
        db.session.commit()

    def delete_user(self):
        db.session.delete(self)
        db.session.commit()

    def json(self):
        return {
            'id': self.id,
            'username': self.username,
            # 'password': self.password,
            'access_level': self.access_level,
            # 'task': [tsk.json() for tsk in self.task.all()],
            # 'projects': [
            #     project.json() for project in self.projects.all()
            # ],
            'curr_projects': [
                proj.json() for proj in self.curr_projects
            ],
        }

    def basicDetails(self):
        return {
            'id': self.id,
            'username': self.username,
        }

    def is_user_admin(self):
        if self.access_level <= AccessLevel.ADMIN:
            return True
        return False

    def is_user_manager(self):
        if self.access_level <= AccessLevel.MANAGER:
            return True
        return False

    def projects(self):
        return {
            'curr_projects': [
                proj.json() for proj in self.curr_projects
            ],
        }

    def has_project(self, project):
        if project in self.curr_projects:
            return True
        return False


class UserRegisterRes(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str, required=True,
                        help='Username Required')
    parser.add_argument('password', type=str, required=True,
                        help='Password Required')
    # parser.add_argument('project_id', type=int, required=True,
    #                     help='Project ID Required')
    parser.add_argument('access_level', type=int, required=True,
                        help='Access level Required')

    @jwt_required
    def get(self):
        claims = get_jwt_claims()
        if not claims['admin']:
            return {'msg': 'Admin rights needed'}, 403

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

    @jwt_required
    def put(self):
        data = UserRegisterRes.parser.parse_args()
        usr = User.find_by_username(data['username'])
        if usr:
            for key, value in data.items():
                setattr(usr, key, value)
            usr.create_update_user()
            return {'msg': 'user updated successfully'}, 200

        # User(id=None, **data).create_update_user()
        # return {'msg': 'User Created Successfully'}, 200

        return {'msg': 'No such user found'}, 400

    @fresh_jwt_required
    def delete(self):
        claims = get_jwt_claims()
        if not claims['admin']:
            return {'msg': 'Admin rights needed'}, 403

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
            expires = timedelta(minutes=10)
            access_token = create_access_token(
                identity=usr.id, fresh=True, expires_delta=expires)
            refresh_token = create_refresh_token(usr.id)
            return{
                'access_token': access_token,
                'refresh_token': refresh_token,
                'username': usr.username
            }, 200
        return {'msg': 'Invalid credentials'}, 401


class UserLogout(Resource):

    @jwt_required
    def delete(self):
        BLACKLIST.add(get_raw_jwt()['jti'])
        return {'msg': 'User logged out successfuilly'}, 200


class TokenRefresh(Resource):

    @jwt_refresh_token_required
    def post(self):

        current_user = get_jwt_identity()
        expires = timedelta(minutes=10)
        new_token = create_access_token(
            identity=current_user, fresh=False, expires_delta=expires)
        return{
            'access_token': new_token,
        }, 200
