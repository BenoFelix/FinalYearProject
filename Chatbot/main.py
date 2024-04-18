import random
import string
import nltk
from flask import Flask, request, jsonify, render_template, url_for, redirect, flash
from pymongo import MongoClient
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from flask_bcrypt import Bcrypt
from extra_functions import encrypt, encrypt_password, hash0, hash1, hash2, decrypt, mail
from bson import ObjectId

nltk.download('punkt')
app = Flask(__name__, template_folder="template", static_folder="static")
bcrypt = Bcrypt(app)
app.config[
    'SECRET_KEY'] = "e9f72b93cea98af52710f2c9bcf338f4d6f7b93f5b40117d08e646606a733e1f0c078c6b872e040992bded944ea123a1ac9451e7f58a4593d57ccdcda9edb84a"
client = MongoClient('mongodb://localhost:27017')
database = client["Dummy"]
db = database["users"]
collection = database["sample"]
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.password = user_data['password']


@login_manager.user_loader
def load_user(user_id):
    user_data = db.find_one({'_id': ObjectId(user_id)})
    return User(user_data) if user_data else None


remove_punc_dict = dict((ord(punc), None) for punc in string.punctuation)

greet_inputs = ('hello', 'hi', 'whassup', 'how are you?', "hai", "Whatsup")
greet_responses = ('hi', 'Hey', 'Hey There!', 'There there!!')


def greet(sentence):
    for word in nltk.word_tokenize(sentence):
        if word.lower() in greet_inputs:
            return random.choice(greet_responses)


def get_keywords(user_response, scheme_data):
    user_keywords = [word.lower() for word in nltk.word_tokenize(user_response)]
    scheme_names = [scheme["scheme_name"].lower() for scheme in scheme_data]
    return user_keywords + scheme_names


def generate_chatbot_response(user_message):
    robo1_response = ''
    matched_schemes = []
    scheme_data = [scheme for scheme in collection.find()]

    greeting = greet(user_message)
    if greeting:
        return greeting

    for scheme in scheme_data:
        if scheme["scheme_name"].lower() in user_message:
            matched_schemes.append(scheme)

    if not matched_schemes:
        for scheme in scheme_data:
            scheme_keywords = scheme.get("keywords", [])
            for keyword in scheme_keywords:
                if keyword.lower() in user_message.lower():
                    matched_schemes.append(scheme)

    if len(matched_schemes) == 1:
        scheme = matched_schemes[0]
        robo1_response = f'Here are the details for the matched scheme - {scheme["scheme_name"].capitalize()}:\n'
        for key, value in scheme.items():
            if key != "_id" and key != "keywords":
                if isinstance(value, str):
                    robo1_response += f"{key.capitalize()}: {value}\n"
                elif isinstance(value, dict):
                    robo1_response += f"{key.capitalize()}: \n"
                    for k, v in value.items():
                        robo1_response += f"    {k.capitalize()}: {v}\n"
    elif len(matched_schemes) > 1:
        robo1_response = "Multiple schemes matched. Please type the number of the scheme you want to know more about:\n"
        for i, scheme in enumerate(matched_schemes, 1):
            robo1_response += f"{i}. {scheme['scheme_name'].capitalize()}\n"

    else:
        robo1_response = "Scheme details not found in the database."

    return robo1_response


def generate_keywords(main_list):
    sub = [main_list[i:j] for i in range(len(main_list)) for j in range(i + 1, len(main_list) + 1)]
    m = []
    for i in sub:
        k = ''
        for j in i:
            k += j
        m.append(k)
    return m


def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")


@app.route('/chat', methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data['user_message']

    reply = generate_chatbot_response(user_message)

    return jsonify({'reply': reply})


@app.route('/scheme', methods=["GET", "POST"])
@login_required
def scheme():
    if request.method == "POST":
        scheme = request.form["name"]
        other = request.form["other"]
        existing_record = collection.find_one(
            {"$or": [{"Scheme Name": scheme}, {"Other Name": other}]}
        )
        if existing_record:
            return jsonify({"error": "Scheme name or other name already exists!"}), 400

        # Get values from the form
        description = request.form["description"]
        link = request.form['link']
        contact = request.form['contact']
        textbox1_values = request.form.getlist('textbox1[]')
        textbox2_values = request.form.getlist('textbox2[]')

        # Generate keywords
        keyword = generate_keywords(list(scheme.split())) + generate_keywords(list(other.split()))

        # Create data dictionary
        data1 = {"Scheme Name": scheme, "Other Name": other,
                 "Description": description,
                 "link": link, "Contact": contact, "keywords": keyword}

        # Add non-empty values from textbox fields to data1
        data = {box1: box2 for box1, box2 in zip(textbox1_values, textbox2_values) if box2.strip() != ""}
        data1.update(data)

        # Remove empty values from data1
        data1 = {key: value for key, value in data1.items() if value.strip() != ""}

        collection.insert_one(data1)

        return 'Data submitted successfully!'
    return render_template("scheme.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = encrypt(request.form['email'])
        salt = 'wqPDlMOPw5PChcOkwoHDn8OZw6I='
        password = hash2(hash1(hash0(encrypt(key="5b40117d08e+646606a733e=1f0c078c6b87",
                                             clear=encrypt_password(request.form['password'] + salt)))))
        user = db.find_one({"email": username})
        if user:
            if encrypt(password) == user["password"]:
                user_object = User(user)  # Create an instance of User class
                msg = "You had logged in our site."
                sub = "Login Detected!!"
                mail(request.form['email'], msg, sub)
                login_user(user_object)  # Pass the user object to login_user
                flash('Logged in successfully.')
                return redirect(url_for('home'))
            else:
                msg = "Someone is trying to log in to our site using your credentials."
                sub = "Someone is trying to log in."
                mail(request.form['email'], msg, sub)
                flash("You have entered the wrong password!")
                return render_template("login.html")

        else:
            flash("There is no account found with the given email!")
            return render_template("login.html")
    return render_template('login.html')


@login_required
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        Name = encrypt(request.form["name"])
        Email = encrypt(request.form["email"])
        user = db.find_one({"email": Email})
        salt = 'wqPDlMOPw5PChcOkwoHDn8OZw6I='
        psw = generate_password()
        print(psw)
        Password = hash2(
            hash1(hash0(encrypt(key="5b40117d08e+646606a733e=1f0c078c6b87", clear=encrypt_password(psw + salt)))))
        if user:
            flash("Email already exists!!")
            return redirect(url_for("home"))
        else:
            msg = (f"Congratulation, Your account has been Created Successfully\n"
                   f"Your account Password is : {psw}\n"
                   f"Don't Share the Password with anyone.")
            subject = "Your account has been created successfully!"
            db.insert_one({
                "email": Email,
                "name": Name,
                "password": encrypt(Password)
            })
            mail(request.form['email'], msg, subject)
            flash("Your account has been created!")
            if current_user.is_authenticated:
                return redirect(url_for("home"))
            else:
                return redirect(url_for("home"))
    return render_template('signup.html')


@app.route(f'/{encrypt("logout")}', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out!")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
