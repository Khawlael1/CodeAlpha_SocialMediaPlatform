from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Post,Comment,Like,Profile,Follow,Notification
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
        # no need for post.comments_list; you can use post.comments.all in template

    comment_form = CommentForm()
    
    # Count unread notifications if you added that
    unread_count = request.user.notifications.filter(read=False).count() if hasattr(request.user, "notifications") else 0

    return render(request, "social/feed.html", {
        "form": form,
        "posts": posts,
        "comment_form": comment_form,
        "unread_count": unread_count
    })

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comment_set.all().order_by('created_at')

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            # Create notification for the post owner
            if request.user != post.user:
                Notification.objects.create(
                    user=post.user,
                    sender=request.user,
                    post=post,
                    type="comment"
                )
            return redirect('post_detail', post_id=post.id)
    else:
        form = CommentForm()

    return render(request, "social/post_detail.html", {
        "post": post,
        "comments": comments,
        "form": form,
        "liked_by_user": post.likes.filter(user=request.user).exists()
    })



@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Only allow the owner to edit
    if post.user != request.user:
        return redirect('feed')

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('feed')
    else:
        form = PostForm(instance=post)

    return render(request, 'social/edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Only allow the owner to delete
    if post.user != request.user:
        return redirect('feed')

    if request.method == 'POST':
        post.delete()
        return redirect('feed')

    return render(request, 'social/delete_post.html', {'post': post})

    
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

    if liked and request.user != post.user:
        Notification.objects.create(
            user=post.user,
            sender=request.user,
            post=post,
            type="like"
        )
    
    

    return JsonResponse({
        "liked": liked,
        "total_likes": post.likes.count(),
    })


# Follow
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

# Comment
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        text = request.POST.get("text")
        if text:
            comment = Comment.objects.create(user=request.user, post=post, text=text)

            # Create notification for the post owner (only if commenter isn’t the owner)
            if post.user != request.user:
                Notification.objects.create(
                    user=post.user,        # receiver = post owner
                    sender=request.user,   # sender = commenter
                    post=post,
                    comment=comment,
                    type="comment"
                )

    return redirect("feed")

# Notification
@login_required
def notifications_view(request):
    # Get all notifications for the user
    notifications = request.user.notifications.all().order_by('-created_at')
    
    # Mark all unread notifications as read
    notifications.filter(read=False).update(read=True)

    return render(request, "social/notifications.html", {"notifications": notifications})

@login_required
def unread_notifications_count(request):
    count = request.user.notifications.filter(read=False).count()
    return JsonResponse({"unread_count": count})

