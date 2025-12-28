# Build stage
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install prop-types --legacy-peer-deps
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

# Production stage
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
