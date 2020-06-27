from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required
from src.utility import TaskStatus
from src.db import db


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(80))
    status = db.Column(db.Integer)

    def __init__(self, subject: str, status: TaskStatus, id: int = None):
        """[summary]

        Arguments:
            _id {int} -- [description]
            subj {str} -- [description]
            status {TaskStatus} -- [description]
        """
        self.id = id
        self.subject = subject
        self.status = status

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
                'status': self.status
                }


class TaskRes(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('subject', type=str, required=True,
                        help='Subject Required')
    parser.add_argument('status', type=str, required=True,
                        help='Status Required')

    @jwt_required
    def get(self):
        tsks = []
        for task in Task.query.all():
            tsks.append(
                task.json()
            )
        return {'tasks': tsks}, 200

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
