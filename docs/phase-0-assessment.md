# Phase 0 评估报告

**日期：** 2026-10-19
**规范：** MASTER_BUILD_SPEC.md v1.0
**仓库状态：** 全新仓库，只有 Phase 0 文档，没有应用代码（D-001、D-002）。

## 1. 范围确认

在规范第 3 节的 MVP 范围上，不增加也不删减。初始排除项完全照规范执行，另外明确三项：

- 不引入 n8n、Qdrant、OpenClaw、Hermes（D-003）。
- 不做行业逻辑；参考包是中立的事件摘要（D-004）。
- 不处理敏感个人数据（D-008）。

## 2. 开放决策覆盖表

规范第 2 节列出的每一项开放决策，都对应到决策日志里的一条：

| 规范开放决策 | 决策 | 状态 |
| --- | --- | --- |
| VPS provider, region, sizing | D-006 | Approved |
| AI provider, model, retention, budget | D-007 | Approved |
| Data sensitivity, data-protection law | D-008 | Approved |
| Pack manifest format, signing scheme | D-009 | Approved |
| Backup destination, retention, deletion SLA | D-010 | Approved |
| Per-tenant encryption keys | D-011 | Approved |
| First reference pack and industry | D-004 | Approved |
| Webhook providers | D-012 | Approved |
| RPO and RTO | D-018 | Approved |
| Approval owners | D-019 | Approved |
| Minimum UI scope | D-020 | Approved |

## 3. 规范缺口与内部矛盾（已在决策中处理）

| # | 缺口 | 后果 | 处理 |
| --- | --- | --- | --- |
| G-1 | pgvector 需要嵌入向量，但"单一 AI 供应商"排除了第二家嵌入 API | Phase 2.5 会卡住 | D-013：本地嵌入模型 |
| G-2 | 只写了 Redis 层的租约和 `XAUTOCLAIM` | 暂停后恢复的旧 Worker 可以覆盖结果，造成双重执行 | D-015：数据库 fencing token |
| G-3 | RLS 只在 pooled 模式开启 | silo 与 pooled 走两套代码路径，迁移到 pooled 时风险集中爆发 | D-014：所有拓扑一律开启 |
| G-4 | 开启 RLS 后，缺少租户上下文时查询返回空集，而不是报错 | 违反"fail closed"，并且会掩盖程序缺陷 | D-014 加测试 T-03：显式检查后抛异常 |
| G-5 | 供应商的计费无法撤回，与"取消进行中的调用"相冲突 | 记账不准，用户困惑 | D-016 |
| G-6 | "Billing alerts are not hard caps"，但没有规定由谁执行硬上限 | 成本失控 | D-007：由应用层的 `usage_ledger` 预留机制执行硬上限 |
| G-7 | Pack 签名的密钥管理没有定义 | 一把私钥就是整个供应链的信任根 | D-009：离线私钥，Phase 2.5 写轮换 runbook |
| G-8 | 第 16 节目录结构与 Canon 要求的 DDD 分层不同 | 结构可能漂移 | `docs/architecture.md` §4：在 `app/` 内部按 DDD 分层 |

## 4. 假设登记

| ID | 假设 | 如果不成立 |
| --- | --- | --- |
| A-01 | 开发和测试全程只用合成数据 | 需要先完成 D-008 的律师审阅 |
| A-02 | 第一批客户的单租户负载不超过 10 万任务/月、10 万条 memory | pgvector HNSW 需要按实测调参（R-06） |
| A-03 | 只有一位开发者，由 AI 编码代理辅助 | 时间表需要重排 |
| A-04 | Anthropic API 在新加坡 VPS 上可以正常访问 | 需要评估出站代理 |
| A-05 | 客户可以接受数据存放在新加坡 | 需要换本地供应商，D-006 重新决策 |

## 5. 风险登记

| ID | 风险 | 严重度 | 缓解 | 负责人 |
| --- | --- | --- | --- | --- |
| R-01 | **与 ELIO 战略重叠。** 两套 Core 并行，一人维护，进度互相拖累，决策互相漂移 | 高 | D-022：两个项目完全独立，产能风险由所有者接受；实际工期超过计划 150% 时触发分工复审 | Alvin |
| R-02 | 单一审批人与开发者，自我批准 | 中 | D-019 冷静期；Tier 3 前用独立 AI 复核；所有证据入库 | Alvin |
| R-03 | AI 供应商条款变化（训练、保留期） | 中 | D-007 书面存档；Phase 3 前重新核验 | Alvin |
| R-04 | 规范的 Phase 计划总计约 11 周，单人能力不足 | 中 | 见 `docs/development-plan.md` 的工期与裁剪规则 | Alvin |
| R-05 | 跨境传输与 PDPA 义务理解有误 | 中 | D-008 律师审阅；DPA 模板 | Alvin |
| R-06 | pgvector 规模与过滤检索性能（先按租户过滤、再排序） | 低 | silo 模式下单表只有一个租户；pooled 模式需要按 `tenant_id` 分区或使用部分索引，Phase 5 做压测 | Alvin |
| R-07 | Pack 签名私钥泄露 | 高 | 私钥离线保存，信任根支持吊销，轮换 runbook | Alvin |
| R-08 | 本地嵌入模型推高 Worker 内存，挤占小规格 VPS | 低 | Phase 2.5 实测；必要时拆出独立 embedding 进程 | Alvin |

## 6. Gate 0 判定

**状态：PASS（2026-10-19）。** 架构、威胁模型和开发计划已经完成；D-001 至 D-022 全部批准；R-01 已由 D-022 处理。

遗留到后续阶段的条件：
- D-007：Phase 3 接入真实供应商之前，必须完成条款核验并存档。
- D-008：Phase 6 生产部署之前，必须完成律师审阅。

**下一步：** 按规范第 2 节，Phase 1 开始前需要另行批准（新增一条决策记录）。
