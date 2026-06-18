<script setup>
import { ref } from 'vue';

const fileRef = ref(null) // 文件选择框
const result_context = ref('') // 解析结果
const loading = ref(false) // 加载中
const progressPercent = ref(0) // 进度条

// 选择文件
const handleSelect = async (e) => {
  const file = e.target.files[0]
  if (!file) return
  const suffix = file.name.split('.').pop().toLowerCase()
  if (!['pdf', 'doc', 'docx'].includes(suffix)) {
    alert('请选择pdf、doc、docx格式的文件')
    e.target.value = ''
    return
  }

  loading.value = true
  result_context.value = ''
  progressPercent.value = 10

  const formData = new FormData()
  formData.append('file', file)

  progressPercent.value = 30
  try {
    const res = await fetch('http://127.0.0.1:8000/api/v1/upload', {
      method: 'POST',
      body: formData
    })

    progressPercent.value = 50
    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')

    progressPercent.value = 80

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value, { stream: true })
      // ==========【核心改动】每次收到分片立刻追加渲染，不要等全部结束 ==========
      result_context.value += chunk
      console.log(result_context);
      
    }
    // 冲刷缓冲区剩余字符
    const remain = decoder.decode()
    if (remain) result_context.value += remain

    progressPercent.value = 100
  } catch (err) {
    alert('上传或解析失败：' + err.message)
    console.error(err)
  } finally {
    loading.value = false
    e.target.value = ''
  }
}
</script>

<template>
<div class="upload-wrap">
  <input
    type="file"
    ref="fileRef"
    accept=".pdf,.doc,.docx"
    @change="handleSelect"
    hidden
  />
  <button @click="$refs.fileRef.click()" :disabled="loading">
    {{ loading ? 'AI审查中...' : '请选择文件上传' }}
  </button>
  <progress :value="progressPercent" max="100"></progress>
  <!-- v-html实时响应result_context变化 -->
  <div class="contract-content" v-if="result_context" v-html="result_context"></div>
</div>
</template>

<style scoped>
.upload-wrap {
  padding: 20px;
}
button {
  padding: 8px 16px;
  cursor: pointer;
}
button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
.contract-content {
  margin-top: 20px;
  white-space: pre-wrap;
  font-family: '微软雅黑', sans-serif;
  line-height: 1.8;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}
.contract-content mark {
  background-color: #fff3cd;
  padding: 2px 4px;
  border-radius: 3px;
}
/* 自定义标签必须用 :deep()，标签名加尖括号匹配 */
:deep(risk) {
  display: inline-block;
  background-color: #f8d7da;
  color: #721c24;
  font-size: 12px;
  padding: 1px 6px;
  border-radius: 10px;
  margin-left: 4px;
}
:deep(safe) {
  background-color: #d4edda;
  padding: 2px 4px;
  border-radius: 3px;
  border-bottom: 2px solid #28a745;
}
</style>