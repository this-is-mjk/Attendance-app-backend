from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson.objectid import ObjectId
from io import BytesIO
import os
import numpy as np
from deepface import DeepFace
from PIL import Image
import cv2
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import jwt
from functools import wraps




# Custom Exceptions for handling errors and returning error easily
class missing_form_data(Exception):
    # (Exception): This specifies that the new class MissingFormDataError inherits from the built-in Exception class. 
    # By inheriting from Exception and pass is to avoid syntax error of empty class.
    pass
class face_not_detected(Exception):
    pass
class user_not_found(Exception):
    pass
class something_went_wrong(Exception):
    pass
class not_admin(Exception):
    pass



### Initalisation of connections ###
#Load pretrained saved face detection model    
net = cv2.dnn.readNetFromCaffe('./saved_model/deploy.prototxt.txt', './saved_model/res10_300x300_ssd_iter_140000.caffemodel')

# create a flask app with Cors to enable local development
app = Flask(__name__)
CORS(app)

# creating the jwt secreat key, will save it in env when deploying
app.config['SECRET_KEY'] = 'this_is_mjk_secret_key'

# connect to database and open users in AttendenceApp database
client = MongoClient('localhost', 27017)
db = client.AttendenceApp
users = db.users


# Raising handelling with requests
@app.errorhandler(missing_form_data)
def handle_missing_form_data(error):
    return jsonify({'status': "Bad Request, Missing Required Data"}), 400
@app.errorhandler(face_not_detected)
def handle_face_not_detected(error):
    return jsonify({'status': "No face detected"}), 400
@app.errorhandler(user_not_found)
def handle_user_not_found(error):
    return jsonify({'status': "User not found"}), 400
@app.errorhandler(something_went_wrong)
def handle_something_went_wrong(error):
    return jsonify({'status': "Something went wrong, Please Try Again Later"}), 400
@app.errorhandler(not_admin)
def handle_not_admin(error):
    return jsonify({'status': "You are not admin"}), 401

# my JWT token system workes good with postman but,
# with react the cookies are not saved for some reason
# so i have implemented the doe without JWT, you can verify it easily by just uncommenting a few lines

# using the JWT this fucntion is the token checker
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the JWT token from cookies
        jwt_token = request.cookies.get('token')
        if not jwt_token:
            return jsonify({'status': 'Please Login!'}), 401
        try:
            # Decode the JWT token
            payload = jwt.decode(jwt_token, app.config['SECRET_KEY'], algorithms=['HS256'])
            # access the payload data
            user_id = payload['user_id']
            # Pass the user_id to the wrapped function
            return f(user_id, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'status': 'Please Login Again!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'status': 'Unauthorised, Please Login'}), 401

    return decorated_function


### Routes ###

# Login
# creates a JWT token and return, also if not admin, it returns the attendence directly.
@app.route('/login', methods=['post'])
def login():
    print("working login")
    # get user_id and image from request
    user_id, image = extract_id_and_image(request)
    # check if user exist
    user = check_and_get_use(user_id, users)
    try:
        # compare image with the image in database after extracting face
        if check_face(BytesIO(extrat_face(image)), BytesIO(user['image'])):
            # generates the JWT Token
            token = jwt.encode({
                'user_id': user_id,
                'exp' : datetime.now(timezone.utc) + timedelta(minutes = 30)
                # 30 min life of token
            }, app.config['SECRET_KEY'], algorithm='HS256')
            # Set token in cookie
            print(token)
            admin = check_admin(user_id, users, "Login", raise_error=False)
            if admin:
                # returns a simple response with admin value
                response = make_response(jsonify({'status': 'Login successful', 'isAdmin': admin}))
                response.set_cookie('token', token)
                return response
            else: 
                # returns the attendence with the response
                response = make_response(jsonify({'status': 'Login successful','isAdmin': admin, 'attendence': user['attendence']}))
                response.set_cookie('token', token)
                return response
        else: 
            return jsonify({'status': 'Face did not matched'}), 401
    except Exception as e:
        # handels all the exceptions with the extraction, checking_face 
        # with the help of above defined exceptions
        print(e)
        return jsonify({'status': str(e)}), 400

# Mark Attendence
# Extracts image, find user, check face, then mark present.
@app.route('/mark-attendence', methods=['post'])
def mark_attendence():
    try:
        # get user_id and image form request
        user_id, image = extract_id_and_image(request)
        #check if user exist
        user = check_and_get_use(user_id, users)
        try:
            # compare image with the image in database after extracting face
            if check_face(BytesIO(extrat_face(image)), BytesIO(user['image'])):
                # if face matched mark present
                mark_present(user)
                return jsonify({'status': 'attendence marked'}), 200
            else:
                return jsonify({'status': 'attendence not marked, face did not matched'}), 401
            
        except Exception as e:
            print(e)
            return jsonify({'status': str(e)}), 400
    except Exception as e:
        print(e)
        return jsonify({'status': str(e)}), 400

# Add Student
# Path is allowed for any one Logged in but request will ne regeted if not admin
# Allowed only for ADMIN to add student, which is id number 230626 from my database.
# currently it is not usng the JWT @token_required, 
# if you use postman it will work just uncomment the line
@app.route('/add-student', methods=['post'])
# @token_required                       #Uncomment
# def add_student(admin_user_id):       #Uncomment
#   try:                                #Uncomment
def add_student():                      #Comment
    try:                                #Comment
        admin_user_id = "230626"        #Comment
        # check if admin
        check_admin(admin_user_id, users, 'add student')
        # get user_id and image form request
        user_id, image = extract_id_and_image(request)
        # check if user already exist
        if check_and_get_use(user_id, users, raise_error=False):
            return jsonify({'status': 'User already exist'}), 400
        # Try save the image in database
        try: 
            users.insert_one({'user_id': user_id, 'image': extrat_face(image), 'attendence': []})
            print('User added')
            return jsonify({'status': 'student added'}), 200
            # # to check what is added in database
            # img1 = Image.open(extrat_face(image))
            # img1.save('img.jpg')
        except Exception as e:
            print(e)
            raise something_went_wrong('Something went wrong, Please Try Again Later')
    except Exception as e:
        print(e)
        return jsonify({'status': str(e)}), 400


# Get Attendence
# it it defined for any one who is logged in to access path
# he/she can access his/her attendence, only admin is allowed to check other's attendence
@app.route('/get-attendence', methods=['post'])
# @token_required                       #Uncomment
# def get_attendence(user_id):          #Uncomment
    # try:                              #Uncomment
def get_attendence():                   #Comment
    try:                                #Comment
        user_id = "230626"              #Comment
        required_attendence_user_id = extract_id_and_image(request, extract_image=False)
        if required_attendence_user_id != user_id:
            check_admin(user_id, users, 'get attendence')
            user = check_and_get_use(required_attendence_user_id, users)
            return jsonify({'status': 'Got Attendence', 'attendence': user['attendence']}), 200
        else:
            # jwt verified so user exist
            return jsonify({'status': 'Got Attendence' ,'attendence': check_and_get_use(user_id, users)['attendence']}), 200
    except Exception as e:
        print(e)
        return jsonify({'status': str(e)}), 400
    
# Mark Absent if not present
# allowed only to admin, markes absent to who is not present on that day
@app.route('/mark-absent-all', methods=['get'])
# @token_required                                           #Uncomment
# def mark_absent_all_not_present_today(admin_user_id):     #Uncomment
#   try:                                                    #Uncomment
def mark_absent_all_not_present_today():                    #Comment
    try:                                                    #Comment
        admin_user_id = "230626"                            #Comment    
        check_admin(admin_user_id, users, 'mark all other absent')
        return jsonify({'status': 'All other marked absent, count: ' + str(mark_absent(users))}), 200
    except Exception as e:
        print(e)
        return jsonify({'status': str(e)}), 401



### Helper functions ###

# Extract ID and Image from the request, 
# Raise exception, Missing Data, which will be returned as response
def extract_id_and_image(request, extract_image=True):  #if you dont have image to acess use false
    print(request)
    try:
        user_id = request.form['user_id']
        if not extract_image:
            return user_id
        image = request.files['image']
        return user_id, image
    except KeyError as e:
        print(e)
        raise missing_form_data('Missing form data') 

# Sole of the program
# Check_face it takes two two BytesIO image file to check if the images have same face
# Raise Exception if need, like the model was not able to process file, it will rasie, somthing went wrong
def check_face(image1, image2):
    # compare the image
    try: 
        # Convert BytesIO images to PIL Images
        img1 = Image.open(image1)
        img2 = Image.open(image2)
        # Save PIL Images files as the deepface model takes path, 
        # i have tried any  way to take PLI images itself but dint found any thing on the net
        img1.save('img1.jpg')
        img2.save('img2.jpg')

        # Use DeepFace to verify images
        # https://viso.ai/computer-vision/deepface/ refer to know about google facenet and other models
        # the results are more accurate when the images have similar lighting conditions, 
        # prefer not to have shadow on your face

        result = DeepFace.verify('img1.jpg', 'img2.jpg', enforce_detection=False, model_name="Facenet")
        # delete the memory used by the files
        os.remove('img1.jpg')
        os.remove('img2.jpg')
        # result is a dictionary of many filed, one of which is verified according to the model
        print(result)
        return result['verified'] 
    except Exception as e:
        print(e)
        raise something_went_wrong('Something went wrong, Please Try Again Later')
    
# It is important to extract face as a image form the whole image, 
# I have taken this fucntion form online and modfied it according to the inputs we have,
# Extracting face better allow us to compare the images and less errors while processing the images by model.
def extrat_face(image):
    # image file already in binary data
    global net
    # convert it to numpy array
    image = np.array(Image.open(image))
    (h,w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300,300)), 1.0, 
                                 (300,300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()
    confidence = detections[0, 0, 0, 2]

    if confidence < 0.5:
        # we raise error if face is not detected
        raise face_not_detected("No face detected")
    box = detections[0, 0, 0, 3:7] * np.array([w,h,w,h])
    (startX, startY, endX, endY) = box.astype('int')
    try: 
        image = image[startY:endY, startX:endX]
        (h,w) = image.shape[:2]
        r = 400 / float(h)
        dim  = (int(w*r), 480)
        image = cv2.resize(image, dim)
    except Exception as e:
        # exception when the face is out of the image, like a portion is not in the frame.
        # return None
        raise something_went_wrong("Not Complete Face")
    
    # We were working with a numpy array, now conver it back to image
    image = Image.fromarray(image)
    # save the image to binary type, or Byte type which was the input
    image_binary = BytesIO()
    image.save(image_binary, 'JPEG')
    image_binary.seek(0)
    try: 
        # Read it as a single line or array of chars and return
        image_binary = image_binary.read()
        # print(image_binary)
    except Exception as e:
        print(e)
        raise face_not_detected('No face detected')
    return image_binary

# Mark Present Helper function.
def mark_present(user):
    # get date, time
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M')
    # push object/dict with 'data' , 'status' , 'time' fields in the attendence array
    users.update_one(user, {'$push': {"attendence" : {'date': date, 'status': 'Present', 'time': time}}})
    print(user['user_id'] + " Present")

# check User and return user, raise error if user not found
def check_and_get_use(user_id, users, raise_error=True):
    user = users.find_one({'user_id': user_id})
    if user is not None:
        return user
    else:
        if raise_error:
            raise user_not_found('User not found')
        else:
            return False

# check admin, raise error if not, print the action taken by admin, like login, add student etc.
def check_admin(admin_user_id, users, action, raise_error=True):
    try:
        admin = check_and_get_use(admin_user_id, users)
        print(admin['user_id']+" Admin status: " + admin['admin'] + "\ntried action: " + action )
        return admin['admin']
    except KeyError:
        if raise_error:
            raise not_admin('You are not admin')
        else:
            return False

# Mark the students which do not have the present marked of today and return the count of such students
def mark_absent(users):
    # get time and date
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M')
    # update the required student objects in data base
    result = users.update_many ({ "attendence": 
                                    { "$not": 
                                        {"$elemMatch": 
                                            {"date": date,
                                            "status": "Present"}
                                        }
                                    } 
                                }, 
                                { "$push": { "attendence": { 'date': date, 'status': 'Absent', 'time': time} } })
    # return the count of the students marked absent
    print("Modified Documents:", result.modified_count)
    return result.modified_count

# star the server eith the python3 app.py
if __name__ == "__main__":
    app.run(host="localh.st", port=5000, debug=True)
    # app.run()