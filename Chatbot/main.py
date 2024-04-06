import random
import string
import nltk
from flask import Flask, request, jsonify, render_template, url_for, redirect
from pymongo import MongoClient
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from flask_bcrypt import Bcrypt

app = Flask(__name__, template_folder="template", static_folder="static")
bcrypt = Bcrypt(app)
app.config[
    'SECRET_KEY'] = "e9f72b93cea98af52710f2c9bcf338f4d6f7b93f5b40117d08e646606a733e1f0c078c6b872e040992bded944ea123a1ac9451e7f58a4593d57ccdcda9edb84a"
client = MongoClient('mongodb://localhost:27017/')
database = client["Dummy"]
db = database["users"]
collection = database["sample"]
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['_id']
        self.username = user_data['username']
        self.password = user_data['password']


@login_manager.user_loader
def load_user(user_id):
    user_data = db.find_one({'_id': user_id})
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
    scheme_data = [scheme for scheme in collection.find()]

    greeting = greet(user_message)
    if greeting:
        return greeting

    matched_schemes = []
    for scheme in scheme_data:
        if scheme["scheme_name"].lower() in user_message.lower():
            matched_schemes.append(scheme)

    if matched_schemes:
        if len(matched_schemes) == 1:
            # If only one scheme is matched, directly provide its details
            scheme = matched_schemes[0]
            robo1_response += f'Here are the details for the matched scheme - {scheme["scheme_name"].capitalize()}:\n'
            for key, value in scheme.items():
                if key != "_id" and key != "keywords":
                    robo1_response += f'{key.capitalize()}: '
                    # Check if value is a list
                    if isinstance(value, list):
                        for item in value:
                            robo1_response += f'\n{" " * (len(key) + 2)}{item.strip()}'
                    else:
                        description_lines = value.split('\n')
                        for line in description_lines:
                            robo1_response += f'\n{" " * (len(key) + 2)}{line.strip()}'
            robo1_response += '\n'
        else:
            # If multiple schemes are matched, ask the user to select one
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
        textbox1_values = request.form.getlist('textbox1[]')
        textbox2_values = request.form.getlist('textbox2[]')
        keyword = generate_keywords(list(scheme.split())) + generate_keywords(list(other.split()))
        data1 = {"Scheme Name": scheme, "Other Name": other,
                 "Description": request.form["description"],
                 "link": request.form['link'], "Contact": request.form['contact'], "keywords": keyword}
        data = {box1: box2 for box1, box2 in zip(textbox1_values, textbox2_values)}
        data1.update(data)
        data1 = {key: value.strip() if isinstance(value, str) else value for key, value in data1.items() if
                 (isinstance(value, str) and value.strip()) or (not isinstance(value, str))}
        collection.insert_one(data1)

        return 'Data submitted successfully!'
    return render_template("scheme.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
