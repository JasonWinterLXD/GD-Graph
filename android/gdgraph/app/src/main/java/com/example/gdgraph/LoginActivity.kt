package com.example.gdgraph

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.gdgraph.api.ApiClient
import com.example.gdgraph.databinding.ActivityLoginBinding
import com.example.gdgraph.model.ErrorResponse
import com.example.gdgraph.model.LoginRequest
import com.example.gdgraph.model.LoginResponse
import com.google.gson.Gson
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class LoginActivity : AppCompatActivity() {
    private lateinit var binding: ActivityLoginBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.loginButton.setOnClickListener {
            val username = binding.usernameEditText.text.toString()
            val password = binding.passwordEditText.text.toString()
            if (username.isNotEmpty() && password.isNotEmpty()) {
                login(username, password)
            } else {
                Toast.makeText(this, "请填写用户名和密码", Toast.LENGTH_SHORT).show()
            }
        }

        binding.registerLink.setOnClickListener {
            startActivity(Intent(this, RegisterActivity::class.java))
        }
    }

    private fun login(username: String, password: String) {
        val request = LoginRequest(username, password)
        ApiClient.apiService.login(request).enqueue(object : Callback<LoginResponse> {
            override fun onResponse(call: Call<LoginResponse>, response: Response<LoginResponse>) {
                if (response.isSuccessful) {
                    val intent = Intent(this@LoginActivity, ChatActivity::class.java)
                    intent.putExtra("username", response.body()?.user)
                    startActivity(intent)
                    finish()
                } else {
                    // 尝试解析错误信息
                    try {
                        val errorBody = response.errorBody()?.string()
                        if (errorBody != null) {
                            val errorResponse = Gson().fromJson(errorBody, ErrorResponse::class.java)
                            val errorMessage = errorResponse.message ?: errorResponse.error
                            
                            when {
                                errorMessage?.contains("user not found", ignoreCase = true) == true ||
                                errorMessage?.contains("username not exist", ignoreCase = true) == true ||
                                errorMessage?.contains("user does not exist", ignoreCase = true) == true -> {
                                    Toast.makeText(this@LoginActivity, "用户名不存在", Toast.LENGTH_SHORT).show()
                                }
                                errorMessage?.contains("incorrect password", ignoreCase = true) == true ||
                                errorMessage?.contains("wrong password", ignoreCase = true) == true ||
                                errorMessage?.contains("invalid password", ignoreCase = true) == true -> {
                                    Toast.makeText(this@LoginActivity, "密码错误", Toast.LENGTH_SHORT).show()
                                }
                                else -> {
                                    Toast.makeText(this@LoginActivity, "登录失败: $errorMessage", Toast.LENGTH_SHORT).show()
                                }
                            }
                        } else {
                            Toast.makeText(this@LoginActivity, "登录失败: ${response.code()}", Toast.LENGTH_SHORT).show()
                        }
                    } catch (e: Exception) {
                        Toast.makeText(this@LoginActivity, "登录失败", Toast.LENGTH_SHORT).show()
                    }
                }
            }

            override fun onFailure(call: Call<LoginResponse>, t: Throwable) {
                Toast.makeText(this@LoginActivity, "网络错误", Toast.LENGTH_SHORT).show()
            }
        })
    }
}