import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { API_BASE_URL } from './config';

export async function login(phone, password) {
  const res = await axios.post(`${API_BASE_URL}/api/v1/auth/login`, { phone, password });
  await AsyncStorage.setItem('token', res.data.token);
  await AsyncStorage.setItem('user', JSON.stringify(res.data.user));
  return res.data;
}

export async function register(phone, password, name) {
  const res = await axios.post(`${API_BASE_URL}/api/v1/auth/register`, { phone, password, name });
  await AsyncStorage.setItem('token', res.data.token);
  await AsyncStorage.setItem('user', JSON.stringify(res.data.user));
  return res.data;
}

export async function logout() {
  await AsyncStorage.removeItem('token');
  await AsyncStorage.removeItem('user');
}

export async function getUser() {
  const data = await AsyncStorage.getItem('user');
  return data ? JSON.parse(data) : null;
}

export async function getToken() {
  return await AsyncStorage.getItem('token');
}

export async function predict(imageUri, lang = 'vi') {
  const token = await getToken();
  const form = new FormData();
  
  const filename = imageUri.split('/').pop() || 'photo.jpg';
  const match = /\.(\w+)$/.exec(filename);
  const type = match ? `image/${match[1].toLowerCase() === 'jpg' ? 'jpeg' : match[1].toLowerCase()}` : 'image/jpeg';

  form.append('file', {
    uri: imageUri,
    name: filename,
    type: type,
  });
  form.append('model_id', 'gpt55_vision');
  form.append('lang', lang);

  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  // NOTE: Do not set Content-Type header manually here so React Native Axios generates boundary automatically
  const res = await axios.post(`${API_BASE_URL}/api/v1/predict`, form, {
    headers,
    timeout: 30000,
  });
  return res.data;
}

export async function appleLogin(identityToken, givenName) {
  const res = await axios.post(`${API_BASE_URL}/api/v1/auth/apple`, {
    identity_token: identityToken,
    name: givenName || '',
  });
  await AsyncStorage.setItem('token', res.data.token);
  await AsyncStorage.setItem('user', JSON.stringify(res.data.user));
  return res.data;
}
