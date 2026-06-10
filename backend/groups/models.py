from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Group(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        MEMBER = 'member', 'Member'
        ADMIN = 'admin', 'Admin'
        HEAD_ADMIN = 'head_admin', 'Head Admin'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)

    class Meta:
        unique_together = ('user', 'group')

    def __str__(self):
        return f'{self.user.username} in {self.group.name} ({self.role})'


class Invitation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations_received')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations_sent')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'invited_user')

    def __str__(self):
        return f'Invitation for {self.invited_user.username} to {self.group.name} ({self.status})'


class Ban(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='bans')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bans_received')
    banned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bans_given')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f'{self.user.username} banned from {self.group.name}'


@receiver(post_save, sender=User)
def create_personal_group(sender, instance, created, **kwargs):
    if created:
        group = Group.objects.create(
            name=f"{instance.username}'s Personal Group",
            owner=instance
        )
        Membership.objects.create(
            user=instance,
            group=group,
            role=Membership.Role.HEAD_ADMIN
        )
