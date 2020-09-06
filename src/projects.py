from flask_restful import Resource, reqparse
from flask_jwt_extended import (jwt_optional, get_jwt_identity,
                                fresh_jwt_required, jwt_required,
                                get_jwt_claims)
from src.user import User
from src.db import db
from typing import List


proj_allocation = db.Table('proj_allocation',
                           db.Column('user_id', db.Integer,
                                     db.ForeignKey('users.id')),
                           db.Column('project_id', db.Integer,
                                     db.ForeignKey('projects.id')),
                           db.UniqueConstraint('user_id', 'project_id',
                                               name='UC_UID_PID')
                           )


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(80))
    project_desc = db.Column(db.String(80))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task = db.relationship("Task", backref="project", lazy='dynamic')
    members = db.relationship("User", secondary=proj_allocation,
                              backref=db.backref('curr_projects',
                                                 lazy='dynamic')
                              )

    def __init__(self, id: int, project_name: str,
                 project_desc: str, owner: int, **kwargs):
        self.id = id
        self.project_name = project_name
        self.project_desc = project_desc
        self.owner_id = owner

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
                'owner': self.owner.basicDetails()['username'],
                # 'members': [usr.json() for usr in self.members],
                # 'task': [tsk.json() for tsk in self.task.all()]
                }

    def editMembers(self, members: List):
        original_users = self.members
        updated_users = []
        if not members:
            return
        for mem in members:
            uname = mem['username']
            mem = User.find_by_username(uname)
            if mem:
                updated_users.append(mem)
        if self.owner not in updated_users:
            updated_users.append(self.owner)
        # Above line is to prevent owner to to lose ownership
        deleted_members = set(original_users) - set(updated_users)
        new_members = set(updated_users) - set(original_users)
        for member in deleted_members:
            self.members.remove(member)
        for member in new_members:
            self.members.append(member)


class ProjectRes(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('project_name', type=str, required=True,
                        help='Project Name Required')
    parser.add_argument('project_desc', type=str, required=True,
                        help='Project Description Required')
    parser.add_argument('project_members', type=dict, required=False,
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
        #     return {'msg': 'Manager rights needed'}, 403

        data = ProjectRes.parser.parse_args()
        if Project.find_by_project_name(data['project_name']):
            return {'msg': 'Project already exists'}, 400

        proj = Project(id=None, **data, owner=user)
        proj.members.append(User.find_by_id(user))
        err = []
        resp = {'msg': 'Project created successfully', 'err': err}
        if data['project_members']:
            for member in data['project_members']:
                mem = User.find_by_username(member['username'])
                if mem:
                    proj.members.append(mem)
                else:
                    err.append(member['username'])
        proj.create_project()

        return resp, 201

    @fresh_jwt_required
    def put(self):
        logged_in_user_id = get_jwt_identity()
        logged_in_user = User.find_by_id(logged_in_user_id)
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True,
                            help='Project ID Required')
        parser.add_argument('project_desc', type=str, required=True,
                            help='Project Description Required')
        parser.add_argument('project_members', type=dict, required=False,
                            action="append", help='Project Members are Required')
        data = parser.parse_args()
        project = Project.find_by_project_id(data['id'])
        if project:
            if logged_in_user is not project.owner:
                return {'msg': 'You can not update this project'}, 403
            project.editMembers(data['project_members'])
            project.project_desc = data['project_desc']
            project.create_project()
            return {'msg': 'Project updated successfully'}, 200
        return {'msg': 'No such project found in your account'}, 404

    @fresh_jwt_required
    def delete(self):
        logged_in_user_id = get_jwt_identity()
        logged_in_user = User.find_by_id(logged_in_user_id)
        # claims = get_jwt_claims()
        # if not claims['admin']:
        #     return {'msg': 'Admin rights needed'}, 403

        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True,
                            help='Project ID Required')
        data = parser.parse_args()

        project = Project.find_by_project_id(data['id'])
        if logged_in_user is not project.owner:
            return {'msg': 'You can not delete this project'}, 403
        if project:
            project.delete_project()
            return {'msg': 'Project deleted successfully'}, 200
        return {'msg': 'No such project found in your account'}, 404


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
        #     return {'msg': 'Manager rights needed'}, 403

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
