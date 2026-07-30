# Multi-stage build for production
# Stage 1: Build (use slim for glibc — native bindings need it)
FROM node:20.18.0-slim AS build

WORKDIR /app

COPY package*.json ./
RUN npm install && npm install @rolldown/binding-linux-x64-gnu

COPY . .
RUN npm run build

# Stage 2: Serve static files (alpine is fine for static serving)
FROM node:20.18.0-alpine

RUN addgroup -S upcp && adduser -S upcp -G upcp

WORKDIR /app

RUN npm install -g serve@14

COPY --from=build --chown=upcp:upcp /app/dist ./dist

USER upcp

EXPOSE 35173

CMD ["serve", "-s", "dist", "-l", "35173"]
