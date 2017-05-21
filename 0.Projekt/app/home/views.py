from flask import render_template, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime,timedelta
from sys import exc_info

from . import home
from .. import db
from app.home.forms import BookForm, UrlBookForm, InvitationForm, BorrowInsideForm
from app.auth.token import generate_confirmation_token, confirm_token
from app.home.myParser import parse_goodreads
from app.models import User, Book, BookData, Borrow
from ..email import send_email

#-----------------------------------Access---------------------------------------------

def owner(id):
	if current_user.id == id:
		return True
	return False
	
def allowed(id):
	if current_user.user_libraries.filter_by(id=id).first() is not None:
		return True
	return False

def check_if_access_is_allowed(id):
	if not (owner(id) or allowed(id)):
		abort(403)

#-----------------------------------Homepage---------------------------------------------
		
@home.route('/', methods=['GET', 'POST'])
def homepage():
	if not current_user.is_authenticated:
		return render_template('home/index.html', title='Welcome',avgP=None,avgBM=None,avgBY=None)
	
	borrows = [ borrow for borrow in Borrow.query.filter_by(lender=current_user,borrower=current_user).all() if borrow.dateBack is not None ]
	books = [borrow.book.data for borrow in borrows ]
	count_b = len(books)
	count_p = 0
	for book in books:
		count_p += book.pages
	now = datetime.utcnow()
	delta = (now - current_user.registered_on)
	d = delta.days + delta.seconds/86400
	avgP = count_p/d
	d = d/30.25
	avgBM = count_b/d
	d = d/12
	avgBY = count_b/d
	
	for borrow in borrows:
		print(borrow)
	
	borrows.sort(key = lambda x : x.dateBack, reverse = True)
	if len(borrows)>1:
		book = borrows[0]
		book = book.book.data
		book = book.title+' by '+book.author
	else:
		book = "No book hast been read"
	
	borrowed = Borrow.query.filter_by(dateBack=None).all()
	currently_read = [borrow.book for borrow in borrowed if borrow.lender==current_user and borrow.borrower==current_user ]
	borrowedBy = [borrow for borrow in borrowed if borrow.lender!=current_user and borrow.borrower==current_user ]
	borrowedTo = [borrow for borrow in borrowed if borrow.lender==current_user and borrow.borrower!=current_user ]

	return render_template('home/index.html',id=current_user.id, title='Welcome',avgP=avgP,avgBM=avgBM,avgBY=avgBY,last_read=book,currently_read=currently_read,borrowedBy=borrowedBy,borrowedTo=borrowedTo)
	
@home.route('/library', methods=['GET', 'POST'])
def main_library():
	seen = set()
	unique = []
	for book in Book.query.all():
		if book.data not in seen:
			seen.add(book.data)
			unique.append(book)
	return render_template('home/main_library.html', title='Welcome', books=unique)
	
#-----------------------------------List---------------------------------------------
	
@home.route('/library/<int:id>', methods=['GET', 'POST'])
@login_required
def library(id):
	user = User.query.get_or_404(id)
	check_if_access_is_allowed(id)
	books = user.books.all()
	
	borrowed_books = [ b.book for b in user.borrowed if b.dateBack is None and b.book.owner_id != id]
	books = books + borrowed_books
	
	return render_template("home/library.html", title=user.username+'\'s Library', id=id, books=books)

@home.route('/befriended/<int:id>', methods=['GET','POST'])
@login_required
def befriended_libraries(id):
	if not owner(id):
		abort(403)
		
	libraries = current_user.user_libraries.all()
	users = current_user.allowed_users.all()
		
	return render_template('home/befriended_libraries.html',title="Befriended Libraries", libraries=libraries, users=users)

#-----------------------------------Create, update, delete---------------------------------------------

def adding_helper(id, form, borrow=False):
	urlForm = UrlBookForm()
	
	if form.validate_on_submit():
		bookData = BookData.query.filter_by(title=form.title.data,author=form.author.data,pages=form.pages.data).first()
		if bookData is None:
			bookData = BookData(
				title=form.title.data,
				author=form.author.data,
				pages=form.pages.data
			)
		book = Book(
			comment=form.comment.data,
			data=bookData,
			owner_id=id
		)
		
		try:
			db.session.add(book)
			db.session.commit()
			flash('Thou hast successfully added a book','success')
		except:
			for err in exc_info():
				flash("Error: {0}".format(err),'danger')
		
		if borrow:
			return read_book(id,book.id,current_user.id,True)			
		
		return redirect(url_for('home.library',id=id))

	if urlForm.validate_on_submit():
		book = parse_goodreads(id,urlForm.url.data)
		return render_template("home/book.html", title="Add a book", form=book, urlform=urlForm)
		
	return render_template("home/book.html", title="Add a book", form=form, urlform=urlForm)

@home.route('/library/<int:id>/add', methods=['GET', 'POST'])
@login_required	
def add_book(id):
	check_if_access_is_allowed(id)
	return adding_helper(id,BookForm(id))

@home.route('/library/<int:id>/import/<int:book_id>', methods=['GET', 'POST'])
@login_required	
def import_book(id, book_id):
	check_if_access_is_allowed(id)
	
	form = BookForm(id)
	book = Book.query.get_or_404(book_id)
	form.title.data = book.data.title
	form.author.data = book.data.author
	form.pages.data = book.data.pages
	
	return adding_helper(id,form)

@home.route('/library/<int:id>/edit/<int:book_id>', methods=['GET', 'POST'])	
@login_required	
def edit_book(id,book_id):
	check_if_access_is_allowed(id)
	
	book = Book.query.get_or_404(book_id)
	form = BookForm(id,obj = book)
	
	if form.validate_on_submit():
		book.data.title=str(form.title.data)
		book.data.author=str(form.author.data)
		book.data.pages=str(form.pages.data)			
			
		book.comment=str(form.comment.data)
		
		db.session.add(book)
		db.session.commit()
		flash('Thou hast successfully edited a book','success')
				
		return redirect(url_for('home.library',id=id))

	form.title.data=book.data.title
	form.author.data=book.data.author
	form.pages.data=book.data.pages
	form.comment.data=book.comment
	form.conf.data = 'F'
		
	return render_template("home/book.html", title="Edit a book", form=form, urlform=None)
	
@home.route('/library/<int:id>/delete/<int:book_id>', methods=['GET', 'POST'])
@login_required	
def delete_book(id,book_id):
	check_if_access_is_allowed(id)
	
	book = Book.query.get_or_404(book_id)
	try:
		if len(book.data.books)<2:
			db.session.delete(book.data)
		db.session.delete(book)
		db.session.commit()
		flash('Thou hast successfully deleted a book')
	except:
		for err in exc_info():
			flash("Error: {0}".format(err))
			
	return redirect(url_for('home.library',id=id))

#-----------------------------------INVITATION---------------------------------------------
	
@home.route('/library/<int:id>/invite', methods=['GET','POST'])
@login_required
def invite(id):	
	if not owner(id):
		abort(403)
		
	form = InvitationForm()
	if form.validate_on_submit():
		token = generate_confirmation_token(form.email.data)
		url = url_for('home.confirm_invitation',id=id,token=token,_external=True)
		html = render_template('home/invitation.html',invitor=current_user,confirm_url=url)
		subject = "Invitation"
		send_email(form.email.data,subject,html)
		
		flash('Thou hast successfully send an invitation to '+form.email.data,'success')
		
		return redirect(url_for('home.library',id=id))
	return render_template('home/invite.html',title='Invite',form=form)
		
@home.route('/library/<int:id>/invite/<token>', methods=['GET','POST'])
@login_required
def confirm_invitation(id,token):
	try:
		x = confirm_token(token)
		owner = User.query.get_or_404(id)
		suplicant = current_user
		suplicant.user_libraries.append(owner)
		db.session.add(suplicant)
		db.session.commit()
		flash('Thou hast gained an access to this library','success')
	except:
		for err in exc_info():
			flash("Error: {0}".format(err),'danger')
		return redirect(url_for('home.library',id=current_user.id))
	return redirect(url_for('home.library',id=id))

#-----------------------------------BORROW---------------------------------------------
@home.route('/library/<int:id>/read/<book_id>/<borrower_id>', methods=['GET','POST'])
@login_required
def read_book(id,book_id,borrower_id,out=False):
	if not owner(id):
		abort(403)
		
	if Borrow.query.filter_by(book_id=book_id,dateBack=None).first():
		flash('This book is being read right now','error')
		return redirect(url_for('home.library',id=id))
		
	borrow = Borrow()
	borrow.book_id = book_id
	if not out:
		borrow.borrower = current_user
	else:
		borrow.borrower = None
	borrow.lender_id = borrower_id

	db.session.add(borrow)
	db.session.commit()
	
	return redirect(url_for('home.library',id=id))
	
@home.route('/library/<int:id>/return/<book_id>', methods=['GET','POST'])
@login_required
def return_book(id,book_id):
	if not owner(id):
		abort(403)
	
	borrow = Borrow.query.filter_by(book_id=book_id,dateBack=None).first()
	if not borrow:
		flash('This book is not being read right now','error')
		return redirect(url_for('home.library',id=id))
		
	borrow.dateBack = datetime.utcnow()
		
	db.session.add(borrow)
	db.session.commit()
	
	if borrow.borrower is None:
		return delete_book(id,book_id)
	
	return redirect(url_for('home.library',id=id))
	
@home.route('/library/<int:id>/borrowIn/<book_id>', methods=['GET','POST'])
@login_required
def borrowIn_book(id,book_id):
	if not owner(id):
		abort(403)
		
	form = BorrowInsideForm()
	if form.validate_on_submit():
		return read_book(id,book_id,form.insider.data.id)
	return render_template('home/borrow_in.html',title="Lend a book",form=form)	

@home.route('/library/<int:id>/borrowFromOut', methods=['GET','POST'])
@login_required
def borrowFromOut_book(id):
	if not owner(id):
		abort(403)
	
	return adding_helper(id,BookForm(id),True)

@home.route('/library/<int:id>/borrowToOut/<int:book_id>', methods=['GET','POST'])
@login_required
def borrowToOut_book(id,book_id):
	if not owner(id):
		abort(403)
	
	return read_book(id,book_id,None);

@home.route('/library/<int:id>/history/<book_id>', methods=['GET','POST'])
@login_required
def history_book(id,book_id):
	check_if_access_is_allowed(id)
	
	book = Book.query.get_or_404(book_id).data
	history = Borrow.query.filter_by(book_id=book_id).all()
	
	return render_template('home/history.html',id=id,book=book,history=history)