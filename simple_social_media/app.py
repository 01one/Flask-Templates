from flask import Flask, request, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from secrets import token_hex
app = Flask(__name__)


app.secret_key = token_hex(32)

# in-memory database
users_db = {}
posts_db = []

def get_post_by_id(post_id):
    return next((post for post in posts_db if post['id'] == post_id), None)

def get_user_posts(username):
    return [post for post in posts_db if post['author'] == username]

def get_feed_posts(username):
    user = users_db.get(username)
    if not user:
        return []
    # list with following users plus current user
    feed_users = user['following'].copy()
    feed_users.append(username)
    return [post for post in posts_db if post['author'] in feed_users]

# Routes
@app.route('/')
def home():
    if 'username' not in session:
        return render_template('home.html')
    posts = get_feed_posts(session['username'])
    return render_template('feed.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users_db.get(username)
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('home'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/profile/<username>')
def profile(username):
    user = users_db.get(username)
    if not user:
        return redirect(url_for('home'))
    posts = get_user_posts(username)
    return render_template('profile.html', user=user, posts=posts)

@app.route('/post/create', methods=['POST'])
def create_post():
    if 'username' not in session:
        return redirect(url_for('login'))
    content = request.form.get('content')
    if content:
        post = {
            'id': len(posts_db) + 1,
            'author': session['username'],
            'content': content,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'likes': [],
            'comments': []
        }
        posts_db.append(post)
    return redirect(url_for('home'))

@app.route('/post/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = get_post_by_id(post_id)
    if post:
        username = session['username']
        if username in post['likes']:
            post['likes'].remove(username)
        else:
            post['likes'].append(username)
    return redirect(request.referrer or url_for('home'))

@app.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    content = request.form.get('content')
    if content and (post := get_post_by_id(post_id)):
        comment = {
            'author': session['username'],
            'content': content,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        post['comments'].append(comment)
    return redirect(request.referrer or url_for('home'))

@app.route('/follow/<username>', methods=['POST'])
def follow_user(username):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = users_db.get(session['username'])
    target_user = users_db.get(username)
    
    if current_user and target_user and username != session['username']:
        if username in current_user['following']:
            current_user['following'].remove(username)
            target_user['followers'].remove(session['username'])
        else:
            current_user['following'].append(username)
            target_user['followers'].append(session['username'])
    
    return redirect(request.referrer or url_for('home'))

if __name__ == '__main__':
    # test users
    users_db['user1'] = {
        'username': 'user1',
        'password': generate_password_hash('password123'),
        'bio': 'Hello, I am user1!',
        'followers': [],
        'following': []
    }
    users_db['user2'] = {
        'username': 'user2',
        'password': generate_password_hash('password123'),
        'bio': 'Hello, I am user2!',
        'followers': [],
        'following': []
    }
    
    app.run(debug=True)
