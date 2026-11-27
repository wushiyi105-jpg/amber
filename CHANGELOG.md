# 更新记录

## Unreleased

- `0001_init` 改为显式 `op.create_table` / `op.create_index`，运行期走 `alembic upgrade`
- `app/` 只依赖 `ports`，新增内存假实现用例
- 开 ruff `E2`/`E3`；CI 增加 `docker build` 与 `/health` 探活

## 1.0.0

- 周吞吐均值与完工预测
- 未来两周负荷检测（> 120% 报警）
- 依赖成环检测，成环抛错
- 逾期 3 天进红列
- 风险说明数字守卫
- CLI 与 Web 双入口
