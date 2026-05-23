import pytest
from django.contrib.auth import get_user_model
from .models import Group, Membership, Invitation, Ban

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def another_user():
    return User.objects.create_user(
        username='anotheruser',
        email='another@example.com',
        password='anotherpass123'
    )


@pytest.fixture
def group(user):
    return Group.objects.create(
        name='Test Group',
        owner=user
    )


@pytest.mark.django_db
class TestSignalCreatePersonalGroup:
    def test_personal_group_created_on_user_creation(self):
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        assert Group.objects.filter(owner=user).exists()

    def test_personal_group_name_format(self):
        user = User.objects.create_user(
            username='john',
            email='john@example.com',
            password='password123'
        )
        personal_group = Group.objects.get(owner=user)
        assert personal_group.name == "john's Personal Group"

    def test_user_added_as_head_admin_to_personal_group(self):
        user = User.objects.create_user(
            username='jane',
            email='jane@example.com',
            password='password123'
        )
        personal_group = Group.objects.get(owner=user)
        membership = Membership.objects.get(user=user, group=personal_group)
        assert membership.role == Membership.Role.HEAD_ADMIN

    def test_personal_group_only_created_once(self):
        user = User.objects.create_user(
            username='uniqueuser',
            email='unique@example.com',
            password='password123'
        )
        personal_groups = Group.objects.filter(owner=user)
        assert personal_groups.count() == 1


@pytest.mark.django_db
class TestGroupModel:
    def test_group_creation(self, user):
        group = Group.objects.create(name='My Group', owner=user)
        assert group.name == 'My Group'
        assert group.owner == user
        assert group.created_at is not None

    def test_group_str(self, user):
        group = Group.objects.create(name='Test Group', owner=user)
        assert str(group) == 'Test Group'


@pytest.mark.django_db
class TestMembershipModel:
    def test_membership_creation(self, user, group):
        membership = Membership.objects.create(
            user=user,
            group=group,
            role=Membership.Role.ADMIN
        )
        assert membership.user == user
        assert membership.group == group
        assert membership.role == Membership.Role.ADMIN

    def test_membership_default_role_is_member(self, user, group):
        membership = Membership.objects.create(user=user, group=group)
        assert membership.role == Membership.Role.MEMBER

    def test_membership_role_choices(self):
        assert Membership.Role.MEMBER == 'member'
        assert Membership.Role.ADMIN == 'admin'
        assert Membership.Role.HEAD_ADMIN == 'head_admin'

    def test_membership_unique_constraint(self, user, group):
        Membership.objects.create(user=user, group=group)
        with pytest.raises(Exception):
            Membership.objects.create(user=user, group=group)

    def test_membership_str(self, user, group):
        membership = Membership.objects.create(user=user, group=group, role=Membership.Role.ADMIN)
        assert 'testuser' in str(membership)
        assert 'Test Group' in str(membership)
        assert 'admin' in str(membership).lower()


@pytest.mark.django_db
class TestInvitationModel:
    def test_invitation_creation(self, group, user, another_user):
        invitation = Invitation.objects.create(
            group=group,
            invited_user=another_user,
            invited_by=user
        )
        assert invitation.group == group
        assert invitation.invited_user == another_user
        assert invitation.invited_by == user
        assert invitation.status == Invitation.Status.PENDING
        assert invitation.created_at is not None

    def test_invitation_status_choices(self):
        assert Invitation.Status.PENDING == 'pending'
        assert Invitation.Status.ACCEPTED == 'accepted'
        assert Invitation.Status.DECLINED == 'declined'

    def test_invitation_unique_constraint(self, group, user, another_user):
        Invitation.objects.create(
            group=group,
            invited_user=another_user,
            invited_by=user
        )
        with pytest.raises(Exception):
            Invitation.objects.create(
                group=group,
                invited_user=another_user,
                invited_by=user
            )

    def test_invitation_str(self, group, user, another_user):
        invitation = Invitation.objects.create(
            group=group,
            invited_user=another_user,
            invited_by=user
        )
        assert 'anotheruser' in str(invitation)
        assert 'Test Group' in str(invitation)


@pytest.mark.django_db
class TestBanModel:
    def test_ban_creation(self, group, user, another_user):
        ban = Ban.objects.create(
            group=group,
            user=another_user,
            banned_by=user
        )
        assert ban.group == group
        assert ban.user == another_user
        assert ban.banned_by == user
        assert ban.created_at is not None

    def test_ban_unique_constraint(self, group, user, another_user):
        Ban.objects.create(group=group, user=another_user, banned_by=user)
        with pytest.raises(Exception):
            Ban.objects.create(group=group, user=another_user, banned_by=user)

    def test_ban_str(self, group, user, another_user):
        ban = Ban.objects.create(group=group, user=another_user, banned_by=user)
        assert 'anotheruser' in str(ban)
        assert 'Test Group' in str(ban)
