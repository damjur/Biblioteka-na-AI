from flask import flash
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, IntegerField, TextAreaField, SubmitField, HiddenField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, URL, Email
from wtforms.fields.html5 import URLField

from ..models import Book,BookData

class UrlBookForm(FlaskForm):
	url = URLField('Goodreads page', validators=[DataRequired(), URL()])
	submit = SubmitField('Fill form')
	
class InvitationForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	submit = SubmitField('Send invitation')
	
class BorrowInsideForm(FlaskForm):
	insider = QuerySelectField(query_factory=lambda: current_user.allowed_users.all(),
                                  get_label="username")
	submit = SubmitField('Submit')

class BookForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])
	author = StringField('Author', validators=[DataRequired()])
	pages = IntegerField('Number of pages')
	comment = TextAreaField('Comment')
	conf = HiddenField('Confirm')
	submit = SubmitField('Submit')
	
	def __init__(self,id,*args,**kwargs):
		FlaskForm.__init__(self,*args,**kwargs)
		self.id = id
	
	def validate(self):
	
		x = FlaskForm.validate(self)
		if not x:
			return False
	
		data = BookData.query.filter_by(title=self.title.data, author= self.author.data , pages=self.pages.data).first()
		book = Book.query.filter_by(owner_id=self.id , data = data).first()

		if book and self.conf.data=='':
			self.conf.data = 'F'
			flash('Thither already exists such a book. Submit again to proceed.','warning')
			return False
			
		return True
			
			
			
			
			
			
			
			
			
			
			
			
			
			
