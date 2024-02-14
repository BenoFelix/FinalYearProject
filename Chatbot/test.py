import nltk
import string
import random
from pymongo import MongoClient
import warnings
from fuzzywuzzy import fuzz

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

nltk.download('punkt')
nltk.download('stopwords')

client = MongoClient("mongodb://localhost:27017/")
database = client["dummy"]
collection = database["sample"]

lem = nltk.stem.WordNetLemmatizer()
remove_punc_dict = dict((ord(punc), None) for punc in string.punctuation)


def LemToken(tokens):
    return [lem.lemmatize(token) for token in tokens]


def LemNormal(text):
    return LemToken(nltk.word_tokenize(text.lower().translate(remove_punc_dict)))


greet_inputs = ('hello', 'hi', 'whassup', 'how are you?')
greet_responses = ('hi', 'Hey', 'Hey There!', 'There there!!')


def greet(sentence):
    for word in nltk.word_tokenize(sentence):
        if word.lower() in greet_inputs:
            return random.choice(greet_responses)


def get_keywords(user_response, scheme_data):
    user_keywords = [word.lower() for word in nltk.word_tokenize(user_response)]

    scheme_names = [scheme["scheme_name"].lower() for scheme in scheme_data]

    return user_keywords + scheme_names


def response(user_response, scheme_data):
    robo1_response = ''
    matched_schemes = []

    for scheme in scheme_data:
        if scheme["scheme_name"].lower() in user_response:
            matched_schemes.append(scheme)

    if not matched_schemes:
        for scheme in scheme_data:
            scheme_keywords = scheme.get("keywords", [])
            if any(keyword.lower() in user_response.lower() for keyword in scheme_keywords):
                matched_schemes.append(scheme)

    if len(matched_schemes) == 1:
        scheme = matched_schemes[0]
        robo1_response = f'Here are the details for the matched scheme - {scheme["scheme_name"].capitalize()}'
        for key, value in scheme.items():
            if key != "_id" and key != "keywords":
                robo1_response += f'\n{key.capitalize()}: {value}'
    elif len(matched_schemes) > 1:
        robo1_response = "Multiple schemes matched. Please type the number of the scheme you want to know more about:\n"
        for i, scheme in enumerate(matched_schemes, 1):
            robo1_response += f"{i}. {scheme['scheme_name'].capitalize()}\n"

        try:
            selected_number = int(input(robo1_response))
            if 1 <= selected_number <= len(matched_schemes):
                scheme = matched_schemes[selected_number - 1]
                robo1_response = f'Here are the details for the matched scheme - {scheme["scheme_name"].capitalize()}'
                for key, value in scheme.items():
                    if key != "_id" and key != "keywords":
                        if isinstance(value, dict):
                            robo1_response += f'\n{key.capitalize()}:'
                            k = 1
                            for i, j in value.items():
                                robo1_response += f'\n  {k}. {i.capitalize()}: {j}'
                                k += 1
                        else:
                            robo1_response += f'\n{key.capitalize()}: {value}'

            else:
                robo1_response = "Invalid number. Please type a valid number."
        except ValueError:
            robo1_response = "Invalid input. Please type a number."
    else:
        robo1_response = "Scheme details not found in the database."

    return robo1_response


flag = True
scheme_data = [scheme for scheme in collection.find()]

print('Hello! I am Bot. Start typing your text. Say bye to end the conversation.')

while flag:
    user_response = input().lower()

    if user_response != 'bye':
        if user_response == 'thank you' or user_response == 'thanks':
            flag = False
            print('Bot: You are Welcome..')
        else:
            if greet(user_response):
                print('Bot: ' + greet(user_response))
            else:
                print('Bot: ', end='')
                print(response(user_response, scheme_data))
    else:
        flag = False
        print('Bot: Goodbye!')
