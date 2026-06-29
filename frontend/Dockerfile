FROM nginx:1.27-alpine

LABEL org.opencontainers.image.title="BioAcervo Frontend"
LABEL org.opencontainers.image.description="Static frontend image for BioAcervo served by Nginx"

COPY index.html /usr/share/nginx/html/index.html
COPY login.html /usr/share/nginx/html/login.html
COPY styles.css /usr/share/nginx/html/styles.css
COPY app.js /usr/share/nginx/html/app.js

EXPOSE 80
