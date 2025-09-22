from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Post,Comment,Like,Profile,Follow
from .forms import PostForm,CommentForm
from django.http import JsonResponse



@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile = Profile.objects.get(user=profile_user)

    # True if request.user follows profile_user
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    return render(request, 'social/profile.html', {
        'profile': profile,
        'is_following': is_following
    })




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
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect("feed")
    else:
        form = PostForm()

    posts = Post.objects.all().order_by("-created_at")

    for post in posts:
        post.liked_by_user = post.likes.filter(user=request.user).exists()

    return render(request, "social/feed.html", {"form": form, "posts": posts})

    
# Like 

@login_required
def like_post(request, post_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=400)

    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if not created:  # Already liked → unlike
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        "liked": liked,
        "total_likes": post.likes.count(),
    })


# Like 
@login_required
def toggle_follow(request, username):
    target_user = get_object_or_404(User, username=username)

    if target_user == request.user:
        messages.error(request, "You cannot follow yourself!")
        return redirect("profile", username=username)

    follow, created = Follow.objects.get_or_create(
        follower=request.user, following=target_user
    )

    if not created:  # already following → unfollow
        follow.delete()
        messages.info(request, f"You unfollowed {target_user.username}")
    else:
        messages.success(request, f"You are now following {target_user.username}")

    return redirect("profile", username=username)