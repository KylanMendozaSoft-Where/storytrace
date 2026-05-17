FROM node:18-alpine

WORKDIR /app

# Install deps first (cached layer — only re-runs when package.json changes)
COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

CMD ["npm", "start"]
