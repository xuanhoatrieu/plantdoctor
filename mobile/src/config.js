// API configuration
// TODO: Replace with production URL when deploying
export const API_BASE_URL = 'http://10.64.220.241:8001';

export const API = {
  predict: `${API_BASE_URL}/api/v1/predict`,
  health: `${API_BASE_URL}/api/v1/health`,
  models: `${API_BASE_URL}/api/v1/models`,
};
