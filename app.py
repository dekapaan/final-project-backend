import hmac
import sqlite3
import datetime

from flask import Flask, request
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS
from flask_mail import Mail, Message

import cloudinary
import cloudinary.uploader

import DNS
import validate_email

class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def init_user_table():
    conn = sqlite3.connect('polaroid.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "profile_img TEXT,"
                 "email TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


# Create product table
def init_post_table():
    conn = sqlite3.connect('polaroid.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS post("
                 "user_id"
                 "post_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "post_img TEXT NOT NULL,"
                 "caption TEXT NOT NULL,"
                 "FOREIGN KEY (user_id) REFERENCES user(user_id))")

    print('post table created successfully')
    conn.close()


def init_comment_table():
    conn = sqlite3.connect('polaroid.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS comment("
                 "user_id,"
                 "post_id,"
                 "comment TEXT NOT NULL)")

    print('post table created successfully')
    conn.close()


def fetch_users():
    with sqlite3.connect('polaroid.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[4], data[5]))
    return new_data


def authenticate(username, password):
    users = fetch_users()
    username_table = {u.username: u for u in users}
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    users = fetch_users()
    userid_table = {u.id: u for u in users}
    user_id = payload['identity']
    return userid_table.get(user_id, None)


# Initialise app
app = Flask(__name__)
app.debug = True

app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(hours=24)   # Extending token expiration

# Mail config
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "onfroz3@gmail.com"
app.config['MAIL_PASSWORD'] = "FwABUqBFLVzt78w#"
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# mail instantiation
mail = Mail(app)

jwt = JWT(app, authenticate, identity)

CORS(app)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


class Database(object):
    def __init__(self):
        self.conn = sqlite3.connect('polaroid.db')
        self.cursor = self.conn.cursor()

    def register(self, first_name, last_name, profile_img, email, username, password):
        cloudinary.config(cloud_name='ddvdj4vy6', api_key='416417923523248',
                          api_secret='v_bGoSt-EgCYGO2wIkFKRERvqZ0')
        upload_result = None

        app.logger.info('%s file_to_upload', profile_img)
        if profile_img:
            upload_result = cloudinary.uploader.upload(profile_img)  # Upload results
            app.logger.info(upload_result)

        self.cursor.execute('INSERT INTO user ('
                            'first_name,'
                            'last_name,'
                            'profile_img'
                            'email,'
                            'username,'
                            'password) VALUES(?, ?, ?, ?, ?, ?)', (first_name, last_name, upload_result['url'], email,
                                                                   username, password))
        self.conn.commit()

        return "success"

    def login(self, user_id):
        self.cursor.execute("SELECT * FROM user WHERE user_id='{}'".format(user_id))
        return self.cursor.fetchall()

    def update(self, user_id, data):
        if data.get('first_name'):
            self.cursor.execute('UPDATE user SET first_name=? WHERE user_id=?', (data.get('first_name'), user_id))
            self.conn.commit()

        if data.get('last_name'):
            self.cursor.execute('UPDATE user SET last_name=? WHERE user_id=?', (data.get('last_name'), user_id))
            self.conn.commit()

        if data.get('profile_img'):
            # Upload image to cloudinary
            cloudinary.config(cloud_name='ddvdj4vy6', api_key='416417923523248',
                              api_secret='v_bGoSt-EgCYGO2wIkFKRERvqZ0')
            upload_result = None

            app.logger.info('%s file_to_upload', data.get('profile_img'))
            if data.get('profile_img'):
                upload_result = cloudinary.uploader.upload(data.get('profile_img'))  # Upload results
                app.logger.info(upload_result)
                # data = jsonify(upload_result)
            self.cursor.execute('UPDATE user SET profile_img=? WHERE user_id=?', (upload_result['url'], user_id))
            self.conn.commit()

        if data.get('email'):
            self.cursor.execute('UPDATE user SET email=? WHERE user_id=?', (data.get('email'), user_id))
            self.conn.commit()

        if data.get('username'):
            self.cursor.execute('UPDATE user SET username=? WHERE user_id=?', (data.get('username'), user_id))
            self.conn.commit()

        if data.get('password'):
            self.cursor.execute('UPDATE user SET password=? WHERE user_id=?', (data.get('password'), user_id))
            self.conn.commit()
            response['status_code']




@app.route('/user/', methods=['GET', 'POST'])
@app.route('/user/<int:user_id>/', methods=['PUT'])
def user(user_id):
    response = {}
    db = Database()

    if request.method == 'POST':
        first_name = request.json('first_name')
        last_name = request.json('last_name')
        profile_img = request.json('profile_img')
        email = request.json('email')
        username = request.json('username')
        password = request.json('password')

        db.register(first_name, last_name, profile_img, email, username, password)

        response['status_code'] = 200
        response['message'] = "User registered successfully"

    if request.method == 'GET':
        response['status_code'] = 200
        response['message'] = "User retrieved successfully"
        response['user'] = db.login(request.json('user_id'))

    if request.method == 'PUT':
        incoming_data = dict(request.json)
        db.update(user_id, incoming_data)



