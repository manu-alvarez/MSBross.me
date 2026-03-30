# Etapa de construcción (Builder)
FROM node:20-alpine as builder

WORKDIR /app

# Copiamos package.json primero para aprovechar caché Docker
COPY package*.json ./

# Instalamos módulos de Node limpios
RUN npm install

# Copiamos código y construimos la web SPA
COPY . .
RUN npm run build

# Etapa de producción (Nginx Alpine)
FROM nginx:alpine

# Copiamos configuración de enrutamiento estático (SPA fallback a index.html)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiamos la build estática compilada desde la etapa anterior
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
