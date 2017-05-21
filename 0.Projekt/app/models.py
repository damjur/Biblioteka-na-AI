from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager

allowed_users_table = db.Table('allowed_users',
				db.Column('user_id',db.Integer,db.ForeignKey('users.id')),
				db.Column('user_library_id',db.Integer,db.ForeignKey('users.id'))
)

class User(UserMixin, db.Model):
	__tablename__ = 'users';
	
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(60), index=True, unique=True, nullable = False)
	username = db.Column(db.String(60), index=True, unique=True, nullable = False)
	password_hash = db.Column(db.String(255), nullable = False)
	confirmed = db.Column(db.Boolean, default=False, nullable = False)
	registered_on = db.Column(db.DateTime, default=datetime.now(), nullable=False)

	allowed_users = db.relationship('User',
								secondary=allowed_users_table,
								primaryjoin = (allowed_users_table.c.user_id == id),
								secondaryjoin = (allowed_users_table.c.user_library_id == id),
								backref = db.backref('user_libraries',lazy = 'dynamic'),
								lazy = 'dynamic')
	
	books = db.relationship('Book',
							backref = 'user',
							lazy = 'dynamic')
	
	@property
	def password(self):
		raise AttributeError('password is not a readable attribute.')
		
	@password.setter
	def password(self,password):
		self.password_hash = generate_password_hash(password)
		
	def verify_password(self,password):
		return check_password_hash(self.password_hash,password) and self.confirmed
	
	def __repr__(self):
		return '<User: {}>'.format(self.username)
		
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))
	

class Book(db.Model):
	__tablename__ = 'books'
	
	id = db.Column(db.Integer, primary_key=True)
	comment = db.Column(db.String(120), nullable = True)
	data = db.relationship("BookData",backref = db.backref("books", cascade="all, delete-orphan"), single_parent=True)
	data_id = db.Column(db.Integer,
						db.ForeignKey('book_data.id'),
						nullable = False)
						
	owner_id = db.Column(db.Integer,
						db.ForeignKey('users.id'),
						nullable = False)
	
	borrows = db.relationship('Borrow',
							 backref="book", 
							 cascade="all, delete-orphan" , 
							 lazy='dynamic')
	
	def __repr__(self):
		return '<Book: {}>'.format(self.comment+' '+self.data.__repr__())

class BookData(db.Model):
	__tablename__= 'book_data'
	__table_args__ = (
        db.UniqueConstraint("title", "author","pages"),
    )
	
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(60), nullable = False)
	author = db.Column(db.String(60), nullable = False)
	pages = db.Column(db.Integer, default = 0)
	
	def __repr__(self):
		return '<BookData: {}>'.format(self.title+' '+self.author)
		
class Borrow(db.Model):
	__tablename__ = 'borrows'
	
	id = db.Column(db.Integer, primary_key=True)
	dateOut = db.Column(db.DateTime, default=datetime.now())
	dateBack = db.Column(db.DateTime, nullable=True)
	
	book_id = db.Column(db.Integer,
						db.ForeignKey('books.id'),
						nullable = False)
	lender_id = db.Column(db.Integer,
						db.ForeignKey('users.id'),
						nullable = True)
	borrower_id = db.Column(db.Integer,
						db.ForeignKey('users.id'),
						nullable = True)
	#do					
	lender = db.relationship('User',
							backref="borrowed", 
							foreign_keys=[lender_id])
					
	#od
	borrower = db.relationship('User',
							backref="borrowing", 
							foreign_keys=[borrower_id])
	
	def __repr__(self):
		return '<Borrow: {}>'.format(str(self.id) + ' ' + str(self.dateOut) + ' ' + str(self.dateBack))