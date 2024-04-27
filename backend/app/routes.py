from flask import request, jsonify, current_app
from werkzeug.security import check_password_hash
from .database import db
from .models import User, ActivityLog
from flask_jwt_extended import create_access_token

def register_routes(app):
    @app.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if username is None or password is None:
            return jsonify({"message": "Missing username or password"}), 400
        if User.query.filter_by(username=username).first() is not None:
            return jsonify({"message": "User already exists"}), 400#

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201

    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        user = User.query.filter_by(username=data.get('username')).first()
        if user is None or not user.check_password(data.get('password')):
            return jsonify({'message': 'Invalid username or password'}), 401
        

        access_token = create_access_token(identity=data['username'])
        return jsonify(access_token=access_token), 200
    
    @app.route('/activity-log', methods=['POST'])
    def log_activity():
        data = request.get_json()
        if not data or 'session_id' not in data or 'event_type' not in data:
            return jsonify({"message": "Missing required data"}), 400

        new_log = ActivityLog(
            session_id=data['session_id'],
            event_type=data['event_type'],
            data=data.get('data')  # Additional data as JSON
        )
        db.session.add(new_log)
        db.session.commit()
        return jsonify({"message": "Activity logged successfully"}), 201


