#!/usr/bin/env bash
# Build command do Static Site do frontend no Render (ver render.yaml).
# BACKEND_HOST vem de `fromService` (property: host) apontando pro Web Service
# do backend. Essa propriedade devolve o hostname da rede *privada* do Render
# (ex: "estoque-backend-dum3", sem `.onrender.com`) — pensada pra comunicação
# interna, não pra uso público no navegador. Completa o domínio quando faltar,
# já que o Angular resolve a apiUrl em tempo de build, não em runtime.
set -o errexit

case "$BACKEND_HOST" in
  *.*) backend_host_publico="$BACKEND_HOST" ;;
  *) backend_host_publico="${BACKEND_HOST}.onrender.com" ;;
esac

cat > src/environments/environment.prod.ts <<EOF
export const environment = {
  production: true,
  apiUrl: 'https://${backend_host_publico}/api',
};
EOF

npm ci
npm run build
