from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Post, Comment
from .forms import PostForm, CommentForm


def post_list(request):
    """Vue pour la liste des articles avec pagination et recherche"""
    posts = Post.objects.all()
    
    # Recherche
    query = request.GET.get('q')
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(author__username__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'blog/post_list.html', context)


def post_detail(request, slug):
    """Vue pour le détail d'un article"""
    post = get_object_or_404(Post, slug=slug)
    comments = post.comments.filter(approved=True)
    is_liked = post.is_liked_by(request.user) if request.user.is_authenticated else False
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Vous devez être connecté pour commenter.')
            return redirect('accounts:login')
        
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            messages.success(request, 'Votre commentaire a été ajouté avec succès.')
            return redirect('blog:post_detail', slug=post.slug)
    else:
        form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'form': form,
        'is_liked': is_liked,
    }
    return render(request, 'blog/post_detail.html', context)


@require_POST
@login_required
def like_post(request, slug):
    """Vue pour liker/unliker un article (AJAX)"""
    post = get_object_or_404(Post, slug=slug)
    
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'likes_count': post.get_likes_count()
    })


@login_required
def admin_dashboard(request):
    """Vue pour le tableau de bord admin"""
    if not request.user.is_admin_user():
        messages.error(request, 'Vous n\'avez pas accès à cette page.')
        return redirect('core:home')
    
    posts = Post.objects.all()
    comments = Comment.objects.all()
    users = request.user.__class__.objects.all()
    
    # Statistiques
    stats = {
        'total_posts': posts.count(),
        'total_comments': comments.count(),
        'total_likes': sum(post.get_likes_count() for post in posts),
        'total_users': users.count(),
        'pending_comments': comments.filter(approved=False).count(),
    }
    
    context = {
        'posts': posts[:10],  # 10 derniers articles
        'comments': comments[:10],  # 10 derniers commentaires
        'users': users[:10],  # 10 derniers utilisateurs
        'stats': stats,
    }
    return render(request, 'blog/admin_dashboard.html', context)


@login_required
def post_create(request):
    """Vue pour créer un article"""
    if not request.user.is_admin_user():
        messages.error(request, 'Vous n\'avez pas accès à cette page.')
        return redirect('core:home')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Article créé avec succès.')
            return redirect('blog:post_detail', slug=post.slug)
    else:
        form = PostForm()
    
    return render(request, 'blog/post_form.html', {'form': form, 'title': 'Créer un article'})


@login_required
def post_edit(request, slug):
    """Vue pour modifier un article"""
    post = get_object_or_404(Post, slug=slug)
    
    if not request.user.is_admin_user() and post.author != request.user:
        messages.error(request, 'Vous n\'avez pas accès à cette page.')
        return redirect('core:home')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article modifié avec succès.')
            return redirect('blog:post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'blog/post_form.html', {'form': form, 'post': post, 'title': 'Modifier l\'article'})


@login_required
def post_delete(request, slug):
    """Vue pour supprimer un article"""
    post = get_object_or_404(Post, slug=slug)
    
    if not request.user.is_admin_user() and post.author != request.user:
        messages.error(request, 'Vous n\'avez pas accès à cette page.')
        return redirect('core:home')
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Article supprimé avec succès.')
        return redirect('blog:post_list')
    
    return render(request, 'blog/post_confirm_delete.html', {'post': post})


@login_required
def comment_delete(request, comment_id):
    """Vue pour supprimer un commentaire"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if not request.user.is_admin_user() and comment.user != request.user:
        messages.error(request, 'Vous n\'avez pas accès à cette page.')
        return redirect('core:home')
    
    post_slug = comment.post.slug
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Commentaire supprimé avec succès.')
        return redirect('blog:post_detail', slug=post_slug)
    
    return render(request, 'blog/comment_confirm_delete.html', {'comment': comment})
