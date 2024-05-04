from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FloatField
from wtforms.validators import DataRequired, URL, NumberRange, Optional
from flask_ckeditor import CKEditorField


class MyMovieForm(FlaskForm):
    rating = FloatField(label='Your Rating Out Of 10 e.g 7.5',
                        validators=[NumberRange(0, 10, 'Rating should be from 0 to 10'), Optional()])
    review = StringField(label='Your Review')
    submit = SubmitField(label='Done')


class MovieTitleForm(FlaskForm):
    title = StringField(label='Movie Title', validators=[DataRequired()])
    submit = SubmitField(label='Done')


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# Create a form to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


# Create a form to add comments
class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
