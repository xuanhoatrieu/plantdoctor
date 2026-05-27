import { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, TextInput, Alert, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import axios from 'axios';
import { getToken } from '../src/api';

const API_BASE = 'http://10.64.220.241:8001';

export default function AdminScreen() {
  const [tab, setTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  const headers = async () => ({ Authorization: `Bearer ${await getToken()}` });

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const h = await headers();
      const res = await axios.get(`${API_BASE}/api/v1/admin/users`, { headers: h });
      setUsers(res.data);
    } catch (e) {
      Alert.alert('Lỗi', 'Không có quyền admin');
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchUsers(); }, []);

  const setRole = async (userId, role) => {
    const h = await headers();
    await axios.put(`${API_BASE}/api/v1/admin/users/${userId}/role`, { role }, { headers: h });
    fetchUsers();
  };

  const deleteUser = async (userId) => {
    Alert.alert('Xác nhận', 'Xóa user này?', [
      { text: 'Hủy', style: 'cancel' },
      { text: 'Xóa', style: 'destructive', onPress: async () => {
        const h = await headers();
        await axios.delete(`${API_BASE}/api/v1/admin/users/${userId}`, { headers: h });
        fetchUsers();
      }},
    ]);
  };

  return (
    <SafeAreaView style={s.container}>
      <ScrollView contentContainerStyle={s.scroll}>
        <Text style={s.title}>⚙️ Quản trị</Text>

        <Text style={s.sectionTitle}>👥 Người dùng ({users.length})</Text>
        {users.map(u => (
          <View key={u.id} style={s.userCard}>
            <View style={s.userInfo}>
              <Text style={s.userName}>{u.name || u.phone}</Text>
              <Text style={s.userPhone}>{u.phone} • {u.role}</Text>
            </View>
            <View style={s.userActions}>
              <TouchableOpacity onPress={() => setRole(u.id, u.role === 'admin' ? 'user' : 'admin')} style={s.roleBtn}>
                <Text style={s.roleBtnText}>{u.role === 'admin' ? '→User' : '→Admin'}</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => deleteUser(u.id)}>
                <Text style={s.deleteBtn}>🗑️</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  scroll: { padding: 20, paddingBottom: 40 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#111', marginBottom: 16 },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: '#333', marginBottom: 10 },
  userCard: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#f9fafb', borderRadius: 12, padding: 12, marginBottom: 8, borderWidth: 1, borderColor: '#e5e7eb' },
  userInfo: { flex: 1 },
  userName: { fontWeight: '600', color: '#111' },
  userPhone: { fontSize: 12, color: '#666', marginTop: 2 },
  userActions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  roleBtn: { backgroundColor: '#e0e7ff', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  roleBtnText: { fontSize: 12, color: '#4338ca', fontWeight: '600' },
  deleteBtn: { fontSize: 18 },
});
