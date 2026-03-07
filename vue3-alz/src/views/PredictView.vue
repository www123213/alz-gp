<script setup>
import { ref, onMounted } from 'vue'
import { predict } from '@/apis/predict'
import { ElButton, ElForm, ElFormItem, ElInput, ElOption, ElSelect, ElMessage } from 'element-plus'

const fileInputRef = ref(null)
const modelInputRef = ref(null)
const selectedFile = ref(null)
const selectedModel = ref(null)
const previewUrl = ref('')
const result = ref(null)
const error = ref('')
const loading = ref(false)
const formRef = ref(null)

// 初始化加载默认推理模型
onMounted(async () => {
  // 在public目录下读取默认模型，名为****.pt
  const defaultModelName = 'Top1-98_93%.pt'
  try {
    const response = await fetch(`/${defaultModelName}`)
    if (response.ok) {
      const blob = await response.blob()
      const file = new File([blob], defaultModelName, { type: 'application/octet-stream' })
      selectedModel.value = file
    }
  } catch (e) {
    console.warn('自动加载默认模型失败，请手动选择', e)
  }
})

// 病人信息表单（统一字段名为 patient_ 前缀）
const patientForm = ref({
  patient_name: '',
  patient_gender: '',
  patient_age: '',
  medical_id: ''
})

const rules = ref({
  patient_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  patient_gender: [
    { required: true, message: '请输入性别', trigger: 'change' }
  ],
  patient_age: [
    { required: true, message: '请输入年龄', trigger: 'blur' },
    { type: 'number', min: 0, max: 150, message: '年龄必须在0-150之间' ,trigger: 'blur' }
  ],
  medical_id: [
    { required: true, message: '请输入病历号', trigger: 'blur' },
    { min: 3, message: '病历号至少3个字符', trigger: 'blur' }
  ]
})

// 中文映射
const classNamesZh = {
  'Mild Impairment': '轻度认知障碍', 'Moderate Impairment': '中度认知障碍', 
  'No Impairment': '无认知障碍', 'Very Mild Impairment': '极轻度认知障碍'
}

// 打开文件选择器
const openFileSelector = () => {
  if (!validatePatientForm()) {
    error.value = '请先填写病人信息'
    return
  }
  fileInputRef.value?.click()
}

// 打开模型选择器
const openModelSelector = () => {
  if (!validatePatientForm()) {
    error.value = '请先填写病人信息'
    return
  }
  modelInputRef.value?.click()
}

// 验证病人信息表单
const validatePatientForm = async () => {
  if (!formRef.value) return false
  try {
    await formRef.value.validate()
    return true
  } catch (error) {
    return false
  }
}

// 图片选择事件
const onFileChange = (e) => {
  // 选择图片点击取消时
  if (e.target.files.length === 0) return

  const file = e.target.files[0]
  selectedFile.value = file
  result.value = null
  error.value = ''
  if (file) previewUrl.value = URL.createObjectURL(file)
}

// 模型选择事件
const onModelChange = (e) => {
  // 选择模型点击取消时
  if (e.target.files.length === 0) return

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
  if (!await validatePatientForm()) {
    error.value = '请先填写并确认信息'
    return 
  }
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
    formData.append('patient_name', patientForm.value.patient_name)
    formData.append('patient_gender', patientForm.value.patient_gender)
    formData.append('patient_age', patientForm.value.patient_age)
    formData.append('medical_id', patientForm.value.medical_id)

    const res = await predict(formData)

    // 统一归一化后端返回格式，确保前端始终能读取下面这些字段
    const normalize = (data) => {
      const out = {
        main_class: null,
        confidence: null,
        all_results: [],
        bboxes: []
      }

      if (!data) return out

      // 优先使用顶层字段
      out.main_class = data.main_class ?? data.result?.main_class ?? out.main_class
      out.confidence = data.confidence ?? data.result?.confidence ?? out.confidence
      out.all_results = data.all_results ?? data.result?.all_results ?? out.all_results
      out.bboxes = data.bboxes ?? data.result?.bboxes ?? out.bboxes

      // 有时后端会把推理结果放在 result 字段里
      if ((!out.main_class || out.main_class === null) && data.result) {
        out.main_class = data.result.main_class ?? out.main_class
      }

      return out
    }

    if (res.data && (res.data.saved_id || res.data.result || res.data.main_class)) {
      if (res.data.saved_id) {
        ElMessage.success(`检测已保存，病历号：${patientForm.value.medical_id || res.data.medical_id || ''}`)
      }
      result.value = normalize(res.data)
    } else {
      // 响应格式异常
      ElMessage.error('检测响应格式异常，请稍后重试')
      result.value = null
    }
  } catch (err) {
    // 错误处理
    if (!err.response) {
      error.value = '网络异常，请检查后端服务是否正常'
      ElMessage.error(error.value)
    } else {
      error.value = err.response.data?.error || '检测失败，请稍后重试'
      ElMessage.error(error.value)
    }
  } finally {
    loading.value = false
  }
}

// 清空病人信息
const clearPatientInfo = () => {
  patientForm.value = {
    patient_name: '',
    patient_gender: '',
    patient_age: '',
    medical_id: ''
  }
  formRef.value?.resetFields()
}

// 清空选择
const clearAll = () => {
  selectedFile.value = null
  previewUrl.value = ''
  selectedModel.value = null
  error.value = ''
  if (fileInputRef.value) fileInputRef.value.value = ''
  if (modelInputRef.value) modelInputRef.value.value = ''

  patientForm.value = {
    patient_name: '',
    patient_gender: '',
    patient_age: '',
    medical_id: ''
  }
  formRef.value?.resetFields()
}

</script>

<template>
  <div class="box">
      <!-- 左侧组件 -->
    <div class="predict-card">
    <h2>阿尔茨海默症MRI检测</h2>
      <div class="card-content">
        <!-- 信息表单 -->
        <div class="patient-form-section">
        <h3>病人信息</h3>
        <ElForm ref="formRef" :model="patientForm" :rules="rules" label-width="100px" class="patient-form">
              <ElFormItem label="姓名" prop="patient_name">
                <ElInput v-model="patientForm.patient_name" placeholder="请输入姓名" />
              </ElFormItem>
              <ElFormItem label="性别" prop="patient_gender">
                <ElSelect v-model="patientForm.patient_gender" placeholder="请选择性别">
                  <ElOption label="男" value="男"/>
                  <ElOption label="女" value="女"/>
                </ElSelect>
              </ElFormItem>
              <ElFormItem label="年龄" prop="patient_age">
                <ElInput v-model.number="patientForm.patient_age" type="number" placeholder="请输入年龄" />
              </ElFormItem>
              <ElFormItem label="病历号" prop="medical_id">
                <ElInput v-model="patientForm.medical_id" placeholder="请输入病历号" />
              </ElFormItem>
          <ElFormItem>
            <ElButton type="warning" @click="clearPatientInfo">清空信息</ElButton>
          </ElFormItem>
        </ElForm>
        </div>

        <!-- 载入图片 -->
        <div class="upload-section">
          <div v-if="!selectedFile" class="file-placeholder" @click="openFileSelector">
            请选择要检测的MRI图像
          </div>
          <div v-else class="file-selected" @click="openFileSelector" title="点击更换图片" style="cursor: pointer;">
            <div class="selected-img-container">
              <img :src="previewUrl" alt="已选MRI图像" class="selected-img">
            </div>
            <p>已选择文件: {{ selectedFile.name }}</p>
          </div>
        </div>
      </div>

      <div class="model-and-btn">
        <p v-if="selectedModel" class="model-name">当前模型: {{ selectedModel.name }}</p>
        <p v-else class="model-hint">未加载模型</p>

        <div class="btn-group">
          <ElButton 
            type="primary"
            @click="onPredict" 
            :disabled="loading || !selectedFile || !selectedModel" 
            >
            开始检测
            </ElButton>
            <ElButton type="default" @click="openModelSelector">
              {{ selectedModel ? '更换模型' : '选择模型' }}
            </ElButton>
            <ElButton type="danger" @click="clearAll">清除全部</ElButton>
        </div>
      </div>
    
    <div v-if="error" class="error">{{ error }}</div>
      <input ref="fileInputRef" type="file" @change="onFileChange" accept="image/*" class="hidden-input" />
      <input ref="modelInputRef" type="file" @change="onModelChange" accept=".pt" class="hidden-input" />
    </div>

  <!-- 右侧组件 -->
    <div class="result-card">
    <h2>MRI分析结果</h2>
    <template v-if="result && result.main_class && patientForm.patient_name">
      <div class="patient-info">
        <h3>病人信息：</h3>
        <p>姓名：{{ patientForm.patient_name }}</p>
        <p>性别：{{ patientForm.patient_gender }}</p>
        <p>年龄：{{ patientForm.patient_age }}</p>
        <p>病历号：{{ patientForm.medical_id }}</p>
      </div>
      <hr>
    </template> 

    <div v-if="loading" class="loading">正在分析，请稍候...</div>
    <template v-if="result && result.main_class">
      <div class="result-main">
        <h3>📊 主要诊断结果：<b>{{ classNamesZh[result.main_class] || result.main_class }}</b></h3>
        <h3>置信度：<b style="color: darkgreen; font-weight: bold;">
        {{ ((result.confidence ?? 0) * 100).toFixed(2) }}%
        </b></h3>
      </div>

      <hr>
      
      <div class="result-section">
        <h3>📈 详细概率分布：</h3>
        <ul class="prob-list" style="list-style: decimal;">
          <li v-for="(item, idx) in result.all_results" :key="idx">
            {{ classNamesZh[item.class] || item.class }}：{{ (item.confidence * 100).toFixed(2) }}%
          </li>
        </ul>
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
  gap: 100px;
  min-height: calc(100vh - 80px);
  align-items: center;
  padding: 20px;
}

.predict-card {
  background: #f8f9fa;
  border-radius: 12px;
  box-shadow: 0 6px 18px #aeaeae;
  padding: 16px;
  flex: 0 0 auto;
}
.predict-card h2{
  text-align: center;
}

.card-content{
  display: grid;
  grid-template-columns: 1fr 1fr;
  align-items: start; 
  gap: 10px ;
}

.patient-form-section{
  display: flex;
  flex-direction: column;
}

.upload-section {
  display: flex;
  flex-direction: column;
  flex: 1;
  align-items: center; 
  margin-top: 20px;
}

.patient-form-section h3{
  color: #333;
  margin-bottom: 10px;
  font-size: 18px;
  text-align: center;
}

.patient-form{
  width: 100%;
  max-width: 280px;
}

.model-and-btn{
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hidden-input{
  display: none;
}

/* 未选文件时的提示框 */
.file-placeholder{
  width: 200px;
  height: 200px;
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
  width: 200px;
  height: 200px;
  margin-bottom: 12px;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f5f5;
  position: relative;
}

.selected-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.file-selected p{
  margin-bottom: 12px;
  max-width: 200px; 
  overflow: hidden; 
  text-overflow: ellipsis;
}

.btn-group{
  display: flex;
  gap: 12px;
  width: 100%;
  justify-content: center;
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
  color:rgb(0, 123, 255);
  font-size: 14px;
  font-weight: bold;
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
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 6px 18px #aeaeae;
  overflow-y: auto;
}

.prob-list{
  list-style: disc;
  padding-left: 20px;
  line-height: 1.6;
}

.prob-list li{
  font-weight: bold;
}

.desc-text{
  line-height: 1.6;
}

.important-note h3,
.important-note p {
  color: red;
}

hr {
  border: none;
  border-top: 2px dashed #515151;
  margin: 12px 0;
}

.patient-form-section .el-form-item:last-child {
  margin-top: auto;
}

h3{
  font-weight: bold;
}
@media screen and (max-width: 1640px) {
  h2 {
    font-size: 20px;
    margin: 5px;
    padding: 0 0 5px;
  }
  .card-content{
    gap: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    max-height: none;
  }
  .result-card{
    max-height: 600px;
    max-width: 500px;
  }
  .patient-info {
    display: flex;
    flex-direction: row;
    align-items: center;
  }
  .result-card p {
    padding-right: 10px;
  }
  hr{
    margin: 10px;
  }
  h3 {
    font-size: 16px;
  }
}
</style>