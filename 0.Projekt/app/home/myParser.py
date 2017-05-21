from lxml.cssselect import CSSSelector
from lxml.html import fromstring
from lxml.etree import tostring
from urllib.request import urlopen

from app.home.forms import BookForm

def parse_goodreads(id,url):
	book = BookForm(id)

	#otwiera stronę
	html = fromstring(urlopen(url).read())

	#selektor
	sel = CSSSelector('#bookTitle')
	title = ''
	for e in sel(html):
		title = e.text.strip()
	book.title.data = title

	sel = CSSSelector('a.authorName > span:nth-child(1),span.authorName')
	author = ''
	for i,e in enumerate(sel(html)):
		if (len(sel(html)) > i+1 and sel(html)[i+1].text == '(Translator)') or e.text == '(Translator)':
			continue
		author += e.text + ', '
	author = author[:-2]
	book.author.data = author

	sel = CSSSelector('#details > div:nth-child(1) > span:nth-child(3)')
	pages = 0
	for e in sel(html):
		pages = e.text
	if pages != 0:
		pages = int(pages.replace(' pages',''))
		
	book.pages.data = pages
	
	return book
	
	
	
if __name__=="__main__":
	parse_goodreads('http://www.goodreads.com/book/show/7144.Crime_and_Punishment')