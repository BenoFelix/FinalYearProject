import random
import string
import nltk
import pymongo
from flask import Flask, request, jsonify, render_template, url_for, redirect, flash
from pymongo import MongoClient
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from flask_bcrypt import Bcrypt
from extra_functions import encrypt, decrypt, mail, final_encrypt
from bson import ObjectId, json_util

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


# Define a global variable to store the selected scheme temporarily
selected_scheme = None


def generate_chatbot_response(user_message):
    global selected_scheme

    robo1_response = ''
    matched_schemes = []
    scheme_data = [scheme for scheme in collection.find()]

    greeting = greet(user_message)
    if greeting:
        return greeting

    if selected_scheme:
        # If a scheme is selected, provide its details and clear the memory
        scheme_index = int(user_message.strip()) - 1
        if 0 <= scheme_index < len(selected_scheme):
            scheme = selected_scheme[scheme_index]
            scheme_name = scheme.get("scheme_name", "").capitalize()
            robo1_response += f'\nHere are the details for the selected scheme - {scheme_name}:\n'
            for key, value in scheme.items():
                if key != "_id" and key != "keywords":
                    if isinstance(value, str):
                        robo1_response += f"{key.capitalize()}: {value}\n"
                    elif isinstance(value, dict):
                        robo1_response += f"{key.capitalize()}: \n"
                        for k, v in value.items():
                            robo1_response += f"    {k.capitalize()}: {v}\n"
            selected_scheme = None  # Clear the memory
        else:
            robo1_response = "Invalid scheme number. Please try again."
        return robo1_response

    for scheme in scheme_data:
        if scheme["scheme_name"].lower() in user_message:
            if scheme not in matched_schemes:
                matched_schemes.append(scheme)

    if not matched_schemes:
        for scheme in scheme_data:
            scheme_keywords = scheme.get("keywords", [])
            for keyword in scheme_keywords:
                if keyword.lower() in user_message.lower():
                    if scheme not in matched_schemes:
                        matched_schemes.append(scheme)

    if matched_schemes:
        if len(matched_schemes) == 1:
            # If only one scheme is matched, display its details
            scheme = matched_schemes[0]
            scheme_name = scheme.get("scheme_name", "").capitalize()
            robo1_response += f'\nHere are the details for the matched scheme - {scheme_name}:\n'
            for key, value in scheme.items():
                if key != "_id" and key != "keywords":
                    if isinstance(value, str):
                        robo1_response += f"{key.capitalize()}: {value}\n"
                    elif isinstance(value, dict):
                        robo1_response += f"{key.capitalize()}: \n"
                        for k, v in value.items():
                            robo1_response += f"    {k.capitalize()}: {v}\n"
        else:
            for i, scheme in enumerate(matched_schemes, 1):
                robo1_response += f"{i}. {scheme['scheme_name'].capitalize()}\n"

            # If multiple schemes are matched, prompt the user to select one
            robo1_response += "\nMultiple schemes matched. Please type the number of the scheme you want to know more about:\n"
            # Store the matched schemes temporarily for selection
            selected_scheme = matched_schemes
    else:
        robo1_response = "Scheme details not found in the database."

    return robo1_response


def generate_keywords(text):
    words = text.lower().split()
    keywords = set(words)
    for i in range(len(words)):
        for j in range(i + 1, len(words)):
            keywords.add("".join(words[i:j]))
            keywords.add(" ".join(words[i:j]))
    return list(keywords)


def generate_password(length=8):
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
        # Get form data
        scheme = request.form["name"]
        other = request.form["other"]
        description = request.form["description"]
        link = request.form['link']
        contact = request.form['contact']
        textbox1_values = request.form.getlist('textbox1[]')
        textbox2_values = request.form.getlist('textbox2[]')

        # Check if scheme name or other name already exists
        existing_record = collection.find_one(
            {"$or": [{"scheme_name": scheme}, {"Other Name": other}]}
        )
        if existing_record:
            flash("Scheme name or other name already exists!", 'error')
            return redirect(url_for('scheme'))

        # Generate keywords
        keywords = generate_keywords(scheme) + generate_keywords(other)

        # Create data dictionary
        data1 = {
            "scheme_name": scheme,
            "Other Name": other,
            "description": description,
            "Link": link,
            "Contact": contact,
            "keywords": keywords
        }

        # Add non-empty values from textbox fields to data1
        additional_data = {box1: box2 for box1, box2 in zip(textbox1_values, textbox2_values) if box2.strip() != ""}
        data1.update(additional_data)

        # Remove empty values from data1
        data1 = {key: value if isinstance(value, list) else value.strip() for key, value in data1.items() if
                 (isinstance(value, str) and value.strip() != "") or (
                         isinstance(value, list) and any(v.strip() != "" for v in value))}

        # Insert data into the database
        try:
            collection.insert_one(data1)
            flash('Scheme added successfully!', 'success')
        except pymongo.errors.WriteError as e:
            print(e)
            flash('Error adding scheme: {}'.format(e), 'error')

        return redirect(url_for('home'))

    return render_template("scheme.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = encrypt(request.form['email'])
        password = final_encrypt(request.form['password'])
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
        psw = generate_password()
        Password = final_encrypt(psw)
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


@app.route('/list_scheme', methods=['GET', 'POST'])
@login_required
def list_scheme():
    data = list(collection.find({}, {"_id": 1, "scheme_name": 1}))
    final_data = [(scheme['_id'], scheme.get('scheme_name', 'Unknown')) for scheme in data]
    return render_template('schemetble.html', data=final_data)


@app.route('/view/<scheme_id>', methods=['GET', 'POST'])
@login_required
def view(scheme_id):
    scheme = collection.find_one({'_id': ObjectId(scheme_id)}, {'keywords': 0})
    if not scheme:
        flash('Scheme not found!', 'error')
        return redirect(url_for('list_scheme'))
    return render_template('view_scheme.html', scheme=scheme)


@app.route('/delete/<scheme_id>', methods=['GET', 'POST'])
@login_required
def delete(scheme_id):
    scheme = collection.find_one({'_id': ObjectId(scheme_id)})
    if not scheme:
        flash('Scheme not found!', 'error')
        return redirect(url_for('list_scheme'))
    collection.delete_one({'_id': ObjectId(scheme_id)})
    return redirect(url_for('list_scheme'))


@app.route('/edit/scheme_id=<scheme_id>', methods=['GET', 'POST'])
@login_required
def edit(scheme_id):
    scheme = collection.find_one({'_id': ObjectId(scheme_id)})
    if not scheme:
        flash('Scheme not found!', 'error')
        return redirect(url_for('list_scheme'))
    return render_template('edit_scheme.html', scheme=scheme)


@app.route('/update_scheme/<scheme_id>', methods=['POST'])
@login_required
def update_scheme(scheme_id):
    # Get the scheme from the database
    scheme = collection.find_one({'_id': ObjectId(scheme_id)})
    if not scheme:
        flash('Scheme not found!', 'error')
        return redirect(url_for('list_scheme'))

    # Get form data for the main scheme fields
    scheme_data = {
        "scheme_name": request.form.get("scheme_name"),
        "other name": request.form.get("other_name"),
        "description": request.form.get("description"),
        "link": request.form.get("link"),
        "contact": request.form.get("contact"),
    }
    final_scheme = {}
    # Add additional key-value pairs from the form
    keys = request.form.getlist('key[]')
    values = request.form.getlist('value[]')
    for key, value in zip(keys, values):
        if key.strip() and value is not None and value != 'None' and value.strip():  # Check if both key and value are not empty
            scheme_data[key.strip()] = value.strip()
    for key, value in scheme_data.items():
        if key.strip() and value is not None and value != 'None' and value.strip():
            final_scheme[key.strip()] = value.strip()

    # Update the scheme in the database
    print(final_scheme)
    try:
        collection.replace_one({'_id': ObjectId(scheme_id)}, final_scheme)
        flash('Scheme updated successfully!', 'success')
    except pymongo.errors.WriteError as e:
        print(e)
        flash('Error updating scheme: {}'.format(e), 'error')

    return redirect(url_for('list_scheme'))


@login_required
@app.route('/delete_user/user_id=<user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    user = db.find_one({'_id': ObjectId(user_id)})
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('dashboard'))
    db.delete_one({'_id': ObjectId(user_id)})
    logout_user()
    flash("Your account was deleted successfully!!")
    return redirect(url_for('home'))


@login_required
@app.route('/dashboard/user_id=<user_id>', methods=['GET', 'POST'])
def dashboard(user_id):
    user = db.find_one({'_id': ObjectId(user_id)})
    if not scheme:
        flash('User not found!', 'error')
        return redirect(url_for('home'))
    Name = decrypt(user['name'])
    Email = decrypt(user['email'])
    return render_template('dashboard.html', name=Name, email=Email, id=user["_id"])


@login_required
@app.route('/change_password/user_id=<user_id>', methods=['GET', 'POST'])
def change_password(user_id):
    if request.method == 'POST':
        user = db.find_one({'_id': ObjectId(user_id)})
        psw = request.form['old_password']
        if encrypt(final_encrypt(psw)) == user['password']:
            new = request.form['new']
            retype = request.form['retype']
            if new == retype:
                password = encrypt(final_encrypt(new))
                if password == user['password']:
                    flash('Both New and Old password are same!!')
                    return redirect(url_for('change_password', user_id=current_user.id))
                else:
                    db.update_one({'_id': ObjectId(current_user.id)}, {'$set': {'password': password}})
                    flash("Password Updated Successfully!!")
                    return redirect(url_for("home"))
            else:
                flash('Both Password not matched!!')
                return redirect(url_for('change_password', user_id=current_user.id))
        else:
            flash("Old Password Wrong!!")
            return redirect(url_for('change_password', user_id=current_user.id))
    return render_template("change_password.html")


if __name__ == '__main__':
    app.run()
