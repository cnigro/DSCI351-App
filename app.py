from flask import Flask, render_template, request, redirect, url_for, session
import boto3

app = Flask(__name__)

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
@app.route('/register', methods=['POST'])
def register():
    if request.method == "POST":
        username = request.form["new-username"]
        password = request.form["new-password"]
        reentered_password = request.form["reenter-new-password"]
        if password == reentered_password:
            result = db_create_user(username, password)
            if result == "User created successfully":
                session["username"] = username
                return redirect(url_for("profile"))
            else:
                return render_template('home.html', error=result)
        else:
            return render_template('home.html', error="Passwords do not match")


# Route for user login
@app.route('/login', methods=['POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if db_check_creds(username, password):
            session["username"] = username
            return redirect(url_for("profile"))
        else:
            return render_template('home.html', error="Invalid credentials")


# Route for user logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


# Route for user profile
@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        items = get_user_items(username)
        return render_template('profile.html', username=username, items=items)
    else:
        return redirect(url_for('home'))


# Route for adding a new travel entry
@app.route('/add_travel', methods=['POST'])
def add_travel():
    if 'username' in session:
        username = session['username']
        data = {
            'date': request.form['date'],
            'user': username,
            'location': request.form['location'],
            'rating': int(request.form['rating']),
            'comments': request.form['comments'],
            'image_url': request.form['image']
        }
        travel_table.put_item(Item=data)
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('home'))


# Function to check user credentials
def db_check_creds(username, password):
    response = user_table.get_item(Key={'username': username})
    if 'Item' in response:
        stored_password = response['Item']['password']
        if stored_password == password:
            return True
    return False


# Function to create a new user
def db_create_user(username, password):
    response = user_table.get_item(Key={'username': username})
    if 'Item' in response:
        return "Username already exists"
    user_table.put_item(Item={'username': username, 'password': password})
    return "User created successfully"


# Function to get user's travel history
def get_user_items(username):
    response = travel_table.scan(FilterExpression=boto3.dynamodb.conditions.Attr('user').eq(username))
    return response.get('Items', [])


if __name__ == '__main__':
    app.run(debug=True)
