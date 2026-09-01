# 输入材料

| 项目 | 内容 |
| --- | --- |
| 产品名 | 简历优化教练 |
| 产品类型 | AI对话应用（Dify工作流/Chatbot） |
| 创建日期 | 2026-08-26 |

## 用户原始想法

把已有的 Dify 工作流「大厂产研简历优化教练-C-Level」产品化——即从"一个能跑的 DSL 工作流"提炼、补全成"能写 PRD、能画原型、能向团队讲清楚"的完整产品定义。

## 已有材料

- `简历审核DSL.zip` → Dify DSL 导出文件（`大厂产研简历优化教练-C-Level.yml`，version 0.4.0）
- 该 DSL 已内含完整业务逻辑：
  - 应用名：大厂产研简历优化教练-C-Level
  - 模式：advanced-chat，支持文件上传（JPG/PNG/PDF 等 document 类型）
  - 模型：deepseek-chat（langgenius/deepseek，temperature 0.7）
  - 工作流：`start → 文档提取器 → LLM×4（串联）→ 最终回答`，共 5 步
  - 角色设定：洞察人心的面试官与资深HRBP（FAANG 级别产品技术招聘委员会核心成员）
  - 核心方法论：批判-解析-建议"三位一体"、分级批判、"所以呢？"拷问法、JD 匹配原则、忠于原文
