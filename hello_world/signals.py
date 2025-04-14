from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, CleoDocument
from .utils import upsert_to_pinecone

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=CleoDocument)
def handle_embedding(sender, instance, created, **kwargs):
    if created or not instance.embedding_id:
        upsert_to_pinecone(instance)