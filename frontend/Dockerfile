# syntax=docker/dockerfile:1

## Stage: builder — produces production SPA bundle
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --include=dev
COPY . .
ARG VITE_API_URL=/api/v1
ARG VITE_CLOUDPAYMENTS_PUBLIC_ID=
ENV VITE_API_URL=$VITE_API_URL \
    VITE_CLOUDPAYMENTS_PUBLIC_ID=$VITE_CLOUDPAYMENTS_PUBLIC_ID
RUN npm run build

## Stage: runtime — nginx serves the built SPA. Prod compose targets this stage.
FROM nginx:1.27-alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
RUN echo 'ok' > /usr/share/nginx/html/_healthz \
    && printf 'server {\n  listen 80;\n  root /usr/share/nginx/html;\n  location /_healthz { access_log off; return 200 "ok"; add_header Content-Type text/plain; }\n  location / { try_files $uri $uri/ /index.html; }\n}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

## Stage: dev — default target for dev docker-compose (Vite HMR on :5173).
## Kept last so `docker build .` without --target still produces the dev image
## for the existing dev compose, while prod compose uses --target=runtime.
FROM node:22-alpine AS dev
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
