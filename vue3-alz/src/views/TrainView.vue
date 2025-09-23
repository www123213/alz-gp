<script setup>
import { ref, onUnmounted } from 'vue'
import axios from 'axios'
import { ElButton, ElCard, ElDivider, ElInputNumber, ElMessage, ElOption, ElSelect, ElTooltip } from 'element-plus'
import { FolderOpened, InfoFilled } from '@element-plus/icons-vue'

const datasetPath = ref('')
const datasetFolderName = ref('')
const epochs = ref(50)
const batchSize = ref(16)
const imgSize = ref(640)
const modelType = ref('s')
const trainStatus = ref('')
const trainLoading = ref(false)
const trainLog = ref('')
let logTimer = null
const currentPid = ref(null)
const isRunning = ref(false)

// 处理文件夹选项
const onDatasetFolderChange = (e) => {
  const files = e.target.files
  if (files.length > 0) {
    // 获取第一个文件的完整路径
    const fullPath = files[0].webkitRelativePath || files[0].name
    const folder = fullPath.split('/')[0]
    datasetFolderName.value = folder
    datasetPath.value = folder
  } else {
    datasetFolderName.value = ''
    datasetPath.value = ''
  }
}

const fetchTrainLog = async () => {
  try {
    const res = await axios.get('http://localhost:8000/train/log')
    trainLog.value = res.data.log
    // 检测 TRAIN_FINISHED / TRAIN_STOPPED 并停止轮询
  if (trainLog.value && trainLog.value.includes('TRAIN_FINISHED')) {
    stopLogPolling()
    isRunning.value = false
    trainStatus.value = '训练已完成'
    ElMessage.success('训练完成')
  }
  if (trainLog.value && trainLog.value.includes('TRAIN_STOPPED')) {
    stopLogPolling()
    isRunning.value = false
    trainStatus.value = '训练已停止'
    ElMessage.info('训练被终止')
  }
  } catch {}
}

const startLogPolling = () => {
  if(logTimer) clearInterval(logTimer)
  logTimer = setInterval(fetchTrainLog, 2000)
}

const stopLogPolling = () => {
  if (logTimer) clearInterval(logTimer)
}

onUnmounted(() => {
  stopLogPolling()
})

const onTrain = async () => {
  trainLoading.value = true
  trainStatus.value = ''
  trainLog.value = ''
  try {
    const formData = new FormData()
    formData.append('dataset_path', datasetPath.value)
    formData.append('epochs', epochs.value)
    formData.append('batch_size', batchSize.value)
    formData.append('img_size', imgSize.value)
    formData.append('model_type', modelType.value)

    const res = await axios.post('http://localhost:8000/train', formData)
    trainStatus.value = res.data.status
    currentPid.value = res.data.pid || null
    isRunning.value = true
    startLogPolling()
    ElMessage.success('训练已开始')
  } catch (err) {
    trainStatus.value = err.response?.data?.msg || err.response?.data?.error || '训练启动失败'
    stopLogPolling()
    ElMessage.error(trainStatus.value)
  } finally {
    trainLoading.value = false
  }
}

const onStopTrain = async () => {
  try {
    const res = await axios.post('http://localhost:8000/train/stop')
    if (res.data.status === 'stopped') {
      trainStatus.value = '训练已停止'
      ElMessage.success('训练已停止')
    } else {
      trainStatus.value = res.data.msg || '停止请求已发送'
      ElMessage.warning(trainStatus.value)
    }
  } catch (err) {
    ElMessage.error('停止训练失败')
  } finally {
    stopLogPolling()
    isRunning.value = false
    currentPid.value = null
  }
}
</script>

<template>
  <div class="box">
    <ElCard class="train-card">
      <div class="train-form">
        <div class="form-item folder-btn-container">
          <!-- 隐藏input -->
          <input ref="fileInput" type="file" webkitdirectory directory @change="onDatasetFolderChange" style="display: none;"/>
          <!-- 通过绑定事件触发input -->
          <ElButton type="primary" plain @click="$refs.fileInput.click()" :icon="FolderOpened" size="large">选择数据集</ElButton>
          <div v-if="datasetFolderName" class="folder-name">
            已选择：{{ datasetFolderName }}
          </div>
        </div>

    <ElDivider />

      <div class="form-item">
        <label>训练轮数：</label>
        <div class="input-with-info">
          <ElInputNumber v-model="epochs" :min="1" :step="1" placeholder="训练轮数" />
          <ElTooltip content="模型在训练集上的迭代次数，轮数越多模型可能越精准，但训练时间更长，默认50轮">
            <InfoFilled class="info-icon" />
          </ElTooltip>
        </div>
      </div>

      <div class="form-item">
        <label>批次大小：</label>
        <div class="input-with-info">
          <ElInputNumber v-model="batchSize" :min="1" :step="1" placeholder="批次大小" />
          <ElTooltip content="每次迭代训练的图片数量，受GPU显存限制。RTX 3060建议8-16之间，值越大训练越快但消耗显存越多">
            <InfoFilled class="info-icon" />
          </ElTooltip>
        </div>
      </div>

      <div class="form-item">
        <label>图片尺寸：</label>
        <div class="input-with-info">
          <ElInputNumber v-model="imgSize" :min="32" :step="32" placeholder="图片尺寸" />
          <ElTooltip content="输入图片的尺寸，统一缩放为正方形，默认640×640像素，与预处理尺寸保持一致">
            <InfoFilled class="info-icon" />
          </ElTooltip>
        </div>
      </div>

      <div class="form-item">
        <label>模型类型：</label>
        <div class="input-with-info">
          <ElSelect v-model="modelType" placeholder="选择模型类型" size="medium">
            <ElOption value="n" label="nano" />
            <ElOption value="s" label="small" />
            <ElOption value="m" label="medium" />
            <ElOption value="l" label="large"/>
            <ElOption value="x" label="xlarge"/>
          </ElSelect>
          <ElTooltip content="n(最快最小) < s(推荐) < m < l < x(最准最大)，模型越大精度可能越高，但训练和推理速度越慢">
            <InfoFilled class="info-icon" />
          </ElTooltip>
        </div>
      </div>

      <div class="train-btn-container">
        <ElButton type="primary" @click="onTrain" :disabled="trainLoading || !datasetFolderName" :loading="trainLoading" size="large">
          开始训练
        </ElButton>
        <ElButton type="danger" @click="onStopTrain" :disabled="!isRunning" size="large">停止训练</ElButton>
      </div>
    </div>
    </ElCard>

    <div class="progress-card">
      <h2>训练进度</h2>
        <div v-if="trainStatus" class="train-status">{{ trainStatus }}</div>
        <div v-if="trainLog" class="train-log">
          <h3>训练日志：</h3>
          <pre>{{ trainLog }}</pre>
        </div>

      <template v-else>
      <span>请上传数据集并开始训练</span>
    </template>
    </div>
  </div>



</template>

<style scoped>
@media screen and (max-width: 1200px){
  .train-card, 
  .progress-card{
    width: 90%;
    max-width: 600px;
  }
  .progress-card{
    max-height: calc(100vh - 300px);
  }
}
.box{
  display: flex;
  justify-content: center;
  gap: 120px;
  min-height: calc(100vh - 80px);
  align-items: center;
}
.train-card {
  background: #e8e8e8;
  border-radius: 12px;
  box-shadow: 0 4px 16px #aeaeae;
  padding: 32px 28px;
  min-width: 420px;
  min-height: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;

}

.form-item{
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  width: 100%;
}
.form-item label{
  margin-bottom: 0;
  margin-right: 12px;
  min-width: 100px;
  font-weight: 500;
}
.input-with-info{
  display: flex;
  align-items: center;
  flex: 1;
}
.info-icon{
  color: #409eff;
  margin-left: 8px;
  cursor: pointer;
  font-size: 16px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.train-status{

  color: #409eff;
  padding: 8px;
  border-radius: 4px;
  background-color: #ecf5ff;
}
.train-log {
  margin-top: 18px;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 4px #eee;
  padding: 12px;
  width: 100%;
  flex: 1 1 auto;
  overflow: auto;
  font-size: 14px;
  color: #333;
  flex-direction: column;
}
.train-log pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 500px;
}
.train-btn-container{
  margin-top: 30px;
  text-align: center;
  width: 100%;
}
.folder-btn-container{
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 16px;
  width: 100%;
}
.folder-name {
  margin-top: 8px;
  color: #666;
  font-size: 16px;
}
.el-divider--horizontal{
  border-top: 3px solid #3498db;
}
.progress-card{
  background-color: #e5ffdc;
  padding: 32px 28px;
  border-radius: 12px;
  box-shadow: 0 4px 16px #aeaeae;
  margin-bottom: 30px;
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-width: 500px;
  max-height: calc(100vh - 90px);
}
</style>
