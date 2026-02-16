# ---- Stage 1: Build ----
FROM node:22-bookworm AS builder

# Bun is required for build scripts
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:${PATH}"

RUN corepack enable

WORKDIR /app

ARG OPENCLAW_DOCKER_APT_PACKAGES=""
RUN if [ -n "$OPENCLAW_DOCKER_APT_PACKAGES" ]; then \
      apt-get update && \
      DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends $OPENCLAW_DOCKER_APT_PACKAGES && \
      apt-get clean && \
      rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*; \
    fi

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
COPY ui/package.json ./ui/package.json
COPY patches ./patches
COPY scripts ./scripts

RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build
ENV OPENCLAW_PREFER_PNPM=1
RUN pnpm ui:build

# Prune to production dependencies only
ENV CI=true
RUN pnpm prune --prod --no-optional && \
    rm -rf node_modules/.cache \
    node_modules/@typescript* \
    node_modules/typescript \
    node_modules/vitest \
    node_modules/@vitest \
    node_modules/rolldown \
    node_modules/tsdown \
    node_modules/oxlint* \
    node_modules/oxfmt* \
    node_modules/tsx \
    node_modules/esbuild \
    node_modules/@esbuild \
    node_modules/.pnpm/typescript@* \
    node_modules/.pnpm/vitest@* \
    node_modules/.pnpm/rolldown@* \
    node_modules/.pnpm/@esbuild* \
    node_modules/.pnpm/esbuild@* \
    node_modules/.pnpm/@vitest* \
    node_modules/.pnpm/oxlint* \
    node_modules/.pnpm/@typescript*

# ---- Stage 2: Runtime (slim) ----
FROM node:22-bookworm-slim

RUN corepack enable

WORKDIR /app

# Copy only what's needed at runtime
COPY --from=builder /app/package.json /app/pnpm-workspace.yaml /app/pnpm-lock.yaml ./
COPY --from=builder /app/.npmrc* ./
COPY --from=builder /app/openclaw.mjs ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/extensions ./extensions
COPY --from=builder /app/skills ./skills
COPY --from=builder /app/docs ./docs
COPY --from=builder /app/ui/package.json ./ui/package.json

ENV NODE_ENV=production
ENV OPENCLAW_PREFER_PNPM=1

# Run as non-root (node user is uid 1000 in the base image)
RUN chown -R node:node /app
USER node

CMD ["node", "openclaw.mjs", "gateway", "--allow-unconfigured"]
