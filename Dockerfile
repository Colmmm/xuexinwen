# Stage 1: Build React app
FROM node:20.9.0-alpine AS build

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install
RUN npm install react-router-dom
RUN npm install axios

# Copy the entire app
COPY . .

# Build the React app
RUN npm run build

# Stage 2: Serve the React app using a lightweight server
FROM nginx:mainline-alpine3.18

# Copy the built React app from the previous stage
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Default command to start Nginx and serve the app
CMD ["nginx", "-g", "daemon off;"]