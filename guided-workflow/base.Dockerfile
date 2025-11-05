# Builds a node:lts image with the dependencies installed

FROM node:lts AS builder
WORKDIR /app
COPY package.json ./
COPY vendor ./vendor
RUN npm install --fetch-timeout=600000