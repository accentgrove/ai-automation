# 架构设计（Phase 0）

依据：MASTER_BUILD_SPEC.md 第 5–12 节。凡是与规范不同的地方，都会注明对应的决策编号。

## 1. 组件与信任边界

```
                    互联网（不可信）
                         │
            ┌────────────┴────────────┐  信任边界 TB-1
            │  Caddy（TLS 终止，只开 443/80） │
            └────────────┬────────────┘
                         │
   ┌─────────────────────┴──────────────────────┐  信任边界 TB-2：鉴权之后
   │  api（FastAPI）                              │
   │   AuthN（API key / session）→ TenantContext  │
   │   → 校验 → 限流 → 预算预留 → 领域服务          │
   └──────┬───────────────────────────┬─────────┘
          │ 同一事务写入                │
   ┌──────┴───────┐            ┌──────┴────────────┐
   │ PostgreSQL   │◄───────────┤ outbox-publisher   │（api 进程内的后台循环，
   │ + pgvector   │  轮询发布    └──────┬────────────┘  可独立部署）
   │ RLS 全开      │                   │ XADD
   └──────▲───────┘            ┌──────┴────────────┐
          │                    │ Redis Streams      │ t:{tenant_id}:tasks
          │ fencing 提交        └──────┬────────────┘
   ┌──────┴────────────────────────────┴─────────┐  信任边界 TB-3：执行
   │  worker（独立进程）                           │
   │   领取（DB 租约）→ Pack 工作流 → 有界 Agent    │
   │   → LLMProvider ──────────────────────────────┼──► Anthropic API（TB-4，出站白名单）
   │   → 本地 embedding（D-013）                   │
   └──────────────────────────────────────────────┘
```

| 边界 | 进入方 | 必须做的检查 |
| --- | --- | --- |
| TB-1 | 任意客户端 | TLS、请求大小上限、边缘限流（Cloudflare 可选，不能替代 TB-2） |
| TB-2 | 已鉴权身份 | `TenantContext` 只从凭证派生；Pydantic 校验；应用层限流 |
| TB-3 | 队列消息 | 消息只携带 `task_id` 和 `tenant_id`；Worker 从数据库重新读取任务并校验租户归属，不信任消息体 |
| TB-4 | 模型输出、外部内容 | 视为不可信；按 schema 校验；绝不当作指令执行 |

## 2. 关键流程

### 2.1 提交任务（规范第 8 节）

1. 用 API key 换出 `TenantContext`，构造后不可变。
2. 校验 workflow 是否属于本租户已激活的 Pack，校验输入 schema 和大小。
3. 检查限流与预算预留，在 `usage_ledger` 里写入 `reserved` 记录。
4. 处理幂等键：
   - 先查 `(tenant_id, idempotency_key)`；
   - 已存在且 payload hash 相同：返回原来的 `task_id`；
   - 已存在但 hash 不同：返回 `409`。
5. 在**同一个事务**里插入 `tasks`（状态 `queued`）和 `outbox_events`。
6. 返回 `202 {task_id}`。
7. Publisher 用 `SELECT ... FOR UPDATE SKIP LOCKED` 批量取出事件，执行 `XADD`，再标记为已发布。如果在 `XADD` 之后、标记之前崩溃，事件会被重复发布；这种情况在第 2.2 节由幂等领取吸收。

### 2.2 执行与 fencing（D-015）

```sql
-- 领取：原子操作，只有一个 Worker 能成功
UPDATE tasks
   SET status = 'running', lease_owner = :worker, lease_expires_at = now() + :ttl,
       fencing_token = fencing_token + 1, attempt = attempt + 1
 WHERE id = :task_id AND tenant_id = :tenant
   AND (status IN ('queued','retrying')
        OR (status = 'running' AND lease_expires_at < now()))
RETURNING fencing_token;

-- 提交：token 不匹配就影响 0 行，表示这是过期 Worker
UPDATE tasks SET status = 'completed', result = :r, lease_owner = NULL
 WHERE id = :task_id AND fencing_token = :token AND status = 'running';
```

- Worker 在每个步骤之后续租；续租同样带 token 条件。
- 只有在提交成功，或者已经写下明确的恢复决定之后，才执行 `XACK`。
- `XAUTOCLAIM` 负责把挂起的消息重新投递出去；收到消息的 Worker 仍然要走上面的领取 SQL，抢不到就直接 `XACK` 丢弃。
- 毒消息：`attempt` 达到 `max_attempts` 时，状态置为 `failed`，并写入死信表 `dead_letters`（运维可见，可以手动重放）。

### 2.3 状态机

```
queued ──claim──► running ──ok──► completed
  ▲                 │ │
  │   transient err │ └─perm err / max attempts──► failed
  └──── retrying ◄──┘
任何非终态 ──cancel_requested──► cancelled（在 Worker 下一个步骤边界生效；D-016）
```

终态：`completed`、`failed`、`cancelled`，进入终态后不可再迁移。数据库层用 CHECK 约束加触发器，禁止非法的状态迁移。

## 3. 租户隔离（规范第 6、12 节；D-014）

- 所有租户表都有 `tenant_id uuid NOT NULL`，并配置 RLS 策略 `USING (tenant_id = current_setting('app.tenant_id')::uuid)`。
- 数据库角色：
  - `app_owner`：执行迁移，是表属主；
  - `app_rw`：应用使用，`NOBYPASSRLS`，不是表属主，没有 DDL 权限；
  - `app_backup`：只读，用于导出。
- 会话层：每个事务开头执行 `SET LOCAL app.tenant_id`；没有 `TenantContext` 时，仓储层直接抛出 `MissingTenantContext`，请求根本不会发到数据库。
- 向量检索：`WHERE tenant_id = :t ORDER BY embedding <=> :q LIMIT k`。租户过滤写在查询之内（再由 RLS 兜底），绝不先做全局 top-k 再过滤。pooled 模式下按 `tenant_id` 建部分 HNSW 索引，或者对表做分区（R-06）。
- Redis：所有键和 stream 都以 `t:{tenant_id}:` 为前缀；不同租户之间不共享 prompt 或 completion 缓存。
- 离场清除：依次删除数据库行（按外键顺序）、Redis 键、挂起的 stream 条目，然后生成删除报告（每张表的计数为 0，并附哈希）；备份按 D-010 轮换过期。

## 4. 代码结构（规范第 16 节，`app/` 内按 DDD 分层）

```
app/
├── core/            # 配置、日志、错误、TenantContext、时钟（无业务逻辑）
├── domain/          # 纯领域：实体、状态机、领域服务；不 import 基础设施
│   ├── identity/    #   tenants, users, api_keys, sessions
│   ├── tasks/       #   tasks, attempts, idempotency, 状态机
│   ├── packs/       #   manifest 模型、生命周期、权限 diff
│   ├── agents/      #   有界运行器、预算、步骤记录
│   ├── memory/      #   memory 条目、提升策略、清除
│   └── approvals/
├── infra/           # 适配器：实现 domain 定义的端口
│   ├── db/          #   SQLAlchemy 模型、仓储、RLS 会话
│   ├── queue/       #   Redis Streams 发布与消费
│   ├── llm/         #   LLMProvider：anthropic、fake
│   └── embedding/   #   fastembed 适配器
├── api/             # FastAPI 路由、依赖、错误映射
└── worker/          # Worker 入口、执行循环、恢复器
packs/
├── schema/manifest.v1.json
└── event-summary/   # 参考包（D-004）
```

依赖方向：`api` 与 `worker` → `domain` ← `infra`。`domain` 不依赖 Redis 或任何供应商 SDK（规范第 5 节）。

## 5. 数据模型草案（规范第 7 节）

所有表都有主键 `id uuid`，以及 `created_at`、`updated_at`（timestamptz）。表名后标 ⓣ 的是租户表（含 `tenant_id` 并开启 RLS）。

| 表 | 关键列 | 约束与索引 |
| --- | --- | --- |
| tenants | name, status, plan_limits jsonb | — |
| users ⓣ | email_ci, password_hash (argon2id), role | UNIQUE(tenant_id, email_ci) |
| api_keys ⓣ | prefix, hash (SHA-256 加 pepper), scopes, expires_at, revoked_at | UNIQUE(prefix)；只存哈希 |
| workflows ⓣ | pack_installation_id, key, input_schema, output_schema | UNIQUE(tenant_id, key) |
| tasks ⓣ | workflow_id, status, input jsonb（≤ 64 KB）, result jsonb, error, idempotency_key, payload_hash, attempt, max_attempts, lease_owner, lease_expires_at, fencing_token, cancel_requested | UNIQUE(tenant_id, idempotency_key)；INDEX(status, lease_expires_at) |
| task_attempts ⓣ | task_id, n, started_at, ended_at, outcome, error_class | UNIQUE(task_id, n) |
| outbox_events ⓣ | topic, payload, published_at | 部分索引 WHERE published_at IS NULL |
| webhook_events ⓣ | provider, event_id, received_at, payload_hash | UNIQUE(tenant_id, provider, event_id) |
| usage_ledger ⓣ | task_id, kind（reserve、commit、release）, tokens_in, tokens_out, cost_micro_usd | INDEX(tenant_id, created_at) |
| approvals ⓣ | subject_type, subject_id, action, status, decided_by, decided_at, reason | — |
| agent_runs ⓣ | task_id, provider, model, budget, used, status | — |
| agent_steps ⓣ | run_id, n, kind, latency_ms, tokens, output_valid | UNIQUE(run_id, n) |
| packs | name, publisher_key_id | 全局表，不含租户数据 |
| pack_versions | pack_id, version, digest, signature, manifest jsonb | UNIQUE(pack_id, version) |
| pack_installations ⓣ | pack_version_id, status（staged、approved、active、rolled_back）, granted_permissions | 每个 pack 同一时间只能有一个 active 安装 |
| memory_items ⓣ | installation_id, scope, content, provenance, trust_level, ttl_at, size_bytes | 内容大小上限 |
| memory_embeddings ⓣ | item_id, model, embedding vector(384) | 每租户一个 HNSW 索引（cosine） |
| memory_audit ⓣ | item_id, action, actor, at | 只追加 |
| dead_letters ⓣ | task_id, reason, payload_ref | **新增表，不在规范列表中**，用于运维可见性 |

保留规则：`webhook_events` 保留 30 天；幂等键保留 7 天（D-021）；`agent_steps` 保留 90 天；审计表永久保留，直到租户离场。

## 6. LLMProvider 接口（规范第 10 节）

```python
class LLMProvider(Protocol):
    async def complete(self, ctx: TenantContext, req: CompletionRequest,
                       budget: BudgetReservation, deadline: float) -> CompletionResult: ...
```

- `CompletionRequest` 包含 system、messages、`output_schema` 和 `max_tokens`。`CompletionResult` 包含解析后的输出、token 用量、延迟和 `provider_request_id`。
- 错误分类：`TransientProviderError`（429、5xx、超时）可以重试；`PermanentProviderError`（4xx、schema 校验失败超过 1 次修复）不可重试。
- 实现有两个：`AnthropicProvider` 和 `FakeProvider`。后者是确定性的，单元测试与 CI 默认使用它。

## 7. Pack 格式草案（D-009）

```yaml
apiVersion: pack/v1
name: event-summary
version: 1.0.0
core: ">=0.1,<0.2"
permissions:
  llm: { models: [default], max_tokens_per_run: 4000 }
  memory: { read: own, write: own }
  tools: []                    # 参考包不使用任何工具
workflows:
  - key: summarize-event
    input_schema: schemas/event.json
    output_schema: schemas/summary.json
    prompt: prompts/summarize.v1.md
    limits: { max_steps: 2, timeout_s: 60 }
    approval: none
policies: { retention_days: 30 }
tests: { fixtures: fixtures/, adversarial: adversarial/ }
signature: { alg: ed25519, key_id: "<发布者公钥 ID>" }
```

生命周期：`import`（校验签名与 schema）→ `stage` → `approve`（展示权限 diff）→ `activate`（按租户）→ `rollback`（回到上一个 active 版本）。

## 8. 部署拓扑（规范第 18 节）

Compose 服务：`caddy`、`api`、`worker`（可以多副本）、`postgres`（pgvector 镜像，固定 digest）、`redis`（开启 AOF）、`backup`（cron 容器，执行 `pg_dump | age | rclone`）。只有 `caddy` 暴露端口。所有容器以非 root 用户运行；`postgres` 和 `redis` 只在内部网络中。
