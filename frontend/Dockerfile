FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG PUBLIC_API_KEY
ENV PUBLIC_API_KEY=${PUBLIC_API_KEY}

RUN npm run build
CMD ["sh", "-c", "rm -rf /frontend_build/* && cp -r /app/dist/. /frontend_build/"]
