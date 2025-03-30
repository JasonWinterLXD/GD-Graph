package com.example.gdgraph.api

import com.example.gdgraph.model.*
import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.POST

interface ApiService {
    @POST("register")
    fun register(@Body request: RegisterRequest): Call<RegisterResponse>

    @POST("login")
    fun login(@Body request: LoginRequest): Call<LoginResponse>

    @POST("logout")
    fun logout(): Call<Void>

    @POST("chat")
    fun sendQuestion(@Body request: QuestionRequest): Call<AnswerResponse>
}