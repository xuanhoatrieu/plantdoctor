import Constants from 'expo-constants';

// Get host IP dynamically from Expo in development, or fallback to local LAN
const getDevServerIp = () => {
  const hostUri = Constants.expoConfig?.hostUri || Constants.manifest2?.extra?.expoGo?.debuggerHost;
  if (hostUri) {
    return hostUri.split(':')[0];
  }
  return '10.64.220.241'; // Host machine LAN IP
};

export const DEV_API_URL = `http://${getDevServerIp()}:8001`;
export const PROD_API_URL = 'https://benhcay.tuaf.edu.vn';

// When running in development mode (__DEV__ = true in Expo / React Native)
// default to the development server URL so local testing works seamlessly.
export const API_BASE_URL = __DEV__ ? DEV_API_URL : PROD_API_URL;

export const API = {
  predict: `${API_BASE_URL}/api/v1/predict`,
  health: `${API_BASE_URL}/api/v1/health`,
  models: `${API_BASE_URL}/api/v1/models`,
};
