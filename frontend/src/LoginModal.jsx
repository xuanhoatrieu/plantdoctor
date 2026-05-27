import { useState } from 'react';
import { useAuth } from './AuthContext';

export default function LoginModal({ onClose, lang }) {
  const [mode, setMode] = useState('login'); // login | register
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login, register } = useAuth();

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      if (mode === 'login') {
        await login(phone, password);
      } else {
        await register(phone, password, name);
      }
      onClose();
    } catch (e) {
      const msg = e.response?.data?.detail || (lang === 'vi' ? 'Có lỗi xảy ra' : 'An error occurred');
      setError(msg);
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-sm space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold text-gray-900">
            {mode === 'login' ? (lang === 'vi' ? 'Đăng nhập' : 'Login') : (lang === 'vi' ? 'Đăng ký' : 'Register')}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
        </div>

        {mode === 'register' && (
          <input type="text" value={name} onChange={e => setName(e.target.value)}
            placeholder={lang === 'vi' ? 'Họ tên' : 'Full name'}
            className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-green-300" />
        )}

        <input type="tel" value={phone} onChange={e => setPhone(e.target.value)}
          placeholder={lang === 'vi' ? 'Số điện thoại' : 'Phone number'}
          className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-green-300" />

        <input type="password" value={password} onChange={e => setPassword(e.target.value)}
          placeholder={lang === 'vi' ? 'Mật khẩu (tối thiểu 6 ký tự)' : 'Password (min 6 chars)'}
          className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-green-300" />

        <button onClick={handleSubmit} disabled={loading || phone.length < 9 || password.length < 6}
          className="w-full py-3 bg-green-600 text-white rounded-xl font-semibold disabled:opacity-50 hover:bg-green-700">
          {loading ? '...' : mode === 'login' ? (lang === 'vi' ? 'Đăng nhập' : 'Login') : (lang === 'vi' ? 'Đăng ký' : 'Register')}
        </button>

        {error && <p className="text-red-500 text-sm text-center">{error}</p>}

        <p className="text-center text-sm text-gray-500">
          {mode === 'login' ? (
            <>{lang === 'vi' ? 'Chưa có tài khoản? ' : "Don't have an account? "}
              <button onClick={() => setMode('register')} className="text-green-600 font-medium">{lang === 'vi' ? 'Đăng ký' : 'Register'}</button>
            </>
          ) : (
            <>{lang === 'vi' ? 'Đã có tài khoản? ' : 'Already have an account? '}
              <button onClick={() => setMode('login')} className="text-green-600 font-medium">{lang === 'vi' ? 'Đăng nhập' : 'Login'}</button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
