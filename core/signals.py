import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

# Local imports
from .models import AdminUsers, PortfolioImages, Professionals, Books, Events, Materials, MobileUsers, Notifications


def delete_file(path):
    if os.path.isfile(path):
        os.remove(path)

@receiver(post_delete, sender=AdminUsers)
@receiver(post_delete, sender=Books)
@receiver(post_delete, sender=Materials)
@receiver(post_delete, sender=Events)
@receiver(post_delete, sender=MobileUsers)
@receiver(post_delete, sender=Notifications)
@receiver(post_delete, sender=PortfolioImages)
def delete_associated_files(sender, instance, **kwargs):
    if instance.image:
        delete_file(instance.image.path)

@receiver(pre_save, sender=AdminUsers)
@receiver(pre_save, sender=Books)
@receiver(pre_save, sender=Materials)
@receiver(pre_save, sender=Events)
@receiver(pre_save, sender=MobileUsers)
@receiver(pre_save, sender=Notifications)
@receiver(post_delete, sender=PortfolioImages)
def delete_old_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_file = sender.objects.get(pk=instance.pk).image
    except sender.DoesNotExist:
        return

    if old_file != instance.image:
        if old_file:
            delete_file(old_file.path)
        return


@receiver(post_delete, sender=Professionals)
def delete_associated_files(sender, instance, **kwargs):
    if instance.banner:
        delete_file(instance.banner.path)

@receiver(pre_save, sender=Professionals)
def delete_old_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_banner = sender.objects.get(pk=instance.pk).banner
    except sender.DoesNotExist:
        return 

    if old_banner:
        new_file = instance.banner
        if old_banner != new_file:
            if old_banner:
                delete_file(old_banner.path)
