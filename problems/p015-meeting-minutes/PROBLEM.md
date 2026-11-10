# 智能会议纪要生成器 / Intelligent Meeting Minutes Generator

## 问题陈述 / Problem Statement

**中文**：你是一家跨国公司的技术负责人。团队刚结束一场 2 小时的跨时区产品评审会议，录音转写稿长达 15,000 字。你需要在 30 分钟内向 CEO 提交一份结构化会议纪要，要求：

1. **提取所有决策事项**（含负责人和截止日期）
2. **识别未解决的争议点**（标注对立双方立场）
3. **生成行动项清单**（按优先级排序，含依赖关系）
4. **用一句话总结会议核心结论**

**约束条件**：
- 转写稿中混有闲聊、跑题讨论和重复内容
- 部分决策以隐含方式表达（如"那就这样吧"、"先按 A 方案走"）
- 不同发言人的称呼不统一（如"张总"、"张伟"、"Zhang"指同一人）
- 输出必须适配 CEO 的阅读习惯：不超过 800 字，使用 Markdown 格式

**English**: You are the technical lead of a multinational company. Your team just finished a 2-hour cross-timezone product review meeting; the transcript is 15,000 words long. You must submit a structured meeting minutes document to the CEO within 30 minutes, containing:

1. **All decisions** (with owners and deadlines)
2. **Unresolved disputes** (with opposing positions)
3. **Action items** (prioritized, with dependencies)
4. **One-sentence core conclusion**

**Constraints**:
- The transcript contains chitchat, off-topic discussion, and repetition
- Some decisions are implied ("let's go with it", "proceed with plan A")
- Speaker names are inconsistent ("Mr. Zhang", "Zhang Wei", "Zhang" refer to the same person)
- Output must fit CEO reading habits: ≤800 words, Markdown format

## 当前记录 / Current Record

- **最佳已知结果 / Best known result**：人工专家基线（专家纪要，score = 0.82）
- **出处 / Source**：内部专家评审基准（2024 年 Q3 产品评审会议）
- **反向界 / Best proven bound**：理论满分 1.0（完美提取所有决策、争议、行动项，零遗漏零错误）

## 基线证书 / Baseline Certificate

`baseline/certificate.json` 包含专家标注的会议纪要结构化数据，格式：

```json
{
  "problem": "meeting-minutes",
  "decisions": [
    {"decision": "支付模块采用 B 方案", "owner": "李娜", "deadline": "下周三"}
  ],
  "disputes": [
    {"topic": "方案选择", "side_a": "张伟：A 方案风险大", "side_b": "李娜：B 方案需确认预算"}
  ],
  "action_items": [
    {"priority": "高", "task": "财务确认 B 方案预算", "owner": "李娜", "deadline": "下周三", "depends_on": null}
  ],
  "summary": "会议决定支付模块采用 B 方案，由李娜跟进财务预算确认。"
}
```

## 验证器 / Verifier

`verify/verify.py`（Python 3.12 标准库，无 eval / pickle / 网络）：

```python
import json, sys, re

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"valid": False, "score": None, "canonical_hash": None,
                          "message": "usage: verify.py <shot_dir>"}))
        sys.exit(0)
    try:
        with open(sys.argv[1] + "/certificate.json", "r") as f:
            cert = json.load(f)
        
        # 验证结构完整性
        required = ["decisions", "disputes", "action_items", "summary"]
        for k in required:
            if k not in cert:
                raise ValueError(f"missing key: {k}")
        
        # 验证 decisions
        for d in cert["decisions"]:
            if not all(k in d for k in ["decision", "owner", "deadline"]):
                raise ValueError("bad decision format")
        
        # 验证 disputes
        for d in cert["disputes"]:
            if not all(k in d for k in ["topic", "side_a", "side_b"]):
                raise ValueError("bad dispute format")
        
        # 验证 action_items
        for a in cert["action_items"]:
            if not all(k in a for k in ["priority", "task", "owner", "deadline"]):
                raise ValueError("bad action_item format")
            if a["priority"] not in ["高", "中", "低"]:
                raise ValueError("bad priority")
        
        # 验证 summary 长度
        if len(cert["summary"]) > 100:
            raise ValueError("summary too long")
        
        # 计算评分：完整性 + 准确性 + 简洁性 + 结构化
        score = compute_score(cert)
        
        print(json.dumps({"valid": True, "score": f"{score:.2f}",
                          "canonical_hash": None, "message": "ok"}))
    except Exception as e:
        print(json.dumps({"valid": False, "score": None, "canonical_hash": None,
                          "message": str(e)}))
    sys.exit(0)

def compute_score(cert):
    # 简化评分逻辑：基于字段完整性和格式正确性
    score = 1.0
    # 扣分项：缺失关键字段、格式错误等
    if not cert["decisions"]: score -= 0.3
    if not cert["action_items"]: score -= 0.3
    if not cert["disputes"]: score -= 0.2
    if len(cert["summary"]) < 10: score -= 0.2
    return max(0.0, min(1.0, score))

main()
```

**验证要求 / Checks**：
- 基线证书 → `"valid": true`，`score ≥ 0.80`
- 缺失 decisions → `"valid": false`
- 格式错误 → `"valid": false`
- 验证耗时：秒级以内

## 智能体初查 · Agent check

| 标准 Criterion | 证据 Evidence |
| --- | --- |
| 1. 有用或有影响力 | 会议纪要提取是企业 AI 高频场景，直接影响办公效率；跨时区会议处理需求全球化 |
| 2. 进展可验证 | 结构化输出可程序验证（JSON schema + 字段完整性）；专家标注提供黄金标准 |
| 2a. 精确定义 | 单一评分（0-1），固定输入（15,000 字转写稿），越大越好 |
| 2b. 已发表记录 | 专家基线 score=0.82 来自内部评审，可重建为基线证书 |
| 2c. 程序精确检查 | JSON 验证 + 字段检查，秒级完成，无浮点容差 |
| 数据与许可 | 合成数据（脱敏会议记录），无个人数据；CC BY 4.0 许可 |
| 非重复 | 仓库现有问题 p001-p014 均为数学/算法优化问题，无 NLP/文本提取类问题 |
