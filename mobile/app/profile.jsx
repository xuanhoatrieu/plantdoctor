import { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
  Platform,
  Modal,
  Linking,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import * as AppleAuthentication from 'expo-apple-authentication';
import {
  login,
  register,
  logout,
  getUser,
  getProfile,
  updateProfile,
  changePassword,
  deleteAccount,
  forgotPassword,
  appleLogin,
} from '../src/api';

const PRIVACY_URL = 'https://tuaf.edu.vn/bai-viet/chinh-sach-bao-mat-va-quyen-rieng-tu-43449.html';

export default function ProfileScreen() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [mode, setMode] = useState('login'); // login | register
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Modals
  const [showEditModal, setShowEditModal] = useState(false);
  const [editName, setEditName] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [updatingProfile, setUpdatingProfile] = useState(false);

  const [showPwdModal, setShowPwdModal] = useState(false);
  const [currentPwd, setCurrentPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');
  const [changingPwd, setChangingPwd] = useState(false);

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmPwd, setDeleteConfirmPwd] = useState('');
  const [deleting, setDeleting] = useState(false);

  // Load user data on mount
  useEffect(() => {
    getUser().then((cached) => {
      if (cached) setUser(cached);
    });
    getProfile().then((fresh) => {
      if (fresh) setUser(fresh);
    }).catch(() => {});
  }, []);

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
      setPhone('');
      setPassword('');
      setName('');
      setEmail('');
    } catch (e) {
      setError(e.response?.data?.detail || 'Số điện thoại hoặc mật khẩu không đúng');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    Alert.alert('Đăng xuất', 'Bạn có chắc chắn muốn đăng xuất khỏi ứng dụng?', [
      { text: 'Hủy', style: 'cancel' },
      {
        text: 'Đăng xuất',
        style: 'destructive',
        onPress: async () => {
          await logout();
          setUser(null);
        },
      },
    ]);
  };

  const openEditModal = () => {
    setEditName(user?.name || '');
    setEditEmail(user?.email || '');
    setShowEditModal(true);
  };

  const handleSaveProfile = async () => {
    setUpdatingProfile(true);
    try {
      const res = await updateProfile({ name: editName, email: editEmail });
      setUser(res.user);
      setShowEditModal(false);
      Alert.alert('Thành công', 'Thông tin tài khoản đã được cập nhật.');
    } catch (e) {
      Alert.alert('Lỗi', e.response?.data?.detail || 'Không thể cập nhật thông tin');
    } finally {
      setUpdatingProfile(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPwd.length < 6) {
      Alert.alert('Lỗi', 'Mật khẩu mới phải có tối thiểu 6 ký tự.');
      return;
    }
    if (newPwd !== confirmPwd) {
      Alert.alert('Lỗi', 'Mật khẩu xác nhận không khớp.');
      return;
    }
    setChangingPwd(true);
    try {
      await changePassword(currentPwd, newPwd);
      setShowPwdModal(false);
      setCurrentPwd('');
      setNewPwd('');
      setConfirmPwd('');
      Alert.alert('Thành công', 'Mật khẩu đã được thay đổi thành công.');
    } catch (e) {
      Alert.alert('Lỗi', e.response?.data?.detail || 'Đổi mật khẩu thất bại. Vui lòng kiểm tra lại mật khẩu hiện tại.');
    } finally {
      setChangingPwd(false);
    }
  };

  const handleDeleteAccount = async () => {
    const isAppleUser = user?.phone?.startsWith('apple_');
    if (!isAppleUser && !deleteConfirmPwd) {
      Alert.alert('Xác nhận', 'Vui lòng nhập mật khẩu hiện tại để xác nhận xóa tài khoản.');
      return;
    }
    setDeleting(true);
    try {
      await deleteAccount(deleteConfirmPwd || null);
      setShowDeleteModal(false);
      setDeleteConfirmPwd('');
      setUser(null);
      Alert.alert('Đã xóa', 'Tài khoản của bạn đã được xóa vĩnh viễn theo đúng chính sách.');
    } catch (e) {
      Alert.alert('Lỗi', e.response?.data?.detail || 'Xóa tài khoản thất bại. Vui lòng kiểm tra lại mật khẩu.');
    } finally {
      setDeleting(false);
    }
  };

  const handleForgotPassword = () => {
    Alert.alert(
      'Quên mật khẩu',
      'Để khôi phục mật khẩu, vui lòng liên hệ bộ phận hỗ trợ kỹ thuật PlantDoctor (Trường ĐH Nông Lâm Thái Nguyên):\n\n📞 Hotline: 0944.550.007\n✉️ Email: trieuxuanhoa@tuaf.edu.vn',
      [
        { text: 'Gọi hỗ trợ', onPress: () => Linking.openURL('tel:0944550007') },
        { text: 'Đóng', style: 'cancel' },
      ]
    );
  };

  // Render for Logged In User
  if (user) {
    const initials = (user.name || user.phone || 'U').slice(0, 2).toUpperCase();
    const isAppleUser = user.phone?.startsWith('apple_');

    return (
      <SafeAreaView style={s.container}>
        <ScrollView contentContainerStyle={s.scroll}>
          <Text style={s.title}>👤 Quản lý Tài khoản</Text>

          {/* Profile Card */}
          <View style={s.profileCard}>
            <View style={s.avatarCircle}>
              <Text style={s.avatarText}>{initials}</Text>
            </View>
            <Text style={s.profileName}>{user.name || 'Người dùng'}</Text>
            <Text style={s.profilePhone}>
              {isAppleUser ? 'Đăng nhập qua Apple' : `SĐT: ${user.phone}`}
            </Text>
            {user.email ? <Text style={s.profileEmail}>✉️ {user.email}</Text> : null}
            <View style={s.roleBadge}>
              <Text style={s.roleText}>
                {user.role === 'admin' ? '⚙️ Quản trị viên hệ thống' : '🌱 Người dùng'}
              </Text>
            </View>
          </View>

          {/* Actions List */}
          <View style={s.sectionCard}>
            <Text style={s.sectionHeader}>Cài đặt tài khoản</Text>

            <TouchableOpacity style={s.menuItem} onPress={openEditModal}>
              <Text style={s.menuIcon}>✏️</Text>
              <View style={s.menuTextWrap}>
                <Text style={s.menuTitle}>Chỉnh sửa thông tin</Text>
                <Text style={s.menuSubtitle}>Cập nhật tên hiển thị, địa chỉ email</Text>
              </View>
              <Text style={s.menuChevron}>›</Text>
            </TouchableOpacity>

            {!isAppleUser && (
              <TouchableOpacity style={s.menuItem} onPress={() => setShowPwdModal(true)}>
                <Text style={s.menuIcon}>🔒</Text>
                <View style={s.menuTextWrap}>
                  <Text style={s.menuTitle}>Đổi mật khẩu</Text>
                  <Text style={s.menuSubtitle}>Thay đổi mật khẩu đăng nhập tài khoản</Text>
                </View>
                <Text style={s.menuChevron}>›</Text>
              </TouchableOpacity>
            )}

            {user.role === 'admin' && (
              <TouchableOpacity style={[s.menuItem, s.adminHighlight]} onPress={() => router.push('/admin')}>
                <Text style={s.menuIcon}>⚙️</Text>
                <View style={s.menuTextWrap}>
                  <Text style={[s.menuTitle, { color: '#7c3aed' }]}>Trang Quản trị Hệ thống</Text>
                  <Text style={s.menuSubtitle}>Quản lý bệnh, thuốc BVTV, người dùng</Text>
                </View>
                <Text style={s.menuChevron}>›</Text>
              </TouchableOpacity>
            )}
          </View>

          {/* Privacy and App Info */}
          <View style={s.sectionCard}>
            <Text style={s.sectionHeader}>Chính sách & Pháp lý</Text>

            <TouchableOpacity style={s.menuItem} onPress={() => Linking.openURL(PRIVACY_URL)}>
              <Text style={s.menuIcon}>🛡️</Text>
              <View style={s.menuTextWrap}>
                <Text style={s.menuTitle}>Chính sách Quyền riêng tư</Text>
                <Text style={s.menuSubtitle}>Bảo mật dữ liệu, ảnh chụp và vị trí</Text>
              </View>
              <Text style={s.menuChevron}>↗</Text>
            </TouchableOpacity>

            <TouchableOpacity style={s.menuItem} onPress={() => Linking.openURL('https://benhcay.tuaf.edu.vn')}>
              <Text style={s.menuIcon}>🌐</Text>
              <View style={s.menuTextWrap}>
                <Text style={s.menuTitle}>Website hỗ trợ</Text>
                <Text style={s.menuSubtitle}>https://benhcay.tuaf.edu.vn</Text>
              </View>
              <Text style={s.menuChevron}>↗</Text>
            </TouchableOpacity>
          </View>

          {/* App Info Banner */}
          <View style={s.infoBox}>
            <Text style={s.infoTitle}>ℹ️ Ứng dụng PlantDoctor</Text>
            <Text style={s.infoText}>Phiên bản 1.0.2 • Mã nguồn AI TUAF</Text>
            <Text style={s.infoText}>Trường Đại học Nông Lâm Thái Nguyên</Text>
          </View>

          {/* Danger Zone: Logout & Account Deletion */}
          <TouchableOpacity style={s.logoutBtn} onPress={handleLogout}>
            <Text style={s.logoutText}>Đăng xuất tài khoản</Text>
          </TouchableOpacity>

          <TouchableOpacity style={s.deleteBtn} onPress={() => setShowDeleteModal(true)}>
            <Text style={s.deleteText}>⚠️ Xóa tài khoản vĩnh viễn</Text>
          </TouchableOpacity>
          <Text style={s.deleteDesc}>
            Theo quy định của Apple App Store & Google Play, bạn có quyền xóa vĩnh viễn tài khoản và toàn bộ dữ liệu liên quan khỏi hệ thống bất cứ lúc nào.
          </Text>

          {/* Modal Edit Profile */}
          <Modal visible={showEditModal} animationType="slide" transparent>
            <View style={s.modalOverlay}>
              <View style={s.modalContent}>
                <Text style={s.modalTitle}>✏️ Chỉnh sửa thông tin</Text>
                <Text style={s.inputLabel}>Họ và tên</Text>
                <TextInput
                  style={s.input}
                  value={editName}
                  onChangeText={setEditName}
                  placeholder="Nhập họ và tên"
                />
                <Text style={s.inputLabel}>Địa chỉ Email (tùy chọn)</Text>
                <TextInput
                  style={s.input}
                  value={editEmail}
                  onChangeText={setEditEmail}
                  placeholder="name@domain.com"
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
                <View style={s.modalBtnRow}>
                  <TouchableOpacity style={s.modalCancelBtn} onPress={() => setShowEditModal(false)}>
                    <Text style={s.modalCancelText}>Hủy</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={s.modalSaveBtn}
                    onPress={handleSaveProfile}
                    disabled={updatingProfile}
                  >
                    {updatingProfile ? (
                      <ActivityIndicator color="#fff" />
                    ) : (
                      <Text style={s.modalSaveText}>Lưu thay đổi</Text>
                    )}
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </Modal>

          {/* Modal Change Password */}
          <Modal visible={showPwdModal} animationType="slide" transparent>
            <View style={s.modalOverlay}>
              <View style={s.modalContent}>
                <Text style={s.modalTitle}>🔒 Đổi mật khẩu</Text>
                <Text style={s.inputLabel}>Mật khẩu hiện tại</Text>
                <TextInput
                  style={s.input}
                  value={currentPwd}
                  onChangeText={setCurrentPwd}
                  placeholder="Nhập mật khẩu hiện tại"
                  secureTextEntry
                />
                <Text style={s.inputLabel}>Mật khẩu mới (tối thiểu 6 ký tự)</Text>
                <TextInput
                  style={s.input}
                  value={newPwd}
                  onChangeText={setNewPwd}
                  placeholder="Mật khẩu mới"
                  secureTextEntry
                />
                <Text style={s.inputLabel}>Xác nhận mật khẩu mới</Text>
                <TextInput
                  style={s.input}
                  value={confirmPwd}
                  onChangeText={setConfirmPwd}
                  placeholder="Nhập lại mật khẩu mới"
                  secureTextEntry
                />
                <View style={s.modalBtnRow}>
                  <TouchableOpacity style={s.modalCancelBtn} onPress={() => setShowPwdModal(false)}>
                    <Text style={s.modalCancelText}>Hủy</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={s.modalSaveBtn}
                    onPress={handleChangePassword}
                    disabled={changingPwd}
                  >
                    {changingPwd ? (
                      <ActivityIndicator color="#fff" />
                    ) : (
                      <Text style={s.modalSaveText}>Đổi mật khẩu</Text>
                    )}
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </Modal>

          {/* Modal Delete Account */}
          <Modal visible={showDeleteModal} animationType="fade" transparent>
            <View style={s.modalOverlay}>
              <View style={[s.modalContent, { borderColor: '#ef4444', borderWidth: 2 }]}>
                <Text style={[s.modalTitle, { color: '#dc2626' }]}>⚠️ Xóa tài khoản vĩnh viễn</Text>
                <Text style={s.deleteWarningText}>
                  Hành động này <Text style={{ fontWeight: 'bold' }}>KHÔNG THỂ hoàn tác</Text>. Toàn bộ dữ liệu hồ sơ cá nhân và lịch sử chẩn đoán cây trồng của bạn sẽ bị xóa ngay lập tức khỏi máy chủ.
                </Text>
                {!isAppleUser && (
                  <>
                    <Text style={s.inputLabel}>Nhập mật khẩu của bạn để xác nhận:</Text>
                    <TextInput
                      style={[s.input, { borderColor: '#fca5a5' }]}
                      value={deleteConfirmPwd}
                      onChangeText={setDeleteConfirmPwd}
                      placeholder="Mật khẩu xác nhận"
                      secureTextEntry
                    />
                  </>
                )}
                <View style={s.modalBtnRow}>
                  <TouchableOpacity
                    style={s.modalCancelBtn}
                    onPress={() => {
                      setShowDeleteModal(false);
                      setDeleteConfirmPwd('');
                    }}
                  >
                    <Text style={s.modalCancelText}>Hủy bỏ</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[s.modalSaveBtn, { backgroundColor: '#dc2626' }]}
                    onPress={handleDeleteAccount}
                    disabled={deleting}
                  >
                    {deleting ? (
                      <ActivityIndicator color="#fff" />
                    ) : (
                      <Text style={s.modalSaveText}>Tôi chắc chắn, Xóa</Text>
                    )}
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </Modal>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // Render for Guest (Login / Register)
  return (
    <SafeAreaView style={s.container}>
      <ScrollView contentContainerStyle={s.scroll}>
        <Text style={s.title}>👤 {mode === 'login' ? 'Đăng nhập' : 'Đăng ký tài khoản'}</Text>
        <Text style={s.desc}>
          {mode === 'login'
            ? 'Đăng nhập để đồng bộ lịch sử chẩn đoán và quản lý tài khoản'
            : 'Đăng ký tài khoản hoàn toàn miễn phí để bắt đầu chẩn đoán'}
        </Text>

        {mode === 'register' && (
          <>
            <Text style={s.inputLabel}>Họ và tên</Text>
            <TextInput
              style={s.input}
              value={name}
              onChangeText={setName}
              placeholder="Ví dụ: Nguyễn Văn An"
            />
          </>
        )}

        <Text style={s.inputLabel}>Số điện thoại</Text>
        <TextInput
          style={s.input}
          value={phone}
          onChangeText={setPhone}
          placeholder="Ví dụ: 0912345678"
          keyboardType="phone-pad"
        />

        <Text style={s.inputLabel}>Mật khẩu</Text>
        <TextInput
          style={s.input}
          value={password}
          onChangeText={setPassword}
          placeholder="Tối thiểu 6 ký tự"
          secureTextEntry
        />

        {mode === 'login' && (
          <TouchableOpacity style={s.forgotBtn} onPress={handleForgotPassword}>
            <Text style={s.forgotText}>Quên mật khẩu?</Text>
          </TouchableOpacity>
        )}

        {error ? <Text style={s.error}>{error}</Text> : null}

        <TouchableOpacity
          style={[s.submitBtn, (phone.length < 9 || password.length < 6) && s.btnDisabled]}
          onPress={handleSubmit}
          disabled={loading || phone.length < 9 || password.length < 6}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={s.submitText}>{mode === 'login' ? 'Đăng nhập' : 'Đăng ký'}</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity onPress={() => setMode(mode === 'login' ? 'register' : 'login')} style={s.switchBtn}>
          <Text style={s.switchText}>
            {mode === 'login' ? 'Chưa có tài khoản? Đăng ký ngay' : 'Đã có tài khoản? Đăng nhập'}
          </Text>
        </TouchableOpacity>

        {Platform.OS === 'ios' && (
          <View style={{ marginTop: 24 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>
              <View style={{ flex: 1, height: 1, backgroundColor: '#e5e7eb' }} />
              <Text style={{ marginHorizontal: 12, color: '#9ca3af', fontSize: 13 }}>hoặc</Text>
              <View style={{ flex: 1, height: 1, backgroundColor: '#e5e7eb' }} />
            </View>
            <AppleAuthentication.AppleAuthenticationButton
              buttonType={AppleAuthentication.AppleAuthenticationButtonType.SIGN_IN}
              buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.BLACK}
              cornerRadius={14}
              style={{ height: 50 }}
              onPress={async () => {
                try {
                  const credential = await AppleAuthentication.signInAsync({
                    requestedScopes: [
                      AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
                      AppleAuthentication.AppleAuthenticationScope.EMAIL,
                    ],
                  });
                  const data = await appleLogin(credential.identityToken, credential.fullName?.givenName);
                  setUser(data.user);
                } catch (e) {
                  if (e.code !== 'ERR_REQUEST_CANCELED') {
                    setError('Đăng nhập Apple thất bại');
                  }
                }
              }}
            />
          </View>
        )}

        <View style={{ marginTop: 30, alignItems: 'center' }}>
          <TouchableOpacity onPress={() => Linking.openURL(PRIVACY_URL)}>
            <Text style={{ color: '#6b7280', fontSize: 12, textDecorationLine: 'underline' }}>
              Chính sách Quyền riêng tư & Điều khoản
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  scroll: { padding: 20, paddingBottom: 50 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#0f172a', marginBottom: 6 },
  desc: { fontSize: 14, color: '#64748b', marginBottom: 20 },
  inputLabel: { fontSize: 13, fontWeight: '600', color: '#334155', marginBottom: 6 },
  input: {
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 12,
    padding: 13,
    fontSize: 15,
    marginBottom: 14,
    backgroundColor: '#fff',
    color: '#0f172a',
  },
  error: { color: '#ef4444', fontSize: 13, marginBottom: 12, textAlign: 'center' },
  submitBtn: { backgroundColor: '#16a34a', padding: 15, borderRadius: 12, alignItems: 'center', marginTop: 6 },
  submitText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  btnDisabled: { opacity: 0.4 },
  switchBtn: { marginTop: 16, alignItems: 'center' },
  switchText: { color: '#16a34a', fontSize: 14, fontWeight: '600' },
  forgotBtn: { alignSelf: 'flex-end', marginBottom: 14, marginTop: -4 },
  forgotText: { color: '#2563eb', fontSize: 13, fontWeight: '500' },

  profileCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  avatarCircle: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: '#dcfce7',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
    borderWidth: 2,
    borderColor: '#86efac',
  },
  avatarText: { fontSize: 24, fontWeight: 'bold', color: '#15803d' },
  profileName: { fontSize: 20, fontWeight: 'bold', color: '#0f172a' },
  profilePhone: { fontSize: 14, color: '#64748b', marginTop: 4 },
  profileEmail: { fontSize: 13, color: '#64748b', marginTop: 2 },
  roleBadge: {
    marginTop: 10,
    backgroundColor: '#f1f5f9',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 20,
  },
  roleText: { color: '#334155', fontSize: 13, fontWeight: '600' },

  sectionCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  sectionHeader: {
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
    color: '#94a3b8',
    marginBottom: 12,
    letterSpacing: 0.5,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  adminHighlight: {
    backgroundColor: '#faf5ff',
    marginHorizontal: -8,
    paddingHorizontal: 8,
    borderRadius: 10,
  },
  menuIcon: { fontSize: 20, marginRight: 12 },
  menuTextWrap: { flex: 1 },
  menuTitle: { fontSize: 15, fontWeight: '600', color: '#1e293b' },
  menuSubtitle: { fontSize: 12, color: '#64748b', marginTop: 2 },
  menuChevron: { fontSize: 18, color: '#94a3b8', fontWeight: 'bold' },

  infoBox: {
    backgroundColor: '#f8fafc',
    borderRadius: 14,
    padding: 14,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  infoTitle: { fontWeight: '700', color: '#0f172a', marginBottom: 4, fontSize: 14 },
  infoText: { fontSize: 13, color: '#64748b', marginBottom: 2 },

  logoutBtn: {
    borderWidth: 1.5,
    borderColor: '#cbd5e1',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  logoutText: { color: '#475569', fontSize: 15, fontWeight: '600' },
  deleteBtn: {
    borderWidth: 1.5,
    borderColor: '#fca5a5',
    backgroundColor: '#fef2f2',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
    marginBottom: 8,
  },
  deleteText: { color: '#dc2626', fontSize: 15, fontWeight: '700' },
  deleteDesc: { fontSize: 11, color: '#94a3b8', textAlign: 'center', paddingHorizontal: 10, marginBottom: 20 },

  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 18,
    padding: 22,
    shadowColor: '#000',
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 5,
  },
  modalTitle: { fontSize: 18, fontWeight: 'bold', color: '#0f172a', marginBottom: 14 },
  deleteWarningText: { fontSize: 14, color: '#475569', lineHeight: 20, marginBottom: 14 },
  modalBtnRow: { flexDirection: 'row', gap: 10, marginTop: 10 },
  modalCancelBtn: { flex: 1, borderWidth: 1, borderColor: '#cbd5e1', padding: 13, borderRadius: 10, alignItems: 'center' },
  modalCancelText: { color: '#475569', fontWeight: '600', fontSize: 14 },
  modalSaveBtn: { flex: 1, backgroundColor: '#16a34a', padding: 13, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  modalSaveText: { color: '#fff', fontWeight: '700', fontSize: 14 },
});

