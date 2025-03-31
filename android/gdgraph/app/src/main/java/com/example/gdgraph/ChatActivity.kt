package com.example.gdgraph

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.gdgraph.adapter.MessageAdapter
import com.example.gdgraph.api.ApiClient
import com.example.gdgraph.databinding.ActivityChatBinding
import com.example.gdgraph.model.AnswerResponse
import com.example.gdgraph.model.Message
import com.example.gdgraph.model.QuestionRequest
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class ChatActivity : AppCompatActivity() {
    private lateinit var binding: ActivityChatBinding
    private val messageList = mutableListOf<Message>()
    private lateinit var adapter: MessageAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityChatBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val username = intent.getStringExtra("username") ?: "用户"
        binding.usernameTextView.text = "欢迎，$username"

        adapter = MessageAdapter(messageList)
        binding.recyclerView.layoutManager = LinearLayoutManager(this)
        binding.recyclerView.adapter = adapter

        binding.sendButton.setOnClickListener {
            val question = binding.inputEditText.text.toString().trim()
            if (question.isNotEmpty()) {
                addMessage(question, "user")
                binding.inputEditText.text?.clear()
                sendQuestion(question)
            }
        }

        binding.logoutButton.setOnClickListener {
            logout()
        }
    }

    private fun addMessage(text: String, type: String) {
        messageList.add(Message(text, type))
        adapter.notifyItemInserted(messageList.size - 1)
        binding.recyclerView.scrollToPosition(messageList.size - 1)
    }

    private fun sendQuestion(question: String) {
        val request = QuestionRequest(question)
        ApiClient.apiService.sendQuestion(request).enqueue(object : Callback<AnswerResponse> {
            override fun onResponse(call: Call<AnswerResponse>, response: Response<AnswerResponse>) {
                if (response.isSuccessful) {
                    val answer = response.body()?.answer ?: "未能获取答案"
                    addMessage(answer, "bot")
                } else {
                    val errorMessage = when (response.code()) {
                        401 -> "登录已过期，请重新登录"
                        500 -> "服务器内部错误，请稍后重试"
                        else -> "获取答案失败，错误码: ${response.code()}"
                    }
                    addMessage(errorMessage, "bot")
                    if (response.code() == 401) {
                        startActivity(Intent(this@ChatActivity, LoginActivity::class.java))
                        finish()
                    }
                }
            }

            override fun onFailure(call: Call<AnswerResponse>, t: Throwable) {
                val errorMessage = when {
                    t is java.net.SocketTimeoutException -> "请求超时，请稍后重试"
                    t is java.net.UnknownHostException -> "无法连接到服务器，请检查网络"
                    else -> "网络错误: ${t.message}"
                }
                addMessage(errorMessage, "bot")
                android.util.Log.e("ChatActivity", "Network error", t)
            }
        })
    }

    private fun logout() {
        ApiClient.apiService.logout().enqueue(object : Callback<Void> {
            override fun onResponse(call: Call<Void>, response: Response<Void>) {
                if (response.isSuccessful) {
                    startActivity(Intent(this@ChatActivity, MainActivity::class.java))
                    finish()
                } else {
                    Toast.makeText(this@ChatActivity, "登出失败，错误码: ${response.code()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<Void>, t: Throwable) {
                Toast.makeText(this@ChatActivity, "登出失败: 网络错误", Toast.LENGTH_SHORT).show()
            }
        })
    }
}