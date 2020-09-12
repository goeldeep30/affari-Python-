from blacklist import BLACKLIST
from src.db import db
from datetime import timedelta
from src.utility import AccessLevel, UserEmailStatus
from token_storage import (ISSUED_RESET_PASSWORD_EMAIL_TOKEN,
                           ISSUED_CONFIRM_EMAIL_TOKEN)
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import make_response, render_template, url_for
from flask_restful import Resource, reqparse
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                fresh_jwt_required, get_jwt_claims,
                                get_jwt_identity, jwt_required,
                                get_raw_jwt, jwt_refresh_token_required)

import requests
from json import loads

s = URLSafeTimedSerializer('Secre@tKey')


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    access_level = db.Column(db.Integer)
    email_confirmed = db.Column(db.Integer)
    task = db.relationship("Task", lazy='dynamic')
    owns_projects = db.relationship("Project", backref='owner', lazy='dynamic')
    # curr_projects = db.relationship("Project", secondary=proj_allocation,
    #                          backref='members', lazy='dynamic')

    # project = db.relationship("Project")

    def __init__(self, username: str, password: str,
                 access_level: int,
                 email_confirmed: int = UserEmailStatus.NOTCONFIRMED,
                 id: int = None):
        self.id = id
        self.username = username
        self.password = password
        self.access_level = access_level
        self.email_confirmed = email_confirmed

    def __str__(self):
        return f"{self.__dict__}"

    @classmethod
    def find_by_username(cls, username,
                         email_confirmed=UserEmailStatus.CONFIRMED):
        return cls.query.filter_by(username=username,
                                   email_confirmed=email_confirmed).first()

    @classmethod
    def find_by_id(cls, _id, email_confirmed=1):
        return cls.query.filter_by(id=_id,
                                   email_confirmed=email_confirmed).first()

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

        if User.find_by_username(data['username'],
                                 UserEmailStatus.NOTCONFIRMED):
            return {'msg': 'User already exists, Please Login'}, 403

        User(id=None, **data).create_update_user()
        mail_uri = 'http://localhost:5000' + \
            url_for('SendConfirmationMailRes', username=data['username'])
        resp = requests.get(mail_uri).content
        resp = loads(resp.decode('utf-8'))['msg']
        return {'msg': f'User created successfully, {resp}'}, 200

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
        usr_unconfirmed = User.find_by_username(data['username'],
                                                UserEmailStatus.NOTCONFIRMED)
        if usr and usr.password == data['password']:
            expires = timedelta(days=30)
            access_token = create_access_token(
                identity=usr.id, fresh=True, expires_delta=expires)
            refresh_token = create_refresh_token(usr.id)
            return{
                'access_token': access_token,
                'refresh_token': refresh_token,
                'username': usr.username
            }, 200
        elif usr_unconfirmed:
            mail_base_url = 'http://localhost:5000'
            mail_uri = url_for('SendConfirmationMailRes',
                               username=usr_unconfirmed.username)
            mail_uri = mail_base_url + mail_uri
            resp = requests.get(mail_uri).content
            resp = loads(resp.decode('utf-8'))['msg']
            return {'msg': f'Email not confirmed, {resp}'}, 401

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
        expires = timedelta(days=30)
        new_token = create_access_token(
            identity=current_user, fresh=False, expires_delta=expires)
        return{
            'access_token': new_token,
        }, 200


class UserActivateRes(Resource):
    def get(cls, token):
        try:
            username = s.loads(token, salt='email-confirm', max_age=24*60*60)
            # 1 Day old signature can be verified
            user = User.find_by_username(username,
                                         UserEmailStatus.NOTCONFIRMED)
            if not user:
                return {'msg': 'No such unconfirmed account'}, 400
            if ISSUED_CONFIRM_EMAIL_TOKEN.pop(username, None) != token:
                return {'msg': 'Expired token'}, 400
            headers = {'Content-Type': 'text/html'}
            user.email_confirmed = UserEmailStatus.CONFIRMED
            user.create_update_user()
            return make_response(render_template('activatedProfileResponse.html'),
                                 200, headers)
        except SignatureExpired:
            return {'msg': 'Expired token'}, 401
        except BadSignature:
            return {'msg': 'Bad signature'}, 400
        return {'msg': 'Something went wrong, Try again'}, 500


class UserResetPasswordRes(Resource):
    def get(cls, username_token):
        try:
            username = s.loads(username_token, salt='password-reset-email',
                               max_age=60*60)
            # 1 Hour old signature can be verified
            user = User.find_by_username(username)
            if not user:
                return {'msg': 'No such activated account'}, 400
            if ISSUED_RESET_PASSWORD_EMAIL_TOKEN.get(username, None) != username_token:
                return {'msg': 'Expired token'}, 400
            headers = {'Content-Type': 'text/html'}
            return make_response(render_template('resetPassword.html'),
                                 200, headers)
        except SignatureExpired:
            return {'msg': 'Expired token'}, 401
        except BadSignature:
            return {'msg': 'Bad signature'}, 400
        return {'msg': 'Something went wrong, Try again'}, 500

    def post(cls, username_token):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('password', type=str, required=True,
                                help='Password Required')
            data = parser.parse_args()
            username = s.loads(username_token, salt='password-reset-email',
                               max_age=60*60)
            password = data['password']
            # 1 Hour old signature can be verified
            user = User.find_by_username(username)
            if not user:
                return {'msg': 'No such activated account'}, 400
            if ISSUED_RESET_PASSWORD_EMAIL_TOKEN.pop(username, None) != username_token:
                return {'msg': 'Expired token'}, 400
            user.password = password
            user.create_update_user()
            return {'msg': 'Password updated successfully'}, 200
        except SignatureExpired:
            return {'msg': 'Expired token'}, 401
        except BadSignature:
            return {'msg': 'Bad signature'}, 400
        return {'msg': 'Something went wrong, Try again'}, 500
