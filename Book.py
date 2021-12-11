
#IS211 Final Project 
#This app will support 2 logins here are username and password in the DB. They are:

# 1st login credentials:

# username - admin 
# password - password

# 2nd login credentials:

# username - agreen
# password - password 

#importing required libraries:
from flask import Flask, render_template, redirect, request, session, g
import  sqlite3
from sqlite3 import Error
import os
import urllib3
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

from flask import g

#connect to the databse
DATABASE = 'bookcatalogue.db'

def get_db():
    #Opens a new database connection if there is none yet for the current application context.
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE) #sqlite3 
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def insert_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    get_db().commit()
    cur.close()
    return None

@app.teardown_appcontext
#Closes the database again at the end of the request.
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/") #route 1
def index():   
    return redirect("/login")

@app.route("/login", methods = ["POST", "GET"]) #creating a route for login
def login():           
    error = ""
    user_lookup = ""
    if request.method == "POST":
        session.pop('user', None)
        query = ""
        try:
            
            for user in query_db('Select * From users Where users.user_name= ? And users.user_password= ?', [str(request.form['uname']), str(request.form['psw'])]):
                user_lookup = str(user[0]) 
            
            #check for the username 
            if user_lookup:
                session['user'] = request.form['uname']
                return redirect("/dashboard/" + user_lookup)
            #if incorrect then display an error
            else:
                error = "Invalid Username or Password"
        except Error as e:
            error = e
        
    return render_template("login.html", error = error) #return to the html page

@app.before_request
#Opens the database at the beginning of the request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']
    
#Function to create dashboard route and select books from catalogue.      
@app.route("/dashboard/<userid>", methods = ["GET"]) #creating a route for dashboard
def dashboard(userid):
    user_lookup = userid
    user_loggedin = ""
    error = ""
    book_data = ""
    no_books_msg = ""
    try:        
        for user in query_db('Select * From users Where users.id= ?', [user_lookup]):
            user_loggedin = str(user[1]) + " " + str(user[2])

        book_data_all = query_db('select * from userbooks Join users on userbooks.user_id = users.id Join books on userbooks.book_id = books.id Where users.id= ?',[user_lookup])
        if book_data_all:
            no_books_msg = ""
        else:
            no_books_msg = "You have no books in your catalogue. Please click on the Add Books button"
            
    except Error as e:
        error = e        
        
    if g.user:        
        return render_template("dashboard.html", user_loggedin = user_loggedin, user_lookup = user_lookup, error = error, book_data_all = book_data_all, no_books_msg = no_books_msg)
    return render_template("login.html")
    
#Function Searches Google Books by ISBN via API
@app.route("/book/add/<userid>/<username>", methods = ["POST", "GET"]) 
def addbook(userid,username):
    userid = userid
    username = username
    lookuperror = ""
    jsondata = ""
    book_num = ""
    book_exist = ""
    isblookupgoogle = "https://www.googleapis.com/books/v1/volumes?q=isbn:" #linking the google API 
    if request.method == "POST":
        if request.form['btn'] == 'lookup':            
            try:
                lookupurl = isblookupgoogle + str(request.form['isbn'])
                response = urllib3.urlopen(lookupurl)
                responsedata = response.read()
                jsondata = json.loads(responsedata)
            except:            
                lookuperror = "An error occured during the lookup process"
            if jsondata:
                try:                    
                    bookdata = jsondata['items'][0]['volumeInfo']
                except:
                    bookdata = "N/A"
                try:
                    bookisbn = bookdata['industryIdentifiers'][0]['identifier']                    
                except:
                    bookisbn = "N/A"
                    
                try:                    
                    booktitle = bookdata['title']
                except:
                    booktitle = "N/A"
                    
                try:                    
                    bookauthor = bookdata['authors'][0]
                except:
                    bookauthor = "N/A"

                try:                    
                    bookpagecount = bookdata['pageCount']
                except:
                    bookpagecount = "N/A"

                try:
                    bookrating = bookdata['averageRating']
                except:
                    bookrating = "N/A"

                try:                    
                    booktumbnail = bookdata['imageLinks']['smallThumbnail']
                except:
                    booktumbnail = "N/A"
                if bookdata != "N/A":
                    try:
                        for book in query_db('Select * From books Where books.book_isbn= ?', [str(request.form['isbn'])]):                            
                            book_num = book[1]
                        if book_num:
                            for user_book in query_db('Select * From userbooks Where userbooks.user_id= ? And userbooks.book_id= ?', [userid, book[0]]):
                                book_exist = user_book[0]
                            if book_exist:
                                lookuperror = "You Already Have This Book In Your Catalogue"
                                return render_template("Book.html", lookuperror = lookuperror, username = username, userid = userid)
                            else:                
                                insert_db('Insert Into userbooks(user_id, book_id) values(?,?)', [userid, book[0]])
                                return redirect("/dashboard/" + userid)
                        else:
                            insert_a = "Insert Into books (book_isbn, book_title, book_author, book_page_count, book_average_rating, book_tumbnail) values (?,?,?,?,?,?)"
                            insert_db(insert_a, [str(request.form['isbn']), str(booktitle), str(bookauthor), str(bookpagecount), str(bookrating), str(booktumbnail)])
                            for book in query_db('Select * From books Where books.book_isbn= ?', [str(request.form['isbn'])]):                                
                                book_num = book[1]
                            insert_db('Insert Into userbooks(user_id, book_id) values(?,?)', [userid, book[0]])
                            return redirect("/dashboard/" + userid)
                    except:
                        lookuperror = "An Error Occurred During The Add Process"
                        return render_template("Book.html", lookuperror = lookuperror, username = username, userid = userid)                    
                    
                else:
                    lookuperror = "An error occured during the lookup process"
                    
    if g.user:        
        return render_template("Book.html", lookuperror = lookuperror, username = username, userid = userid)
    return render_template("login.html")

#Function to delete the book from the catalogue
@app.route("/deletebook/<userid>/<bookid>")
def deletebook(userid, bookid):
    insert_db('Delete From userbooks Where user_id =? And book_id =?', [userid, bookid])

    return redirect("/dashboard/" + userid)
    
@app.route("/dropsession")
def dropsession():
    session.pop('user', None)
    return render_template("login.html")

if __name__ == "__main__": 
    app.run(debug=True)
#end of the code