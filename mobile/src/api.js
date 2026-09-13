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

  const headers = {
    Accept: 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  // Use native fetch to ensure React Native stream multipart boundary is handled correctly without Axios interceptor issues
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120000);

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/predict`, {
      method: 'POST',
      body: form,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const responseText = await res.text();
    let data;
    try {
      data = JSON.parse(responseText);
    } catch {
      throw new Error(`Phản hồi không hợp lệ từ máy chủ (${res.status}): ${responseText.slice(0, 100)}`);
    }

    if (!res.ok) {
      const detail = data?.detail || `Lỗi máy chủ (${res.status})`;
      const err = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
      err.status = res.status;
      err.response = { status: res.status, data };
      throw err;
    }

    return data;
  } catch (e) {
    clearTimeout(timeoutId);
    if (e.name === 'AbortError') {
      const err = new Error('Quá thời gian chờ phản hồi AI (hơn 120 giây). Vui lòng thử lại với ảnh rõ nét hơn.');
      err.code = 'ECONNABORTED';
      throw err;
    }
    throw e;
  }
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
