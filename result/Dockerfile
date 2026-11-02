FROM node:24.22.2-trixie-slim AS dependencies
WORKDIR /usr/local/app
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force

FROM node:24.22.2-trixie-slim
# Package managers are build tools; the runtime only needs Node and locked app dependencies.
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack /opt/yarn* && \
    rm -f /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack /usr/local/bin/yarn /usr/local/bin/yarnpkg
WORKDIR /usr/local/app
COPY --from=dependencies /usr/local/app/node_modules ./node_modules
COPY . .
ENV PORT=80 NODE_ENV=production
EXPOSE 80
CMD ["node", "server.js"]
