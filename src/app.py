from flask import Flask
from flask_restful import Resource, Api, request, reqparse
from tasks import Task, TaskStatus
from flask_jwt import JWT, jwt_required
from authenticate import authenticate, identity

import json

app = Flask(__name__)
app.secret_key = "mySecret"
api = Api(app)

jwt = JWT(app, authenticate, identity)

tsks = [
    Task(111, 'demo1', TaskStatus.TODO.value).__dict__
]


class task(Resource):
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


api.add_resource(task, '/tasks')

if __name__ == "__main__":
    app.run(debug=True)
