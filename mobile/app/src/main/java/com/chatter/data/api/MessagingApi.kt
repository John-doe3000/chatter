package com.chatter.data.api

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.http.*

interface MessagingApi {
    @GET("api/groups/{id}/messages/")
    suspend fun getMessages(
        @Path("id") groupId: Int,
        @Query("since") since: String? = null
    ): List<Message>

    @Multipart
    @POST("api/groups/{id}/messages/")
    suspend fun sendMessage(
        @Path("id") groupId: Int,
        @Part("body") body: RequestBody?,
        @Part attachment: MultipartBody.Part?,
        @Part("kind") kind: RequestBody?
    ): Message
}
