<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { UploadFilled } from '@element-plus/icons-vue';

const loading = ref(false) // 加载中
const progressPercent = ref(0) // 进度条
const result_context = ref('') // 解析结果
const fileList = ref([]) // 文件列表
const progressInterval = ref(null) // 进度条定时器
const startReceiving = ref(false) // 是否开始接收数据

// 平滑进度条动画
const animateProgress = (target, duration = 500) => {
  return new Promise((resolve) => {
    const start = progressPercent.value
    const startTime = performance.now()

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      const easeProgress = 1 - Math.pow(1 - progress, 3) // 缓动函数

      progressPercent.value = Math.floor(start + (target - start) * easeProgress)

      if (progress < 1) {
        requestAnimationFrame(animate)
      } else {
        resolve()
      }
    }

    requestAnimationFrame(animate)
  })
}

// 模拟进度条快速增长（适应快速响应）
const startSlowProgress = () => {
  if (progressInterval.value) {
    clearTimeout(progressInterval.value)
  }

  const intervals = [
    { threshold: 30, speed: 200, step: 7 },   // 30% 以下，每 200ms 增加 3%
    { threshold: 60, speed: 150, step: 5 },   // 30-60%，每 150ms 增加 4%
    { threshold: 85, speed: 100, step: 5 },   // 60-85%，每 100ms 增加 5%
    { threshold: 95, speed: 80, step: 3 },    // 85-95%，每 80ms 增加 3%
    { threshold: 99, speed: 120, step: 1 },   // 95-99%，每 120ms 增加 1%
  ]

  const runProgress = () => {
    const currentPercent = progressPercent.value
    let speed = 150
    let step = 3

    for (const { threshold, speed: s, step: st } of intervals) {
      if (currentPercent < threshold) {
        speed = s
        step = st
        break
      }
    }

    // 接近 100% 时快速减慢，避免跳变
    if (currentPercent >= 95) {
      const increment = Math.max(0.5, (99.5 - currentPercent) / 8)
      progressPercent.value = Math.min(99.5, currentPercent + increment)
    } else {
      progressPercent.value = Math.min(99, currentPercent + step)
    }

    // 动态调整下一次执行的时间间隔
    clearTimeout(progressInterval.value)
    progressInterval.value = setTimeout(runProgress, speed)
  }

  runProgress()
}

// 停止进度条
const stopSlowProgress = () => {
  if (progressInterval.value) {
    clearInterval(progressInterval.value)
    progressInterval.value = null
  }
}

// 上传前校验
const beforeUpload = (file) => {
  const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
  const validExtensions = ['pdf', 'doc', 'docx']
  const fileExtension = file.name.split('.').pop().toLowerCase()

  const isValid = validTypes.includes(file.type) || validExtensions.includes(fileExtension)

  if (!isValid) {
    ElMessage.error('请上传 PDF、DOC 或 DOCX 格式的文件')
    return false
  }

  const maxSize = 20 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 20MB')
    return false
  }

  return true
}

// 文件上传处理
const handleFileUpload = async (file) => {
  if (!beforeUpload(file.raw)) {
    fileList.value = []
    return false
  }

  loading.value = true
  result_context.value = ''
  progressPercent.value = 0
  startReceiving.value = false

  // 开始缓慢增长进度条
  startSlowProgress()

  await animateProgress(15, 800) // 初始 15%

  const formData = new FormData()
  formData.append('file', file.raw)

  try {
    const res = await fetch('http://127.0.0.1:8000/api/v1/upload', {
      method: 'POST',
      body: formData
    })

    if (!res.ok) {
      throw new Error(`上传失败: ${res.status}`)
    }

    // 开始接收数据
    startReceiving.value = true

    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value, { stream: true })
      result_context.value += chunk
    }

    // 冲刷缓冲区剩余字符
    const remain = decoder.decode()
    if (remain) result_context.value += remain

    // 完成时平滑到 100%
    stopSlowProgress()
    await animateProgress(100, 600)
    ElMessage.success('解析完成！')

  } catch (err) {
    ElMessage.error('上传或解析失败：' + err.message)
    console.error(err)
    stopSlowProgress()
    progressPercent.value = 0
  } finally {
    loading.value = false
    fileList.value = []
  }

  return false // 阻止自动上传
}
</script>

<template>
  <div class="upload-container">
    <!-- 头部标题 -->
    <div class="header">
      <div class="header-icon">📄</div>
      <h1>合同智能审查</h1>
      <p class="subtitle">上传您的合同文件，AI 将自动识别并标注潜在风险点</p>
    </div>

    <!-- 文件上传区域 -->
    <div class="upload-card">
      <el-upload
        drag
        v-model:file-list="fileList"
        :auto-upload="false"
        :show-file-list="true"
        :limit="1"
        :on-change="handleFileUpload"
        :disabled="loading"
        accept=".pdf,.doc,.docx"
        class="upload-drag"
      >
        <div class="upload-content">
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、Word（doc/docx）格式，文件大小不超过 20MB
          </div>
        </template>
      </el-upload>

      <!-- 进度条 -->
      <div v-if="loading" class="progress-container">
        <div class="progress-wrapper">
          <el-progress
            :percentage="Math.floor(progressPercent)"
            :status="progressPercent >= 99.5 ? 'success' : ''"
            :stroke-width="10"
            :show-text="false"
            striped
            striped-flow
          />
          <div class="progress-info">
            <span class="percentage-value">{{ Math.floor(progressPercent) }}%</span>
            <span class="loading-text">
              {{ progressPercent < 30 ? '正在上传文件...' : progressPercent < 70 ? 'AI 正在分析合同内容...' : '正在生成分析报告...' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 解析结果展示 -->
    <transition name="fade-slide">
      <div v-if="result_context" class="result-card">
        <div class="result-header">
          <div class="header-left">
            <div class="header-icon-small">📋</div>
            <h2>审查结果</h2>
          </div>
          <el-tag type="success" size="large" class="success-tag">
            <el-icon><check /></el-icon>
            分析完成
          </el-tag>
        </div>
        <div class="contract-content" v-html="result_context"></div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
/* 动画关键帧 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* 过渡动画 */
.fade-slide-enter-active {
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(40px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.upload-container {
  max-width: 100vw;
  margin: 0 auto;
  padding: 40px 20px;
  min-height: 100vh;
  background: #e3f1ff;
  animation: fadeIn 0.8s ease;
}

.header {
  text-align: center;
  color: white;
  margin-bottom: 40px;
  animation: slideUp 0.8s ease;
}

.header-icon {
  font-size: 48px;
  margin-bottom: 16px;
  animation: pulse 3s ease-in-out infinite;
}

.header h1 {
  font-size: 36px;
  font-weight: 600;
  margin: 0 0 12px 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
  letter-spacing: 1px;
}

.subtitle {
  font-size: 16px;
  opacity: 0.95;
  margin: 0;
  font-weight: 300;
  letter-spacing: 0.5px;
}

.upload-card {
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  margin-bottom: 30px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.upload-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.2);
}

.upload-drag {
  width: 100%;
}

.upload-content {
  padding: 20px;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  border: 2px dashed #d9d9d9;
  border-radius: 12px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(135deg, #fafbfc 0%, #f8f9fa 100%);
}

:deep(.el-upload-dragger:hover) {
  border-color: #667eea;
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
}

:deep(.el-icon--upload) {
  font-size: 48px;
  color: #667eea;
  margin: 20px 0 16px;
  transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover .el-icon--upload) {
  color: #764ba2;
  transform: scale(1.1);
}

:deep(.el-upload__text) {
  font-size: 16px;
  color: #606266;
  font-weight: 400;
  transition: all 0.3s ease;
}

:deep(.el-upload__text em) {
  color: #667eea;
  font-weight: 500;
  font-style: normal;
  transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover .el-upload__text em) {
  color: #764ba2;
  text-decoration: underline;
  text-decoration-thickness: 2px;
  text-underline-offset: 4px;
}

.el-upload__tip {
  color: #909399;
  font-size: 14px;
  margin-top: 12px;
  text-align: center;
  font-weight: 300;
}

.progress-container {
  margin-top: 30px;
  padding: 24px;
  background: linear-gradient(135deg, #f8f9fa 0%, #f1f3f4 100%);
  border-radius: 12px;
  animation: fadeIn 0.5s ease;
}

.progress-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

:deep(.el-progress-bar__outer) {
  background: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
}

:deep(.el-progress-bar__inner) {
  border-radius: 10px;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

:deep(.el-progress.is-success .el-progress-bar__inner) {
  background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
  box-shadow: 0 2px 8px rgba(64, 192, 87, 0.3);
}

:deep(.el-progress-bar__inner::after) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.percentage-value {
  font-weight: 600;
  font-size: 18px;
  color: #667eea;
  min-width: 60px;
}

.loading-text {
  color: #6c757d;
  font-size: 14px;
  font-weight: 400;
  flex: 1;
  text-align: right;
}

.result-card {
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  margin-bottom: 30px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.result-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.2);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f0f0f0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon-small {
  font-size: 24px;
}

.result-header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.success-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  padding: 8px 16px;
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border: 1px solid #81c784;
  color: #2e7d32;
}

.contract-content {
  white-space: pre-wrap;
  font-family: 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, sans-serif;
  line-height: 2;
  font-size: 15px;
  color: #2c3e50;
  background: linear-gradient(135deg, #fafbfc 0%, #f8f9fa 100%);
  padding: 28px;
  border-radius: 12px;
  border-left: 4px solid #667eea;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
  animation: fadeIn 0.8s ease;
}

.contract-content :deep(mark) {
  background-color: #fff3cd;
  color: #856404;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
  border: 1px solid #ffeeba;
  box-shadow: 0 1px 2px rgba(133, 100, 4, 0.1);
}

.contract-content :deep(risk) {
  display: inline-block;
  background: linear-gradient(135deg, #ffe5e5 0%, #ffcccc 100%);
  color: #c62828;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 12px;
  margin-left: 6px;
  font-weight: 500;
  border: 1px solid #ffcdd2;
  box-shadow: 0 2px 4px rgba(198, 40, 40, 0.15);
}

.contract-content :deep(safe) {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  color: #2e7d32;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 500;
  margin-right: 4px;
  border: 1px solid #81c784;
  box-shadow: 0 2px 4px rgba(46, 125, 50, 0.15);
}
</style>