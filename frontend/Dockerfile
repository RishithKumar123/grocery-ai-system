FROM node:18-alpine

WORKDIR /app

# Copy dependency configs
COPY package.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start app in dev mode for local environment setup
CMD ["npm", "run", "dev"]
