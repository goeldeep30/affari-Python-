from flask_restful import Resource, reqparse, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.projects import Project
from src.user import User
from src.utility import TaskStatus
from src.db import db
from src.utility import AccessLevel
import copy
import werkzeug


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(80))
    description = db.Column(db.String(500))
    status = db.Column(db.Integer)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, subject: str, description: str, status: TaskStatus,
                 project_id: int, user_id: int, id: int = None, **kwargs):
        """[summary]

        Args:
            subject (str): [description]
            status (TaskStatus): [description]
            project_id (int): [description]
            user_id (int): [description]
            id (int, optional): [description]. Defaults to None.
        """
        self.id = id
        self.subject = subject
        self.description = description
        self.project_id = project_id
        self.user_id = user_id
        self.status = Task.validateStatus(status)

    @ classmethod
    def find_by_taskID(cls, tID):
        return cls.query.filter_by(id=tID).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_task(self):
        db.session.delete(self)
        db.session.commit()

    def json(self):
        user = User.find_by_id(self.user_id)
        username = user.basicDetails()['username'] if user else None
        return {'id': self.id,
                'subject': self.subject,
                'description': self.description,
                'status': self.status,
                'project_id': self.project_id,
                'assigned_user': username,
                'user_id': self.user_id,
                }

    @classmethod
    def validateStatus(cls, status):
        """ To prevent status values to go beyond 0-3, if 
        so task status has defalut value 0

        Args:
            status ([int]): [status]

        Returns:
            [int]: [valid status]
        """
        if status < 0:
            status = 0
        if status > 3:
            status = 3
        return status


class TaskRes(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('subject', type=str, required=True,
                        help='Subject Required')
    parser.add_argument('description', type=str, required=False,
                        help='Task description Required')
    parser.add_argument('status', type=int, required=True,
                        help='Status Required')
    parser.add_argument('project_id', type=int, required=True,
                        help='Project ID Required')
    parser.add_argument('user_id', type=int, required=True,
                        help='User ID Required')
    parser.add_argument('ref_image', type=werkzeug.datastructures.FileStorage,
                        location='files', required=False)

    @jwt_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('project_id', type=int, required=True,
                            help='Project ID Required')
        data = parser.parse_args()
        logged_in_user_id = get_jwt_identity()
        logged_in_user = User.find_by_id(logged_in_user_id)
        proj = Project.find_by_project_id(data['project_id'])
        shared_filter = {'project_id': data['project_id']}

        if logged_in_user.has_project(proj):
            resp = {}
            tsks = []
            for task in Task.query.filter_by(status=TaskStatus.BLOCKED,
                                             **shared_filter):
                tsks.append(
                    task.json()
                )
            resp['blocked'] = tsks

            tsks = []
            for task in Task.query.filter_by(status=TaskStatus.TODO,
                                             **shared_filter):
                tsks.append(
                    task.json()
                )
            resp['to_do'] = tsks

            tsks = []
            for task in Task.query.filter_by(status=TaskStatus.INPROGRESS,
                                             **shared_filter):
                tsks.append(
                    task.json()
                )
            resp['in_progress'] = tsks

            tsks = []
            for task in Task.query.filter_by(status=TaskStatus.DONE,
                                             **shared_filter):
                tsks.append(
                    task.json()
                )
            resp['done'] = tsks
            return resp, 200
        return {'msg': 'No such project found in your account'}, 404

    @jwt_required
    def post(self):
        data = TaskRes.parser.parse_args()
        logged_in_user_id = get_jwt_identity()
        logged_in_user = User.find_by_id(logged_in_user_id)
        proj = Project.find_by_project_id(data['project_id'])
        assigned_user = User.find_by_id(data['user_id'])
        # if Task.find_by_taskID(data['id']):
        #     return {'msg': 'Duplicate task'}, 400
        if proj:
            data['id'] = None
            if (not assigned_user) or (assigned_user not in proj.members):
                return {'msg': 'Not a member of this project'}, 403
            if logged_in_user.has_project(proj):
                Task(**data).save_to_db()
                if (data['ref_image']):
                    data['ref_image'].save("assets/Projects/" +
                                           data['ref_image'].filename)
                return {'msg': 'Task created successfully'}, 200
        return {'msg': 'No such project found in your account'}, 404

    @jwt_required
    def put(self):
        parser = copy.deepcopy(TaskRes.parser)
        parser.add_argument('id', type=str, required=True,
                            help='ID Required')
        data = parser.parse_args()
        logged_in_user_id = get_jwt_identity()
        logged_in_user = User.find_by_id(logged_in_user_id)
        assigned_user = User.find_by_id(data['user_id'])
        tsk = Task.find_by_taskID(data['id'])
        proj = tsk.project if tsk else None
        if proj and tsk:
            if (not assigned_user or (assigned_user not in proj.members)):
                return {'msg': 'Not a member of this project'}, 403
            if logged_in_user.has_project(tsk.project):
                tsk.subject = data['subject']
                tsk.description = data['description']
                tsk.status = Task.validateStatus(data['status'])
                tsk.user_id = data['user_id']
                tsk.save_to_db()
                if (data['ref_image']):
                    data['ref_image'].save(
                        f"assets/Projects/{tsk.id}" +
                        data['ref_image'].filename)
                return {'msg': 'Task updated successfully'}, 200
        return {'msg': 'No such task found in this project'}, 404

    @jwt_required
    def delete(self):
        logged_in_user_id = get_jwt_identity()
        logged_in_user = User.find_by_id(logged_in_user_id)

        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True,
                            help='ID Required')
        data = parser.parse_args()
        tsk = Task.find_by_taskID(data['id'])
        if tsk and logged_in_user.has_project(tsk.project):
            assigned_user = User.find_by_id(tsk.user_id)
            if (assigned_user is not logged_in_user):
                return {'msg': 'Not a task assignee'}, 403
            tsk.delete_task()
            return {'msg': 'Task deleted successfully'}, 202
        return {'msg': 'Task not found in your account'}, 404


class TaskBulkRes(Resource):
    @jwt_required
    def post(cls):
        bb = request.get_json()
        logged_in_user_id = get_jwt_identity()
        logged_in_user = User.find_by_id(logged_in_user_id)
        # if logged_in_user.access_level == AccessLevel.DEVELOPER:
        for dataS in bb['bulkData']:
            for data in dataS:
                proj = Project.find_by_project_id(data['project_id'])
                assigned_user = User.find_by_id(data['user_id'])
                if proj:
                    data['id'] = None
                    if (not assigned_user) or (assigned_user not in proj.members):
                        print({'msg': 'Not a member of this project'}, 403)
                    if logged_in_user.has_project(proj):
                        Task(**data).save_to_db()
                        if (data.get('ref_image', None)):
                            data['ref_image'].save("assets/Projects/" +
                                                    data['ref_image'].filename)
                        print({'msg': 'Task created successfully'}, 200)
                print({'msg': 'No such project found in your account'}, 404)
