from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import current_user, login_required

import main
from website.forms import UpdateAccountForm, PostForm
import secrets
from PIL import Image
import os

from website import db
from website.models import Post, User

views = Blueprint('views', __name__)


@views.route('/home')
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', title='Home', posts=posts, user=current_user)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.split(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(main.app.root_path, 'static/profile_pics', picture_fn)

    # Resize images before upload
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@views.route('/account', methods=['POST', 'GET'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', category='success')
        return redirect(url_for('views.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', form=form, image_file=image_file)


@views.route('/')
def index():
    return render_template('index.html', title='Landing')


@views.route('/post/new', methods=['POST', 'GET'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created successfully!', category='success')
        return redirect(url_for('views.home'))
    return render_template('create_post.html', title='New post', form=form, legend='New Post')


@views.route('/int:post/<post_id>/update', methods=['POST', 'GET'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post was updated!', category='success')
        return redirect(url_for('views.post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update_Post', post=post, form=form, legend='Update Post')


@views.route('/int:post/<post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=Post.title, post=post)


@views.route('/int:post/<post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post was deleted!', category='success')
    return redirect(url_for('views.home'))


@views.route('/user/<string:username>')
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


@views.route('/about')
def about():
    return render_template('about.html', title='About')


@views.route('/contact')
def contact():
    return render_template('contact.html', title='Contacts')