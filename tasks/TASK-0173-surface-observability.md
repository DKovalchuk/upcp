# TASK-0173 — Surface-aware observability: корреляция, трейсы, метрики, rate-limit по типу API

**Source:** SPEC-0028 §3.6 (S28.6); Dmitry 2026-11-02 («запросы от веб и
от агентов должны отслеживаться и анализироваться по разному… разные
форматы корреляции, префикс или разные форматы»)
**Milestone:** auth rework (SPEC-0028 batch)
**Spec:** SPEC-0028 §3.6, AC9
**Points:** 3
**Status:** PENDING (реализация не начата)

## Context

`CorrelationMiddleware`, `TracingMiddleware`, `MetricsMiddleware`,
`RateLimitMiddleware` — общие и не знают, кто вызывает (web-браузер или
агент). Разделять нужно **данными**, а не дублированием middleware:
`web_auth`/`agent_auth` выставляют `request.state.api_surface`, и
общие middleware читают её. Отдельно: `rate_limit_middleware.py:33`
содержит тот же строковый хардкод префиксов — устранить (переход на
контракт «поверхность из контекста/реестра», а не `startswith`).

## Goals

1. `api_surface` (`web|agent|public`) в `request.state` от auth-зависимостей;
   контекстный признак в structured logs (contextvar, выставляемый в том
   же request-контексте — с учётом, что sync-зависимости в threadpool
   контекст не возвращают: либо async-обёртка, либо чтение scope-state).
2. Корреляция: `X-Request-ID` с префиксом поверхности
   (`web:<uuid>` / `agent:<uuid>`) — ответ и логи; входящий
   клиентский `X-Request-ID` сохраняется (суффиксом/после префикса).
3. OTel: span-атрибуты `upcp.auth.surface` (+ `upcp.auth.principal_type`);
   метрики: label `surface` на request-metrics и auth-denials.
4. Rate-limit: policy по поверхности (конфиги в `settings`:
   `UPCP_RATE_LIMIT_WEB_*` / `*_AGENT_*` — имена уточнить по
   префиксу-контракту TASK-0119), хардкод-строки `startswith` убраны
   (классификация — по registry/`scope["route"]` после маршрутизации
   либо через surface из auth-зависимости — решение в задаче по
   измеримому cost'у).
5. Наблюдаемость без нагрузки: surface-знание доступно до логирования
   хендлера (иначе префикс в логах бесполезен).

## Test design (совместная проработка до кода — SPEC-0028 §6 / D6)

- **Behavior:** web-запрос → id с префиксом `web:`, span-атрибут
  surface=web, метрика с label; agent-запрос — соответственно.
- **Boundaries:** публичные запросы (surface=public, свой префикс);
  входящий `X-Request-ID` от клиента; запрос, отклонённый auth-зависимостью
  ДО хендлера (401-ответ тоже должен быть размечен поверхностью —
  иначе отклонения не разделить!); CORS-OPTIONS (minust surface).
- **Conditions:** tracing установлен/не установлен (opentelemetry
  опционален — существующий паттерн guard'а); disable_rate_limit=true.
- **AC:** SPEC-0028 AC9.
- **Matrix:**
  - unit: формирование id по surface (позитив ×3, граница: клиентский
    id с префиксом уже); span-атрибуты через span-spy; label-чтение
    метрики.
  - integration: парные запросы web/agent → ассерт различий в заголовке,
    лог-записи (capture) и span; 401-отклонение размечено.
  - perf: не добавлять матчинг маршрутов второй раз в middleware
    (измерить overhead ≤ фонового) — «не превращаемся в безупречную
    улитку».

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | surface в контексте + формат id/логов (red-тесты парности) | 0169, 0170 |
| 2 | Span-атрибуты + метрики-labels | 1 |
| 3 | Rate-limit: policy по поверхности, удаление startswith-хардкода | 1 |
| 4 | Evidence: парные интеграционные тесты + замер overhead | 2-3 |
