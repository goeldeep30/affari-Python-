from flask_restful import Resource, reqparse
from flask_jwt_extended import (jwt_optional, get_jwt_identity,
                                fresh_jwt_required, jwt_required,
                                get_jwt_claims)
from src.user import User
from src.db import db


proj_allocation = db.Table('proj_allocation',
                           db.Column('user_id', db.Integer,
                                     db.ForeignKey('users.id')),
                           db.Column('project_id', db.Integer,
                                     db.ForeignKey('projects.id')),
                           )


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(80))
    project_desc = db.Column(db.String(80))
    # owner = db.Column(db.Integer, db.ForeignKey('users.id'))
    task = db.relationship("Task", lazy='dynamic')
    members = db.relationship("User", secondary=proj_allocation,
                              backref=db.backref('curr_projects',
                                                 lazy='dynamic')
                              )

    def __init__(self, id: int, project_name: str,
                 project_desc: str, owner: int, **kwargs):
        self.id = id
        self.project_name = project_name
        self.project_desc = project_desc
        # self.owner = owner

    @classmethod
    def find_by_project_id(cls, project_id):
        return cls.query.filter_by(id=project_id).first()

    @classmethod
    def find_by_project_name(cls, project_name):
        return cls.query.filter_by(project_name=project_name).first()

    def has_member(self, user):
        if user in self.members:
            return True
        return False

    def create_project(self):
        db.session.add(self)
        db.session.commit()

    def delete_project(self):
        db.session.delete(self)
        db.session.commit()

    def json(self):
        return {'id': self.id,
                'project_name': self.project_name,
                'project_desc': self.project_desc,
                # 'owner': self.owner,
                # 'members': [usr.json() for usr in self.members],
                # 'task': [tsk.json() for tsk in self.task.all()]
                }


class ProjectRes(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('project_name', type=str, required=True,
                        help='Project Name Required')
    parser.add_argument('project_desc', type=str, required=True,
                        help='Project Description Required')
    parser.add_argument('project_members', type=dict, required=True,
                        action="append", help='Project Members are Required')

    @jwt_optional
    def get(self):
        user = get_jwt_identity()
        projects = []
        resp = {}
        # if not user:
        #     for project in Project.query.all():
        #         projects.append(
        #             project.project_name
        #             # project.json()
        #         )
        #         resp['msg'] = 'Login for more details'
        # else:
        # print(User.query.filter_by(id=user).first().curr_projects.all())
        for project in User.find_by_id(user).curr_projects:
            projects.append(
                project.json()
            )

        resp['Projects'] = projects
        return resp, 200

    @jwt_required
    def post(self):
        user = get_jwt_identity()
        # claims = get_jwt_claims()
        # if not claims['manager']:
        #     return {'msg': 'Manager rights needed'}, 401

        data = ProjectRes.parser.parse_args()
        print(data['project_members'])
        if Project.find_by_project_name(data['project_name']):
            return {'msg': 'Project already exists'}, 400

        proj = Project(id=None, **data, owner=user)
        proj.members.append(User.find_by_id(user))
        err = []
        resp = {'msg': 'Project created successfully', 'err': err}
        for member in data['project_members']:
            mem = User.find_by_username(member['username'])
            if mem:
                proj.members.append(mem)
            else:
                err.append(member['username'])
        proj.create_project()

        return resp, 201

    @fresh_jwt_required
    def delete(self):
        claims = get_jwt_claims()
        if not claims['admin']:
            return {'msg': 'Admin rights needed'}, 401

        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True,
                            help='Project ID Required')
        data = parser.parse_args()

        project = Project.find_by_project_id(data['id'])
        if project:
            project.delete_project()
            return {'msg': 'Project deleted successfully'}, 200

        return {'msg': 'No such project found'}, 404


class ProjectAllocate(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('project_id', type=str, required=True,
                        help='Project ID Required')
    parser.add_argument('user_id', type=str, required=True,
                        help='User ID Required')

    @jwt_required
    def post(self):
        logged_in_user_id = get_jwt_identity()
        logged_in_user = User.find_by_id(logged_in_user_id)
        # claims = get_jwt_claims()
        # if not claims['manager']:
        #     return {'msg': 'Manager rights needed'}, 401

        data = ProjectAllocate.parser.parse_args()
        proj = Project.find_by_project_id(data['project_id'])
        user = User.find_by_id(data['user_id'])

        if not user:
            return {'msg': 'User not found'}, 404
        if not proj:
            return {'msg': 'Project not found'}, 404
        if logged_in_user.has_project(proj):
            proj.members.append(user)
            proj.create_project()
            return {'msg': 'Members added to project'}, 200
        # Project(id=None, **data, owner=user).create_project()
        return {'msg': 'Project not found in your account'}, 404


class ProjectMembers(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('project_id', type=str, required=True,
                        help='Project ID Required')

    @jwt_required
    def get(self, project_id):
        logged_in_user_id = get_jwt_identity()
        logged_in_user = User.find_by_id(logged_in_user_id)
        project = Project.find_by_project_id(project_id)
        if not project:
            return {'msg': 'Project not found'}, 404
        if not logged_in_user_id:
            return {'msg': 'User not found'}, 404
        if logged_in_user.has_project(project):
            members = [member.basicDetails() for member in project.members]
            return {'members': members}, 200
        return {'msg': 'Project not found in your account'}, 404
