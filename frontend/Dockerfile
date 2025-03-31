FROM node:20-alpine AS development-dependencies-env
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

FROM node:20-alpine AS build-env
WORKDIR /app
COPY . .
COPY --from=development-dependencies-env /app/node_modules /app/node_modules

# Create the app directory structure directly in the Dockerfile instead of using a script
RUN mkdir -p app && \
    cp -r src/app/* app/ || true

RUN npm run build

FROM node:20-alpine AS production
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=build-env /app/build /app/build
EXPOSE 3000
CMD ["npm", "run", "start"]