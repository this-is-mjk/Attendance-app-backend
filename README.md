### Project Attendence App
    -- By this_is_mjk Manas Jain Kuniya
This app uses facial recogintion by DeepFace to mark attedence, mongodb as data base, python with flask for server, and react for frontend

demo vedio link:- https://drive.google.com/file/d/1dHEqofvBiVSwp0DsM_fATmrwoBwefYhS/view?usp=sharing

### github link 

frontend:-https://github.com/this-is-mjk/Attendance-App.git

backend:- https://github.com/this-is-mjk/Attendance-app-backend.git
this repo have a bit more, you can test it yourself bysing the admin_db_object with your image or use the images in the test_images, it have many images to explore, with mine as manas1, manas2.

initially i thought of deploying them that's why i made 2 repos

used vrsel to deploy the frontend, did't got time to deploy backend and data base, tries on GCP, did't worked, was thinking to look on AWS and Mongodb atlas.

### Area of Improvement
1. to make the code more readable by using file organising for different function
2. JWT implementation intergration with the frontend.
3. front end is very messy with a lot of code repetation, would like to organise the same and learn new concept to use multiple useStae variables across the react app without passing every where,
4. React code can get full of errors in no time, i want to make it organised and compact so that it is esay to use at multiple places, modularity is my focus.

### Features
1.  User Authentication: JWT-based  authentication, workes with postman, issues with the react frontend
2. Face Detection and verification
3. Attendance Management
4. Admin Power of Adding students, getting attendence and mark absent all

### Used technologies
1. Backend: Flask
2. Database: MongoDB
3. Facial Recognition: OpenCV, DeepFace
4. Token Management: JWT


### Backend

### Pre requisites
1. Python
2. MongoDB compass
3. pip for python

### API Endpoints
## Login
    URL: /login
    Method: POST
    Description: Logs in the user and returns a JWT token.
    Request:
    Form Data:
        user_id: User ID
        image: User image file
    Response:
        Success: { "status": "Login successful", "isAdmin": boolean, "attendence": [] }
        Error: { "status": "Error message" }
## Mark Attendance
    URL: /mark-attendance
    Method: POST
    Description: Marks the user's attendance.
    Request:
    Form Data:
        user_id: User ID
        image: User image file
    Response:
        Success: { "status": "attendance marked" }
        Error: { "status": "Error message" }
## Add Student
    URL: /add-student
    Method: POST
    Description: Adds a new student to the system (Admin only).
    Request:
    Form Data:
            user_id: User ID
            image: User image file
    Response:
        Success: { "status": "student added" }
        Error: { "status": "Error message" }
## Get Attendance
    URL: /get-attendance
    Method: POST
    Description: Gets the attendance records for the user or another user (Admin only).
    Request:
        Form Data:
        user_id: User ID (of the user whose attendance is requested)
    Response:
        Success: { "status": "Got Attendance", "attendance": [] }
        Error: { "status": "Error message" }
## Mark Absent All
    URL: /mark-absent-all
    Method: GET
    Description: Marks all users as absent who have not marked their attendance for the day (Admin only).
    Response:
        Success: { "status": "All other marked absent, count: n" }
        Error: { "status": "Error message" }

### Error Handling

Custom exceptions are used to handle errors and return appropriate responses:
1. missing_form_data
2. face_not_detected
3. user_not_found
4. something_went_wrong
5. not_admin

### Helper Functions
1. extract_id_and_image: Extracts user ID and image from the request.
2. check_face: Compares two images to check if they have the same face.
3. extrat_face: Extracts the face from an image.
4. mark_present: Marks a user as present.
5. check_and_get_use: Checks if a user exists and returns the user.
6. check_admin: Checks if a user is an admin.
7. mark_absent: Marks all users as absent who have not marked their attendance for the day.


### what i learned for this project
1. got my weekness of react, like cookies and a bit of await, known and will now work on it
2. got to know i can ignore the CORS issue of localhost by using localh.st
3. came to know about Flask and DeepFace technologies
4. helped me to brush me up with a few mongo db resources and python
5. came to know about pip freeze > requirements.txt to list all requirements easily.
