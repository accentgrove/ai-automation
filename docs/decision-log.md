# 决策日志（Decision Log）

规范第 2 节要求的唯一审批记录。每条决策都包含规范规定的全部字段；`scripts/verify_phase0.py` 会逐条校验字段是否完整。

- **状态取值：** `Approved`（已批准）、`Proposed`（待批准）、`Rejected`（否决）、`Superseded`（被取代）。
- **审批人：** 全部为 Alvin Yew（见 D-019）。
- **规则：** 只要还有 `Proposed` 状态的决策，Gate 0 就不能通过。批准方式是把 Status 改成 `Approved`，并在 Evidence 里写上批准日期和渠道。

---

## A. 已批准决策（2026-10-19）

### D-001 独立新仓库，与 ELIO 分离
- **Decision:** 本项目是独立的新仓库 `ai-automation`，从零开始，不复用 ELIO（automation-control-center）的代码、契约或 Gate。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 本规范与 ELIO 的 ADR-003/004 在部署模型、行业包、RPO/RTO 上高度重叠。
- **Alternatives:** 作为 ELIO Core 的重建基线；作为客户定制交付项目。
- **Rationale:** 由所有者选定。
- **Security/Ops impact:** 两套代码库并行，运维与决策维护成本翻倍。风险登记见 R-01（`docs/phase-0-assessment.md`）。
- **Reversibility:** 可逆。Phase 1 前合并或停止的成本很低，Phase 3 之后成本显著上升。
- **Evidence:** 2026-10-19 chat 中所有者的选择。
- **Status:** Approved

### D-002 本轮交付范围只到 Phase 0
- **Decision:** 本轮只交付 Phase 0（评估与设计），不写应用代码。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范第 2、19 节要求每个阶段开始前都要批准，且禁止一次性未经审查地完成整个平台。
- **Alternatives:** Phase 0 + 1；一直做到 Phase 2。
- **Rationale:** 由所有者选定。先把开放决策关掉，再动代码。
- **Security/Ops impact:** 无运行时影响。
- **Reversibility:** 完全可逆。
- **Evidence:** 2026-10-19 chat 中所有者的选择。
- **Status:** Approved

### D-003 技术栈严格按规范，向量只用 pgvector
- **Decision:** 技术栈以规范第 4 节为准：单一 PostgreSQL（含 pgvector），不引入 Qdrant、n8n、OpenClaw、Hermes 或其他重型 agent 框架。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** Founder's Canon 指定的是 Qdrant + n8n，与规范第 1 节"避免多数据库、重型框架"冲突。
- **Alternatives:** 按 Canon 引入 Qdrant 与 n8n，并在本日志中写明偏离理由。
- **Rationale:** 单库意味着事务一致、备份恢复只有一条路径、租户隔离只有一处 RLS 需要证明。
- **Security/Ops impact:** 隔离面缩小为一处；pgvector 的规模上限见 R-06。
- **Reversibility:** 可逆。检索放在 `MemoryRetriever` 接口后面，日后可以替换。
- **Evidence:** 2026-10-19 chat 中所有者的选择。
- **Status:** Approved

### D-004 参考包：中立的事件摘要包
- **Decision:** 第一个参考包是 `event-summary`，接收任意事件 JSON，产出结构化摘要，不含任何行业逻辑。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范第 10 节建议的示例；可选方案是美容包。
- **Alternatives:** 美容与美学包。
- **Rationale:** 最能证明 Core 行业中立、Core 与 Pack 边界清晰；不会把行业字段带进 Core 的 schema。
- **Security/Ops impact:** 只用合成事件，没有个人数据风险。
- **Reversibility:** 可逆。第二个包可以是行业包。
- **Evidence:** 2026-10-19 chat 中所有者的选择。
- **Status:** Approved

### D-005 规范基线决策（v1.0 已确认）
- **Decision:** 采纳规范第 2 节的五项基线：每客户独立 VPS（silo）为默认；MVP 中 Pack 只能是声明式；向量用 pgvector；禁止跨租户学习、微调和汇总内容分析；租户 memory 严格隔离。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范 v1.0 标注为已确认。
- **Alternatives:** 无，规范已定。
- **Rationale:** 规范基线。
- **Security/Ops impact:** 定义了隔离与执行的边界。
- **Reversibility:** 变更任何一项都需要新的 Tier 2 决策。
- **Evidence:** MASTER_BUILD_SPEC.md 第 2 节。
- **Status:** Approved

---

## B. Phase 0 开放决策（2026-10-19 全部批准）

以下各项原为建议默认值，已于 2026-10-19 获批生效（规范第 2 节）。详细论证见 `docs/phase-0-assessment.md`。

### D-006 VPS 供应商、区域与规格
- **Decision:** 默认 Hetzner Cloud，新加坡区域；起步规格 4 vCPU / 8 GB RAM / 160 GB SSD；备选 DigitalOcean SGP1。最终型号在 Phase 5 按容量实测确定。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 目标客户在马来西亚；新加坡延迟低，两家供应商都有该区域。
- **Alternatives:** DigitalOcean SGP1（价格较高、生态成熟）；本地马来西亚 IDC（合规叙事好，但 API 与自动化能力弱）。
- **Rationale:** 在 Canon 范围内成本最低；有 API 可以自动化建机。
- **Security/Ops impact:** 数据存放在马来西亚境外，构成 PDPA 下的跨境传输，必须在合同或 DPA 中写明（见 D-008）。
- **Reversibility:** 可逆。全部 Docker Compose 部署，换供应商就是一次备份恢复。
- **Evidence:** 2026-10-19 chat 中所有者批准。后续实施证据：Phase 5 容量实测报告。
- **Status:** Approved

### D-007 AI 供应商、模型、保留条款、预算
- **Decision:** 单一供应商 Anthropic API。默认模型 `claude-haiku-5-5`，用于事件摘要；在批准之前不引入第二个模型。开发期月预算硬上限 USD 50，由应用层的 `usage_ledger` 预留机制强制执行。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范第 1 节要求单一 AI 供应商；第 12 节要求供应商条款排除用客户数据训练，并限定保留期。
- **Alternatives:** `claude-sonnet-5-5`（质量更高、单价更高）；OpenAI 或 Gemini（违反 Canon 中 Claude 作为核心推理的定位）。
- **Rationale:** 摘要任务用小模型足够；成本可控。
- **Security/Ops impact:** 需要**书面确认**当前商业条款中的训练排除与保留期，确认结果存档到 `docs/evidence/`。这是 Phase 3 接入真实供应商之前的阻断项。
- **Reversibility:** 可逆。模型名只出现在配置里。
- **Evidence:** 2026-10-19 chat 中所有者批准。后续实施证据：条款核验存档。
- **Status:** Approved

### D-008 数据敏感度与适用法律
- **Decision:** 适用马来西亚《个人数据保护法》（PDPA 2010，含 2024 修正案）。MVP 不处理"敏感个人数据"；开发与测试只用合成数据。silo 模式下，客户是数据控制者，我方是数据处理者。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 2024 修正案已于 2025 年分阶段生效：处理者直接承担安全原则义务；取消跨境传输白名单；强制数据泄露通报与 DPO 委任。
- **Alternatives:** 允许敏感数据（需要逐字段加密、单独同意流程，MVP 不承担）。
- **Rationale:** 先把合规面压到最小。
- **Security/Ops impact:** 必须具备泄露通报所需的审计与取证能力（结构化日志、访问审计）。具体义务以律师意见为准，本条不构成法律意见。**附加条件：律师审阅必须在 Phase 6 生产部署前完成，否则 Phase 6 Gate 不得通过。**
- **Reversibility:** 放宽到敏感数据需要新的 Tier 3 决策。
- **Evidence:** 2026-10-19 chat 中所有者批准。后续实施证据：律师审阅意见。
- **Status:** Approved

### D-009 Pack 清单格式与签名方案
- **Decision:** 清单用 YAML，按 `packs/schema/manifest.v1.json`（JSON Schema）校验。打包为确定性 tar（排序、固定 mtime），对 SHA-256 摘要做 Ed25519 分离签名（Python `cryptography` 库）。每台 VPS 的信任根配置可信公钥列表。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范第 11 节要求导入时签名可验证。
- **Alternatives:** Sigstore cosign（依赖外网 OIDC，离线 VPS 不友好）；GPG（工具链笨重）。
- **Rationale:** 零外部依赖，离线可用，实现小、易审计。
- **Security/Ops impact:** 私钥离线保存。密钥泄露时的轮换流程在 Phase 2.5 写入 runbook。
- **Reversibility:** 可逆。清单里有 `signature.alg` 字段，可以迁移到其他算法。
- **Evidence:** 2026-10-19 chat 中所有者批准。
- **Status:** Approved

### D-010 备份目标、保留期与删除 SLA
- **Decision:** 每日 `pg_dump` 逻辑备份，用 age 和**每租户独立密钥**加密，传到 Cloudflare R2（S3 兼容）。保留：7 个日备、4 个周备、3 个月备。离场删除 SLA：线上数据 7 天内清除；备份随轮换在 90 天内自然过期，并出具删除报告。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** RPO 24 小时，每日备份即可满足（D-018）。
- **Alternatives:** Hetzner Object Storage；WAL 归档加 PITR（RPO 可以做到分钟级，但运维复杂度高）。
- **Rationale:** R2 在 Canon 的 Cloudflare 生态内，且没有出站流量费。
- **Security/Ops impact:** 必须定期做恢复演练，没有演练过的备份不算备份（Phase 5 证据）。
- **Reversibility:** 可逆。
- **Evidence:** 2026-10-19 chat 中所有者批准。
- **Status:** Approved

### D-011 每租户加密密钥
- **Decision:** MVP 中备份必须使用每租户独立密钥（见 D-010）；应用层的字段级每租户加密列为可选，延后到有敏感数据需求时再做。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** silo 模式下每台 VPS 已经物理隔离，磁盘加密由供应商提供。
- **Alternatives:** 现在就做字段级加密，KMS 选 HashiCorp Vault 或云 KMS。
- **Rationale:** 在没有敏感数据的前提下，字段级加密的成本高于收益。
- **Security/Ops impact:** pooled 模式上线之前，必须重新评估本条。
- **Reversibility:** 可逆，但事后加密存量数据需要迁移。
- **Evidence:** 2026-10-19 chat 中所有者批准。
- **Status:** Approved

### D-012 Webhook 提供方
- **Decision:** MVP 只支持一种通用提供方 `generic-hmac`：HMAC-SHA256 签名，头部格式 `X-Signature: t=<unix>,v1=<hex>`，时间容差 300 秒，事件 ID 通过 `webhook_events` 去重。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范第 9 节。目前没有确定的第三方 webhook 需求。
- **Alternatives:** 直接接 Stripe、WhatsApp Cloud API 等具体提供方。
- **Rationale:** 一种实现就能证明签名、防重放和去重三件事；具体提供方等有客户需求时，再作为适配器加入。
- **Security/Ops impact:** 每个 VPS、每个提供方使用独立密钥。
- **Reversibility:** 可逆。
- **Evidence:** 2026-10-19 chat 中所有者批准。
- **Status:** Approved

### D-013 嵌入（embedding）来源
- **Decision:** Worker 内用本地 CPU 嵌入模型（`fastembed`，ONNX，多语言小模型 `intfloat/multilingual-e5-small`，384 维），不调用第二家云供应商。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** **规范缺口。** pgvector 需要嵌入向量，但 Anthropic 不提供嵌入 API。规范第 1 节又禁止多个 AI 供应商。
- **Alternatives:** Voyage AI 嵌入 API（会成为第二个供应商，并带来数据出境）；参考包暂时不用语义检索。
- **Rationale:** 不增加供应商，数据不出 VPS，支持马来语、中文、英文。
- **Security/Ops impact:** Worker 镜像大约增加 150–250 MB，内存占用大约增加 0.5 GB。模型文件构建时固定版本与哈希。
- **Reversibility:** 可逆，但换模型需要全量重建向量。
- **Evidence:** 2026-10-19 chat 中所有者批准。后续实施证据：Phase 2.5 检索质量与延迟实测。
- **Status:** Approved

### D-014 RLS 在所有拓扑下一律开启
- **Decision:** 从第一个迁移开始，所有租户表都执行 `ENABLE` 加 `FORCE ROW LEVEL SECURITY`，silo 模式也不例外。应用以非表属主、`NOBYPASSRLS` 的角色连接；每个事务用 `SET LOCAL app.tenant_id` 设置租户上下文。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范只要求 pooled 模式开 RLS。如果 silo 不开，两种模式就有两套代码路径，迁移到 pooled 时，从未被测试过的那一套会成为风险。
- **Alternatives:** 只在 pooled 模式开启。
- **Rationale:** 一套路径，一套测试；"迁移靠配置而不是重写"才成立。
- **Security/Ops impact:** 缺少租户上下文时查询返回空集，而不是报错。因此必须加一层显式检查，让它 fail closed 抛异常（见 T-03）。
- **Reversibility:** 可逆。
- **Evidence:** 2026-10-19 chat 中所有者批准。
- **Status:** Approved

### D-015 任务租约用数据库 fencing token
- **Decision:** 执行权以 PostgreSQL 为准：`tasks` 表有 `lease_owner`、`lease_expires_at`、`fencing_token`（单调递增）三列；Worker 提交结果时必须带上 token，`UPDATE ... WHERE fencing_token = :token` 影响 0 行即视为过期 Worker，结果被拒绝。Redis `XAUTOCLAIM` 只负责重新投递消息，不赋予执行权。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** **规范缺口。** 规范只写了"Worker leases + XAUTOCLAIM"；Redis 层面的认领无法阻止一个被暂停又恢复的旧 Worker 写回结果。
- **Alternatives:** 只依赖 Redis 租约。
- **Rationale:** 这是能在数据库层被证明的唯一方案。
- **Security/Ops impact:** 必须有在真实 PostgreSQL 上运行的并发测试（RT-07、RT-08）。
- **Reversibility:** 可逆。
- **Evidence:** 2026-10-19 chat 中所有者批准。
- **Status:** Approved

### D-016 取消语义
- **Decision:** 取消请求先把任务标为 `cancel_requested`。Worker 在每个步骤边界检查这个标记，并主动中断正在进行的 HTTP 请求；已经发生的供应商用量照常记账；最终状态为 `cancelled`。已经 `completed` 的任务不可取消（返回 409）。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范第 8 节要求明确取消语义。供应商侧的计费无法撤回。
- **Alternatives:** 立即强制终止 Worker 进程。
- **Rationale:** 结果确定、可测试，记账准确。
- **Security/Ops impact:** 需要做竞态测试：取消请求和完成写入同时到达（RT-09）。
- **Reversibility:** 可逆。
- **Evidence:** 2026-10-19 chat 中所有者批准。
- **Status:** Approved

### D-017 工具链
- **Decision:** Python 3.12（锁定次版本）；依赖用 `uv` 管理，并提交 `uv.lock`；类型检查用 `mypy --strict`；代码检查与格式化用 Ruff；反向代理用 Caddy（自动 TLS）；日志用 `structlog` 输出 JSON；追踪用 `opentelemetry-api`，exporter 默认关闭。
- **Date:** 2026-10-19
- **Tier:** 1
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范第 4 节要求锁定依赖，并做静态类型检查。
- **Alternatives:** Poetry、pip-tools；pyright；Nginx 加 certbot；Traefik。
- **Rationale:** `uv` 速度快、锁文件可复现；Caddy 零配置 TLS，配置最少。
- **Security/Ops impact:** 镜像中固定 digest，并做依赖扫描（`pip-audit` 加 Trivy）。
- **Reversibility:** 完全可逆。
- **Evidence:** 2026-10-19 chat 中所有者批准。
- **Status:** Approved

### D-018 RPO 与 RTO
- **Decision:** RPO 24 小时，RTO 4 小时（按规范建议默认值）。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范第 2 节建议的默认值。
- **Alternatives:** RPO 1 小时（需要 WAL 归档）。
- **Rationale:** 与单 VPS、每日备份的部署模型一致；不对外承诺高可用。
- **Security/Ops impact:** Phase 5 必须提供计时证据的恢复演练。
- **Reversibility:** 可逆。收紧指标需要追加 WAL 归档。
- **Evidence:** 2026-10-19 chat 中所有者批准。
- **Status:** Approved

### D-019 审批人与响应时限
- **Decision:** 三个审批层级的审批人都是 Alvin Yew。Tier 1：CI 全绿加自审即可合并。Tier 2：2 个工作日内给出答复。Tier 3：书面批准，且在作出决定后至少间隔 24 小时才执行，作为冷静期。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范要求在 Phase 0 约定审批人响应期望。目前只有一个人。
- **Alternatives:** 为 Tier 3 引入外部第二审批人（顾问或律师）。
- **Rationale:** 一人公司的现实。冷静期弥补缺少第二双眼睛的问题。
- **Security/Ops impact:** 存在单点风险（R-02）。生产部署建议引入 AI 独立复核作为补充，但它不能替代批准。
- **Reversibility:** 可逆。
- **Evidence:** 2026-10-19 chat 中所有者批准。
- **Status:** Approved

### D-020 最小 UI 范围
- **Decision:** MVP UI 只包含：登录与登出；提交任务；任务列表与状态；任务详情、结果与失败原因；审批队列（批准或拒绝）。Pack 管理只通过 CLI 和 API 完成，不做界面。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范第 3 节与第 19 节 Phase 4。
- **Alternatives:** 增加 Pack 管理与用量看板。
- **Rationale:** 满足 Phase 4 Gate 的最小集合。
- **Security/Ops impact:** 后台入口越少，攻击面越小。
- **Reversibility:** 可逆。
- **Evidence:** 2026-10-19 chat 中所有者批准。
- **Status:** Approved

### D-021 幂等键保留窗口与限额默认值
- **Decision:** 幂等键在租户内唯一，保留 7 天。默认限额：请求体 ≤ 256 KB；任务输入 JSON ≤ 64 KB；每次运行最多 8 步、32k token、120 秒；最多重试 5 次（指数退避加抖动，上限 5 分钟）；每租户每分钟 60 次 API 请求。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 规范第 8、10、18 节要求定义这些数值。
- **Alternatives:** 保留 24 小时（容易让客户端的延迟重试失去保护）。
- **Rationale:** 保守默认值；都放在配置中，可以按租户覆盖。
- **Security/Ops impact:** 防止成本滥用与重试风暴。
- **Reversibility:** 可逆。
- **Evidence:** 2026-10-19 chat 中所有者批准。
- **Status:** Approved

### D-022 ELIO 分工：两个项目完全独立
- **Decision:** ai-automation 与 ELIO（automation-control-center）是两个完全独立的项目：不共享代码、契约、Gate 或路线图，也不预设合并或迁移计划。
- **Date:** 2026-10-19
- **Tier:** 2
- **Owner:** Alvin Yew
- **Approver:** Alvin Yew
- **Context:** 风险 R-01，两个项目在部署模型与行业包上高度重叠。
- **Alternatives:** 本项目作为通用 Core、ELIO 作为行业 OS；本项目取代 ELIO Core；本项目只作参考或学习用途。
- **Rationale:** 由所有者选定。
- **Security/Ops impact:** 边界已经明确，但一人同时维护两套 Core 的产能风险依然存在，由所有者接受。缓解措施：每个 Phase 结束时的报告必须写明本阶段实际投入的工时；如果某个 Phase 的实际工期超过计划的 150%，就触发一次分工复审。
- **Reversibility:** 可逆。可以随时用新决策改为合并或迁移。
- **Evidence:** 2026-10-19 chat 中所有者的选择。
- **Status:** Approved
