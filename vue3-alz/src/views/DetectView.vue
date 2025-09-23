<script setup>
import { ref } from 'vue'
import axios from 'axios'

const fileInputRef = ref(null)
const modelInputRef = ref(null)
const selectedFile = ref(null)
const selectedModel = ref(null)
const previewUrl = ref('')
const result = ref(null)
const error = ref('')
const loading = ref(false)

// 中文映射
const classNamesZh = {
  'Mild Impairment': '轻度认知障碍',
  'Moderate Impairment': '中度认知障碍', 
  'No Impairment': '无认知障碍',
  'Very Mild Impairment': '极轻度认知障碍'
}

// 打开文件选择器
const openFileSelector = () => {
    fileInputRef.value?.click()
}

// 打开模型选择器
const openModelSelector = () => {
    modelInputRef.value?.click()
}

// 图片选择事件
const onFileChange = (e) => {
  const file = e.target.files[0]
  selectedFile.value = file
  result.value = null
  error.value = ''
  if (file) previewUrl.value = URL.createObjectURL(file)
  else previewUrl.value = ''
}

// 模型选择事件
const onModelChange = (e) => {
  const file = e.target.files[0]
  selectedModel.value = file
  error.value = ''
  // 验证模型文件格式
  if (file && !file.name.endsWith('.pt')) {
    error.value = '请选择.pt格式的模型文件'
    selectedModel.value = null
  }
}

// 检测请求
const onPredict = async () => {
  if (!selectedFile.value) {
    error.value = '请先选择要检测的图片'
    return
  }
  if (!selectedModel.value) {
    error.value = '请先选择模型文件'
    return
  }
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('model_file', selectedModel.value)
    const res = await axios.post('http://localhost:8000/predict', formData)
    result.value = res.data
  } catch (err) {
    error.value = err.response?.data?.error || '检测失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 清空图片
const clearImage = () => {
  selectedFile.value = null
  previewUrl.value = ''
  error.value = ''
  fileInputRef.value && (fileInputRef.value.value = '')
}

// 清空模型
const clearModel = () => {
  selectedModel.value = null
  error.value = ''
  modelInputRef.value && (modelInputRef.value.value = '')
}

// 清空选择
const clearAll = () => {
  clearImage()
  clearModel()
  result.value = null // 可选：清空历史检测结果
}
</script>

<template>
  <div class="box">
      <!-- 左侧组件 -->
    <div class="detect-card">
    <h2>阿尔茨海默症MRI检测</h2>
    <div class="upload-section">
      <div v-if="!selectedFile" class="file-placeholder" @click="openFileSelector">
        请选择要检测的MRI图像
      </div>
      <div v-else class="file-selected">
        <div class="selected-img-container">
          <img :src="previewUrl" alt="已选MRI图像" class="selected-img">
        </div>
        <p>已选择文件: {{ selectedFile.name }}</p>
      </div>

      <div class="model-selection">
        <div class="model-btn-group">
          <button @click="openModelSelector" class="model-btn">选择模型</button>
        </div>
        <p v-if="selectedModel" class="model-name">已选模型: {{ selectedModel.name }}</p>
        <p v-else class="model-hint">请选择.pt格式的模型文件</p>
      </div>

        <div class="btn-group">
          <button @click="onPredict" 
          :disabled="loading || !selectedFile || !selectedModel" 
          class="predict-btn">
          开始检测
          </button>
          <button class="clear-btn" @click="clearImage">清除图片</button>
          <button class="clear-btn" @click="clearModel">清除模型</button>
          <button class="clear-btn" @click="clearAll">清除选择</button>
        </div>
    </div>
    <div v-if="error" class="error">{{ error }}</div>
      <input ref="fileInputRef" type="file" @change="onFileChange" accept="image/*" class="hidden-input" />
      <input ref="modelInputRef" type="file" @change="onModelChange" accept=".pt" class="hidden-input" />
    </div>

  <!-- 右侧组件 -->
    <div class="result-card">
    <h2>检测结果</h2>
    <div v-if="loading" class="loading">正在检测，请稍候...</div>
    <template v-if="result && result.main_class">

      <div class="result-main">
        <h3>📊 主要诊断结果：<b>{{ classNamesZh[result.main_class] || result.main_class }}</b></h3>
        <h3>置信度：<b style="color: darkgreen;">{{ (result.confidence * 100).toFixed(2) }}%</b></h3>
      </div>
      
      <div class="result-section">
        <h3>📈 详细概率分布：</h3>
        <ul class="prob-list">
          <li v-for="item in result.all_results" :key="item.class">
            {{ classNamesZh[item.class] || item.class }}：{{ (item.confidence * 100).toFixed(2) }}%
          </li>
        </ul>
      </div>

      <hr>

      <div class="result-section">
        <h3>📚 医学说明：</h3>
        <div class="desc-text">
          无认知障碍: 正常的大脑状态，无明显认知功能下降<br>
          极轻度认知障碍: 最轻微的认知下降，可能是正常老化或早期病理变化<br>
          轻度认知障碍: 轻微的认知功能下降，日常生活能力基本保持<br>
          中度认知障碍: 明显的认知功能损害，影响日常生活和工作能力
        </div>
      </div>
      
      <hr>

      <div class="important-note">
        <h3>⚠️ 重要提示：</h3>
        <p>本YOLOv8检测系统仅供辅助参考，不能替代专业医疗诊断。<br>
          如有疑虑，请及时就医并咨询专业医师。</p>
      </div>

    </template>

    <template v-else-if="result && result.error">
      <span style="color:red">{{ result.error }}</span>
    </template>
    
    <template v-else>
      <span>请上传图片并点击检测</span>
    </template>
    </div>
  </div>
</template>

<style scoped>
.box {
  display: flex;
  justify-content: center;
  gap: 120px;
  min-height: calc(100vh - 80px);
  align-items: center;
}

.detect-card {
  background: #e8e8e8;
  border-radius: 12px;
  box-shadow: 0 4px 16px #aeaeae;
  max-height: 720px;
  padding: 32px 28px;
}

.upload-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  gap: 30px;
  margin-top: 20px;
  flex: 1;
}

.hidden-input{
  display: none;
}
/* 未选文件时的提示框 */
.file-placeholder{
  width: 225px;
  height: 225px;
  border: 2px dashed #ccc;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  cursor: pointer;
  background-color: #f5f5f5;
  transition: all 0.3s ease;
  margin-bottom: 16px;
}
.file-placeholder:hover{
  border-color: #409eff;
  color: #409eff;
}
.file-selected{
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}
.selected-img-container {
  width: 225px;
  height: 225px;
  margin-bottom: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f5f5;
}
.selected-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.file-selected p{
  margin-bottom: 12px;
}
.model-selection{
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  margin-bottom: 16px;
}
.model-btn-group{
  display: flex;
  gap: 10px;
}
.model-btn {
  background-color: #67c23a;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  margin-bottom: 8px;
  transition: background-color 0.3s ease;
}

.clear-btn,
.predict-btn {
  width: 25%;
  white-space: nowrap;
  padding: 6px 8px !important;
  font-size: 15px !important;
}

.model-btn:hover {
  background-color: #85ce61;
}
.clear-model-btn{
  background-color: #f56c6c;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}
.clear-model-btn:hover{
  background-color: #fa8989;
}
.model-name {
  color: #67c23a;
  font-size: 14px;
  margin: 8px 0;
}
.model-hint {
  color: #909399;
  font-size: 14px;
  margin: 8px 0;
}
p{
  color:chocolate;
  font-size: 14px;
  margin: 8px 0;
}
.btn-group{
  display: flex;
  gap: 10px;
}
.predict-btn{
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 8px;
  transition: background-color 0.3s ease;
}
.predict-btn:hover{
  background-color: #66b1ff;
}
.predict-btn:disabled{
  background-color: #ccc;
  cursor: not-allowed;
}
.clear-btn{
  background-color: #fff;
  color: #409eff;
  border: 1px solid #409eff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.clear-btn:hover{
  background-color: #e6f7ff;
}
.loading {
  color: #409eff;
  margin: 16px 0;
}
.error {
  color: #e74c3c;
  margin: 16px 0;
  text-align: center;
  width: 100%;
}
.result-card{
  background-color: #fff0dc;
  padding: 32px 28px;
  border-radius: 12px;
  box-shadow: 0 4px 16px #aeaeae;
  max-height: 720px;
  overflow-y: auto;
}
.result-main{
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #515151;
}
.result-section{
  margin: 16px 0;
}
.prob-list{
  list-style: disc;
  padding-left: 20px;
  line-height: 1.6;
}
.desc-text{
  line-height: 1.6;
}
.important-note{
  margin-top: 16px;
}
.important-note h3,
.important-note p {
  color: red;
}
hr {
  border: none;
  border-top: 1px dashed #515151;
  margin: 12px 0;
}


@media screen and (max-width: 1640px) {
  h2 {
    font-size: 20px;
  }

  .upload-section {
    margin-top: 20px;
    gap: 20px;
  }
}
</style>
