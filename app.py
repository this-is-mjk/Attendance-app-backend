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

# Custom Exceptions for handling errors
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

#Load pretrained face detection model    
net = cv2.dnn.readNetFromCaffe('./saved_model/deploy.prototxt.txt', './saved_model/res10_300x300_ssd_iter_140000.caffemodel')

# create a flask app with Cors to enable local development
app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'this_is_mjk_secret_key'

# connect to database and open users in AttendenceApp database
client = MongoClient('localhost', 27017)
db = client.AttendenceApp
users = db.users

# Raising errors
@app.errorhandler(missing_form_data)
def handle_missing_form_data(error):
    return jsonify({'error': "Bad Request, Missing Required Data"}), 400
@app.errorhandler(face_not_detected)
def handle_face_not_detected(error):
    return jsonify({'error': "No face detected"}), 400
@app.errorhandler(user_not_found)
def handle_user_not_found(error):
    return jsonify({'error': "User not found"}), 400
@app.errorhandler(something_went_wrong)
def handle_something_went_wrong(error):
    return jsonify({'error': "Something went wrong, Please Try Again Later"}), 400

    
@app.route('/add-student', methods=['post'])
def add_student():
    try:
        # get user_id and image form request
        user_id, image = extract_id_and_image(request)
        # check if user already exist
        if check_user_exist(user_id, users, raise_error=False):
            return jsonify({'error': 'User already exist'}), 400
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
        return jsonify({'error': str(e)}), 400
    
@app.route('/mark-attendence', methods=['post'])
def mark_attendence():
    try:
        # get user_id and image form request
        user_id, image = extract_id_and_image(request)
        #check if user exist
        user = check_user_exist(user_id, users)
        try:
            # compare image with the image in database after extracting face
            if check_face(BytesIO(extrat_face(image)), BytesIO(user['image'])):
                # if face matched mark present
                mark_present(user)
                return jsonify({'status': 'attendence marked'}), 200
            else:
                return jsonify({'status': 'attendence not marked, face did not matched'}), 400
            
        except Exception as e:
            print(e)
            return jsonify({'error': 'Something Bad Happened, Please Try Again'}), 400
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['get'])
def login():
    # get user_id and image form request
    user_id, image = extract_id_and_image(request)
    #check if user exist
    user = check_user_exist(user_id, users)
    try:
        # compare image with the image in database after extracting face
        if check_face(BytesIO(extrat_face(image)), BytesIO(user['image'])):
            # generates the JWT Token
            token = jwt.encode({
                'user_id': user_id,
                'exp' : datetime.now(timezone.utc) + timedelta(minutes = 30)
                # 30 min life of token
            }, app.config['SECRET_KEY'])
            # Set token in cookie
            response = make_response(jsonify({'message': 'Login successful'}))
            response.set_cookie('token', token)
            return response
        else: 
            return jsonify({'error': 'Face did not matched'}), 400
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 400
def extract_id_and_image(request):
    try:
        user_id = request.form['user_id']
        image = request.files['image']
        return user_id, image
    except KeyError as e:
        print(e)
        raise missing_form_data('Missing form data') 
    
def check_face(image1, image2):
    # compare the image
    try: 
        # Convert BytesIO images to PIL Images
        img1 = Image.open(image1)
        img2 = Image.open(image2)
        # Save PIL Images files
        img1.save('img1.jpg')
        img2.save('img2.jpg')
        # Use DeepFace to verify images
        result = DeepFace.verify('img1.jpg', 'img2.jpg', enforce_detection=False)
        # delete the memory used by the files
        os.remove('img1.jpg')
        os.remove('img2.jpg')
        # print(result)
        return result['verified']
    except Exception as e:
        print(e)
        raise something_went_wrong('Something went wrong, Please Try Again Later')
    
def extrat_face(image):
    # image file already in binary data
    global net
    image = np.array(Image.open(image))
    (h,w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300,300)), 1.0, 
                                 (300,300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()
    confidence = detections[0, 0, 0, 2]

    if confidence < 0.5:
        return None
    box = detections[0, 0, 0, 3:7] * np.array([w,h,w,h])
    (startX, startY, endX, endY) = box.astype('int')
    try: 
        image = image[startY:endY, startX:endX]
        (h,w) = image.shape[:2]
        r = 400 / float(h)
        dim  = (int(w*r), 480)
        image = cv2.resize(image, dim)
    except Exception as e:
        return None
    
    image = Image.fromarray(image)
    image_binary = BytesIO()
    image.save(image_binary, 'JPEG')
    image_binary.seek(0)
    try: 
        image_binary = image_binary.read()
        # print(image_binary)
    except Exception as e:
        print(e)
        raise face_not_detected('No face detected')
    return image_binary

def mark_present(user):
    date = datetime.now().strftime('%Y-%m-%d %H:%M')
    users.update_one(user, {'$push': {"attendence" : {date: 'present'}}})

def check_user_exist(user_id, users, raise_error=True):
    user = users.find_one({'user_id': user_id})
    if user is not None:
        return user
    else:
        if raise_error:
            raise user_not_found('User not found')
        else:
            return False


if __name__ == "__main__":
    app.run(host="localh.st", port=5000, debug=True)
    # app.run()