package com.chatter.data.api

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class User(
    val id: Int,
    val username: String,
    val email: String,
    @Json(name = "first_name") val firstName: String,
    @Json(name = "last_name") val lastName: String
)

@JsonClass(generateAdapter = true)
data class AuthToken(
    val token: String
)

@JsonClass(generateAdapter = true)
data class Group(
    val id: Int,
    val name: String,
    val owner: User,
    @Json(name = "created_at") val createdAt: String
)

@JsonClass(generateAdapter = true)
data class GroupDetail(
    val id: Int,
    val name: String,
    val owner: User,
    @Json(name = "created_at") val createdAt: String,
    val memberships: List<Membership>
)

@JsonClass(generateAdapter = true)
data class Membership(
    val id: Int,
    val user: User,
    val role: String // "member", "admin", "head_admin"
)

@JsonClass(generateAdapter = true)
data class Invitation(
    val id: Int,
    val group: Group,
    @Json(name = "invited_user") val invitedUser: User,
    @Json(name = "invited_by") val invitedBy: User,
    val status: String,
    @Json(name = "created_at") val createdAt: String
)

@JsonClass(generateAdapter = true)
data class Message(
    val id: Int,
    val group: Int,
    val sender: Int,
    @Json(name = "sender_username") val senderUsername: String,
    val body: String?,
    val attachments: List<Attachment>,
    @Json(name = "created_at") val createdAt: String
)

@JsonClass(generateAdapter = true)
data class Attachment(
    val id: Int,
    val file: String,
    val kind: String, // "image", "video", "voice"
    @Json(name = "created_at") val createdAt: String
)

// Request Models
@JsonClass(generateAdapter = true)
data class CreateGroupRequest(
    val name: String
)

@JsonClass(generateAdapter = true)
data class InviteUserRequest(
    val username: String
)

@JsonClass(generateAdapter = true)
data class PromoteUserRequest(
    val role: String
)
