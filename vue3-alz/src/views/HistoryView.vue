<script setup>
import { ElButton, ElInput, ElNotification, ElTable, ElTableColumn, ElMessageBox, ElDialog, ElForm, ElFormItem, ElInputNumber } from 'element-plus';
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

//数据状态
const list = ref([])
const editing = ref(false)
const editItem = ref({})
const viewingImage = ref(false)
const imagePreviewUrl = ref('')
const highlightId = ref(null)
const filterForm = ref({
  name: '',
  medicalId: ''
})

const route = useRoute()
const router = useRouter()

// 中文映射
const classNamesZh = {
  'Mild Impairment': '轻度认知障碍',
  'Moderate Impairment': '中度认知障碍',
  'No Impairment': '无认知障碍',
  'Very Mild Impairment': '极轻度认知障碍'
}

// 表格行类名：根据检测结果分配不同类名
const tableRowClassName = ({ row }) => {
  const label = row?.label
  if (!label) return '';

  switch (label) {
    case 'No Impairment': 
      return 'success-row';
    case 'Very Mild Impairment':
      return 'info-row';
    case 'Mild Impairment':
      return 'warning-row'; 
    case 'Moderate Impairment':
      return 'danger-row';
  }
}

//获取历史记录列表
const fetchList = async () => {
  try {
    const params = {}
    if (filterForm.value.name) params.patient_name = filterForm.value.name
    if (filterForm.value.medicalId) params.medical_id = filterForm.value.medicalId

    const r = await axios.get('http://localhost:8000/detections/', { params })
      list.value = r.data
    } catch (e) {
        ElNotification.error('获取列表失败')
    }
}

const openEdit = (item) => {
  editItem.value = { ...item }
  editing.value = true
}

const beforeCloseHandler = (done) => {
  editing.value = false;
  editItem.value = {};
  done();
}

const closeEditSimple = () => {
  editing.value = false;
  editItem.value = {};
}

const saveEdit = async () => {
  try {
    const id = editItem.value.id;
    if (!id) {
      ElNotification.error('记录ID不存在，保存失败');
      return;
    }
    const payload = {
      patient_name: editItem.value.patient_name,
      patient_gender: editItem.value.patient_gender,
      patient_age: editItem.value.patient_age,
      medical_id: editItem.value.medical_id,
      label: editItem.value.label,
      confidence: editItem.value.confidence
    };
    await axios.put(`http://localhost:8000/detections/${id}`, payload);
    ElNotification.success('保存成功');
    editing.value = false;
    fetchList();
  } catch (e) {
    console.error('保存失败：', e.response ? e.response.data : e);
    const status = e?.response?.status;
    const body = e?.response?.data;
    const msg = body?.detail || body?.error || (e && e.message) || '保存失败';
    ElNotification.error({
      title: `保存失败${status ? ' (状态 ' + status + ')' : ''}`,
      message: msg + (body && typeof body === 'object' ? '\n' + JSON.stringify(body) : '')
    });
  }
};

const remove = async (id) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条记录吗？',
      '删除确认',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch (e) {
    return
  }

  try {
    await axios.delete(`http://localhost:8000/detections/${id}`)
    ElNotification.success('删除成功')
    await fetchList()
  } catch (e) {
    console.error('删除失败：', e.response ? e.response.data : e)
    ElNotification.error('删除失败')
  }
}

const viewImage = (item) => {
  if (!item.image_path) { 
    ElNotification.warning('没有图片可供查看')
    return 
  }
  
  imagePreviewUrl.value = item.image_path.startsWith('http') 
    ? item.image_path 
    : `http://localhost:8000/${item.image_path}`
  viewingImage.value = true
}

const closeImage = () => { 
  viewingImage.value = false
  imagePreviewUrl.value = '' 
}

const formatDate = (s) => {
  if (!s) return ''
  try {
    const d = new Date(s)
    return d.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
  } catch (e) {
    return s
  }
}

const handleFilter = () => {
  fetchList()
}

onMounted(() => {
  fetchList()
  if (route.query.highlight) {
    highlightId.value = Number(route.query.highlight)
  }
})
</script>

<template>
    <div class="history">
    <h2>检测历史</h2>
      <div class="filter-bar">
        <ElInput class="input-info" v-model="filterForm.name" placeholder="请输入姓名"/>
        <ElInput class="input-info" v-model="filterForm.medicalId" placeholder="请输入完整病历号"/>
        <ElButton type="primary" @click="handleFilter">筛选</ElButton>
        <ElButton type="primary" @click="fetchList">刷新</ElButton>
      </div>

      <ElTable 
        :data="list" 
        style="width: 100%; margin-top: 20px; font-size: 16px;"
        :row-class-name="tableRowClassName"
        :row-style="(row) => (row && row.id === highlightId ? { backgroundColor: '#fffbcc' } : {})"
      >
        
        <ElTableColumn label="序号" width="80" :formatter="(row, column, cellValue, index) => index + 1" />
        
        <ElTableColumn prop="patient_name" label="姓名" width="80" />
        <ElTableColumn prop="medical_id" label="病历号" width="100"/>
        <ElTableColumn prop="patient_gender" label="性别" width="80" />
        <ElTableColumn prop="patient_age" label="年龄" width="80" />
        <ElTableColumn label="检测时间" :formatter="(row) => formatDate(row?.created_at)" />
        <ElTableColumn label="检测结果" :formatter="(row) => classNamesZh[row?.label] || row?.label" />
        <ElTableColumn 
            prop="confidence" 
            label="置信度" 
            :formatter="(row) => row && row.confidence != null ? (row.confidence * 100).toFixed(2) + '%' : ''"
            width="120" 
        />
        <ElTableColumn label="操作" width="300">
          <template #default="scoped">
            <ElButton type="text" @click="viewImage(scoped.row)" v-if="scoped.row.image_path">
              查看图片
            </ElButton>
            <ElButton type="text" @click="openEdit(scoped.row)">
              修改
            </ElButton>
            <ElButton type="text" text-color="#ff4d4f" @click="remove(scoped.row.id)">
              删除
            </ElButton>
          </template>
        </ElTableColumn>    
      </ElTable>

        <!-- 编辑对话框 -->
      <ElDialog 
        title="修改检测记录"
        v-model="editing" 
        :before-close="beforeCloseHandler"
        width="500px">
          <ElForm :model="editItem" label-width="100px">
            <ElFormItem label="姓名">
            <ElInput v-model="editItem.patient_name" />
            </ElFormItem>
            <ElFormItem label="性别">
            <ElInput v-model="editItem.patient_gender" />
            </ElFormItem>
            <ElFormItem label="年龄">
            <ElInputNumber 
                v-model="editItem.patient_age" 
                :min="0" 
                :max="150" 
                controls-position="right"
            />
            </ElFormItem>
            <ElFormItem label="病历号">
            <ElInput v-model="editItem.medical_id" />
            </ElFormItem>
            <ElFormItem label="结果">
            <ElInput v-model="editItem.label" />
            </ElFormItem>
            <ElFormItem label="置信度">
            <ElInputNumber 
                v-model="editItem.confidence" 
                :min="0" 
                :max="1" 
                :step="0.01"
                controls-position="right"
            />
            </ElFormItem>
          </ElForm>
          <template #footer>
            <ElButton @click="closeEditSimple">取消</ElButton>
            <ElButton type="primary" @click="saveEdit">保存</ElButton>
          </template>
        </ElDialog>

        <!-- 图片查看对话框 -->
        <ElDialog 
        title="图片预览" 
        v-model="viewingImage" 
        :before-close="closeImage"
        width="800px">
            <div style="text-align: center;">
                <img 
                :src="imagePreviewUrl" 
                style="max-width: 100%; max-height: 600px;" 
                alt="检测图片"/>
            </div>
      </ElDialog>
    </div>
</template>

<style scoped>
.history{
    padding: 40px;
}
.filter-bar{
    padding: 20px;
}
.input-info{
    width: 200px;
    margin-right: 10px;
}
.info{
    margin-top: 10px;
}
</style>

<style>
.el-table .success-row {
  --el-table-tr-bg-color: var(--el-color-success-light-8);
}
.el-table .warning-row {
  --el-table-tr-bg-color: var(--el-color-warning-light-8);
}
.el-table .info-row {
  --el-table-tr-bg-color: var(--el-color-info-light-8);
}
.el-table .danger-row {
  --el-table-tr-bg-color: var(--el-color-danger-light-8);
}
</style>
