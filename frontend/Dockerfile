FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM alpine

COPY --from=build /app/dist /usr/share/nginx/html
