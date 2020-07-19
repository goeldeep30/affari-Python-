from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.utility import TaskStatus
from src.db import db


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(80))
    description = db.Column(db.String(500))
    status = db.Column(db.Integer)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, subject: str, description: str, status: TaskStatus,
                 project_id: int, user_id: int, id: int = None):
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
        self.status = status
        self.description = description
        self.project_id = project_id
        self.user_id = user_id

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
        return {'id': self.id,
                'subject': self.subject,
                'description': self.description,
                'status': self.status,
                'project_id': self.project_id,
                'user_id': self.user_id,
                }


class TaskRes(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('subject', type=str, required=True,
                        help='Subject Required')
    parser.add_argument('description', type=str, required=True,
                        help='Task description Required')
    parser.add_argument('status', type=str, required=True,
                        help='Status Required')
    parser.add_argument('project_id', type=int, required=True,
                        help='Project ID Required')
    parser.add_argument('user_id', type=int, required=True,
                        help='User ID Required')

    @jwt_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('project_id', type=int, required=True,
                            help='Project ID Required')
        data = parser.parse_args()
        current_user = get_jwt_identity()
        shared_filter = {'user_id': current_user,
                         'project_id': data['project_id']}
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

    @jwt_required
    def post(self):
        data = TaskRes.parser.parse_args()
        # if Task.find_by_taskID(data['id']):
        #     return {'msg': 'Duplicate task'}, 400

        Task(**data).save_to_db()
        return {'msg': 'Task created successfully'}, 200

    @jwt_required
    def put(self):
        TaskRes.parser.add_argument('id', type=str, required=True,
                                    help='ID Required')
        data = TaskRes.parser.parse_args()
        TaskRes.parser.remove_argument('id')

        tsk = Task.find_by_taskID(data['id'])
        if tsk:
            tsk.subject = data['subject']
            tsk.description = data['description']
            tsk.status = data['status']
            tsk.save_to_db()
            return {'msg': 'Status updated successfully'}, 200

        # Task(**data).save_to_db()
        # return {'msg': 'Task created successfully'}, 200
        return {'msg': 'No such task found'}, 404

    @jwt_required
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, required=True,
                            help='ID Required')
        data = parser.parse_args()
        tsk = Task.find_by_taskID(data['id'])
        if tsk:
            tsk.delete_task()
            return {'msg': 'Task deleted successfully'}, 202

        return {'msg': 'Task not found'}, 404
