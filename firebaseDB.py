import pyrebase

const firebaseConfig = {
  "apiKey": "AIzaSyBVTqIXGx0BiFFnHTzPWqZws128fAQ2B1c",
  "authDomain": "dsci351-4624a.firebaseapp.com",
  "databaseURL": "https://dsci351-4624a-default-rtdb.firebaseio.com",
  "projectId": "dsci351-4624a",
  "storageBucket": "dsci351-4624a.appspot.com",
  "messagingSenderId": "706659319452",
  "appId": "1:706659319452:web:498a8f3b97bfa9ba177759",
  "measurementId": "G-8BYLQPJ4ZG"
};
#initialize database
firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

#path to update (should be changed later to reflect correct path)
data_path = "/user/fight_on"

# Example of data format
new_data = {
    "age": 21,
    "name": "Tommy Trojan",
    "password": "123",
    "username": "fight_on"
}

# Update data
db.child(data_path).update(new_data)
