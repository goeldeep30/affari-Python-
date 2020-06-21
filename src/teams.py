from flask_restful import Resource, reqparse
from src.db import db


class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(80))
    user = db.relationship("User", lazy='dynamic')

    def __init__(self, id: int, team_name: str):
        self.id = id
        self.team_name = team_name

    @classmethod
    def find_by_team_name(cls, team_name):
        return cls.query.filter_by(team_name=team_name).first()

    def create_team(self):
        db.session.add(self)
        db.session.commit()

    def delete_team(self):
        db.session.delete(self)
        db.session.commit()

    def json(self):
        return {'id': self.id,
                'team_name': self.team_name,
                'members': [usr.json() for usr in self.user.all()]
                }


class TeamRes(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('team_name', type=str, required=True,
                        help='Team Name Required')

    def get(self):
        teams = []
        for team in Team.query.all():
            teams.append(
                team.json()
            )
        return {'Teams': teams}, 200

    def post(self):
        data = TeamRes.parser.parse_args()
        if Team.find_by_team_name(data['team_name']):
            return {'message': 'Team already exists'}, 400

        Team(id=None, **data).create_team()
        return {'message': 'Team created successfully'}, 200

    def delete(self):
        data = TeamRes.parser.parse_args()
        team = Team.find_by_team_name(data['team_name'])
        if team:
            team.delete_team()
            return {'message': 'Team deleted successfully'}, 200

        return {'message': 'Invalid Details'}, 404
