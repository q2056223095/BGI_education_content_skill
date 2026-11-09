# 每周批次无人值守规范 V1.2

## 默认设置
目标账号：华大生命科学教育与人才培养观察。
周期调度由ChatGPT任务设置决定，本仓库不自行设定运行时刻。
每批择优3–5题，不凑数；每题1篇完整小红书正文 + **2张GPT图像模型直接生成的独立主题图**，不代发社交平台。
文件日期按 Asia/Bangkok 时区。新账号Google Drive根文件夹ID未配置时只生成本地ZIP，不使用旧科研热点目录。

## 执行
1. 每次读取最新 SKILL.md、README.md、AGENTS.md、docs/content_scope.md、docs/source_and_compliance.md、docs/editorial_style.md、docs/visual_guide.md、docs/image_quality_gate.md、docs/weekly_automation.md、templates/topic_card.md、templates/xiaohongshu_copy.md、templates/two_image_plan.md、templates/gpt_image_prompt.md、templates/batch_manifest.md、config.example.json。
2. 检索政策原文、华大/合作高校报道、真实课程与科研材料、专业指南，分类核验日期、身份与科学/政策边界。通过事实门槛后六维评分，按综合价值保留3–5题，优先前三。
3. 每题写真实完整的小红书正文（5–8标签），**所有新闻事实、日期、政策条款、数字、学习内容、项目具体情况及来源解释均写在正文**，不要写在图片中。
4. 设计简短GPT图片提示词：P1是强视觉标题封面，P2是另一个完整主题场景。两张图均**不可是信息页/新闻页**。最终两张必须直接使用GPT图像生成模型出图，不使用代码合成文字/绘画/拼版。
5. 先生成P1并实际查看，检查标题、错字、主题、新闻内容禁区、拼版、图源身份、隐私、尺寸，通过后生成独立P2并用同样方法检视。P2允许无字，禁止要点解释。失败修改提示词并GPT整图重试，每张最多2次，不能后期代码修补。
6. 保存每题 小红书文案.txt、P1.png、P2.png、来源与合规.md、图片验收.md；创建本周候选筛选报告.md、批次清单.md、图片质检汇总.md、ZIP。核查各文件真实存在与清晰度；若缺图则只标部分完成。
7. 如有新教育账号明确的Google Drive根ID，以精确ID上传日期文件夹和ZIP、逐项读回验证；未配置时说明“新云盘目录未配置”，不上传旧目录。
8. 一次性通知各题、完整数量、合格图片数量、缺件/失败、链接及合规边界。

## 目录
YYYY-MM-DD/
  本周候选筛选报告.md
  批次清单.md
  图片质检汇总.md
  云端验收记录.md
  01_题目/
    小红书文案.txt
    P1.png
    P2.png
    来源与合规.md
    图片验收.md
  02_题目/...
  YYYY-MM-DD_华大教育内容_整包.zip

## 失败定义
- GPT图片模型不可用：停止图片步骤，保留正文和缺图记录，不能用其他工具补字冒充成品。
- 图中出现新闻详情、P1无主题标题、错字、拼版、假现场/假Logo：判失败并GPT重生。
- P2没有说明文字不是失败；图像应仍有主题表达与独立构图。
- Google Drive写入受阻：仅能报告本地交付，不能声称云端成功。
