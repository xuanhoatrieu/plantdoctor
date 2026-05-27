import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_BASE = 'http://10.64.220.241:8001';

export async function login(phone, password) {
  const res = await axios.post(`${API_BASE}/api/v1/auth/login`, { phone, password });
  await AsyncStorage.setItem('token', res.data.token);
  await AsyncStorage.setItem('user', JSON.stringify(res.data.user));
  return res.data;
}

export async function register(phone, password, name) {
  const res = await axios.post(`${API_BASE}/api/v1/auth/register`, { phone, password, name });
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
  form.append('file', { uri: imageUri, name: 'photo.jpg', type: 'image/jpeg' });
  form.append('model_id', 'gpt55_vision');
  form.append('lang', lang);
  const headers = { 'Content-Type': 'multipart/form-data' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await axios.post(`${API_BASE}/api/v1/predict`, form, { headers, timeout: 30000 });
  return res.data;
}
