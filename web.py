"""
Supporting Code for Frank's List,
an open source webapp for buying and
selling items across college campuses.

@author(s): 
Jasper Katzban, Olin '23
Jonas Kazlauskas, Olin '23
Kelly Yen, Olin '23
"""


from flask import Flask, render_template, request, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from User import *
from Item import *
from datetime import timedelta

app = Flask(__name__)
app.secret_key="JKKYJK"
app.permanent_session_lifetime = timedelta(days=2) #how long session lasts

def get_all_items():
  '''Gets all the items in Items DB
     Returns them as a list of dictionaries'''
  items = DB.collection(u'Items').stream()
  items_list = []
  for item in items:
    item_dict = item.to_dict()
    item_dict.update({'id':item.id})
    items_list.append(item_dict)
  return items_list

def login_validate(email, password):
    ''' validates login by checking for matching email and password
        Returns:
        -True/False: whether login credentials are valid
        -user.id: id of user '''

    users = DB.collection(u'Users').stream()
    for user in users:
        if user.get('password') == password and user.get('email') == email:
            return True, user.id
    return False, user.id

def check_email(email): 
    '''checks if the email a user is signing up with is approved (whether they're a student or not)
        Returns True of email is approved and not taken, returns False otherwise'''
    emails = DB.collection(u'Emails').stream()
    for e in emails:
        if email == e.get('email') and not e.get('taken'):
            return True
    return False

@app.route('/')
def splash(): 
    '''displays the landing page and prompts user to sign up or log in'''
    return render_template('index.html')

@app.route('/login')
def login():
    ''' Checks if user is already logged into a session, if not asks them to log in'''
    if "userid" in session:
        return redirect(url_for("userhome"))
    else:
        return render_template('login.html')

@app.route("/signup")
def signup():
    '''Displays sign up page'''
    return render_template("signup.html")

@app.route('/loginerror')
def loginerror():
    '''Displays an error if user logs in with invalid credentials'''
    return render_template('loginerror.html')

@app.route('/signuperror')
def signuperror():
    '''Displays an error if user signs up with invalid credentials'''
    return render_template("loginerror.html")

@app.route('/validatelogin', methods = ['POST', 'GET'])
def validate_login():
    '''validates a user's log in
    if user provided valid credentials, renders the userhome page, otherwise redirects to login error'''
    if request.method == 'POST':
       valid, userid = login_validate(request.form['email'], request.form['password'])
       if valid:
            session.permanent = True
            session['userid'] = userid
            return redirect(url_for("userhome"))
       else: 
            error = "Incorrect username or password"
            return redirect(url_for('loginerror'))
        
    return redirect(url_for('error'))

@app.route('/validatesignup', methods = ['POST', 'GET'])
def validate_signup():
    '''validates sign up by checking to make sure all fields are filled out properly, email belongs to a student, and password matches confirmed password'''
    if request.method == 'POST':
       if 0 not in {len(request.form['fname']), len(request.form['lname']), len(request.form['email']), len(request.form['school']), len(request.form['password'])}: 
            if check_email(request.form['email']) and request.form['password'] == request.form['confirmpass']:
                user=User(request.form['fname'],request.form['lname'],request.form['email'],request.form['password'],request.form['school'],request.form['phone'])
                DB.collection(u'Users').add(user.to_dict())   
                return redirect(url_for("login")) #user must log in after creating account
            else:
                error = "Invalid email or password confirmation"
                redirect(url_for('signuperror'))
       else:
            error = "Missing fields"
            return redirect(url_for('signuperror'))
            
   
    return redirect(url_for('signuperror'))

@app.route("/userhome")
def userhome():
    '''displays the user homepage, which consists of item listings and navbar'''
    if "userid" in session:
        userid = session['userid']
        first_name = DB.collection(u'Users').document(userid).get().get('fname')
        items = get_all_items()
        return render_template("userhome.html", user_id=userid, name=first_name, items = items)
    else:
        return redirect(url_for("login"))
    
@app.route("/logout")
def logout():
    '''log out of session and redirects to log in page'''
    session.pop("userid", None)
    return(redirect(url_for("login")))

@app.route("/list")
def list_item():
    '''displays form for user to list new item'''
    if 'userid' in session:
        return render_template("list.html")
    else:
        return redirect(url_for("login"))


@app.route("/item/<itemid>") 
def item(itemid):
    '''displays one item's information in depth'''
    if "userid" in session:
        userid = session['userid']
        item = DB.collection(u'Items').document(itemid).get().to_dict()
        return render_template("item.html", item=item, itemid=itemid)
    else:
        return redirect(url_for("login")) 
    


if __name__ == '__main__':
    # Configures database and gets access to the database
    cred = credentials.Certificate('ServiceAccountKey.json')
    firebase_admin.initialize_app(cred)

    # Initialize the client for interfacing with the database
    DB = firestore.client()

    #test if firebase connection is working
    # doc_ref = DB.collection(u'Users').limit(1)
    # try:
    #     docs = doc_ref.get()
    #     for doc in docs:
    #         print(u'Doc Data:{}'.format(doc.to_dict()))
    # except google.cloud.exceptions.NotFound:
    #     print(u'Missing data')
        
    app.run()
