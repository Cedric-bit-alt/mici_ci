from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


@receiver(post_migrate)
def create_default_admin(sender, **kwargs):
    """Crée un admin par défaut si aucun superutilisateur n'existe"""
    # Ne s'exécuter que pour l'application accounts
    if sender.name == 'accounts':
        # Utiliser une transaction pour éviter les créations multiples
        with transaction.atomic():
            # Vérifier si un superutilisateur existe déjà
            if not User.objects.filter(is_superuser=True).exists():
                # Vérifier aussi si l'utilisateur 'admin' existe déjà
                admin_username = 'admin'
                if not User.objects.filter(username=admin_username).exists():
                    try:
                        # Créer l'admin par défaut
                        admin_email = 'admin@mici.com'
                        admin_password = 'admin123'  # À changer en production !
                        
                        admin_user = User.objects.create_superuser(
                            username=admin_username,
                            email=admin_email,
                            password=admin_password,
                            role='Admin',
                            first_name='Administrateur',
                            last_name='MICI'
                        )
                        print(f"\n{'='*50}")
                        print("✓ Admin par défaut créé avec succès !")
                        print(f"{'='*50}")
                        print(f"Nom d'utilisateur: {admin_username}")
                        print(f"Email: {admin_email}")
                        print(f"Mot de passe: {admin_password}")
                        print(f"{'='*50}")
                        print("⚠️  ATTENTION: Changez le mot de passe en production !")
                        print(f"{'='*50}\n")
                    except Exception as e:
                        print(f"\n⚠️  Erreur lors de la création de l'admin par défaut: {e}\n")

