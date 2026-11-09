# Agent运行规范（V1.2）

1. 每轮先读取最新 `SKILL.md`、`docs/content_scope.md`、`docs/source_and_compliance.md`、`docs/editorial_style.md`、`docs/visual_guide.md`、`docs/image_quality_gate.md`、`docs/weekly_automation.md` 及相关模板。
2. 账号核心：专业认证、高校联合培养、青少年教育，兼顾政策、华大科研、办学成果、科研素养。以真实华大教育工作为基础。
3. 每批择优3–5题，每题完整真实自然小红书正文、两张独立3:4 GPT图像模型成片及来源/合规说明。
4. **图片只做主题视觉，不刊登任何新闻事实或详细信息。** P1仅主题标题和可选短副标题；P2为视觉延展，必须有一句简短主题标题/引导语，不可完全无字。报道日期、人数、合作事件、政策条款、科研结论、课程内容、风险均写入小红书正文。
5. **最终图片必须GPT图像模型直接生成。禁止Pillow、Canvas、SVG、HTML、Python或其他程序进行后期文字叠加、图文信息卡拼贴。** 纯尺寸格式转换不应改变内容。
6. 视觉质检后不合格必须修改提示词、由GPT重新生成；每张最多重试2次。无字P2不是失败，但无主标题P1是失败。无版权许可不得呈现真实孩子肖像，AI示意图不得冒称实拍。
7. 旧版 `scripts/render_and_validate.py` 与 `scripts/verify_batch.py` 的代码叠字工作流已废弃，禁止引用或回退；按 docs/image_quality_gate.md 的视觉审核和真实文件检查验收。
8. 仅在新教育账号指定的云盘文件夹下交付；否则提供本地文件并明确说明未上传。绝不代发小红书。
