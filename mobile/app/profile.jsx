import { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { login, register, logout, getUser } from '../src/api';

export default function ProfileScreen() {
  const [user, setUser] = useState(null);
  const [mode, setMode] = useState('login'); // login | register
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { getUser().then(setUser); }, []);

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      let data;
      if (mode === 'login') {
        data = await login(phone, password);
      } else {
        data = await register(phone, password, name);
      }
      setUser(data.user);
      setPhone(''); setPassword(''); setName('');
    } catch (e) {
      setError(e.response?.data?.detail || 'Có lỗi xảy ra');
    } finally { setLoading(false); }
  };

  const handleLogout = () => {
    Alert.alert('Đăng xuất', 'Bạn muốn đăng xuất?', [
      { text: 'Hủy', style: 'cancel' },
      { text: 'Đăng xuất', onPress: async () => { await logout(); setUser(null); } },
    ]);
  };

  if (user) {
    const router = useRouter();
    return (
      <SafeAreaView style={s.container}>
        <ScrollView contentContainerStyle={s.scroll}>
          <Text style={s.title}>👤 Tài khoản</Text>
          <View style={s.profileCard}>
            <Text style={s.profileName}>{user.name || 'Người dùng'}</Text>
            <Text style={s.profilePhone}>{user.phone}</Text>
            <View style={s.roleBadge}>
              <Text style={s.roleText}>{user.role === 'admin' ? '⚙️ Quản trị viên' : '👤 Người dùng'}</Text>
            </View>
          </View>

          {user.role === 'admin' && (
            <TouchableOpacity style={s.adminBtn} onPress={() => router.push('/admin')}>
              <Text style={s.adminBtnText}>⚙️ Vào trang quản trị</Text>
            </TouchableOpacity>
          )}

          <View style={s.infoBox}>
            <Text style={s.infoTitle}>ℹ️ Thông tin ứng dụng</Text>
            <Text style={s.infoText}>PlantDoctor v1.0.0</Text>
            <Text style={s.infoText}>Powered by Triệu Xuân Hòa</Text>
            <Text style={s.infoText}>Trường Đại học Nông Lâm Thái Nguyên</Text>
          </View>

          <TouchableOpacity style={s.logoutBtn} onPress={handleLogout}>
            <Text style={s.logoutText}>Đăng xuất</Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={s.container}>
      <ScrollView contentContainerStyle={s.scroll}>
        <Text style={s.title}>👤 {mode === 'login' ? 'Đăng nhập' : 'Đăng ký'}</Text>
        <Text style={s.desc}>Đăng nhập để lưu lịch sử và sử dụng đầy đủ tính năng</Text>

        {mode === 'register' && (
          <TextInput style={s.input} value={name} onChangeText={setName} placeholder="Họ tên" />
        )}
        <TextInput style={s.input} value={phone} onChangeText={setPhone} placeholder="Số điện thoại" keyboardType="phone-pad" />
        <TextInput style={s.input} value={password} onChangeText={setPassword} placeholder="Mật khẩu (tối thiểu 6 ký tự)" secureTextEntry />

        {error ? <Text style={s.error}>{error}</Text> : null}

        <TouchableOpacity style={[s.submitBtn, (phone.length < 9 || password.length < 6) && s.btnDisabled]}
          onPress={handleSubmit} disabled={loading || phone.length < 9 || password.length < 6}>
          <Text style={s.submitText}>{loading ? '...' : mode === 'login' ? 'Đăng nhập' : 'Đăng ký'}</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => setMode(mode === 'login' ? 'register' : 'login')} style={s.switchBtn}>
          <Text style={s.switchText}>
            {mode === 'login' ? 'Chưa có tài khoản? Đăng ký' : 'Đã có tài khoản? Đăng nhập'}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  scroll: { padding: 20, paddingBottom: 40 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#111', marginBottom: 8 },
  desc: { fontSize: 14, color: '#666', marginBottom: 20 },
  input: { borderWidth: 1, borderColor: '#d1d5db', borderRadius: 14, padding: 14, fontSize: 15, marginBottom: 12, backgroundColor: '#f9fafb' },
  error: { color: '#ef4444', fontSize: 13, marginBottom: 10, textAlign: 'center' },
  submitBtn: { backgroundColor: '#16a34a', padding: 16, borderRadius: 14, alignItems: 'center', marginTop: 4 },
  submitText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  btnDisabled: { opacity: 0.4 },
  switchBtn: { marginTop: 16, alignItems: 'center' },
  switchText: { color: '#16a34a', fontSize: 14, fontWeight: '500' },
  profileCard: { backgroundColor: '#f0fdf4', borderRadius: 16, padding: 20, alignItems: 'center', marginBottom: 20, borderWidth: 1, borderColor: '#86efac' },
  profileName: { fontSize: 20, fontWeight: 'bold', color: '#166534' },
  profilePhone: { fontSize: 14, color: '#666', marginTop: 4 },
  roleBadge: { marginTop: 10, backgroundColor: '#dcfce7', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 20 },
  roleText: { color: '#166534', fontSize: 13, fontWeight: '600' },
  infoBox: { backgroundColor: '#f9fafb', borderRadius: 14, padding: 16, marginBottom: 20 },
  infoTitle: { fontWeight: '700', color: '#111', marginBottom: 8 },
  infoText: { fontSize: 13, color: '#666', marginBottom: 3 },
  logoutBtn: { borderWidth: 2, borderColor: '#ef4444', borderRadius: 14, padding: 14, alignItems: 'center' },
  logoutText: { color: '#ef4444', fontSize: 15, fontWeight: '600' },
  adminBtn: { backgroundColor: '#7c3aed', borderRadius: 14, padding: 16, alignItems: 'center', marginBottom: 16 },
  adminBtnText: { color: '#fff', fontSize: 15, fontWeight: '700' },
});
