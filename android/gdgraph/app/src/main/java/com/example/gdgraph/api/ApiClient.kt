package com.example.gdgraph.api

import okhttp3.JavaNetCookieJar
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.net.CookieManager
import java.util.concurrent.TimeUnit

object ApiClient {
    private const val BASE_URL = "http://8.210.25.250:80/"

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)  // 连接超时
        .readTimeout(30, TimeUnit.SECONDS)     // 读取超时
        .writeTimeout(30, TimeUnit.SECONDS)    // 写入超时
        .cookieJar(JavaNetCookieJar(CookieManager()))
        .build()

    val apiService: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}