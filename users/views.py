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
# Create your views here.

def register(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)
            # print(request.POST)
            profile.user = User.objects.get(username=request.POST['username'])
            profile.save()
            username = user_form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        user_form = UserRegisterForm()
        profile_form = ProfileForm()

    context = {'user_form':user_form, 'profile_form':profile_form}
    return render(request, 'users/register.html', context)

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
    
    print(request.user)
    print(request)
    context = {'user_form':user_form, 'profile_form':profile_form}
    return render(request, 'users/profile_update.html', context)

def face_auth(user):
    ''' This function returns true if valid face found for the user '''
    path = os.path.join(settings.MEDIA_ROOT,str(user.profile.image))
    # Load a sample picture and learn how to recognize it.
    user_image = face_recognition.load_image_file(path)
    user_face_encoding = face_recognition.face_encodings(user_image)[0]
    

    # Get a reference to webcam #0 (the default one)
    video_capture = cv2.VideoCapture(0)
    process_this_frame = True
    t_end = time.time() + 10 # waits for 10 sec
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
        print(request.POST)
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if face_auth(user):
                    login(request, user)
                    messages.success(request, 'Welcome.. {} :)'.format(username))
                    return redirect('profile')
                else:
                    messages.warning(request, f'Valid face not found for user {username}!')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form':form})

# def face_login_view(request):
#     pass











