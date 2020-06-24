from flask import Flask
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager
# from src.authenticate import authenticate, identity
from src.user import UserRegisterRes, UserLoginRes, TokenRefresh, User
from src.tasks import TaskRes
from src.teams import TeamRes
from src.db import db

app = Flask(__name__)
app.secret_key = "mySecret"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
api = Api(app)
db.init_app(app)


@app.before_first_request
def create_db():
    db.create_all()


jwt = JWTManager(app)


@jwt.user_claims_loader
def add_claims_to_jwt(identity):
    claims = {}
    claims['admin'] = User.find_by_id(identity).is_user_admin()
    return claims


class HomeRes(Resource):
    def get(self):
        return {'msg': 'Welcome to Affari'}, 200


api.add_resource(HomeRes, '/')
api.add_resource(TaskRes, '/tasks')
api.add_resource(UserRegisterRes, '/register')
api.add_resource(UserLoginRes, '/login')
api.add_resource(TeamRes, '/teams')
api.add_resource(TokenRefresh, '/refresh')

if __name__ == "__main__":
    app.run(debug=True)
