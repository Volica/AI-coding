# 《Agent开发实战与系统设计》大纲

## 第一部分：基础认知

### 第1章 Agent 概述

* 什么是 Agent（与传统AI的区别）
* Agent 的核心特征：自主、感知反应、主动、交互、学习
* 应用场景
* 常见挑战与局限性

---

### 第2章 LLM 基础

* LLM 的本质：概率语言模型
* Transformer 简述（Attention 直觉理解即可）
* 幻觉（Hallucination）与不确定性
* API调用与推荐

---

### 第3章 Token 与上下文机制

* Token 是什么
* 上下文窗口（Context Window）
* Token 成本与性能权衡

---

## 第二部分：Agent 核心能力构建

### 第4章 Prompt Engineering

* Prompt 基础结构（System / User / Tool）
* Few-shot / Zero-shot

---

### 第5章 Agent 核心组件

* Perception（输入处理）
* Memory（短期/长期）
* Tools 使用（API/函数调用）
* Planning（任务分解 ReAct CoT）
* Reflection（自我修正纠错/改进）


### 第6章 Agent 工作原理

* Think（推理）：缺什么信息？该调用什么工具？
* Act（行动）：调用外部工具（搜索 / API / 数据库）。
* Observe（观察）：拿到工具返回的真实结果，喂给模型，进入下一轮思考。
* Think Again
* Act Again
* Observe Again
* 循环直到能给出最终答案
---

## 第三部分：知识与检索

### 第7章 RAG（Retrieval-Augmented Generation）

* 为什么需要 RAG
* 向量数据库（Embedding）
* Chunking 策略
* 检索策略（Top-K / Hybrid）
* RAG 的常见问题（召回失败、噪声）

---

### 第8章 Memory 系统设计

* 短期记忆（Conversation Buffer）
* 长期记忆（Vector DB / Knowledge Base）
* Episodic vs Semantic Memory
* Memory 更新策略

---

## 第四部分：Agent 架构设计

### 第9章 Agent 架构模式

* 单 Agent 架构
* Self-Reflection
* Plan & Execute
* Multi-Agent（协作 / 竞争）
* Workflow/DAG

---

### 第10章 多 Agent 系统

* 角色分工（Planner / Executor / Critic）
* 通信机制
* 协作协议
* 冲突解决

---

## 第五部分：知识拓展（TBD）

### 第11章 Agent 框架与工具链

* LangChain
* AutoGPT
* OpenAI Assistants API
* LlamaIndex
* 国内的框架
* 各框架优缺点对比

---

### 第12章 Harness Engineering
* 什么是Harness Engineering
* 为什么需要Harness Engineering
* Harness Engineering 的四大支柱
* 先进团队的实战

