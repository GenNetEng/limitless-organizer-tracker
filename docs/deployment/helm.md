# Helm Reference

Chart location: `charts/limitless-organizer-tracker/`. One chart serves
both staging and production — environment differences live entirely in
values files, not separate charts.

## Chart structure

```
charts/limitless-organizer-tracker/
├── Chart.yaml                  # name, version, Bitnami Redis dependency
├── values.yaml                 # production defaults
├── values.staging.yaml         # staging overrides (see Staging)
├── fleet-staging.yaml          # staging GitOps descriptor (unused — see below)
├── charts/redis-20.13.4.tgz    # vendored Bitnami Redis subchart
└── templates/
    ├── deployment-backend.yaml
    ├── deployment-frontend.yaml
    ├── deployment-celery-worker.yaml
    ├── deployment-celery-beat.yaml
    ├── service-backend.yaml
    ├── service-frontend.yaml
    ├── ingress.yaml             # conditional on ingress.enabled
    ├── percona-pgcluster.yaml   # conditional on percona.enabled
    ├── configmap.yaml           # non-sensitive backend env (CORS, Limitless base URL/app ID)
    ├── secret.yaml              # DATABASE_URL, Celery URLs, Discord webhook, Limitless creds, API key
    └── _helpers.tpl
```

## Values reference

| Key | Production default | Purpose |
|-----|--------------------|---------|
| `namespace` | `limitless` | Target namespace |
| `backend.image.repository` / `.tag` | `ghcr.io/genneteng/limitless-organizer-tracker/backend` / `latest` | Backend image |
| `backend.replicas` | `1` | Backend pod count |
| `backend.port` | `8000` | Container + readiness/liveness probe port (`GET /healthz`) |
| `backend.env.CORS_ALLOWED_ORIGINS` | dashboard hostname | Goes into `configmap.yaml` |
| `backend.env.LIMITLESS_BASE_URL` | `https://play.limitlesstcg.com` | Goes into `configmap.yaml` |
| `backend.env.LIMITLESS_APPLICATION_ID` | `""` | Goes into `configmap.yaml`; set per environment |
| `frontend.image.*`, `frontend.replicas`, `frontend.port` | — | Same pattern as `backend.*` |
| `worker.image.*` | — | Image used by both `celery-worker` and `celery-beat` deployments |
| `celery.worker.replicas` / `celery.beat.replicas` | `1` / `1` | Pod counts |
| `ingress.enabled` | `true` | Whether to render `ingress.yaml` |
| `ingress.className` / `.host` / `.tls` | `nginx` / dashboard hostname / `false` | Ingress spec |
| `secrets.*` | all `""` | `databaseUrl`, `celeryBrokerUrl`, `celeryResultBackend`, `discordWebhookUrl`, `limitlessUsername`, `limitlessPassword`, `apiKeys` — **never commit real values**; pass via `--set` or a values file outside version control |
| `percona.enabled` | `true` | Whether to render the `PerconaPGCluster` CRD |
| `percona.clusterName` | `limitless-pg` | Percona cluster name |
| `percona.pgVersion` | `"16"` | Postgres major version |
| `percona.storageSize` | `5Gi` | PVC size for the PG instance |
| `redis.enabled` | `true` | Whether to install the Bitnami Redis subchart |
| `redis.architecture` | `standalone` | No replication |
| `redis.auth.enabled` | `false` | No Redis password (cluster-internal only) |
| `redis.master.persistence.size` | `1Gi` | Redis PVC size |

## Staging vs production

| | Production (`values.yaml`) | Staging (`values.staging.yaml`) |
|---|---|---|
| Namespace | `limitless-production`* | `limitless-staging` |
| Ingress | `enabled: true`, nginx | `enabled: false` (Cloudflare Tunnel points directly at services) |
| Percona storage | `5Gi`, backups on | `1Gi`, `disableBackups: true` |
| Redis persistence | `1Gi` | `512Mi` |
| `LIMITLESS_APPLICATION_ID` | real application | staging test application |
| Deployment mechanism | Rancher Fleet GitOps (`fleet.yaml`, watches `main`) | Manual `helm upgrade` / `kubectl set image` (see [Staging](staging.md)) |

\* `values.yaml`'s `namespace` key is `limitless`, but `fleet.yaml`'s
`defaultNamespace` (`limitless-production`) is what Fleet actually applies
to in practice — the chart's own `namespace` value is informational unless
a template reads it directly.

`fleet-staging.yaml` exists in the chart directory but is **not** used for
GitOps — it's deliberately named to avoid Fleet's recursive auto-discovery
of `fleet.yaml` files, since staging deploys are manual. Don't rename it to
`fleet.yaml`.

## The Percona PG cluster

`templates/percona-pgcluster.yaml` renders a `PerconaPGCluster` CRD
(`pgv2.percona.com/v2`, `crVersion: "3.0.0"`) when `percona.enabled` is
true:

- Image: `percona/percona-distribution-postgresql:16-ubi8`
- One instance, one replica, a `ReadWriteOnce` PVC sized by
  `percona.storageSize`
- `pgbackrest` backups (image `percona/percona-pgbackrest:2.58.0`) to a
  separate PVC, sized by `percona.backupStorageSize` (falls back to
  `percona.storageSize`)
- Creates a `limitless` superuser on the `limitless_tracker` database

Percona v3 requires the `spec.backups` block even when backups are
effectively disabled (staging sets `disableBackups: true` at the values
level, not by omitting `backups` from the template).

## Redis subchart

The Bitnami Redis chart (vendored at
`charts/redis-20.13.4.tgz`, `condition: redis.enabled`) runs standalone, no
auth, and serves as both the Celery broker and result backend — the same
Redis instance also backs the dynamic beat schedule via `celery-redbeat`
(see [Configuration](../configuration.md#beat-schedule-reload)). Bitnami
removed versioned image tags for the Redis image itself, so
`redis.image.tag` is pinned to `latest`.

## Common commands

```bash
# Install/upgrade staging
helm upgrade --install limitless-staging charts/limitless-organizer-tracker \
  -f charts/limitless-organizer-tracker/values.staging.yaml \
  --namespace limitless-staging --create-namespace \
  --set secrets.databaseUrl="..." --set secrets.discordWebhookUrl="..." \
  --kube-context mcgee-local

# Roll back a bad release
helm rollback limitless-staging --kube-context mcgee-local

# Render templates locally without applying (debugging)
helm template charts/limitless-organizer-tracker -f charts/limitless-organizer-tracker/values.staging.yaml
```

Production is **not** managed with manual `helm` commands — Fleet applies
`values.yaml` automatically on every push to `main`. See
[Production](production.md).
