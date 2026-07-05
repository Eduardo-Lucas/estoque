#!/usr/bin/env bash
# Build command do Static Site do frontend no Render (ver render.yaml).
# BACKEND_HOST vem de `fromService` apontando pro Web Service do backend —
# escreve o environment.prod.ts antes de buildar, já que o Angular resolve
# a apiUrl em tempo de build, não em runtime.
set -o errexit

cat > src/environments/environment.prod.ts <<EOF
export const environment = {
  production: true,
  apiUrl: 'https://${BACKEND_HOST}/api',
};
EOF

npm ci
npm run build
