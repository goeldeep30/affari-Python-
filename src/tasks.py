from enum import Enum
from flask_restful import Resource, request, reqparse
from flask_jwt import jwt_required

import sqlite3


class TaskStatus(Enum):
    BLOCKED = 0
    TODO = 1
    INPROGRESS = 2
    DONE = 3


class Task:
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

    @classmethod
    def find_by_taskID(cls, tID):
        connection = sqlite3.connect('data.db')
        cursor = connection.cursor()

        query = "SELECT * FROM tasks WHERE id=?"
        result = cursor.execute(query, (tID,))
        row = result.fetchone()
        if row:
            task = cls(*row)
        else:
            task = None

        connection.close()
        return task

class TaskRes(Resource):
    # @jwt_required()
    def get(self):
        connection = sqlite3.connect('data.db')
        cursor = connection.cursor()

        query = "SELECT * FROM tasks"
        tasks = [Task(*res).__dict__ for res in cursor.execute(query)]
        return {'tasks': tasks}, 200

    def post(self):
        data = request.get_json()
        if Task.find_by_taskID(data['_id']):
            return {'message':'Duplicate task'}, 400

        connection = sqlite3.connect('data.db')
        cursor = connection.cursor()
        query = 'INSERT INTO tasks VALUES(NUll,?,?)'
        cursor.execute(query, (data['subj'], data['status']))
        connection.commit()
        connection.close()
        return {'message': 'Task Created Successfully'}, 200

    def put(self):
        data = request.get_json()
        tsk = Task.find_by_taskID(data['_id'])
        if tsk:
            connection = sqlite3.connect('data.db')
            cursor = connection.cursor()
            query = 'UPDATE tasks SET status = ? where id = ?'
            cursor.execute(query, (data['status'], data['_id']))
            connection.commit()
            connection.close()
            return {'message':'status updated successfully'}, 200

        return {'message': 'Can not find task'}, 400

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('_id',
                            type=int,
                            required=True,
                            help='Need a ID in ')
        data = parser.parse_args()
        tsk = Task.find_by_taskID(data['_id'])
        if tsk:
            connection = sqlite3.connect('data.db')
            cursor = connection.cursor()
            query = 'DELETE FROM tasks where id = ?'
            cursor.execute(query, (data['_id'],))
            connection.commit()
            connection.close()
            return {'message':'Task Deleted successfully'}, 202

        return {'message': 'Can not find task'}, 400


if __name__ == "__main__":
    import pdb
    pdb.set_trace()
    t = Task(111, 'demo', TaskStatus.TODO.value)
    print(t)
