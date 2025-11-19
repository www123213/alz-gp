
<template>
    <div class="main">
        <h2>欢迎使用「阿尔茨海默辅助诊断系统」</h2>

        <div class="box-card">
          <div class="content-card">
              <h3>1. 阿尔茨海默症科普:</h3>
              <p>
                  阿尔茨海默症（Alzheimer's Disease, AD）是一种神经退行性疾病，
                  以<strong>记忆力衰退、认知功能进行性下降</strong>为主要特征，
                  是老年痴呆最常见的病因。由于早期症状（如轻微健忘）易被误认为"正常衰老"，
                  <strong>「早发现、早干预」对延缓病情进展至关重要。</strong>——可有效延缓脑萎缩，
                  保留患者的生活自理能力与认知尊严。
              </p>
              <p>近年AD呈"年轻化趋势"，30-50岁中青年患者渐增。
                  这与当代人长期高压工作、熬夜、高油糖饮食、缺乏运动等生活方式密切相关，
                  需全年龄段（尤其中青年）的重视。
                </p>
          </div>
          <img src="/img1.png" alt="阿尔茨海默1">
        </div>

        <div class="box-card">
          <div class="content-card">
            <h3>2. AD发病的"多因素诱因"</h3>
            <p>AD 的诱发是<strong>遗传 + 生活方式 + 基础疾病</strong>等多因素共同作用的结果，
              其中<strong>生活方式对中青年群体的影响尤为突出</strong>可能包括：</p>
            <p>遗传因素：家族中有 AD 患者（尤其是父母等直系亲属），或携带 APOEε4 等风险基因，会使发病概率显著升高；</p>
            <p>生活方式损伤：当代年轻人常陷入"熬夜文化"——长期睡眠不足会严重干扰大脑"胶质淋巴系统"清除β淀粉样蛋白的机制（这类蛋白的异常沉积是AD的核心病理特征）；</p>
            <p>高压 / 焦虑 / 抑郁：职场竞争、经济压力导致的长期情绪问题，会刺激体内炎症因子释放，损伤神经细胞的突触连接，加速认知功能衰退；</p>
            <p>久坐 / 缺乏运动：多数年轻人因工作长期久坐，脑部供血不足会直接削弱神经细胞的活力与修复能力，降低大脑对损伤的抵抗力；</p>
            <p>高油糖饮食：频繁摄入快餐、奶茶等高油糖食物，易引发肥胖与胰岛素抵抗，间接导致大脑神经元对葡萄糖的利用效率降低，加速脑衰老；</p>
            <p>基础疾病影响：高血压、糖尿病、高血脂等慢性病，会损伤脑血管内皮细胞，导致脑部供血不足或微梗死，为AD发生埋下隐患；</p>
            <p>其他诱因：头部外伤史、长期接触重金属等有毒物质，或长期社交隔离、孤独感，也会通过影响神经炎症与突触可塑性，增加AD发病风险。</p>
          </div>
          <img src="/img2.png" alt="阿尔茨海默2">
        </div>

        <div class="box-card">
          <div class="content-card">
            <h3>3. 早期识别与日常护脑建议</h3>
            <p>AD早期若出现<strong>近期记忆明显减退、做事步骤混乱、找词困难、方向感变差</strong>且持续加重，建议尽早就医。</p>
            <p>日常护脑可从四方面入手：</p>
            <p>认知锻炼：学乐器、下棋或深度阅读，保持大脑活跃；</p>
            <p>生活调节：每天7-8小时睡眠，多吃深海鱼、绿叶菜，每周150分钟中等运动（如快走、游泳）；</p>
            <p>心理社交：多参与社交、用冥想/聊天缓解压力；</p>
            <p>高危人群：定期做认知筛查，监测血压、血糖。</p>
          </div>
          <img src="/img3.png" alt="阿尔茨海默3">
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
}

.box-card {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 30px;
}

.box-card > .content-card {
  margin-bottom: 0;
}

.box-card > img {
  object-fit: cover;
  height: auto;
  width: 440px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.content-card{
    background-color: #e6f7ff;
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    flex: 1;
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