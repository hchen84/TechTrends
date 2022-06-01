import sqlite3
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging
import os
import json


def get_db_connection():
    """
    Function to get a database connection.
    This function connects to database with the name `database.db`
    """
    if os.path.exists("database.db"):
        connection = sqlite3.connect('database.db')
        connection.row_factory = sqlite3.Row
        app.config["DB_CONN_COUNTER"] += 1
        return connection
    else:
        app.logger.error(
            '"database.db" doesn not exist. Please run python init_db.py to create "database.db"')
        return None


def get_post_count():
    """ Function to get count of posts from db """
    connection = get_db_connection()
    if connection is None:
        return 0
    else:
        post = connection.execute('SELECT count(*) FROM posts',
                                  ).fetchone()
        connection.close()
        return post[0]


def get_post(post_id):
    """ Function to get a post using its ID """
    try:
        connection = get_db_connection()
        post = connection.execute('SELECT * FROM posts WHERE id = ?',
                                  (post_id,)).fetchone()
        connection.close()
        return post
    except:
        return None


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.config["DB_CONN_COUNTER"] = 0


@app.route('/')
def index():
    """ Define the main route of the web application """
    try:
        connection = get_db_connection()
        posts = connection.execute('SELECT * FROM posts').fetchall()
        connection.close()
        return render_template('index.html', posts=posts)
    except:
        return render_template('404.html'), 404


@app.route('/healthz')
def healthcheck():
    """ Function to check the health of app """
    if os.path.exists("database.db"):
        # response = app.response_class(
        #     response=json.dumps({"result": "OK - healthy"}),
        #     status=200,
        #     mimetype='application/json'
        # )
        app.logger.info('Status request successfull')
        return jsonify({"result": "OK - healthy"})
    else:
        app.logger.error('Status request failed')
        return jsonify({"result": "Error - Missing database.db"}, 500)


@app.route('/metrics')
def metrics():
    """ Function to get the metrics """
    global db_connection_count
    response = app.response_class(
        response=json.dumps({"status": "success", "code": 0, "data": {
                            "db_connection_count": app.config["DB_CONN_COUNTER"], "post_count": get_post_count()}}),
        status=200,
        mimetype='application/json'
    )
    app.logger.info('Metrics request successfull')
    return response


@app.route('/<int:post_id>')
def post(post_id):
    """
    Define how each individual article is rendered
    If the post ID is not found a 404 page is shown
    """
    post = get_post(post_id)
    if post is None:
        app.logger.error("post with id %s not found!", post_id)
        return render_template('404.html'), 404
    else:
        app.logger.info('%r article retrieved!', post[2])
        return render_template('post.html', post=post)


@app.route('/about')
def about():
    """ Define the About Us page """
    app.logger.info('About US request successfull!')
    return render_template('about.html')


@app.route('/create', methods=('GET', 'POST'))
def create():
    """  Define the post creation functionality """

    if not os.path.exists("database.db"):
        return render_template('404.html'), 404

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()

            app.logger.info('%r article created!', title)
            return redirect(url_for('index'))

    return render_template('create.html')


# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(
        handlers=[logging.StreamHandler()], format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s", level=logging.DEBUG,  datefmt="%Y-%m-%d %H:%M:%S")
    app.run(host='0.0.0.0', port='3111')
