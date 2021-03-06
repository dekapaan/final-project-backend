import hmac
import sqlite3
import datetime

# flask modules
from flask import Flask, request
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS
from flask_mail import Mail, Message

# image upload module
import cloudinary
import cloudinary.uploader

import DNS
import validate_email

# User class for jwt
class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# initiate user table
def init_user_table():
    conn = sqlite3.connect('polaroid.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "profile_img TEXT,"
                 "bio TEXT,"
                 "email TEXT UNIQUE NOT NULL,"
                 "username TEXT UNIQUE NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


# Create product table
def init_post_table():
    conn = sqlite3.connect('polaroid.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS post("
                 "user_id INTEGER,"
                 "username,"
                 "post_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "post_img TEXT NOT NULL,"
                 "caption TEXT NOT NULL,"
                 "FOREIGN KEY (username) REFERENCES user(username),"
                 "FOREIGN KEY (user_id) REFERENCES user(user_id))")

    print('post table created successfully')
    conn.close()

# initiate comment table
def init_comment_table():
    conn = sqlite3.connect('polaroid.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS comment("
                 "comment_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "user_id,"
                 "username,"
                 "post_id,"
                 "comment TEXT NOT NULL,"
                 "seen BOOLEAN NOT NULL,"
                 "FOREIGN KEY (user_id) REFERENCES user(user_id),"
                 "FOREIGN KEY (username) REFERENCES user(username),"
                 "FOREIGN KEY (post_id) REFERENCES post(post_id))")

    print('post table created successfully')
    conn.close()

# initiate like table
def init_like_table():
    conn = sqlite3.connect('polaroid.db')
    print('opened database successfully')

    conn.execute("CREATE TABLE IF NOT EXISTS like("
                 "user_id,"
                 "post_id,"
                 "seen BOOLEAN NOT NULL,"
                 "FOREIGN KEY (user_id) REFERENCES user(user_id),"
                 "FOREIGN KEY (post_id) REFERENCES post(post_id))")
    print('like table create successfully')
    conn.close()

# initiate follow table
def init_follow_table():
    conn = sqlite3.connect('polaroid.db')
    print("opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS follow("
                 "follower INTEGER,"
                 "followed INTEGER,"
                 "seen BOOLEAN NOT NULL,"
                 "FOREIGN KEY (follower) REFERENCES user(user_id),"
                 "FOREIGN KEY (followed) REFERENCES user(user_id))")

    print('table successfully created')

    conn.close()


init_user_table()
init_post_table()
init_comment_table()
init_like_table()
init_follow_table()

# fetch users from database
def fetch_users():
    with sqlite3.connect('polaroid.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[6], data[7]))
    return new_data


# user variable
users = fetch_users()
username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


# auth function (jwt)
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

# config jwt
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

# JWT instantiation
jwt = JWT(app, authenticate, identity)

# CORS
CORS(app)

# JWT route
@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity

# Database class
class Database(object):
    def __init__(self):
        # Establishing connection to database
        self.conn = sqlite3.connect('polaroid.db')
        self.conn.row_factory = self.dict_factory
        self.cursor = self.conn.cursor()

    # renders database inquiries as key:value pairs
    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    # send registration details to user table
    def register(self, first_name, last_name, email, username, password):
        self.cursor.execute('INSERT INTO user ('
                            'first_name,'
                            'last_name,'
                            'email,'
                            'username,'
                            'password) VALUES(?, ?, ?, ?, ?)', (first_name, last_name, email,
                                                                   username, password))
        self.conn.commit()

        return "success"

    # fetches user with username as search filter
    def login(self, username):
        self.cursor.execute("SELECT * FROM user WHERE username='{}'".format(username))
        return self.cursor.fetchone()

    # fetches user with user_id as search filter
    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM user WHERE user_id='{}'".format(user_id))
        return self.cursor.fetchall()

    # update user in user table
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
            self.cursor.execute('PRAGMA foreign_keys = OFF;')
            self.cursor.execute('UPDATE comment SET username=? WHERE user_id=?;', (data.get('username'), user_id))
            self.cursor.execute('UPDATE post SET username=? WHERE user_id=?;', (data.get('username'), user_id))
            self.cursor.execute('UPDATE user SET username=? WHERE user_id=?;', (data.get('username'), user_id))
            self.cursor.execute('PRAGMA foreign_keys = ON;')
            self.conn.commit()

        if data.get('password'):
            self.cursor.execute('UPDATE user SET password=? WHERE user_id=?', (data.get('password'), user_id))
            self.conn.commit()

    # delete user from user table
    def delete_user(self, user_id):
        self.cursor.execute("DELETE FROM like WHERE user_id='{}'".format(user_id))
        self.cursor.execute("DELETE FROM dm WHERE sender ='{}'".format(user_id))
        self.cursor.execute("DELETE FROM dm WHERE receiver ='{}'".format(user_id))
        self.cursor.execute("DELETE FROM comment WHERE user_id ='{}'".format(user_id))
        self.cursor.execute("DELETE FROM post WHERE user_id ='{}'".format(user_id))
        self.cursor.execute("DELETE FROM follow WHERE follower='{}'".format(user_id))
        self.cursor.execute("DELETE FROM follow WHERE followed='{}'".format(user_id))
        self.cursor.execute("DELETE FROM user WHERE user_id='{}'".format(user_id))
        self.conn.commit()

    # add post to database
    def post(self, user_id, caption, img, username):
        cloudinary.config(cloud_name='ddvdj4vy6', api_key='416417923523248',
                          api_secret='v_bGoSt-EgCYGO2wIkFKRERvqZ0')
        upload_result = None

        app.logger.info('%s file_to_upload', img)
        if img:
            upload_result = cloudinary.uploader.upload(img)  # Upload results
            app.logger.info(upload_result)

        self.cursor.execute('INSERT INTO post (user_id, caption, post_img, username) VALUES(?, ?, ?, ?)',
                            (user_id, caption, upload_result['url'], username))
        self.conn.commit()

    # get gost from post table with post_id as filter
    def get_post(self, post_id):
        self.cursor.execute("SELECT * FROM post WHERE post_id='{}'".format(post_id))
        return self.cursor.fetchone()

    # fetch all posts
    def get_all_posts(self):
        self.cursor.execute('SELECT * FROM post')
        return self.cursor.fetchall()

    # fetch user followers, posts, and user_id and profile_img
    def get_user_info(self, username):
        user = {}
        self.cursor.execute("SELECT user_id, profile_img FROM user where username='{}'".format(username))
        user['user'] = self.cursor.fetchall()

        user['followers'] = self.get_followers(user['user'][0]['user_id'])
        user['following'] = self.get_following(user['user'][0]['user_id'])

        self.cursor.execute("SELECT * FROM post WHERE username='{}'".format(username))
        user['posts'] = self.cursor.fetchall()

        return user

    # fetch follower username and profile_img with user_id as filter
    def get_followers_info(self, user_id):
        self.cursor.execute('SELECT username, profile_img FROM user where user_id={}'.format(user_id))
        return self.cursor.fetchall()

    # fetch following username and profile_img with user_id as filter
    def get_following_info(self, user_id):
        self.cursor.execute('SELECT username, profile_img FROM user where user_id={}'.format(user_id))
        return self.cursor.fetchall()

    # fetch posts from people user is following
    def get_follow_posts(self, user_id_list):
        posts = []

        query = "SELECT * FROM post WHERE "

        for i in range(len(user_id_list)):
            if i < (len(user_id_list) - 1):
                query += 'user_id={} OR '.format(user_id_list[i])

            else:
                query += 'user_id={}'.format(user_id_list[i])
        print(query)
        self.cursor.execute(query)
        posts.append(self.cursor.fetchall())

        return posts

    # delete post from username
    def delete_post(self, post_id):
        self.cursor.execute("DELETE FROM post WHERE post_id='{}'".format(post_id))
        self.conn.commit()

    # insert follow interaction to database
    def follow(self, follower, followed):
        self.cursor.execute('INSERT into follow ('
                            'follower,'
                            'followed,'
                            'seen'
                            ') VALUES (? ,?, 0)', (follower, followed))

        self.conn.commit()

    # remove follow interaction from database
    def unfollow(self, follower, followed):
        self.cursor.execute('DELETE FROM follow WHERE followed=? and follower=?', (followed, follower))
        self.conn.commit()

    # fetch followers user_ids with user_id as filter
    def get_followers(self, user_id):
        self.cursor.execute("SELECT follower, seen FROM follow WHERE followed='{}'".format(user_id))
        followers = self.cursor.fetchall()

        return followers

    # fetch following user_ids with user_id as filter
    def get_following(self, user_id):
        self.cursor.execute("SELECT followed, seen FROM follow WHERE follower='{}'".format(user_id))
        following = self.cursor.fetchall()

        return following

    # add like to database
    def like(self, user_id, post_id):
        self.cursor.execute('INSERT INTO like('
                            'post_id,'
                            'user_id,'
                            'seen'
                            ') VALUES (?, ?, 0)', (post_id, user_id))

        self.conn.commit()

    # remove like to database
    def unlike(self, user_id, post_id):
        self.cursor.execute("DELETE FROM like WHERE post_id=? AND user_id=?", (post_id, user_id))
        self.conn.commit()

    # fetch likes
    def get_likes(self, post_id):
        self.cursor.execute("SELECT * FROM like WHERE post_id={}".format(post_id))
        return self.cursor.fetchall()

    # fetch likes by user
    def get_user_likes(self, user_id):
        self.cursor.execute("SELECT * FROM like WHERE user_id={}".format(user_id))
        return self.cursor.fetchall()

    # add comment to database
    def add_comment(self, post_id, user_id, username, comment):
        self.cursor.execute('INSERT INTO comment (user_id, username, post_id, comment, seen) VALUES (?, ?, ?, ?, 0)',
                            (user_id, username, post_id, comment))
        self.conn.commit()

    # delete comment from database
    def delete_comment(self, comment_id):
        self.cursor.execute("DELETE FROM comment WHERE comment_id={}".format(comment_id))
        self.conn.commit()

    # get comments with post_id as filter
    def get_comments(self, post_id):
        self.cursor.execute("SELECT * FROM comment WHERE post_id={}".format(post_id))
        return self.cursor.fetchall()

    # search user table for users like username_string
    def search(self, username_string):
        self.cursor.execute("SELECT * FROM user WHERE username LIKE '%{}%'".format(username_string))
        return self.cursor.fetchall()


# user endpoint
@app.route('/user/', methods=['POST'])
def register():
    response = {}
    db = Database()

    # register
    if request.method == 'POST':
        first_name = request.json['first_name']
        last_name = request.json['last_name']
        email = request.json['email']
        username = request.json['username']
        password = request.json['password']

        db.register(first_name, last_name, email, username, password)

        global users
        users = fetch_users()

        response['status_code'] = 200
        response['message'] = "User registered successfully"

    return response


# get user endpoint (login)
@app.route('/user/<username>')
def login(username):
    response = {}
    db = Database()

    if request.method == 'GET':
        response['status_code'] = 200
        response['message'] = 'User retrieved successfully'
        response['user'] = db.login(username)

    return response


@app.route('/user/<int:user_id>', methods=['GET', 'PATCH', 'PUT'])
@jwt_required()
def user(user_id):
    response = {}
    db = Database()

    # get user with user_id
    if request.method == 'GET':
        response['status_code'] = 200
        response['message'] = "User retrieved successfully"
        response['user'] = db.get_user(user_id)

    # update user
    if request.method == 'PATCH':
        incoming_data = dict(request.json)
        db.update(user_id, incoming_data)

        response['status_code'] = 200
        response['message'] = 'User details updated successfully'

    # delete user
    if request.method == 'PUT':
        db.delete_user(user_id)

        response['status_code'] = 200
        response['message'] = 'User deleted successfully'

    # update user variable
    global users
    users = fetch_users()

    return response


# search endpoint
@app.route('/search/<username_query>/')
def search(username_query):
    response = {}

    db = Database()

    if request.method == "GET":
        response['users'] = db.search(username_query)
        response['status_code'] = 200
        response['message'] = 'Search query successful'

    return response


# post endpoint
@app.route('/post/', methods=['GET', 'POST'])
@jwt_required()
def post():
    response = {}

    db = Database()

    # add post
    if request.method == 'POST':
        user_id = request.json['user_id']
        caption = request.json['caption']
        img = request.json['img']
        username = request.json['username']

        db.post(user_id, caption, img, username)
        response['status_code'] = 200
        response['message'] = 'Post made successful'

    # get posts
    if request.method == 'GET':
        response['posts'] = db.get_all_posts()

        response['status_code'] = 200
        response['message'] = 'Posts retrieved successfully'

    return response


# get all user info (posts, followers, following)
@app.route('/user-info/<username>/', methods=['GET'])
@jwt_required()
def get_user_post(username):
    response = {}

    db = Database()

    if request.method == 'GET':
        response['user'] = db.get_user_info(username)
        response['status_code'] = 200
        response['message'] = 'Posts fetched successfully'

    return response


# delete post endpoint
@app.route('/delete_post/<post_id>', methods=['PATCH'])
@jwt_required()
def delete_post(post_id):
    response = {}
    db = Database()

    if request.method == "PATCH":
        db.delete_post(post_id)
        response['status_code'] = 200
        response['message'] = "Post deleted successfully"

    return response


# follow endpoint
@app.route('/follow/<int:user_id>/', methods=['GET', 'POST', 'PATCH'])
@jwt_required()
def follow(user_id):
    response = {}

    db = Database()

    # get followers and following
    if request.method == 'GET':
        response['followers'] = db.get_followers(user_id)
        response['following'] = db.get_following(user_id)
        response['status_code'] = 200
        response['message'] = 'User follow info retrieved successfully'

    # add follow interaction
    if request.method == "POST":
        followed = request.json['followed']
        db.follow(user_id, followed)
        response['status_code'] = 200
        response['message'] = 'Follow interaction successful'

    # remove follow interaction (unfollow)
    if request.method == "PATCH":
        followed = request.json['followed']
        db.unfollow(user_id, followed)
        response['status_code'] = 200
        response['message'] = 'Unfollow interaction successful'

    return response


# get followers username profile_img endpoint
@app.route('/followers/<int:user_id>')
@jwt_required()
def get_followers_info(user_id):
    response = {}

    db = Database()

    if request.method == 'GET':
        response['followers'] = db.get_followers_info(user_id)
        response['status_code'] = 200
        response['message'] = 'Followers info retrieved successfully'

    return response


# get following username profile_img endpoint
@app.route('/following/<int:user_id>')
@jwt_required()
def get_following_info(user_id):
    response = {}

    db = Database()

    if request.method == 'GET':
        response['following'] = db.get_following_info(user_id)
        response['status_code'] = 200
        response['message'] = 'Following info retrieved successfully'

    return response


# post endpoint
@app.route('/posts/<int:user_id>', methods=['GET'])
@jwt_required()
def get_posts(user_id):
    response = {}

    db = Database()

    # get following posts
    if request.method == 'GET':
        user_follow_data = db.get_following(user_id)
        user_id_list = []

        for i in range(len(user_follow_data)):
            global user_id_lst
            user_id_list.append(int(user_follow_data[i]['followed']))

        print(user_id_list)
        response['status_code'] = 200
        response['message'] = 'posts retrieved successfully'
        response['posts'] = db.get_follow_posts(user_id_list)

    return response


# like endpoint
@app.route('/like/<int:post_id>/', methods=['GET', 'POST', 'PATCH'])
@jwt_required()
def like(post_id):
    response = {}
    db = Database()

    # get likes
    if request.method == 'GET':
        response['status_code'] = 200
        response['message'] = 'Retrieved like information successfully'
        response['like_data'] = db.get_likes(post_id)

    # add like
    if request.method == 'POST':
        user_id = request.json['user_id']
        db.like(user_id, post_id)

        response['status_code'] = 200
        response['message'] = 'Like successful'

    # remove like
    if request.method == 'PATCH':
        user_id = request.json['user_id']
        db.unlike(user_id, post_id)

        response['status_code'] = 200
        response['message'] = 'Unlike successful'

    return response


# get user likes endpoint
@app.route('/user-like/<user_id>/')
@jwt_required()
def get_liked_posts(user_id):
    response = {}

    db = Database()

    if request.method == 'GET':
        response['likes'] = db.get_user_likes(user_id)
        response['status_code'] = 200
        response['message'] = 'Likes retrieved successfully'

    return response


# comment endpoint (add)
@app.route('/comment/', methods=['POST'])
@jwt_required()
def comment():
    response = {}
    db = Database()

    # add comment
    if request.method == 'POST':
        post_id = request.json['post_id']
        comment = request.json['comment']
        user_id = request.json['user_id']
        username = request.json['username']

        db.add_comment(post_id, user_id, username, comment)

        response['status_code'] = 200
        response['message'] = 'Comment added successfully'

    return response


# comment endpoint (delete)
@app.route('/comment/<int:comment_id>/', methods=['PATCH'])
@jwt_required()
def delete_comment(comment_id):
    response = {}
    db = Database()

    # delete comment
    if request.method == 'PATCH':
        db.delete_comment(comment_id)

        response['status_code'] = 200
        response['message'] = 'Comment deleted successfully'

    return response


# comment endpoint (post specific)
@app.route('/comment/<int:post_id>/', methods=['GET'])
@jwt_required()
def get_comment(post_id):
    response = {}
    db = Database()

    if request.method == 'GET':
        response['comment'] = db.get_comments(post_id)
        response['status_code'] = 200
        response['message'] = 'Comments retrieved successfully'

    return response


# run app
if __name__ == '__main__':
    app.run(debug=True)