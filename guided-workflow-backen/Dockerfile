FROM 837578041534.dkr.ecr.us-east-1.amazonaws.com/bases/node AS builder
# Set the working directory to /app inside the container
WORKDIR /app
ENV NODE_ENV=production
ENV GENERATE_SOURCEMAP=false
ENV NODE_OPTIONS=--max_old_space_size=4096
#==========Install dependencies (if they are different from builder)==========
COPY ["package.json", "./"]
RUN npm install --fetch-timeout=600000
#========Build App Code==============================
COPY . .
RUN npm run build

FROM 837578041534.dkr.ecr.us-east-1.amazonaws.com/bases/nginx AS server
EXPOSE 80
RUN rm /etc/nginx/conf.d/default.conf && rm /etc/nginx/nginx.conf
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/api.conf /etc/nginx/conf.d
COPY --from=builder /app/dist /usr/share/nginx/html
CMD ["nginx", "-g", "daemon off;"]