package com.chatter.data.api

import retrofit2.http.*

interface GroupsApi {
    @GET("api/groups/")
    suspend fun getGroups(): List<Group>

    @POST("api/groups/")
    suspend fun createGroup(@Body request: CreateGroupRequest): Group

    @GET("api/groups/{id}/")
    suspend fun getGroupDetail(@Path("id") id: Int): GroupDetail

    @POST("api/groups/{id}/invitations/")
    suspend fun inviteUser(@Path("id") id: Int, @Body request: InviteUserRequest): Invitation

    @POST("api/invitations/{id}/accept/")
    suspend fun acceptInvitation(@Path("id") id: Int)

    @POST("api/groups/{id}/members/{user_id}/kick/")
    suspend fun kickMember(@Path("id") groupId: Int, @Path("user_id") userId: Int)

    @POST("api/groups/{id}/members/{user_id}/promote/")
    suspend fun promoteMember(@Path("id") groupId: Int, @Path("user_id") userId: Int, @Body request: PromoteUserRequest)

    @POST("api/groups/{id}/members/{user_id}/ban/")
    suspend fun banMember(@Path("id") groupId: Int, @Path("user_id") userId: Int)
}
