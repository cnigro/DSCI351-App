from flask import Flask, render_template, request, redirect, url_for, session
import boto3
import uuid
from firebase import firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db as firebase_db

app = Flask(__name__)
app.secret_key = 'ABCDEFG123456789'

aws_region = 'us-west-1'
access_key = ''
secret_key = ''

# Replace 'your_access_key' and 'your_secret_key' with your AWS credentials
dynamodb = boto3.resource('dynamodb', region_name=aws_region, aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)
travel_table = dynamodb.Table('content_table')

cred = credentials.Certificate("C:\\Users\\tpros\\Downloads\\dsci351-4624a-firebase-adminsdk-m1ufs-ec5baf6035.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://dsci351-4624a-default-rtdb.firebaseio.com'
})

firebase = firebase.FirebaseApplication('https://dsci-351-final-default-rtdb.firebaseio.com/', None)


# Route for home page
@app.route('/')
def home():
    return render_template('home.html')


# Route for user registration
@app.route('/action/register', methods=['POST'])
def register():
  """
    Gets called from the home.html form submit
    Adds a new user to the database

    :return: redirects to profile.html if they are successfully created and home.html if there is an error
    """
    if request.method == "POST":
        username = request.form["new-username"]
        name = request.form["new-name"]
        age = request.form["new-age"]
        password = request.form["new-password"]
        reentered_password = request.form["reenter-new-password"]

        if password == reentered_password:
            result = db_create_user(username, password, name, age)
            if result["success"]:
                session["username"] = username
                return redirect(url_for('profile'))
            else:
                return render_template('home.html', error=result["message"])
        else:
            return render_template('home.html', error="Passwords do not match")


# Route for user login
@app.route('/action/login', methods=['POST'])
def login():
  """
    Gets called from home.html form submit
    Checks to see if the user credentials are correct

    :return: redirects to profile if logged in successfully and home otherwise
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if db_check_creds(username, password):
            session["username"] = username
            return redirect(url_for('profile'))
        else:
            return render_template('home.html', error="Invalid credentials")


# Route for user logout
@app.route('/logout', methods=["POST"])
def logout():
    """
    Removes the user from the session and logs them out

    :return: redirects to the home page
    """
    if request.method == 'POST':
        session['logged_in'] = False
        session.pop('username', None)
    return redirect(url_for('home'))


# Route for user profile
@app.route('/profile')
def profile():
  """
    Displays the current user's items if they are logged in

    :return: renders profile if logged in and home otherwise
    """
    if 'username' in session:
        username = session['username']
        items = get_user_items()
        return render_template('profile.html', user=username, entry=items)
    else:
        return redirect(url_for('home'))


@app.route('/content')
def content():
  """
    Gets the user's items and displays them

    :return: renders content.html
    """
    items = get_user_items()
    return render_template('content.html', entry=items)


@app.route('/action/add_travel', methods=['POST'])
def add_travel():
  """
    Adds a new item to the dynamoDB table

    :return: Redirects back to profile so that the new item will be displayed
    """
    username = session.get('username')
    unique_id = f'{username}-{uuid.uuid4()}'
    travel_table.put_item(
        Item={
            'date': request.form['date'],
            'comments': request.form['comments'],
            'TripID': unique_id,
            'imageURL': request.form['image'],
            'location': request.form['location'],
            'rating': int(request.form['rating']),
            'username': username
        })
    return redirect(url_for('profile'))


@app.route('/action/edit_travel', methods=['POST'])
def edit_travel():
    travel_table.update_item(
        Key={
            'TripID': request.form['TripID']  # Specify the primary key of the item to update
        },
        UpdateExpression='SET #dt = :new_date, #cmt = :new_comments, #img = :new_image, #loc = :new_location, '
                         '#rt = :new_rating',
        ExpressionAttributeNames={
            '#dt': 'date',
            '#cmt': 'comments',
            '#img': 'imageURL',
            '#loc': 'location',
            '#rt': 'rating'
        },
        ExpressionAttributeValues={
            ':new_date': request.form['date'],
            ':new_comments': request.form['comments'],
            ':new_image': request.form['image'],
            ':new_location': request.form['location'],
            ':new_rating': int(request.form['rating'])
        })
    return redirect(url_for('profile'))


@app.route('/restaurants')
def restaurants():
    """
    Displays all the entries the user has

    :return: redirects to restaurants.html if user is signed in and home.html otherwise
    """
    if 'username' in session:
        username = session['username']
        items = get_restaurants()
        print(items)
        return render_template('restaurants.html', user=username, entry=items)
    else:
        return redirect(url_for('home'))


@app.route('/add_restaurant', methods=["POST"])
def add_restaurant():
    """
    Adds a new restaurant entry to the firebase database

    :return: redirects to restaurants.html
    """
    if request.method == "POST":
        username = session.get('username')
        data = {
            "username": username,
            "date": request.form['date'],
            'comments': request.form['comments'],
            'imageURL': request.form['image'],
            'location': request.form['location'],
            'rating': int(request.form['rating']),
            'name': request.form['name'],
            'item': request.form['item']
        }
        firebase.post("/Restaurants/places", data)
    return redirect(url_for('restaurants'))


# Function to check user credentials
def db_check_creds(username, password):
  """
    Checks to see if the given credentials are correct

    :param username: username to check
    :param password: password to check
    :return: returns True if the user exists and False otherwise
    """
    ref = firebase_db.reference('/user')

    user_data = ref.child(username).get()

    if user_data is None:
        return False, "User not found"  # User does not exist

    if user_data.get("password") == password:
        return True, "Credentials match"  # Username and password match
    else:
        return False, "Incorrect password"  # Password does not match


def get_user_items():
  """
    Gets the current users items from the travel table

    :return: The current users travel logs
    """
    username = session.get('username')
    response = travel_table.scan()
    items = response.get('Items', [])

    user_items = [item for item in items if item.get('username') == username]
    print(user_items)
    return user_items


# Function to create a new user
def db_create_user(username, password, name, age):
  """
    Creates a user and adds them to the table

    :param username: username to add
    :param password: password to add
    :return: Return True if the user was successfully added and False if there was an error or the user already exists
    """
    data_path = f"/user/{username}"

    data = {
        "age": age,
        "name": name,
        "password": password,  # Store the hashed password
        "username": username
    }

    # Get a reference to the Firebase database
    ref = firebase_db.reference(data_path)

    try:
        ref.set(data)
        return {"success": True, "message": "User created successfully"}  # Return success dictionary
    except Exception as e:
        return {"success": False, "message": f"Error creating user: {str(e)}"}  # Return error dictionary


def get_restaurants():
    """
    Gets all the restaurant information for the correct user and returns them

    :return: a list of dictionaries with each dictionary being one restaurant
    """
    username = session.get('username')
    result = firebase.get('/Restaurants/places', None)
    user_items = [result[restaurant] for restaurant in result if result[restaurant]['username'] == username]
    return user_items



if __name__ == '__main__':
    app.run(debug=True)
