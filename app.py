import os
from flask import Flask
from flask_restful import Resource, Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from blacklist import BLACKLIST

from src.user import (UserRegisterRes, UserLoginRes,
                      UserLogout, TokenRefresh, User)
from src.tasks import TaskRes
from src.projects import ProjectRes, ProjectAllocate, ProjectMembers
from src.db import db

# import logging
# logging.basicConfig(
#     filename='trace.log',
#     level=logging.DEBUG,
#     format='%(created)f:%(levelname)s:%(message)s'
# )


app = Flask(__name__)
CORS(app)
app.secret_key = "mySecret"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL',
                                                       'sqlite:///data.db')
api = Api(app)
db.init_app(app)


@app.before_first_request
def create_db():
    db.create_all()
    # User('deep', 'admin', 0, None).make_dev_user()


jwt = JWTManager(app)


@jwt.user_claims_loader
def add_claims_to_jwt(identity):
    claims = {}
    # claims['logged_in_user_id'] = identity
    claims['admin'] = User.find_by_id(identity).is_user_admin()
    claims['manager'] = User.find_by_id(identity).is_user_manager()
    return claims


@jwt.token_in_blacklist_loader
def token_in_blacklist(decrypted_token):
    return decrypted_token['jti'] in BLACKLIST


@jwt.expired_token_loader
def expired_token_callback(reason):
    return {
        'resp': reason,
        'msg': 'Token has expired',
        'err': 'EXPIRED_TOKEN_ERR'
    }, 401


@jwt.invalid_token_loader
def invalid_token_callback(reason):
    return {
        'resp': reason,
        'msg': 'Token signatute verification failed',
        'err': 'INVALID_TOKEN_ERR'
    }, 401


@jwt.unauthorized_loader
def no_token_callback(reason):
    return {
        'resp': reason,
        'msg': 'No token found',
        'err': 'UNDEFINED_TOKEN_ERR'
    }, 401


@jwt.needs_fresh_token_loader
def non_fresh_token_callback():
    return {
        'msg': 'Fresh token required for verification',
        'err': 'NEED_FRESH_TOKEN_ERR'
    }, 403


@jwt.revoked_token_loader
def revoked_token_callback():
    return {
        'msg': 'Token has been revoked',
        'err': 'REVOKED_TOKEN_ERR'
    }, 401


class HomeRes(Resource):
    def get(self):
        return {'msg': 'Affari is up and running'}, 200


api.add_resource(HomeRes, '/')
api.add_resource(TaskRes, '/tasks')
api.add_resource(UserRegisterRes, '/register')
api.add_resource(UserLoginRes, '/login')
api.add_resource(UserLogout, '/logout')
api.add_resource(ProjectRes, '/projects')
api.add_resource(ProjectAllocate, '/assignmember')
api.add_resource(ProjectMembers, '/project_members/<int:project_id>')
api.add_resource(TokenRefresh, '/refresh')

if __name__ == "__main__":
    app.run(debug=True)
