package com.chatter.data.api

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface AuthApi {
    @POST("api/auth/register/")
    suspend fun register(@Body request: Map<String, String>): AuthToken

    @POST("api/auth/login/")
    suspend fun login(@Body request: Map<String, String>): AuthToken

    @POST("api/auth/logout/")
    suspend fun logout()

    @GET("api/users/me/")
    suspend fun getCurrentUser(): User
}
