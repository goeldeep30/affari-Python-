from flask_restful import Resource, reqparse
from db import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
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

    def create_user(self):
        db.session.add(self)
        db.session.commit()


class UserRegisterRes(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str, required=True,
                        help='username Required')
    parser.add_argument('password', type=str, required=True,
                        help='password Required')

    def get(self):
        usrs = []
        for user in User.query.all():
            usrs.append(
                {'id': user.id, 'subject': user.username, 'status': user.password}
            )
        return {'tasks': usrs}, 200

    def post(self):
        data = UserRegisterRes.parser.parse_args()
        if User.find_by_username(data['username']):
            return {'message': 'user already exists'}, 400

        data['id'] = None
        User(**data).create_user()
        return {'message': 'User Created Successfully'}, 200
