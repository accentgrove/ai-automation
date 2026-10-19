# ai-automation — Agentic AI Automation Core

安全、可扩展、行业中立的 AI 自动化核心系统。规范见 [MASTER_BUILD_SPEC.md](MASTER_BUILD_SPEC.md)（v1.0）。

## 当前状态

**Gate 0 已通过（2026-10-19）。** Phase 1 等待启动批准。仓库中还没有应用代码。

## 文档

| 文件 | 内容 |
| --- | --- |
| [docs/phase-0-assessment.md](docs/phase-0-assessment.md) | 范围确认、开放决策覆盖、规范缺口、假设、风险、Gate 0 判定 |
| [docs/decision-log.md](docs/decision-log.md) | 全部决策（22 条，全部已批准） |
| [docs/architecture.md](docs/architecture.md) | 组件、信任边界、关键流程、租户隔离、数据模型、接口、Pack 格式 |
| [docs/threat-model.md](docs/threat-model.md) | 27 条威胁，逐条映射到红队测试和对应 Phase |
| [docs/development-plan.md](docs/development-plan.md) | Phase 1–6 的工期、入口与退出条件、证据要求、裁剪规则 |
| [AGENTS.md](AGENTS.md) | AI 编码代理的工作规则 |

## 校验

```bash
python3 scripts/verify_phase0.py          # 校验文档完整性（应当通过）
python3 scripts/verify_phase0.py --gate   # 判定 Gate 0
```

只依赖 Python 3.10 以上的标准库。

## 如何批准

在 `docs/decision-log.md` 中，把对应决策的 `Status` 改为 `Approved`，并在 `Evidence` 中写上日期和渠道。然后运行 `--gate`。
