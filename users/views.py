# https://stackoverflow.com/questions/32942529/django-not-null-constraint-failed-userprofile-user-id-in-case-of-uploading-a-fil
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import UserRegisterForm, ProfileForm, UserUpdateForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.conf import settings
import os
import face_recognition
import cv2
import time
import base64
# Create your views here.
''' You can get current logged in user object by name 'user'  '''

# def register(request):
#     if request.method == 'POST':
#         user_form = UserRegisterForm(request.POST)
#         profile_form = ProfileForm(request.POST, request.FILES)
#         if user_form.is_valid() and profile_form.is_valid():
#             # if the photo uploaded by user does not contain face ask her to reupload
#             # request.FILES is a dictionary like object
#             # the value is UploadedFile object, we can use read() function to read whole object at a time
#             with open('./media/check.jpeg', 'wb+') as f:
#                 f.write(request.FILES['image'].read())
            
#             user_image = face_recognition.load_image_file('./media/check.jpeg')
#             user_face_encoding = face_recognition.face_encodings(user_image)
#             if len(user_face_encoding) == 0:
#                 messages.warning(request, 'Error: Face was not found in the image. Please upload valid Picture.')
#             elif len(user_face_encoding) > 1:
#                 messages.warning(request, 'Error: Multiple faces were found in the picture')
#             else:
#                 user_form.save()
#                 profile = profile_form.save(commit=False)
#                 profile.user = User.objects.get(username=request.POST['username'])
#                 profile.save()
#                 username = user_form.cleaned_data.get('username')
#                 messages.success(request, f'Account created for {username}!')
#                 return redirect('login')
#     else:
#         user_form = UserRegisterForm()
#         profile_form = ProfileForm()

#     context = {'user_form':user_form, 'profile_form':profile_form}
#     return render(request, 'users/register.html', context)

def register(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        if user_form.is_valid():
            user_form.save()
            username = user_form.cleaned_data.get('username')
            messages.success(request, f'One more step {username}! Please put your face close to camera')
            return render(request, 'users/image-upload.html', {'username':username})
    else:
        user_form = UserRegisterForm()
    return render(request, 'users/register.html', {'user_form':user_form})

@login_required
def profile(request):
    return render(request, 'users/profile.html')

@login_required
def profile_update_view(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
        
    context = {'user_form':user_form, 'profile_form':profile_form}
    return render(request, 'users/profile-update.html', context)

def face_auth(user):
    ''' This function returns true if valid face found for the user '''
    stringimage = user.profile.auth_image
    imgdata = base64.b64decode(stringimage)
    path = './media/check.png'
    with open(path, 'wb') as f:
        f.write(imgdata)

    user_image = face_recognition.load_image_file(path)
    user_face_encoding = face_recognition.face_encodings(user_image)[0]
    

    # Get a reference to webcam #0 (the default one)
    video_capture = cv2.VideoCapture(0)
    process_this_frame = True
    t_end = time.time() + 5 # waits for 5 sec
    while time.time() < t_end:
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every other frame of video to save time
        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces([user_face_encoding], face_encoding, tolerance=0.5)
                if matches[0] == True:
                    # release handle to the webcam
                    video_capture.release()
                    return True# break
        process_this_frame = not process_this_frame
    return False



def login_view(request):
    if request.user.is_authenticated:
        return redirect('company:home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.profile.auth_image == '':
                    messages.warning(request, 'Please complete the registration process to login.'.format(username))
                    return render(request, 'users/image-upload.html', {'username':user.username})
                elif face_auth(user):
                    login(request, user)# this call actually  makes user login
                    return redirect('company:home')
                else:
                    messages.warning(request, f'Valid face not found for user {username}!')
    else:
        messages.warning(request, 'PUT YOUR FACE CLOSE TO THE CAM TO AUTHENTICATE AFTER PRESSING ENTER.')
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form':form})

def is_valid_pic(stringimage):
    ''' 
    This function takes base64 string image, saves it as check.png
    returns number of faces
    '''

    imgdata = base64.b64decode(stringimage)
    with open('./media/check.png', 'wb') as f:
        f.write(imgdata)
    
    user_image = face_recognition.load_image_file('./media/check.png')
    user_face_encoding = face_recognition.face_encodings(user_image)
    return len(user_face_encoding)

def image_upload(request):
    if request.method == 'POST':
        username = request.POST['username']
        stringimage = request.POST['stringimage']
        # stringimage contains 'data:image/png;base64,' at the front which is not needed, so removing it
        stringimage = stringimage[22:]
        faces = is_valid_pic(stringimage) # no of faces
        if faces == 0:
            messages.warning(request, 'Error: Face was not found in the image. Please upload valid Picture.')
        elif faces > 1:
            messages.warning(request, 'Error: Multiple faces were found in the picture')
        else:
            # for now, user is allowed to submit data if he is coming from login/register page only.
            if username == '':
                messages.warning(request, 'You cannot submit data. Invalid session.')
            else:
                user = User.objects.get(username=username)
                user.profile.auth_image = stringimage
                user.save()
                messages.success(request, 'success: Your registration process is completed! Now you can login!')
            return redirect('login')
    else:
        username = ''
    return render(request, 'users/image-upload.html',{'username':username})
