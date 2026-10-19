# 开发计划（Phase 1–6）

依据：规范第 15、19 节。每个阶段都写明入口条件、交付物、验收证据和退出条件。**开始任何一个阶段前，都需要在 `decision-log.md` 中新增一条批准记录**（规范第 2 节）。

工期估算基于假设 A-03：一位开发者，由 AI 编码代理辅助，每周投入约 25 小时。总计约 11 周。如果同时推进 ELIO，按 R-01 处理。

| Phase | 工期 | 入口条件 | 核心交付 | 退出证据（只有实际记录的证据才算数） | 必须通过的红队测试 |
| --- | --- | --- | --- | --- | --- |
| 1 基础 | 1.5 周 | Gate 0 通过 | 配置、structlog、FastAPI、PostgreSQL 加 pgvector、Alembic 全部表与 RLS、`TenantContext`、健康检查、Compose、CI、API key 与会话鉴权、端口接口 | `make verify` 一条命令完成启动、迁移、健康检查和测试；CI 链接；跳过的测试数为 0 | RT-01 至 RT-05、RT-22、RT-24 |
| 2 可靠执行 | 2 周 | Phase 1 Gate 通过 | outbox、Streams、Worker、状态机、幂等、重试、fencing 租约、死信、取消、恢复器 | 在真实 PostgreSQL 上跑并发与崩溃测试：杀掉 Worker、重启 Redis、重启 PostgreSQL，任务不丢失、不重复提交 | RT-06 至 RT-11 |
| 2.5 Pack 基础 | 2 周 | Phase 2 Gate 通过；D-009、D-013 已批准 | Pack CLI（打包、签名、导入）、注册表、生命周期、权限 diff、memory 层与 embedding、`event-summary` 参考包 | 参考包能完成安装、激活、回滚；金丝雀测试套件全绿 | RT-13 至 RT-18 |
| 3 AI 工作流与 API | 1.5 周 | Phase 2.5 Gate 通过；D-007 条款核验已存档；真实供应商冒烟测试的预算已批准 | `AnthropicProvider`、有界 Agent 运行器、预算预留与结算、输出校验、审批 API、webhook | 在非生产环境中，一个已鉴权的请求跑通 `summarize-event` 全流程；保留真实供应商冒烟测试的日志 | RT-12、RT-19 至 RT-21、RT-26 |
| 4 UI | 1.5 周 | Phase 3 Gate 通过 | 移动优先的界面，范围见 D-020，包含加载、空、错误、重试等状态 | 手机和桌面的截图；Playwright E2E 测试；用户不调用 API 也能完成主流程 | RT-23 |
| 5 加固 | 1.5 周 | Phase 4 Gate 通过 | 全量红队测试、备份恢复演练、回滚演练、成本控制测试、容量实测 | 有计时的恢复演练，结果满足 RPO 24h 和 RTO 4h；Critical 和 High 发现为 0，或有带期限的例外；所有残余风险都有负责人和到期日 | RT-25、RT-27，以及全部回归测试 |
| 6 部署交付 | 1 周 | Phase 5 Gate 通过；有 Tier 3 生产批准 | 在已批准的 VPS 上完成部署、监控、冒烟测试、运维手册，并披露已知限制 | 部署证据；线上恢复与回滚验证；所有者签字放行 | 冒烟测试集 |

## 裁剪规则（如果工期不足）

按以下顺序延后，以下内容都不影响 MVP 的 Definition of Done：

1. OpenTelemetry exporter（只保留 API）。
2. 每租户的部分 HNSW 索引（silo 模式下不需要）。
3. UI 中的审批队列（改为由 API 和 CLI 审批；需要先修订 D-020）。

**不可裁剪：** RLS、fencing、金丝雀测试套件、备份恢复演练、预算硬上限。

## 每个阶段结束时的报告

报告提交到 `docs/phase-reports/phase-<n>.md`，必须包含：

- 改动的文件与执行过的命令；
- 测试结果，包括跳过数（必须为 0）；
- 红队测试结果；
- 残余风险；
- 回滚方法；
- 下一阶段需要的批准。
