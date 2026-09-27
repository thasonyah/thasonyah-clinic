import axios from 'axios';

const getApiBaseUrl = () => {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL;
  if (configuredBaseUrl) return configuredBaseUrl;

  if (typeof window !== 'undefined' && window.location.hostname === 'clinic-web-3z3c.onrender.com') {
    return 'https://clinic-api-rl26.onrender.com/api/v1';
  }

  return '/api/v1';
};

export const api = axios.create({ baseURL: getApiBaseUrl(), timeout: 15000 });
