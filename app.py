import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import json
import logging

# parameter to count db_connection
global db_connection_count


def get_db_connection():
    """
    Function to get a database connection.
    This function connects to database with the name `database.db`
    """
    global db_connection_count
    db_connection_count += 1
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection


def get_post_count():
    """ Function to get count of posts from db """
    connection = get_db_connection()
    post = connection.execute('SELECT count(*) FROM posts',
                              ).fetchone()
    connection.close()
    return post[0]


def get_post(post_id):
    """ Function to get a post using its ID """
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


@app.route('/')
def index():
    """ Define the main route of the web application """
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)


@app.route('/healthz')
def healthcheck():
    """ Function to check the health of app """
    response = app.response_class(
        response=json.dumps({"result": "OK - healthy"}),
        status=200,
        mimetype='application/json'
    )
    app.logger.info('Status request successfull')
    return response


@app.route('/metrics')
def metrics():
    """ Function to get the metrics """
    global db_connection_count
    response = app.response_class(
        response=json.dumps({"status": "success", "code": 0, "data": {
                            "db_connection_count": db_connection_count, "post_count": get_post_count()}}),
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
        app.logger.info('post_id {} does not exist!'.format(post_id))
        return render_template('404.html'), 404
    else:
        app.logger.info('Article "{}" retrieved!'.format(post[2]))
        return render_template('post.html', post=post)


@app.route('/about')
def about():
    """ Define the About Us page """
    app.logger.info('About US request successfull!')
    return render_template('about.html')


@app.route('/create', methods=('GET', 'POST'))
def create():
    """  Define the post creation functionality """
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

            app.logger.info('Article "{}" created!'.format(title))
            return redirect(url_for('index'))

    return render_template('create.html')


# start the application on port 3111
if __name__ == "__main__":
    db_connection_count = 0
    logging.basicConfig(
        handlers=[logging.StreamHandler()], format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s", level=logging.DEBUG,  datefmt="%Y-%m-%d %H:%M:%S")
    # handlers=[logging.FileHandler(logfile),
    #                   logging.StreamHandler()],
    app.run(host='0.0.0.0', port='3111')
