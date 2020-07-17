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
                 project_desc: str, owner: int):
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
        claims = get_jwt_claims()
        if not claims['manager']:
            return {'msg': 'Manager rights needed'}, 401

        data = ProjectRes.parser.parse_args()
        if Project.find_by_project_name(data['project_name']):
            return {'msg': 'Project already exists'}, 400

        proj = Project(id=None, **data, owner=user)
        # print(User.find_by_id(user))
        proj.members.append(User.find_by_id(user))
        proj.create_project()

        return {'msg': 'Project created successfully'}, 200

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
        # user = get_jwt_identity()
        # claims = get_jwt_claims()
        # if not claims['manager']:
        #     return {'msg': 'Manager rights needed'}, 401

        data = ProjectAllocate.parser.parse_args()
        proj = Project.find_by_project_id(data['project_id'])
        if proj:
            # print(proj.json())
            # print(User.find_by_id(data['user_id']))
            proj.members.append(User.find_by_id(data['user_id']))
            proj.create_project()
            return {'msg': 'Member added to project'}, 200

        # Project(id=None, **data, owner=user).create_project()
        return {'msg': 'Project not found'}, 404


class ProjectMembers(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('project_id', type=str, required=True,
                        help='Project ID Required')

    @jwt_required
    def get(self, project_id):
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        project = Project.find_by_project_id(project_id)
        if project in user.curr_projects:
            members = [member.basicDetails() for member in project.members]
            return {'members': members}, 200
        return {'msg': 'Project not found'}, 404
