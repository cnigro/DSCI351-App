from boto3.dynamodb.conditions import Key
from flask import Flask, render_template, request, redirect, url_for, session
import boto3
import uuid

app = Flask(__name__)
app.secret_key = 'ABCDEFG123456789'

aws_region = 'us-west-1'
access_key = ''
secret_key = ''

# Replace 'your_access_key' and 'your_secret_key' with your AWS credentials
dynamodb = boto3.resource('dynamodb', region_name=aws_region, aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)
travel_table = dynamodb.Table('content_table')
user_table = dynamodb.Table('app_users')


# Route for home page
@app.route('/')
def home():
    return render_template('home.html')


# Route for user registration
@app.route('/action/register', methods=['POST'])
def register():
    if request.method == "POST":
        username = request.form["new-username"]
        password = request.form["new-password"]
        reentered_password = request.form["reenter-new-password"]

        if password == reentered_password:
            result = db_create_user(username, password)
            if result == "User created successfully":
                session["username"] = username
                return redirect(url_for('profile'))
            else:
                return render_template('home.html', error=result)
        else:
            return render_template('home.html', error="Passwords do not match")


# Route for user login
@app.route('/action/login', methods=['POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if db_check_creds(username, password):
            session["username"] = username
            return redirect(url_for('profile'))
        else:
            return render_template('home.html', error="Invalid credentials")


# Route for user logout
@app.route('/update_profile')
def update_user():
    return False


# Route for user profile
@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        items = get_user_items()
        return render_template('profile.html', user=username, entry=items)
    else:
        return redirect(url_for('home'))


@app.route('/content')
def content():
    items = get_user_items()
    return render_template('content.html', entry=items)


@app.route('/action/add_travel', methods=['POST'])
def add_travel():
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


# Function to check user credentials
def db_check_creds(username, password):
    response = user_table.get_item(Key={'username': username})
    if 'Item' in response:
        stored_password = response['Item']['password']
        if stored_password == password:
            return True
    return False


def get_user_items():
    username = session.get('username')
    response = travel_table.scan()
    items = response.get('Items', [])

    user_items = [item for item in items if item.get('username') == username]
    print(user_items)
    return user_items


# Function to create a new user
def db_create_user(username, password):
    # Check if the username already exists
    response = user_table.get_item(Key={'username': username})
    if 'Item' in response:
        return False, "Username already exists"

    # Store the user data in the table
    try:
        user_table.put_item(Item={'username': username, 'password': password})
        return True, "User created successfully"
    except Exception as e:
        # Log the exception or handle it accordingly
        print(f"Error creating user: {e}")
        return False, "Failed to create user"


if __name__ == '__main__':
    app.run(debug=True)
