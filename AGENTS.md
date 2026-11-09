# AI Agent 指令

执行本项目任务时先阅读 SKILL.md；再按需读取 docs/content_scope.md、docs/source_and_compliance.md、docs/editorial_style.md、docs/visual_guide.md、docs/weekly_automation.md，以及全部 templates 文件。

不可自动复用旧版生命科学科研热点项目的“每题五张图”规则。本仓库最新默认：教育相关7大板块、每周择优3–5个、每题1篇完整小红书正文 + P1和P2各1张独立1080×1440 PNG + 合规资料、无人值守自动自检；不代发布。

具体认证资质、合作状态、学员/未成年人成果和科研细节必须核对来源；未获授权不发布未成年人的个人信息、肖像。没有指定新的 Google Drive 目标文件夹ID不得以旧项目目录代替，也不得声称云盘已交付。

## V1.1图片必须有文字的硬门槛

不允许只生成纯场景图片后直接交付。每个选题先核准P1/P2中文文案、再生成两张独立无字背景，并使用 `scripts/render_and_validate.py` 叠加准确中文：P1有主标题、副标题与图源标签；P2有标题、2–3条有实质内容的解释、图源标签。各页运行 `verify`，批次运行 `scripts/verify_batch.py`。脚本无中文字体/不可运行、视觉检查失败或无QA记录，都不能算完整成品；必须记录缺件。严格参见 `docs/image_quality_gate.md`。
