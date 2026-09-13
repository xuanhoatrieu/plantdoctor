export const PROD_API_URL = 'https://benhcay.tuaf.edu.vn';
export const DEV_API_URL = 'http://10.64.220.241:8001';

// Default to online HTTPS API (https://benhcay.tuaf.edu.vn)
// so the mobile app always works seamlessly on real devices across 4G/5G and Wi-Fi.
export const API_BASE_URL = PROD_API_URL;

export const API = {
  predict: `${API_BASE_URL}/api/v1/predict`,
  health: `${API_BASE_URL}/api/v1/health`,
  models: `${API_BASE_URL}/api/v1/models`,
};
