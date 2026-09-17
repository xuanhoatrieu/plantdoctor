import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  StyleSheet,
  Modal,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  adminGetUsers,
  adminCreateUser,
  adminUpdateUser,
  adminResetPassword,
  adminToggleActive,
  adminDeleteUser,
} from '../src/api';

export default function AdminScreen() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [filterRole, setFilterRole] = useState('all'); // all | admin | user

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [newUser, setNewUser] = useState({ phone: '', password: '', name: '', email: '', role: 'user' });
  const [creating, setCreating] = useState(false);

  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', phone: '', email: '', role: 'user', is_active: true });
  const [updating, setUpdating] = useState(false);

  const [showResetModal, setShowResetModal] = useState(false);
  const [resetPwdUser, setResetPwdUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [resetting, setResetting] = useState(false);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (search.trim()) params.q = search.trim();
      if (filterRole !== 'all') params.role = filterRole;
      const data = await adminGetUsers(params);
      setUsers(data);
    } catch (e) {
      Alert.alert('Lỗi', e.response?.data?.detail || 'Không thể tải danh sách người dùng hoặc bạn không có quyền Admin');
    } finally {
      setLoading(false);
    }
  }, [search, filterRole]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCreateUser = async () => {
    if (newUser.phone.length < 9 || newUser.password.length < 6) {
      Alert.alert('Lỗi', 'Số điện thoại (tối thiểu 9 số) và mật khẩu (tối thiểu 6 ký tự) không hợp lệ');
      return;
    }
    setCreating(true);
    try {
      await adminCreateUser(newUser);
      setShowAddModal(false);
      setNewUser({ phone: '', password: '', name: '', email: '', role: 'user' });
      Alert.alert('Thành công', 'Đã tạo tài khoản mới thành công');
      fetchUsers();
    } catch (e) {
      Alert.alert('Lỗi', e.response?.data?.detail || 'Không thể tạo người dùng');
    } finally {
      setCreating(false);
    }
  };

  const openEdit = (user) => {
    setSelectedUser(user);
    setEditForm({
      name: user.name || '',
      phone: user.phone || '',
      email: user.email || '',
      role: user.role || 'user',
      is_active: user.is_active !== false,
    });
    setShowEditModal(true);
  };

  const handleSaveEdit = async () => {
    if (!selectedUser) return;
    setUpdating(true);
    try {
      await adminUpdateUser(selectedUser.id, editForm);
      setShowEditModal(false);
      Alert.alert('Thành công', 'Đã cập nhật thông tin người dùng');
      fetchUsers();
    } catch (e) {
      Alert.alert('Lỗi', e.response?.data?.detail || 'Không thể cập nhật người dùng');
    } finally {
      setUpdating(false);
    }
  };

  const handleToggleActive = async (user) => {
    const action = user.is_active ? 'Khóa tài khoản' : 'Mở khóa tài khoản';
    Alert.alert(action, `Bạn muốn ${action.toLowerCase()} ${user.phone}?`, [
      { text: 'Hủy', style: 'cancel' },
      {
        text: 'Đồng ý',
        onPress: async () => {
          try {
            await adminToggleActive(user.id);
            fetchUsers();
          } catch (e) {
            Alert.alert('Lỗi', e.response?.data?.detail || 'Không thể thay đổi trạng thái');
          }
        },
      },
    ]);
  };

  const openResetPwd = (user) => {
    setResetPwdUser(user);
    setNewPassword('');
    setShowResetModal(true);
  };

  const handleResetPassword = async () => {
    if (!resetPwdUser || newPassword.length < 6) {
      Alert.alert('Lỗi', 'Mật khẩu mới phải có tối thiểu 6 ký tự');
      return;
    }
    setResetting(true);
    try {
      await adminResetPassword(resetPwdUser.id, newPassword);
      setShowResetModal(false);
      setNewPassword('');
      Alert.alert('Thành công', `Đã cấp mật khẩu mới cho tài khoản ${resetPwdUser.phone}`);
    } catch (e) {
      Alert.alert('Lỗi', e.response?.data?.detail || 'Không thể đặt lại mật khẩu');
    } finally {
      setResetting(false);
    }
  };

  const handleDeleteUser = (user) => {
    Alert.alert('Xóa người dùng', `Bạn có chắc chắn muốn xóa vĩnh viễn tài khoản ${user.phone}?`, [
      { text: 'Hủy', style: 'cancel' },
      {
        text: 'Xóa vĩnh viễn',
        style: 'destructive',
        onPress: async () => {
          try {
            await adminDeleteUser(user.id);
            fetchUsers();
          } catch (e) {
            Alert.alert('Lỗi', e.response?.data?.detail || 'Không thể xóa tài khoản');
          }
        },
      },
    ]);
  };

  return (
    <SafeAreaView style={s.container}>
      <ScrollView contentContainerStyle={s.scroll}>
        <View style={s.headerRow}>
          <Text style={s.title}>⚙️ Quản lý Người dùng</Text>
          <TouchableOpacity style={s.addBtn} onPress={() => setShowAddModal(true)}>
            <Text style={s.addBtnText}>+ Thêm user</Text>
          </TouchableOpacity>
        </View>

        {/* Search Bar */}
        <View style={s.searchWrap}>
          <TextInput
            style={s.searchInput}
            placeholder="🔍 Tìm kiếm theo SĐT, họ tên..."
            value={search}
            onChangeText={setSearch}
          />
          {search ? (
            <TouchableOpacity onPress={() => setSearch('')} style={s.clearBtn}>
              <Text style={s.clearText}>✕</Text>
            </TouchableOpacity>
          ) : null}
        </View>

        {/* Filter Chips */}
        <View style={s.filterRow}>
          {[
            { id: 'all', label: 'Tất cả' },
            { id: 'admin', label: 'Quản trị viên' },
            { id: 'user', label: 'Người dùng' },
          ].map((f) => (
            <TouchableOpacity
              key={f.id}
              style={[s.chip, filterRole === f.id && s.chipActive]}
              onPress={() => setFilterRole(f.id)}
            >
              <Text style={[s.chipText, filterRole === f.id && s.chipTextActive]}>
                {f.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={s.countText}>
          Hiển thị {users.length} tài khoản {loading ? '(Đang tải...)' : ''}
        </Text>

        {/* Users List */}
        {users.map((u) => {
          const isApple = u.phone?.startsWith('apple_');
          return (
            <View key={u.id} style={[s.userCard, !u.is_active && s.cardDisabled]}>
              <View style={s.userInfo}>
                <View style={s.nameRow}>
                  <Text style={s.userName}>{u.name || (isApple ? 'Người dùng Apple' : u.phone)}</Text>
                  {!u.is_active ? (
                    <View style={s.lockedBadge}>
                      <Text style={s.lockedText}>Đã khóa</Text>
                    </View>
                  ) : null}
                </View>
                <Text style={s.userSub}>
                  {u.phone} • Vai trò: <Text style={{ fontWeight: '700' }}>{u.role}</Text>
                </Text>
                {u.email ? <Text style={s.userEmail}>✉️ {u.email}</Text> : null}
              </View>

              <View style={s.actionRow}>
                <TouchableOpacity style={s.actionBtn} onPress={() => openEdit(u)}>
                  <Text style={s.actionBtnText}>✏️ Sửa</Text>
                </TouchableOpacity>

                {!isApple && (
                  <TouchableOpacity style={s.actionBtn} onPress={() => openResetPwd(u)}>
                    <Text style={s.actionBtnText}>🔑 Đổi pass</Text>
                  </TouchableOpacity>
                )}

                <TouchableOpacity
                  style={[s.actionBtn, u.is_active ? s.btnLock : s.btnUnlock]}
                  onPress={() => handleToggleActive(u)}
                >
                  <Text style={s.actionBtnText}>{u.is_active ? '🔒 Khóa' : '🔓 Mở'}</Text>
                </TouchableOpacity>

                <TouchableOpacity style={s.deleteBtn} onPress={() => handleDeleteUser(u)}>
                  <Text style={s.deleteBtnText}>🗑️</Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })}

        {/* Modal Add User */}
        <Modal visible={showAddModal} animationType="slide" transparent>
          <View style={s.modalOverlay}>
            <View style={s.modalContent}>
              <Text style={s.modalTitle}>+ Thêm người dùng mới</Text>
              <Text style={s.inputLabel}>Họ và tên</Text>
              <TextInput
                style={s.input}
                value={newUser.name}
                onChangeText={(v) => setNewUser({ ...newUser, name: v })}
                placeholder="Nguyễn Văn A"
              />
              <Text style={s.inputLabel}>Số điện thoại (*)</Text>
              <TextInput
                style={s.input}
                value={newUser.phone}
                onChangeText={(v) => setNewUser({ ...newUser, phone: v })}
                placeholder="0912345678"
                keyboardType="phone-pad"
              />
              <Text style={s.inputLabel}>Mật khẩu (*)</Text>
              <TextInput
                style={s.input}
                value={newUser.password}
                onChangeText={(v) => setNewUser({ ...newUser, password: v })}
                placeholder="Tối thiểu 6 ký tự"
                secureTextEntry
              />
              <Text style={s.inputLabel}>Email (tùy chọn)</Text>
              <TextInput
                style={s.input}
                value={newUser.email}
                onChangeText={(v) => setNewUser({ ...newUser, email: v })}
                placeholder="email@domain.com"
                keyboardType="email-address"
              />
              <Text style={s.inputLabel}>Vai trò</Text>
              <View style={{ flexDirection: 'row', gap: 10, marginBottom: 16 }}>
                {['user', 'admin'].map((r) => (
                  <TouchableOpacity
                    key={r}
                    style={[s.roleOption, newUser.role === r && s.roleOptionActive]}
                    onPress={() => setNewUser({ ...newUser, role: r })}
                  >
                    <Text style={[s.roleOptionText, newUser.role === r && s.roleOptionTextActive]}>
                      {r === 'admin' ? 'Quản trị viên' : 'Người dùng'}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <View style={s.modalBtnRow}>
                <TouchableOpacity style={s.modalCancelBtn} onPress={() => setShowAddModal(false)}>
                  <Text style={s.modalCancelText}>Hủy</Text>
                </TouchableOpacity>
                <TouchableOpacity style={s.modalSaveBtn} onPress={handleCreateUser} disabled={creating}>
                  {creating ? <ActivityIndicator color="#fff" /> : <Text style={s.modalSaveText}>Tạo tài khoản</Text>}
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>

        {/* Modal Edit User */}
        <Modal visible={showEditModal} animationType="slide" transparent>
          <View style={s.modalOverlay}>
            <View style={s.modalContent}>
              <Text style={s.modalTitle}>✏️ Sửa thông tin tài khoản</Text>
              <Text style={s.inputLabel}>Họ và tên</Text>
              <TextInput
                style={s.input}
                value={editForm.name}
                onChangeText={(v) => setEditForm({ ...editForm, name: v })}
              />
              <Text style={s.inputLabel}>Số điện thoại</Text>
              <TextInput
                style={s.input}
                value={editForm.phone}
                onChangeText={(v) => setEditForm({ ...editForm, phone: v })}
                keyboardType="phone-pad"
              />
              <Text style={s.inputLabel}>Email</Text>
              <TextInput
                style={s.input}
                value={editForm.email}
                onChangeText={(v) => setEditForm({ ...editForm, email: v })}
              />
              <Text style={s.inputLabel}>Vai trò</Text>
              <View style={{ flexDirection: 'row', gap: 10, marginBottom: 16 }}>
                {['user', 'admin'].map((r) => (
                  <TouchableOpacity
                    key={r}
                    style={[s.roleOption, editForm.role === r && s.roleOptionActive]}
                    onPress={() => setEditForm({ ...editForm, role: r })}
                  >
                    <Text style={[s.roleOptionText, editForm.role === r && s.roleOptionTextActive]}>
                      {r === 'admin' ? 'Quản trị viên' : 'Người dùng'}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <View style={s.modalBtnRow}>
                <TouchableOpacity style={s.modalCancelBtn} onPress={() => setShowEditModal(false)}>
                  <Text style={s.modalCancelText}>Hủy</Text>
                </TouchableOpacity>
                <TouchableOpacity style={s.modalSaveBtn} onPress={handleSaveEdit} disabled={updating}>
                  {updating ? <ActivityIndicator color="#fff" /> : <Text style={s.modalSaveText}>Lưu cập nhật</Text>}
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>

        {/* Modal Reset Password */}
        <Modal visible={showResetModal} animationType="slide" transparent>
          <View style={s.modalOverlay}>
            <View style={s.modalContent}>
              <Text style={s.modalTitle}>🔑 Cấp lại mật khẩu</Text>
              <Text style={{ fontSize: 13, color: '#64748b', marginBottom: 12 }}>
                Tài khoản: <Text style={{ fontWeight: 'bold' }}>{resetPwdUser?.phone}</Text>
              </Text>
              <Text style={s.inputLabel}>Mật khẩu mới (tối thiểu 6 ký tự)</Text>
              <TextInput
                style={s.input}
                value={newPassword}
                onChangeText={setNewPassword}
                placeholder="Nhập mật khẩu mới"
                secureTextEntry
              />
              <View style={s.modalBtnRow}>
                <TouchableOpacity style={s.modalCancelBtn} onPress={() => setShowResetModal(false)}>
                  <Text style={s.modalCancelText}>Hủy</Text>
                </TouchableOpacity>
                <TouchableOpacity style={s.modalSaveBtn} onPress={handleResetPassword} disabled={resetting}>
                  {resetting ? <ActivityIndicator color="#fff" /> : <Text style={s.modalSaveText}>Cập nhật</Text>}
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  scroll: { padding: 18, paddingBottom: 50 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#0f172a' },
  addBtn: { backgroundColor: '#16a34a', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 10 },
  addBtnText: { color: '#fff', fontSize: 13, fontWeight: '700' },
  searchWrap: { position: 'relative', marginBottom: 12 },
  searchInput: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 12,
    padding: 11,
    paddingRight: 35,
    fontSize: 14,
  },
  clearBtn: { position: 'absolute', right: 12, top: 11 },
  clearText: { color: '#94a3b8', fontSize: 16, fontWeight: 'bold' },
  filterRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  chip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, backgroundColor: '#e2e8f0' },
  chipActive: { backgroundColor: '#16a34a' },
  chipText: { fontSize: 12, fontWeight: '600', color: '#475569' },
  chipTextActive: { color: '#fff' },
  countText: { fontSize: 12, color: '#64748b', marginBottom: 10 },

  userCard: {
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  cardDisabled: { backgroundColor: '#fef2f2', borderColor: '#fca5a5' },
  userInfo: { marginBottom: 10 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  userName: { fontSize: 15, fontWeight: '700', color: '#0f172a' },
  lockedBadge: { backgroundColor: '#ef4444', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 6 },
  lockedText: { color: '#fff', fontSize: 10, fontWeight: '700' },
  userSub: { fontSize: 13, color: '#64748b', marginTop: 2 },
  userEmail: { fontSize: 12, color: '#64748b', marginTop: 2 },

  actionRow: { flexDirection: 'row', alignItems: 'center', gap: 6, borderTopWidth: 1, borderTopColor: '#f1f5f9', paddingTop: 10 },
  actionBtn: { backgroundColor: '#f1f5f9', paddingHorizontal: 8, paddingVertical: 5, borderRadius: 8 },
  actionBtnText: { fontSize: 12, fontWeight: '600', color: '#334155' },
  btnLock: { backgroundColor: '#fee2e2' },
  btnUnlock: { backgroundColor: '#dcfce7' },
  deleteBtn: { marginLeft: 'auto', padding: 5 },
  deleteBtnText: { fontSize: 16 },

  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 20 },
  modalContent: { backgroundColor: '#fff', borderRadius: 16, padding: 20 },
  modalTitle: { fontSize: 17, fontWeight: 'bold', color: '#0f172a', marginBottom: 14 },
  inputLabel: { fontSize: 12, fontWeight: '600', color: '#475569', marginBottom: 5 },
  input: { borderWidth: 1, borderColor: '#cbd5e1', borderRadius: 10, padding: 10, fontSize: 14, marginBottom: 12 },
  roleOption: { flex: 1, borderWidth: 1, borderColor: '#cbd5e1', borderRadius: 8, padding: 10, alignItems: 'center' },
  roleOptionActive: { backgroundColor: '#16a34a', borderColor: '#16a34a' },
  roleOptionText: { fontSize: 13, fontWeight: '600', color: '#475569' },
  roleOptionTextActive: { color: '#fff' },
  modalBtnRow: { flexDirection: 'row', gap: 10, marginTop: 10 },
  modalCancelBtn: { flex: 1, borderWidth: 1, borderColor: '#cbd5e1', padding: 12, borderRadius: 10, alignItems: 'center' },
  modalCancelText: { color: '#475569', fontWeight: '600', fontSize: 14 },
  modalSaveBtn: { flex: 1, backgroundColor: '#16a34a', padding: 12, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  modalSaveText: { color: '#fff', fontWeight: '700', fontSize: 14 },
});

