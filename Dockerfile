FROM node:20.9.0-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the app
COPY . .

# Set environment variable for development
ENV VITE_PRODUCTION=false

# Expose port 5173 for Vite's development server
EXPOSE 5173

# Start Vite development server with host set to 0.0.0.0
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
