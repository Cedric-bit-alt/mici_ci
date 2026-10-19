from django.contrib import admin
from .models import Post, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin pour le modèle Post"""
    list_display = ('title', 'author', 'created_at', 'updated_at', 'get_likes_count')
    list_filter = ('created_at', 'author')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'slug', 'author', 'image')
        }),
        ('Contenu', {
            'fields': ('content',)
        }),
        ('Métadonnées', {
            'fields': ('likes', 'created_at', 'updated_at')
        }),
    )
    
    filter_horizontal = ('likes',)
    
    def get_likes_count(self, obj):
        return obj.get_likes_count()
    get_likes_count.short_description = 'Nombre de likes'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin pour le modèle Comment"""
    list_display = ('user', 'post', 'created_at', 'approved')
    list_filter = ('approved', 'created_at')
    search_fields = ('user__username', 'post__title', 'content')
    list_editable = ('approved',)
    readonly_fields = ('created_at',)
