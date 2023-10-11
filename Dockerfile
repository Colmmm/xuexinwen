# Use an official Node.js image as the base image
FROM node:14

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the entire app to the working directory
COPY . .

# Build the React app
RUN npm run build

# Expose a port (e.g., 3000) if needed
EXPOSE 3000

# Define the command to start the app
CMD ["npm", "start"]
