// config.js
const isProduction = import.meta.env.VITE_PRODUCTION === 'true';

const config = {
  apiUrl: isProduction ? '/api' : 'http://localhost:5000/api',
};

export default config;
