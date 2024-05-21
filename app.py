from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from io import BytesIO
import os
import numpy as np
from deepface import DeepFace
from PIL import Image
import cv2

#Load pretrained face detection model    
net = cv2.dnn.readNetFromCaffe('./saved_model/deploy.prototxt.txt', './saved_model/res10_300x300_ssd_iter_140000.caffemodel')

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.AttendenceApp
users = db.users

@app.route('/check-student', methods=['get'])
def check_user():
    pr
    data = request.get_json()
    if not data or 'user_id' not in data or data['user_id'] == '':
        return jsonify({'error': 'Bad Request'}), 400
    #get user_id
    user_id = data['user_id']
    #check for user_id
    if users.count_documents({'user_id': user_id}) > 0:
        return jsonify({'exists': True}), 200
    else:
        return jsonify({'exists': False}), 200
    
@app.route('/add-student', methods=['post'])
def add_student():
    # get user_id and image form request
    try:
        # print(request.form)
        user_id = request.form['user_id']
        image = request.files['image']
        # image file already in binary data
        try: 
            image_binary = extrat_face(image).read()
            # print(image_binary)
        except Exception as e:
            print(e)
            return jsonify({'error': 'No face detected'}), 400   
        # save the image in database
        users.insert_one({'user_id': user_id, 'image': image_binary})
        print('User added')
        # # to check what is added in database
        # img1 = Image.open(extrat_face(image))
        # img1.save('img.jpg')
        return jsonify({'status': 'student added'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Bad Request'}), 400
@app.route('/mark-attendence', methods=['post'])
def mark_attendence():
    try:
        # print(request.form)
        user_id = request.form['user_id']
        image = request.files['image']
        # find the user in database
        user = users.find_one({'user_id': user_id})
        if user:
            try: 
                image_binary = extrat_face(image).read()
                # print(image_binary)
            except Exception as e:
                print(e)
                return jsonify({'error': 'No face detected'}), 400 
            # compare image with the image in database
            if check_face(BytesIO(image_binary), BytesIO(user['image'])):
                return jsonify({'status': 'attendence marked'}), 200
            else:
                return jsonify({'status': 'attendence not marked, face did not matched'}), 200
        else:
            return jsonify({'status': 'student not found'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Bad Request'}), 400
    

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

        return result['verified']
    except Exception as e:
        print(e)
        return False
def extrat_face(image):
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
    return image_binary

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
    # app.run()