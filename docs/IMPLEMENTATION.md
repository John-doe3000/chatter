# Chatter

This app is an Android client app developed in Android studio and maintained in the /mobile directory, and a Django DRF backend app that is maintained in the /backend directory. The app should:

- allow uses to have private text messages between each other
- When a new user joins, they're assigned their own personal group and are admin on that group.
- Users can also create new groups and are automatically the admin of that group.
- Users can invite other people to groups they're admin for. They can also kick people out of groups they're admin in, and can also promote other users in a group that they're admin for to being an admin.
- There should be two levels of admin: head admin and admin. Head admins can permanently ban users from a group.
- The backend should use sqlite as a database, and use polling on a 30-second interval for new messages
