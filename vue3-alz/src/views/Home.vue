
<template>
    <div class="main">
        <h2>欢迎使用「阿尔茨海默辅助诊断系统」</h2>

        <div class="box-card">
          <div class="content-card">
              <h3>1. 系统功能介绍</h3>
              <p>
                  本系统基于YOLOv8深度学习模型，专为阿尔茨海默症（AD）的辅助诊断设计，核心功能包括：
              </p>
              <p>• <strong>MRI图像检测</strong>：上传脑部MRI图像，系统自动分析并生成认知障碍程度评估</p>
              <p>• <strong>历史记录管理</strong>：保存检测结果，支持查询、编辑和删除，方便跟踪患者病情变化</p>
              <p>• <strong>多类别评估</strong>：精准区分无认知障碍、极轻度/轻度/中度认知障碍，辅助临床决策</p>
          </div>
          <div class="img-wrapper">
            <img src="/img1.png" alt="阿尔茨海默1">
          </div>
        </div>

        <div class="box-card">
          <div class="content-card">
            <h3>2. 系统使用流程</h3>
            <p>使用本系统进行辅助诊断的操作步骤：</p>
            <p>1. 登录管理员账号</p>
            <p>2. 进入“目标推理”页面，填写患者基本信息（姓名、性别、年龄、病历号）</p>
            <p>3. 选择预训练模型（系统默认加载Top-1准确率99.13%的模型），点击“开始检测”按钮</p>
            <p>4. 查看检测结果，包含认知障碍类别、置信度</p>
            <p>5. 检测结果自动保存至“检测历史”页面中，可随时查阅和管理</p>
          </div>
          <div class="img-wrapper">
            <img src="/img2.png" alt="阿尔茨海默2">
          </div>
        </div>

        <div class="box-card">
          <div class="content-card">
            <h3>3. 认知障碍程度说明</h3>
            <p>无认知障碍: 正常的大脑状态，无明显认知功能下降</p>
            <p>极轻度认知障碍: 最轻微的认知下降，可能是正常老化或早期病理变化</p>
            <p>轻度认知障碍: 轻微的认知功能下降，日常生活能力基本保持</p>
            <p>中度认知障碍: 明显的认知功能损害，影响日常生活和工作能力</p>
          </div>
          <div class="img-wrapper">
            <img src="/img3.png" alt="阿尔茨海默3">
          </div>
        </div>

        
    </div>
</template>

<style scoped>
@media screen and (max-width: 900px){
  .box-card{
    flex-direction: column;
  }
}
.main{
  padding: 40px;
  max-width: 1600px;
  margin: 0 auto;
}

.box-card {
  display: flex;
  justify-content: space-between;
  gap: 30px;
  margin-bottom: 30px;
  align-items: stretch;
}

.content-card{
  background-color: #e6f7ff;
  padding: 32px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  flex: 1.5;
}

.img-wrapper{
  flex: 1;
  position: relative;
  min-height: 100%;
}

.img-wrapper img{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: block;
}

h3 {
  font-size: 20px;
  color: #34495e;
  margin-top: 0;
  margin-bottom: 16px;
}

p {
  line-height: 1.7; 
  color: #555;      
  margin-bottom: 12px;
  font-size: 16px;
}

strong {
  font-weight: bold;
}
</style>