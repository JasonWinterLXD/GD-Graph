package com.example.gdgraph

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.gdgraph.api.ApiClient
import com.example.gdgraph.databinding.ActivityRegisterBinding
import com.example.gdgraph.model.ErrorResponse
import com.example.gdgraph.model.RegisterRequest
import com.example.gdgraph.model.RegisterResponse
import com.google.gson.Gson
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class RegisterActivity : AppCompatActivity() {
    private lateinit var binding: ActivityRegisterBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRegisterBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.registerButton.setOnClickListener {
            val username = binding.usernameEditText.text.toString()
            val email = binding.emailEditText.text.toString()
            val password = binding.passwordEditText.text.toString()
            val confirmPassword = binding.confirmPasswordEditText.text.toString()
            
            if (username.isNotEmpty() && email.isNotEmpty() && 
                password.isNotEmpty() && confirmPassword.isNotEmpty()) {
                if (password == confirmPassword) {
                    register(username, email, password)
                } else {
                    Toast.makeText(this, "两次输入的密码不一致", Toast.LENGTH_SHORT).show()
                }
            } else {
                Toast.makeText(this, "请填写所有字段", Toast.LENGTH_SHORT).show()
            }
        }

        binding.loginLink.setOnClickListener {
            startActivity(Intent(this, LoginActivity::class.java))
        }
    }

    private fun register(username: String, email: String, password: String) {
        val request = RegisterRequest(username, email, password)
        ApiClient.apiService.register(request).enqueue(object : Callback<RegisterResponse> {
            override fun onResponse(call: Call<RegisterResponse>, response: Response<RegisterResponse>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@RegisterActivity, "注册成功，请登录", Toast.LENGTH_SHORT).show()
                    startActivity(Intent(this@RegisterActivity, LoginActivity::class.java))
                    finish()
                } else {
                    // 尝试解析错误信息
                    try {
                        val errorBody = response.errorBody()?.string()
                        if (errorBody != null) {
                            val errorResponse = Gson().fromJson(errorBody, ErrorResponse::class.java)
                            val errorMessage = errorResponse.message ?: errorResponse.error
                            
                            when {
                                errorMessage?.contains("username already exists", ignoreCase = true) == true -> {
                                    Toast.makeText(this@RegisterActivity, "用户名已存在", Toast.LENGTH_SHORT).show()
                                }
                                errorMessage?.contains("email already exists", ignoreCase = true) == true -> {
                                    Toast.makeText(this@RegisterActivity, "邮箱已被注册", Toast.LENGTH_SHORT).show()
                                }
                                errorMessage?.contains("already exists", ignoreCase = true) == true -> {
                                    Toast.makeText(this@RegisterActivity, "用户名或邮箱已被注册", Toast.LENGTH_SHORT).show()
                                }
                                else -> {
                                    Toast.makeText(this@RegisterActivity, "注册失败: $errorMessage", Toast.LENGTH_SHORT).show()
                                }
                            }
                        } else {
                            Toast.makeText(this@RegisterActivity, "注册失败: ${response.code()}", Toast.LENGTH_SHORT).show()
                        }
                    } catch (e: Exception) {
                        Toast.makeText(this@RegisterActivity, "注册失败", Toast.LENGTH_SHORT).show()
                    }
                }
            }

            override fun onFailure(call: Call<RegisterResponse>, t: Throwable) {
                Toast.makeText(this@RegisterActivity, "网络错误", Toast.LENGTH_SHORT).show()
            }
        })
    }
}