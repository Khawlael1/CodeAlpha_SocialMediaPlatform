from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile
from .models import Post,Comment,Like
from .forms import PostForm,CommentForm

@login_required
def profile_view(request, username):
    user = User.objects.get(username=username)
    profile = Profile.objects.get(user=user)
    return render(request, 'social/profile.html', {'profile': profile})

@login_required
def edit_profile_view(request):
    profile = request.user.profile
    if request.method == "POST":
        bio = request.POST.get("bio")
        avatar = request.FILES.get("avatar")

        profile.bio = bio
        if avatar:
            profile.avatar = avatar
        profile.save()
        return redirect('profile', username=request.user.username)

    return render(request, 'social/edit_profile.html', {'profile': profile})


# Home page (public for now)
def home_view(request):
    return render(request, 'social/home.html')

# Register new users
def register_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password != password2:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect('register')

        user = User.objects.create_user(username=username, password=password)
        user.save()
        messages.success(request, "Account created! You can log in now.")
        return redirect('login')

    return render(request, 'social/register.html')


# Login users
def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('login')

    return render(request, 'social/login.html')


# Logout users
def logout_view(request):
    logout(request)
    return redirect('login')

#Comment
@login_required
def feed(request):
    if request.method == "POST":
        if 'post_submit' in request.POST:
            form = PostForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.user = request.user
                post.save()
                return redirect("feed")
        elif 'comment_submit' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.user = request.user
                comment.post_id = request.POST.get("post_id")
                comment.save()
                return redirect("feed")
    else:
        form = PostForm()
        comment_form = CommentForm()

    posts = Post.objects.all().order_by("-created_at")
    return render(request, "social/feed.html", {
        "form": form,
        "posts": posts,
        "comment_form": comment_form
    })

# Like 
@login_required
def toggle_like(request, post_id):
    post = Post.objects.get(id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()  # unlike if already liked
    return redirect("feed")