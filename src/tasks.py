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
    def __init__(self, _id: int, subj: str, status: TaskStatus):
        """[summary]

        Arguments:
            _id {int} -- [description]
            subj {str} -- [description]
            status {TaskStatus} -- [description]
        """
        self.id = _id
        self.subject = subj
        self.status = status

    @classmethod
    def find_by_taskID(cls, tID):
        connection = sqlite3.connect('data.db')
        cursor = connection.cursor()

        query = "SELECT * FROM users WHERE username=?"
        # result = cursor.execute(query, (username,))
        row = result.fetchone()
        if row:
            user = cls(*row)
        else:
            user = None

        connection.close()
        return user


tsks = [
    Task(111, 'demo1', TaskStatus.TODO.value).__dict__
]


class TaskRes(Resource):
    # @jwt_required()
    def get(self):
        return {'tasks': tsks}, 200

    def post(self):
        data = request.get_json()
        task = Task(**data)
        tsks.append(task.__dict__)
        return {'message': 'task created'}, 201

    def put(self):
        data = request.get_json()
        _id = data.get('_id', None)
        status = data.get('status', None)
        for tsk in tsks:
            if tsk['id'] == _id:
                tsk['status'] = status
                return {'message': 'status updated'}, 202
        return {'message': 'Can not find task'}, 400

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('_id',
                            type=int,
                            required=True,
                            help='Need a ID in ')
        data = parser.parse_args()

        # data = request.get_json()
        _id = data.get('_id', None)
        for tsk in tsks:
            if tsk['id'] == _id:
                tsks.remove(tsk)
                return {'message': 'Task removed'}, 202
        return {'message': 'Can not find task'}, 400


if __name__ == "__main__":
    import pdb
    pdb.set_trace()
    t = Task(111, 'demo', TaskStatus.TODO.value)
    print(t)
