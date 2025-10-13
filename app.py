#!/usr/bin/env python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# coding: utf-8
from asg import ASGDirector
from firebase_admin import auth
from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/')
def yay():
    return {'yay?': 'yay!'}, 200


@app.route('/game', methods=['POST'])
def gameStartup():
    ret = {
        'success': False,
        'errorMsg': 'Unknown'
    }
    try:
        asg = ASGDirector()
        if 'Authorization' in request.headers:
            token = request.headers.get('Authorization').split(' ')[1]
            auth.verify_id_token(token)
        else:
            return "Unauthorized", 401

        data = request.get_json()

        # Validate required parameters
        if not data or 'game' not in data or 'gameType' not in data or 'action' not in data:
            return {'success': False, 'errorMsg': 'Missing required parameters: game, gameType, action'}, 400

        game = data['game']
        game_type = data['gameType']
        action = data['action']

        # Validate action
        if action not in ['start', 'stop']:
            return {'success': False, 'errorMsg': 'Invalid action. Must be "start" or "stop"'}, 400

        # Validate game and gameType exist in configuration
        available_games = asg.getGames()
        if game not in available_games:
            return {'success': False, 'errorMsg': 'Invalid game specified'}, 400
        if game_type not in available_games[game]:
            return {'success': False, 'errorMsg': 'Invalid gameType for specified game'}, 400

        resp = asg.scale(game, game_type, action)
        status = resp['ResponseMetadata']['HTTPStatusCode']
        if status == 200:
            ret['success'] = True
            ret['errorMsg'] = None
        else:
            ret['success'] = False
            ret['errorMsg'] = 'AWS Problems'
    except auth.InvalidIdTokenError:
        return {'success': False, 'errorMsg': 'Invalid authentication token'}, 401
    except Exception as e:
        ret['success'] = False
        ret['errorMsg'] = 'An error occurred processing your request'
        print(f"Error in gameStartup: {e}")  # Log detailed error server-side only
        return ret, 400
    return ret, status


@app.route('/allGames', methods=['GET'])
def allGames():
    try:
        asg = ASGDirector()
        ret = asg.getGames()
        status = 200
    except Exception as e:
        ret = {'success': False, 'errorMsg': 'Unable to retrieve games'}
        print(f"Error in allGames: {e}")  # Log detailed error server-side only
        status = 500
    print(ret)
    return ret, status

# @app.route('/status/<game>/<game_type>', methods=['GET'])
# def gameStatus(game, game_type):
#     ret = dict()
#     try:
#         asg = ASGDirector()
#         ret = asg.status(game, game_type)
#         status = 200
#         return ret, status
#     except Exception as e:
#         ret['success'] = False
#         ret['errorMsg'] = e
#         status = 500
#         return ret, status
