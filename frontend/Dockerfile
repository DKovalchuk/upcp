# Multi-stage build for production
# Stage 1: Build
FROM node:20.18.0-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve static files
FROM node:20.18.0-alpine

RUN addgroup -S upcp && adduser -S upcp -G upcp

WORKDIR /app

RUN npm install -g serve@14

COPY --from=build --chown=upcp:upcp /app/dist ./dist

USER upcp

EXPOSE 35173

CMD ["serve", "-s", "dist", "-l", "35173"]
