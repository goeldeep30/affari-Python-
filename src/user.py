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
        # connection = sqlite3.connect('data.db')
        # cursor = connection.cursor()
        # query = "SELECT * FROM users WHERE username=?"
        # result = cursor.execute(query, (username,))
        # row = result.fetchone()
        # if row:
        #     user = cls(*row)
        # else:
        #     user = None

        # connection.close()
        # return user
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, _id):
        # connection = sqlite3.connect('data.db')
        # cursor = connection.cursor()
        # query = "SELECT * FROM users WHERE id=?"
        # result = cursor.execute(query, (_id,))
        # row = result.fetchone()
        # if row:
        #     user = cls(*row)
        # else:
        #     user = None

        # connection.close()
        # return user
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

    # def get(self):
    #     connection = sqlite3.connect('data.db')
    #     cursor = connection.cursor()
    #     select_query = "SELECT * FROM users"
    #     for row in cursor.execute(select_query):
    #         print(row)

    def post(self):
        data = UserRegisterRes.parser.parse_args()
        if User.find_by_username(data['username']):
            return {'message': 'user already exists'}, 400

        # connection = sqlite3.connect('data.db')
        # cursor = connection.cursor()
        # query = 'INSERT INTO users VALUES(NUll,?,?)'
        # cursor.execute(query, (data['username'], data['password']))
        # connection.commit()
        # connection.close()
        data['id'] = None
        User(**data).create_user()
        return {'message': 'User Created Successfully'}, 200


# users = [
#     User(1, 'joe', 'pass'),
#     User(2, 'user2', 'abcxyz'),
# ]

# username_table = {u.username: u for u in users}
# userid_table = {u.id: u for u in users}
