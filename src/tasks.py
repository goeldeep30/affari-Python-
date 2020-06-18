from enum import Enum
from flask_restful import Resource, request, reqparse
from flask_jwt import jwt_required
from db import db

import sqlite3


class TaskStatus(Enum):
    BLOCKED = 0
    TODO = 1
    INPROGRESS = 2
    DONE = 3


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(80))
    status = db.Column(db.Integer)

    def __init__(self, t_id: int, subject: str, status: TaskStatus):
        """[summary]

        Arguments:
            _id {int} -- [description]
            subj {str} -- [description]
            status {TaskStatus} -- [description]
        """
        self.id = t_id
        self.subject = subject
        self.status = status

    @ classmethod
    def find_by_taskID(cls, tID):
        return cls.query.filter_by(id=tID).first()
        # connection = sqlite3.connect('data.db')
        # cursor = connection.cursor()

        # query = "SELECT * FROM tasks WHERE id=?"
        # result = cursor.execute(query, (tID,))
        # row = result.fetchone()
        # if row:
        #     task = cls(*row)
        # else:
        #     task = None

        # connection.close()
        # return task

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()


class TaskRes(Resource):
    @ jwt_required()
    def get(self):
        # connection = sqlite3.connect('data.db')
        # cursor = connection.cursor()

        # query = "SELECT * FROM tasks"
        # tasks = [Task(*res).__dict__ for res in cursor.execute(query)]
        # # return {'tasks': tasks}, 200
        print(Task.query.filter_by().first().__dict__)
        return {'tasks': 'Task.query.filter_by()'}, 200

    @ jwt_required()
    def post(self):
        data = request.get_json()
        if Task.find_by_taskID(data['t_id']):
            return {'message': 'Duplicate task'}, 400

        # connection = sqlite3.connect('data.db')
        # cursor = connection.cursor()
        # query = 'INSERT INTO tasks VALUES(NUll,?,?)'
        # cursor.execute(query, (data['subj'], data['status']))
        # connection.commit()
        # connection.close()

        Task(**data).save_to_db()
        return {'message': 'Task Created Successfully'}, 200

    @ jwt_required()
    def put(self):
        data = request.get_json()
        tsk = Task.find_by_taskID(data['t_id'])
        if tsk:
            # connection = sqlite3.connect('data.db')
            # cursor = connection.cursor()
            # query = 'UPDATE tasks SET status = ? where id = ?'
            # cursor.execute(query, (data['status'], data['_id']))
            # connection.commit()
            # connection.close()
            Task(**data).save_to_db()
            return {'message': 'status updated successfully'}, 200

        return {'message': 'Can not find task'}, 400

    @ jwt_required()
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('t_id',
                            type=int,
                            required=True,
                            help='Need a ID in ')
        data = parser.parse_args()
        tsk = Task.find_by_taskID(data['t_id'])
        if tsk:
            # connection = sqlite3.connect('data.db')
            # cursor = connection.cursor()
            # query = 'DELETE FROM tasks where id = ?'
            # cursor.execute(query, (data['t_id'],))
            # connection.commit()
            # connection.close()
            db.session.delete(Task(**data))
            return {'message': 'Task Deleted successfully'}, 202

        return {'message': 'Can not find task'}, 400


if __name__ == "__main__":
    import pdb
    pdb.set_trace()
    t = Task(111, 'demo', TaskStatus.TODO.value)
    print(t)
