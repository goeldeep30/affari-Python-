from flask_restful import Resource, reqparse
from flask_jwt_extended import (jwt_optional, get_jwt_identity,
                                fresh_jwt_required, jwt_required,
                                get_jwt_claims)
from src.db import db


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(80))
    user = db.relationship("User", backref='projects', lazy='dynamic')

    def __init__(self, id: int, project_name: str):
        self.id = id
        self.project_name = project_name

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
                # 'members': [usr.json() for usr in self.user.all()]
                }


class ProjectRes(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('project_name', type=str, required=True,
                        help='Project Name Required')

    @jwt_optional
    def get(self):
        user = get_jwt_identity()
        print(user)
        projects = []
        resp = {}
        if not user:
            for project in Project.query.all():
                projects.append(
                    project.project_name
                    # project.json()
                )
                resp['msg'] = 'Login for more details'
        else:
            for project in Project.query.all():
                projects.append(
                    project.json()
                )

        resp['Projects'] = projects
        return resp, 200

    @jwt_required
    def post(self):
        claims = get_jwt_claims()
        if not claims['manager']:
            return {'msg': 'Manager rights needed'}, 401

        data = ProjectRes.parser.parse_args()
        if Project.find_by_project_name(data['project_name']):
            return {'msg': 'Project already exists'}, 400

        Project(id=None, **data).create_project()
        return {'msg': 'Project created successfully'}, 200

    @fresh_jwt_required
    def delete(self):
        claims = get_jwt_claims()
        if not claims['admin']:
            return {'msg': 'Admin rights needed'}, 401

        data = ProjectRes.parser.parse_args()
        project = Project.find_by_project_name(data['project_name'])
        if project:
            project.delete_project()
            return {'msg': 'Project deleted successfully'}, 200

        return {'msg': 'No such project found'}, 404
