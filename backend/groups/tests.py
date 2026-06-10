import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from .models import Group, Membership, Invitation, Ban

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


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
def third_user():
    return User.objects.create_user(
        username='thirduser',
        email='third@example.com',
        password='thirdpass123'
    )


@pytest.fixture
def group(user):
    group = Group.objects.create(
        name='Test Group',
        owner=user
    )
    Membership.objects.create(user=user, group=group, role=Membership.Role.HEAD_ADMIN)
    return group


@pytest.fixture
def group_no_membership(user):
    return Group.objects.create(
        name='Test Group',
        owner=user
    )


@pytest.fixture
def authenticated_client(api_client, user):
    token = Token.objects.get_or_create(user=user)[0]
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


@pytest.fixture
def another_authenticated_client(api_client, another_user):
    token = Token.objects.get_or_create(user=another_user)[0]
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


@pytest.fixture
def member_in_group(user, group, another_user):
    Membership.objects.create(user=another_user, group=group, role=Membership.Role.MEMBER)
    return another_user


@pytest.fixture
def admin_in_group(user, group, another_user):
    Membership.objects.create(user=another_user, group=group, role=Membership.Role.ADMIN)
    return another_user


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
    def test_membership_creation(self, user, group_no_membership):
        membership = Membership.objects.create(
            user=user,
            group=group_no_membership,
            role=Membership.Role.ADMIN
        )
        assert membership.user == user
        assert membership.group == group_no_membership
        assert membership.role == Membership.Role.ADMIN

    def test_membership_default_role_is_member(self, user, group_no_membership):
        membership = Membership.objects.create(user=user, group=group_no_membership)
        assert membership.role == Membership.Role.MEMBER

    def test_membership_role_choices(self):
        assert Membership.Role.MEMBER == 'member'
        assert Membership.Role.ADMIN == 'admin'
        assert Membership.Role.HEAD_ADMIN == 'head_admin'

    def test_membership_unique_constraint(self, user, group_no_membership):
        Membership.objects.create(user=user, group=group_no_membership)
        with pytest.raises(Exception):
            Membership.objects.create(user=user, group=group_no_membership)

    def test_membership_str(self, user, group_no_membership):
        membership = Membership.objects.create(user=user, group=group_no_membership, role=Membership.Role.ADMIN)
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


@pytest.mark.django_db
class TestGroupListCreate:
    def test_list_groups_unauthenticated(self, api_client):
        response = api_client.get('/api/groups/')
        assert response.status_code == 401

    def test_list_groups_authenticated(self, authenticated_client, group, user):
        response = authenticated_client.get('/api/groups/')
        assert response.status_code == 200
        assert len(response.data) > 0

    def test_create_group_success(self, authenticated_client):
        response = authenticated_client.post('/api/groups/', {'name': 'New Group'})
        assert response.status_code == 201
        assert response.data['name'] == 'New Group'
        group = Group.objects.get(name='New Group')
        membership = Membership.objects.get(user__username='testuser', group=group)
        assert membership.role == Membership.Role.HEAD_ADMIN


@pytest.mark.django_db
class TestGroupDetail:
    def test_get_group_detail_as_member(self, authenticated_client, group, user):
        response = authenticated_client.get(f'/api/groups/{group.id}/')
        assert response.status_code == 200
        assert response.data['name'] == 'Test Group'
        assert 'memberships' in response.data


@pytest.mark.django_db
class TestInvitePermissions:
    def test_invite_as_head_admin_success(self, authenticated_client, group, user, another_user):
        response = authenticated_client.post(
            f'/api/groups/{group.id}/invite/',
            {'username': 'anotheruser'}
        )
        assert response.status_code == 201
        assert Invitation.objects.filter(invited_user=another_user, group=group).exists()

    def test_invite_as_member_fails(self, api_client, group, user, another_user, member_in_group):
        token = Token.objects.get_or_create(user=member_in_group)[0]
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        third_user = User.objects.create_user(username='thirduser', password='pass')

        response = api_client.post(
            f'/api/groups/{group.id}/invite/',
            {'username': 'thirduser'}
        )
        assert response.status_code == 403

    def test_invite_banned_user_fails(self, authenticated_client, group, user, another_user):
        Ban.objects.create(group=group, user=another_user, banned_by=user)
        response = authenticated_client.post(
            f'/api/groups/{group.id}/invite/',
            {'username': 'anotheruser'}
        )
        assert response.status_code == 400
        assert 'banned' in response.data['detail'].lower()

    def test_invite_already_member_fails(self, authenticated_client, group, user, another_user):
        Membership.objects.create(user=another_user, group=group, role=Membership.Role.MEMBER)
        response = authenticated_client.post(
            f'/api/groups/{group.id}/invite/',
            {'username': 'anotheruser'}
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestKickPermissions:
    def test_kick_as_admin_success(self, api_client, group, user, another_user, third_user):
        Membership.objects.create(user=another_user, group=group, role=Membership.Role.ADMIN)
        Membership.objects.create(user=third_user, group=group, role=Membership.Role.MEMBER)

        token = Token.objects.get_or_create(user=another_user)[0]
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = api_client.post(
            f'/api/groups/{group.id}/kick/',
            {'username': 'thirduser'}
        )
        assert response.status_code == 200

    def test_kick_as_member_fails(self, api_client, group, user, another_user, member_in_group):
        token = Token.objects.get_or_create(user=member_in_group)[0]
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = api_client.post(
            f'/api/groups/{group.id}/kick/',
            {'username': 'anotheruser'}
        )
        assert response.status_code == 403

    def test_kick_removes_membership(self, authenticated_client, group, user, another_user):
        Membership.objects.create(user=another_user, group=group, role=Membership.Role.MEMBER)
        assert Membership.objects.filter(user=another_user, group=group).exists()

        response = authenticated_client.post(
            f'/api/groups/{group.id}/kick/',
            {'username': 'anotheruser'}
        )
        assert response.status_code == 200
        assert not Membership.objects.filter(user=another_user, group=group).exists()


@pytest.mark.django_db
class TestPromotePermissions:
    def test_promote_as_admin_success(self, api_client, group, user, another_user, third_user):
        Membership.objects.create(user=another_user, group=group, role=Membership.Role.ADMIN)
        Membership.objects.create(user=third_user, group=group, role=Membership.Role.MEMBER)

        token = Token.objects.get_or_create(user=another_user)[0]
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = api_client.post(
            f'/api/groups/{group.id}/promote/',
            {'username': 'thirduser', 'role': 'admin'}
        )
        assert response.status_code == 200

    def test_promote_as_member_fails(self, api_client, group, user, another_user, member_in_group):
        token = Token.objects.get_or_create(user=member_in_group)[0]
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = api_client.post(
            f'/api/groups/{group.id}/promote/',
            {'username': 'anotheruser', 'role': 'admin'}
        )
        assert response.status_code == 403

    def test_promote_updates_role(self, authenticated_client, group, user, another_user):
        Membership.objects.create(user=another_user, group=group, role=Membership.Role.MEMBER)

        response = authenticated_client.post(
            f'/api/groups/{group.id}/promote/',
            {'username': 'anotheruser', 'role': 'admin'}
        )
        assert response.status_code == 200
        membership = Membership.objects.get(user=another_user, group=group)
        assert membership.role == Membership.Role.ADMIN


@pytest.mark.django_db
class TestBanPermissions:
    def test_ban_as_head_admin_success(self, authenticated_client, group, user, another_user):
        Membership.objects.create(user=another_user, group=group, role=Membership.Role.MEMBER)
        response = authenticated_client.post(
            f'/api/groups/{group.id}/ban/',
            {'username': 'anotheruser'}
        )
        assert response.status_code == 200
        assert Ban.objects.filter(group=group, user=another_user).exists()

    def test_ban_as_admin_fails(self, api_client, group, user, another_user):
        Membership.objects.create(user=another_user, group=group, role=Membership.Role.ADMIN)
        token = Token.objects.get_or_create(user=another_user)[0]
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        third_user = User.objects.create_user(username='thirduser', password='pass')
        Membership.objects.create(user=third_user, group=group, role=Membership.Role.MEMBER)

        response = api_client.post(
            f'/api/groups/{group.id}/ban/',
            {'username': 'thirduser'}
        )
        assert response.status_code == 403

    def test_ban_removes_membership_and_invitations(self, authenticated_client, group, user, another_user):
        Membership.objects.create(user=another_user, group=group, role=Membership.Role.MEMBER)
        Invitation.objects.create(group=group, invited_user=another_user, invited_by=user)

        response = authenticated_client.post(
            f'/api/groups/{group.id}/ban/',
            {'username': 'anotheruser'}
        )
        assert response.status_code == 200
        assert not Membership.objects.filter(user=another_user, group=group).exists()
        assert not Invitation.objects.filter(invited_user=another_user, group=group).exists()


@pytest.mark.django_db
class TestInvitationAcceptDecline:
    def test_accept_invitation_success(self, api_client, group, user, another_user):
        invitation = Invitation.objects.create(
            group=group,
            invited_user=another_user,
            invited_by=user
        )
        token = Token.objects.get_or_create(user=another_user)[0]
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = api_client.post(
            '/api/groups/accept_invitation/',
            {'invitation_id': invitation.id}
        )
        assert response.status_code == 200
        assert Membership.objects.filter(user=another_user, group=group).exists()
        invitation.refresh_from_db()
        assert invitation.status == Invitation.Status.ACCEPTED

    def test_decline_invitation_success(self, api_client, group, user, another_user):
        invitation = Invitation.objects.create(
            group=group,
            invited_user=another_user,
            invited_by=user
        )
        token = Token.objects.get_or_create(user=another_user)[0]
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = api_client.post(
            '/api/groups/decline_invitation/',
            {'invitation_id': invitation.id}
        )
        assert response.status_code == 200
        invitation.refresh_from_db()
        assert invitation.status == Invitation.Status.DECLINED
