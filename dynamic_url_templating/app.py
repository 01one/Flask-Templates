from flask import Flask, render_template, url_for, request, redirect, flash
from datetime import datetime
from secrets import token_hex

app = Flask(__name__)
#app.secret_key = 'set_secret_key'  # Required for flash messages
#or you can use a random secret key for security
# Generate a random secret key for session management
# This should be kept secret in a real application
# In a production environment, use a secure method to generate and store the secret key
app.secret_key = token_hex(32)


# Sample data - In a real app, this would come from a database
users = {
    'user1': {'name': 'user1', 'role': 'Admin', 'joined': '2023-01-15'},
    'user2': {'name': 'user2', 'role': 'Editor', 'joined': '2023-03-22'},
    'user3': {'name': 'user3', 'role': 'User', 'joined': '2023-06-10'}
}

posts = {
    1: {'title': 'Introduction to Flask', 'content': 'Flask is a micro web framework...', 'author': 'user1', 'date': '2023-04-10'},
    2: {'title': 'Dynamic URLs in Flask', 'content': 'Learn how to use dynamic URLs...', 'author': 'user2', 'date': '2023-05-22'},
    3: {'title': 'Flask Templates', 'content': 'Jinja2 templates allow you to...', 'author': 'user3', 'date': '2023-06-15'}
}

@app.context_processor
def inject_global_vars():
    return dict(users=users, posts=posts)

@app.route('/')
def home():
    return render_template('home.html', posts=posts)

@app.route('/user/<username>')
def profile(username):
    if username in users:
        user_data = users[username]
        user_posts = {id: post for id, post in posts.items() if post['author'] == username}
        return render_template('profile.html', username=username, user_data=user_data, user_posts=user_posts)
    else:
        flash(f"User '{username}' not found!", 'error')
        return redirect(url_for('home'))

@app.route('/post/<int:post_id>')
def show_post(post_id):
    if post_id in posts:
        post = posts[post_id]
        author = users[post['author']]
        return render_template('post.html', post_id=post_id, post=post, author=author)
    else:
        flash(f"Post #{post_id} not found!", 'error')
        return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('search.html')
    
    results = []
    for id, post in posts.items():
        if query.lower() in post['title'].lower() or query.lower() in post['content'].lower():
            results.append((id, post))
    
    return render_template('search.html', query=query, results=results)

@app.context_processor
def utility_processor():
    def current_year():
        return datetime.now().year
    return {'current_year': current_year}

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
