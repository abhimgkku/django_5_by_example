from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage,PageNotAnInteger
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView

from .models import FavouritePost, Post
from .forms import EmailPostForm,CommentForm


def post_share(request,post_id):
    post = get_object_or_404(Post,id=post_id,status=Post.Status.PUBLISHED)
    sent = False
    if request.method =='POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = (
                f"{cd['name']} ({cd['email']})"
                f"recommends you read {post.title}"
            )
            message = (
                f"Read {post.title} at {post_url}\n\n"
                f"{cd['name']}\s comments: {cd['comments']}"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[cd['to']]
            )
            sent = True
    else:
        form = EmailPostForm()
    return render(
        request,
        'post/share.html',
        {
        'post': post,
        'form': form,
        'sent': sent
        }
    )

class PostListView(ListView):
    """
    Alternative Post list view
    
    """
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'post/list.html'



def post_list(request):
    post_list = Post.published.all()
    paginator = Paginator(post_list,3)
    page_number = request.GET.get('page',1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
        
    return render(
        request,
        'post/list.html',
        {'posts': posts}
    )


def post_detail(request, year, month, day, post):
    favourite_post = None
    post = get_object_or_404(
        Post,
        status=Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day
    )
    comments = post.comments.filter(active=True)
    form = CommentForm()
    try:
        if request.user.is_authenticated:
            favourite_post = FavouritePost.objects.get(
                user=request.user, post=post
            )
    except FavouritePost.DoesNotExist:
        pass
    return render(
        request,
        'post/detail.html',
        {
            'is_favourite': favourite_post is not None,
            'post': post,
            'comments': comments,
            'form': form
        }
    )

def add_favourite(request, id):
    """ A view to add a post to favourites. Redirects to post detail when favourite added. """
    post = get_object_or_404(Post, id=id)
    FavouritePost.objects.get_or_create(
        user=request.user, post=post
    )
    return HttpResponseRedirect(post.get_absolute_url())

@login_required
def favourites(request):
    """ A view to list all favourite posts. """
    favourite_posts = Post.objects.filter(
        id__in=FavouritePost.objects.filter(
            user=request.user
        ).values_list('post_id', flat=True)
    )
    return render(
        request,
        'post/favourites.html',
        {'favourite_posts': favourite_posts}
    )
@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status = Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    return render(
        request,
        'post/comment.html',
        {
            'post':post,
            'form':form,
            'comment':comment
        }
        
    )