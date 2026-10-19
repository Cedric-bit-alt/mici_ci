from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée un admin par défaut si aucun superutilisateur n\'existe'

    def handle(self, *args, **options):
        # Vérifier si un superutilisateur existe déjà
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING('Un superutilisateur existe déjà. Aucun admin par défaut créé.')
            )
            return

        # Vérifier si l'utilisateur 'admin' existe déjà
        admin_username = 'admin'
        if User.objects.filter(username=admin_username).exists():
            self.stdout.write(
                self.style.WARNING(f'L\'utilisateur "{admin_username}" existe déjà. Aucun admin par défaut créé.')
            )
            return

        # Créer l'admin par défaut
        admin_email = 'admin@mici.com'
        admin_password = 'admin123'  # À changer en production !

        try:
            admin_user = User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                role='Admin',
                first_name='Administrateur',
                last_name='MICI'
            )
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Admin par défaut créé avec succès !\n')
            )
            self.stdout.write(f'Nom d\'utilisateur: {admin_username}')
            self.stdout.write(f'Email: {admin_email}')
            self.stdout.write(f'Mot de passe: {admin_password}')
            self.stdout.write(
                self.style.WARNING('\n⚠️  ATTENTION: Changez le mot de passe en production !\n')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de la création de l\'admin par défaut: {e}')
            )

