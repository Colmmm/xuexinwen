// config.js
const isProduction = process.env.PRODUCTION === 'true';

const config = {
  Url: isProduction ? 'http://xue-xinwen.com' : 'http://localhost:3000',
  apiUrl: isProduction ? 'http://xue-xinwen.com:5000' : 'http://localhost:5000',
};


export default config;
