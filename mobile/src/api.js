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

export async function predict(imageInput, lang = 'vi', plantHint = null) {
  const token = await getToken();
  const form = new FormData();
  
  const uris = Array.isArray(imageInput) ? imageInput.filter(Boolean) : [imageInput];
  if (uris.length === 0) {
    throw new Error('Vui lòng chọn ít nhất một hình ảnh');
  }

  uris.forEach((uri, idx) => {
    const filename = uri.split('/').pop() || `photo_${idx}.jpg`;
    const match = /\.(\w+)$/.exec(filename);
    const type = match ? `image/${match[1].toLowerCase() === 'jpg' ? 'jpeg' : match[1].toLowerCase()}` : 'image/jpeg';

    if (uris.length === 1) {
      form.append('file', {
        uri: uri,
        name: filename,
        type: type,
      });
    } else {
      form.append('files', {
        uri: uri,
        name: filename,
        type: type,
      });
    }
  });

  form.append('model_id', 'gpt55_vision');
  form.append('lang', lang);
  if (plantHint && plantHint.trim()) {
    form.append('plant_hint', plantHint.trim());
  }

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

export async function clarifyPrediction(sessionToken, selectedPlant, lang = 'vi') {
  const token = await getToken();
  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}/api/v1/predict/clarify`, {
    method: 'POST',
    body: JSON.stringify({
      session_token: sessionToken,
      selected_plant: selectedPlant,
      lang,
    }),
    headers,
  });

  const responseText = await res.text();
  let data;
  try {
    data = JSON.parse(responseText);
  } catch {
    throw new Error(`Phản hồi không hợp lệ (${res.status})`);
  }

  if (!res.ok) {
    const detail = data?.detail || 'Lỗi khi xác nhận làm rõ loại cây';
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }

  return data;
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

export async function getProfile() {
  const token = await getToken();
  if (!token) return null;
  const res = await axios.get(`${API_BASE_URL}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  await AsyncStorage.setItem('user', JSON.stringify(res.data));
  return res.data;
}

export async function updateProfile(data) {
  const token = await getToken();
  const res = await axios.put(`${API_BASE_URL}/api/v1/auth/profile`, data, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.data?.user) {
    await AsyncStorage.setItem('user', JSON.stringify(res.data.user));
  }
  return res.data;
}

export async function changePassword(currentPassword, newPassword) {
  const token = await getToken();
  const res = await axios.post(
    `${API_BASE_URL}/api/v1/auth/change-password`,
    { current_password: currentPassword, new_password: newPassword },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.data;
}

export async function deleteAccount(password = null) {
  const token = await getToken();
  const res = await axios.delete(`${API_BASE_URL}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { password },
  });
  await logout();
  return res.data;
}

export async function forgotPassword(phone) {
  const res = await axios.post(`${API_BASE_URL}/api/v1/auth/forgot-password`, { phone });
  return res.data;
}

// Admin Helpers
export async function adminGetUsers(params = {}) {
  const token = await getToken();
  const res = await axios.get(`${API_BASE_URL}/api/v1/admin/users`, {
    headers: { Authorization: `Bearer ${token}` },
    params,
  });
  return res.data;
}

export async function adminCreateUser(userData) {
  const token = await getToken();
  const res = await axios.post(`${API_BASE_URL}/api/v1/admin/users`, userData, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

export async function adminUpdateUser(userId, data) {
  const token = await getToken();
  const res = await axios.put(`${API_BASE_URL}/api/v1/admin/users/${userId}`, data, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

export async function adminResetPassword(userId, newPassword) {
  const token = await getToken();
  const res = await axios.post(
    `${API_BASE_URL}/api/v1/admin/users/${userId}/reset-password`,
    { new_password: newPassword },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.data;
}

export async function adminToggleActive(userId) {
  const token = await getToken();
  const res = await axios.put(
    `${API_BASE_URL}/api/v1/admin/users/${userId}/toggle-active`,
    {},
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.data;
}

export async function adminDeleteUser(userId) {
  const token = await getToken();
  const res = await axios.delete(`${API_BASE_URL}/api/v1/admin/users/${userId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}
