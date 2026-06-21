"""
views.py file is used for handling the requests and responses of the application. 
It contains the logic for rendering the templates and processing the data.

"""
import json
import os
import assemblyai as aai
import openai
import yt_dlp as youtube_dl
import datetime
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from pytube import YouTube
from .models import Blogpost



# Create your views here.

@login_required
def index(request):
    """render the index page"""
    return render(request, 'index.html')

def user_login(request):
    """
    user login method is used for login to user account by POST method.
    
    """
 
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password.'})
    return render(request, 'login.html')

def user_logout(request):
    """ user logout method is used for logout from user account"""
    logout(request)
    return redirect('/')

def user_signup(request):
    """
    user signup method is used for create new user account by POST method.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password == confirm_password:
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                login(request, user)
                return redirect('/')
            except (email, username, password) as e:
                return render(request, 'signup.html', {'error': str(e)})
        else:
            return render(request, 'signup.html', {'error': 'Passwords do not match.'})
    return render(request, 'signup.html')

@csrf_exempt
def generate_blog(request):
    """
    generate_blog method is used for generate blog content by POST method.
    """
    if request.method == 'POST':
        try:
            data =json.loads(request.body)
            youtube_link = data.get('link')
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'error': 'Invalid request data.'}, status=400)
   
        # get yt title
        youtube_title = get_youtube_title(youtube_link)
   
        # get transcript
        tracscription = get_youtube_transcript(youtube_link)
        if tracscription is None:
            return JsonResponse({'error': 'Failed to retrieve transcript.'}, status=500)
     
        # use openai api to generate blog content
        blog_content = generate_blog_content(tracscription)
        if blog_content is None:
            return JsonResponse({'error': 'Failed to generate blog content.'}, status=500)
      
        # save the blog content to database
        new_blog = Blogpost.objects.create(
            user = request.user,
            youtube_title = youtube_title,
            youtube_url = youtube_link,
            content = blog_content,
            created_date = datetime.datetime.now()
        )
        # return the generated blog content as JSON response
        return JsonResponse({'content': blog_content})
    
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

def get_youtube_title(youtube_link):
    """
    get_youtube_title method is used for get youtube video title by using pytube library.
    """   
    yt = YouTube(youtube_link)
    return yt.title

def download_youtube_video(youtube_link):
    """
    download_youtube_video method is used for download youtube video by using pytube library.
    """
    try:
        ydl_opts = { 'format': 'bestaudio/best',
                    'ffmpeg_location': "C:\\Users\\darshanim\\Downloads\\ffmpeg-8.1.1-essentials_build\\ffmpeg-8.1.1-essentials_build\\bin",
            'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(settings.MEDIA_ROOT, '%(title)s.%(ext)s')
        }
        # yt = youtube_dl.YoutubeDL(ydl_opts)
        # outfile =yt.extract_info(youtube_link, download=True)
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(youtube_link, download=True)

            audio_file = os.path.join(
                settings.MEDIA_ROOT,
                f"{info['title']}.mp3"
            )

        print("Audio File Path:", audio_file)
       
        return audio_file
    except Exception as e:
        print(f"Error occurred while downloading YouTube video: {e}")
        return None
    
def get_youtube_transcript(youtube_link):
    """
    get_youtube_transcript method is used for get youtube video transcript by using youtube_transcript_api library.
    """
    audio_file = download_youtube_video(youtube_link)
    print(f'audio file is {audio_file}')
    print(f'aai api key is {settings.ASSEMBLYAI_API_KEY}')
    aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
    transcriber = aai.Transcriber()
    print(f'transcriber passed: {transcriber}')
    transcript = transcriber.transcribe(audio_file)
    print(f'transcript generated: {transcript.text}')
    return transcript.text

def generate_blog_content(transcript):
    """
    generate_blog_content method is used for generate blog content by using openai api.
    """
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcript}\n\nArticle:"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.7,
    )
    blog_content = response.choices[0].text.strip()
    return blog_content

def blog_list(request):
    """
    blog_list method is used for display the list of generated blogs.
    """
    blogs = Blogpost.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'all_blogs.html', {'blogs': blogs})

def blog_detail(request, blog_id):
    """
    blog_detail method is used for display the detail of generated blog.
    """
    # blog_id = request.GET.get('id')
    blog = Blogpost.objects.get(id=blog_id)
    if request.user == blog.user:
        return render(request, 'blog_detail.html', {'blog': blog})
    else:
        return render('/')