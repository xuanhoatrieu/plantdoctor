import { useState, useEffect } from 'react'
import { useAuth } from './AuthContext'
import axios from 'axios'

function api(token) {
  return axios.create({ headers: { Authorization: `Bearer ${token}` } })
}
export default function AdminView({ lang, onConfigUpdated }) {
  const { token } = useAuth()
  const [tab, setTab] = useState('diseases')

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold text-gray-900">⚙️ {lang === 'vi' ? 'Quản trị hệ thống' : 'Admin Panel'}</h2>
      <div className="flex gap-2 flex-wrap">
        {[
          { id: 'diseases', label: lang === 'vi' ? '📚 Thư viện bệnh' : '📚 Disease Library' },
          { id: 'pesticides', label: lang === 'vi' ? '🧪 Thuốc BVTV' : '🧪 Pesticides' },
          { id: 'users', label: lang === 'vi' ? '👥 Người dùng' : '👥 Users' },
          { id: 'settings', label: lang === 'vi' ? '⚙️ Cấu hình AI Model' : '⚙️ AI Model Config' },
          { id: 'mobile', label: lang === 'vi' ? '📱 Link tải App Mobile' : '📱 Mobile App Links' },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${tab === t.id ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>
            {t.label}
          </button>
        ))}
      </div>
      {tab === 'diseases' && <DiseasesAdmin token={token} lang={lang} />}
      {tab === 'pesticides' && <PesticidesAdmin token={token} lang={lang} />}
      {tab === 'users' && <UsersAdmin token={token} lang={lang} />}
      {tab === 'settings' && <SettingsAdmin token={token} lang={lang} />}
      {tab === 'mobile' && <MobileAppsAdmin token={token} lang={lang} onConfigUpdated={onConfigUpdated} />}
    </div>
  )
}


// ==================== DISEASES ====================
function DiseasesAdmin({ token, lang }) {
  const [items, setItems] = useState([])
  const [editing, setEditing] = useState(null) // null=list, {}=new, {id:...}=edit
  const [loading, setLoading] = useState(false)

  const fetch_ = () => {
    setLoading(true)
    api(token).get('/api/v1/admin/diseases').then(r => setItems(r.data)).finally(() => setLoading(false))
  }
  useEffect(fetch_, [])

  const save = async (data) => {
    if (data.id) {
      await api(token).put(`/api/v1/admin/diseases/${data.id}`, data)
    } else {
      await api(token).post('/api/v1/admin/diseases', data)
    }
    setEditing(null)
    fetch_()
  }

  const del = async (id) => {
    if (!confirm('Xác nhận xóa?')) return
    await api(token).delete(`/api/v1/admin/diseases/${id}`)
    fetch_()
  }

  if (editing !== null) return <DiseaseForm data={editing} onSave={save} onCancel={() => setEditing(null)} lang={lang} />

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <p className="text-sm text-gray-500">{items.length} bệnh</p>
        <button onClick={() => setEditing({})} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">+ Thêm bệnh</button>
      </div>
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div className="space-y-2">
          {items.map(item => (
            <div key={item.id} className="bg-white border rounded-lg p-3 flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">{item.name_vi || item.name_en}</p>
                <p className="text-xs text-gray-500">{item.crop} • {item.scientific_name}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setEditing(item)} className="text-blue-600 text-sm hover:underline">Sửa</button>
                <button onClick={() => del(item.id)} className="text-red-500 text-sm hover:underline">Xóa</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function DiseaseForm({ data, onSave, onCancel, lang }) {
  const [form, setForm] = useState({
    crop: '', name_vi: '', name_en: '', scientific_name: '', severity: 'medium',
    symptoms_vi: '', symptoms_en: '', conditions_vi: '', conditions_en: '',
    prevention_vi: '', prevention_en: '', treatment_vi: '', treatment_en: '', image_url: '',
    ...data,
  })
  const set = (k, v) => setForm({ ...form, [k]: v })

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h3 className="font-bold">{form.id ? 'Sửa bệnh' : 'Thêm bệnh mới'}</h3>
        <button onClick={onCancel} className="text-gray-500 text-sm">← Quay lại</button>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        <Input label="Cây trồng" value={form.crop} onChange={v => set('crop', v)} placeholder="VD: Lúa" />
        <Input label="Mức độ" value={form.severity} onChange={v => set('severity', v)} placeholder="low/medium/high" />
        <Input label="Tên bệnh (VI)" value={form.name_vi} onChange={v => set('name_vi', v)} />
        <Input label="Tên bệnh (EN)" value={form.name_en} onChange={v => set('name_en', v)} />
        <Input label="Tên khoa học" value={form.scientific_name} onChange={v => set('scientific_name', v)} />
        <Input label="URL hình ảnh" value={form.image_url} onChange={v => set('image_url', v)} />
      </div>
      <Textarea label="Triệu chứng (VI)" value={form.symptoms_vi} onChange={v => set('symptoms_vi', v)} />
      <Textarea label="Triệu chứng (EN)" value={form.symptoms_en} onChange={v => set('symptoms_en', v)} />
      <Textarea label="Điều kiện phát bệnh (VI)" value={form.conditions_vi} onChange={v => set('conditions_vi', v)} />
      <Textarea label="Phòng tránh (VI)" value={form.prevention_vi} onChange={v => set('prevention_vi', v)} placeholder="Mỗi dòng 1 biện pháp" />
      <Textarea label="Điều trị (VI)" value={form.treatment_vi} onChange={v => set('treatment_vi', v)} placeholder="Mỗi dòng 1 phương pháp" />
      <button onClick={() => onSave(form)} className="w-full py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700">
        {form.id ? 'Cập nhật' : 'Thêm mới'}
      </button>
    </div>
  )
}

// ==================== PESTICIDES ====================
function PesticidesAdmin({ token, lang }) {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [page, setPage] = useState(0)
  const [editing, setEditing] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetch_ = () => {
    setLoading(true)
    const params = { page, size: 30 }
    if (search) params.q = search
    if (category) params.category = category
    api(token).get('/api/v1/admin/pesticides', { params }).then(r => {
      setItems(r.data.items || [])
      setTotal(r.data.total || 0)
    }).finally(() => setLoading(false))
  }
  useEffect(fetch_, [page, search, category])

  const save = async (data) => {
    if (data.id) {
      await api(token).put(`/api/v1/admin/pesticides/${data.id}`, data)
    } else {
      await api(token).post('/api/v1/admin/pesticides', data)
    }
    setEditing(null)
    fetch_()
  }

  const del = async (id) => {
    if (!confirm('Xác nhận xóa?')) return
    await api(token).delete(`/api/v1/admin/pesticides/${id}`)
    fetch_()
  }

  if (editing !== null) return <PesticideForm data={editing} onSave={save} onCancel={() => setEditing(null)} />

  return (
    <div className="space-y-3">
      <div className="flex gap-2 flex-wrap items-center">
        <input type="text" value={search} onChange={e => { setSearch(e.target.value); setPage(0) }}
          placeholder="Tìm kiếm..." className="flex-1 min-w-[200px] px-3 py-2 border rounded-lg text-sm" />
        <select value={category} onChange={e => { setCategory(e.target.value); setPage(0) }} className="px-3 py-2 border rounded-lg text-sm bg-white">
          <option value="">Tất cả loại</option>
          <option value="Thuốc trừ sâu">Trừ sâu</option>
          <option value="Thuốc trừ bệnh">Trừ bệnh</option>
          <option value="Thuốc trừ cỏ">Trừ cỏ</option>
          <option value="Thuốc trừ chuột">Trừ chuột</option>
          <option value="Thuốc trừ ốc">Trừ ốc</option>
        </select>
        <button onClick={() => setEditing({})} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium">+ Thêm</button>
      </div>
      <p className="text-xs text-gray-500">{total} sản phẩm • Trang {page + 1}/{Math.ceil(total / 30) || 1}</p>
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="bg-gray-50 text-left">
              <th className="px-2 py-2">Tên</th><th className="px-2 py-2">Hoạt chất</th><th className="px-2 py-2 hidden md:table-cell">Công ty</th><th className="px-2 py-2 w-20"></th>
            </tr></thead>
            <tbody>
              {items.map(item => (
                <tr key={item.id} className="border-t hover:bg-gray-50">
                  <td className="px-2 py-1.5 font-medium">{item.name}</td>
                  <td className="px-2 py-1.5 text-gray-600">{item.active_ingredient}</td>
                  <td className="px-2 py-1.5 text-gray-500 text-xs hidden md:table-cell">{item.company}</td>
                  <td className="px-2 py-1.5">
                    <button onClick={() => setEditing(item)} className="text-blue-600 text-xs mr-2">Sửa</button>
                    <button onClick={() => del(item.id)} className="text-red-500 text-xs">Xóa</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="flex justify-center gap-2">
        <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0} className="px-3 py-1 border rounded text-sm disabled:opacity-30">←</button>
        <button onClick={() => setPage(page + 1)} disabled={(page + 1) * 30 >= total} className="px-3 py-1 border rounded text-sm disabled:opacity-30">→</button>
      </div>
    </div>
  )
}

function PesticideForm({ data, onSave, onCancel }) {
  const [form, setForm] = useState({
    name: '', active_ingredient: '', target: '', company: '', category: 'Thuốc trừ sâu', status: 'allowed',
    ...data,
  })
  const set = (k, v) => setForm({ ...form, [k]: v })

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h3 className="font-bold">{form.id ? 'Sửa thuốc BVTV' : 'Thêm thuốc mới'}</h3>
        <button onClick={onCancel} className="text-gray-500 text-sm">← Quay lại</button>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        <Input label="Tên thương phẩm" value={form.name} onChange={v => set('name', v)} />
        <Input label="Hoạt chất" value={form.active_ingredient} onChange={v => set('active_ingredient', v)} />
        <Input label="Công ty" value={form.company} onChange={v => set('company', v)} />
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Loại</label>
          <select value={form.category} onChange={e => set('category', e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm bg-white">
            <option value="Thuốc trừ sâu">Trừ sâu</option>
            <option value="Thuốc trừ bệnh">Trừ bệnh</option>
            <option value="Thuốc trừ cỏ">Trừ cỏ</option>
            <option value="Thuốc trừ chuột">Trừ chuột</option>
            <option value="Thuốc trừ ốc">Trừ ốc</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Trạng thái</label>
          <select value={form.status} onChange={e => set('status', e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm bg-white">
            <option value="allowed">Được phép</option>
            <option value="banned">Cấm</option>
          </select>
        </div>
      </div>
      <Textarea label="Đối tượng phòng trừ" value={form.target} onChange={v => set('target', v)} />
      <button onClick={() => onSave(form)} className="w-full py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700">
        {form.id ? 'Cập nhật' : 'Thêm mới'}
      </button>
    </div>
  )
}

// ==================== USERS ====================
function UsersAdmin({ token, lang }) {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)
  const [adding, setAdding] = useState(false)
  const [newUser, setNewUser] = useState({ phone: '', password: '', name: '', role: 'user' })

  const fetch_ = () => {
    setLoading(true)
    api(token).get('/api/v1/admin/users').then(r => setUsers(r.data)).finally(() => setLoading(false))
  }
  useEffect(fetch_, [])

  const setRole = async (userId, role) => {
    await api(token).put(`/api/v1/admin/users/${userId}/role`, { role })
    fetch_()
  }

  const deleteUser = async (userId) => {
    if (!confirm('Xác nhận xóa user này?')) return
    await api(token).delete(`/api/v1/admin/users/${userId}`)
    fetch_()
  }

  const createUser = async () => {
    if (newUser.phone.length < 9 || newUser.password.length < 6) return
    try {
      await api(token).post('/api/v1/admin/users', newUser)
      setAdding(false)
      setNewUser({ phone: '', password: '', name: '', role: 'user' })
      fetch_()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error')
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <p className="text-sm text-gray-500">{users.length} người dùng</p>
        <button onClick={() => setAdding(!adding)} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium">+ Thêm user</button>
      </div>

      {adding && (
        <div className="bg-gray-50 border rounded-lg p-4 space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <input type="text" value={newUser.name} onChange={e => setNewUser({...newUser, name: e.target.value})} placeholder="Họ tên" className="px-3 py-2 border rounded-lg text-sm" />
            <input type="tel" value={newUser.phone} onChange={e => setNewUser({...newUser, phone: e.target.value})} placeholder="Số điện thoại" className="px-3 py-2 border rounded-lg text-sm" />
            <input type="text" value={newUser.password} onChange={e => setNewUser({...newUser, password: e.target.value})} placeholder="Mật khẩu" className="px-3 py-2 border rounded-lg text-sm" />
            <select value={newUser.role} onChange={e => setNewUser({...newUser, role: e.target.value})} className="px-3 py-2 border rounded-lg text-sm bg-white">
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <button onClick={createUser} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm">Tạo</button>
        </div>
      )}

      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div className="space-y-2">
          {users.map(u => (
            <div key={u.id} className="bg-white border rounded-lg p-3 flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">{u.name || u.phone}</p>
                <p className="text-xs text-gray-500">{u.phone} • {u.created_at?.slice(0, 10)}</p>
              </div>
              <div className="flex items-center gap-2">
                <select value={u.role} onChange={e => setRole(u.id, e.target.value)}
                  className={`px-3 py-1 rounded-lg text-sm font-medium border ${u.role === 'admin' ? 'bg-purple-50 text-purple-700 border-purple-200' : 'bg-gray-50 text-gray-700 border-gray-200'}`}>
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
                <button onClick={() => deleteUser(u.id)} className="text-red-500 text-xs hover:text-red-700">🗑️</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ==================== SHARED COMPONENTS ====================
function Input({ label, value, onChange, placeholder }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-700 mb-1">{label}</label>
      <input type="text" value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder}
        className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-300" />
    </div>
  )
}

function Textarea({ label, value, onChange, placeholder }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-700 mb-1">{label}</label>
      <textarea value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder} rows={3}
        className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-300 resize-y" />
    </div>
  )
}

function SettingsAdmin({ token, lang }) {
  const [settings, setSettings] = useState({
    llm_provider: 'cliproxy',
    llm_api_url: '',
    llm_api_key: '',
    llm_model_name: '',
  })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [availableModels, setAvailableModels] = useState([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const fetchSettings = () => {
    setLoading(true)
    api(token).get('/api/v1/admin/settings')
      .then(r => {
        setSettings({
          llm_provider: r.data.llm_provider || 'cliproxy',
          llm_api_url: r.data.llm_api_url || '',
          llm_api_key: r.data.llm_api_key || '',
          llm_model_name: r.data.llm_model_name || '',
        })
      })
      .catch(e => setError(e.response?.data?.detail || 'Failed to fetch settings'))
      .finally(() => setLoading(false))
  }

  useEffect(fetchSettings, [])

  const save = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    setError('')
    try {
      await api(token).put('/api/v1/admin/settings', {
        llm_provider: settings.llm_provider,
        llm_api_url: settings.llm_api_url,
        llm_api_key: settings.llm_api_key,
        llm_model_name: settings.llm_model_name,
      })
      setMessage(lang === 'vi' ? '✅ Cập nhật cấu hình AI Model thành công!' : '✅ AI Model settings updated successfully!')
      fetchSettings()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  const testConnection = async () => {
    setTesting(true)
    setMessage('')
    setError('')
    try {
      const res = await api(token).post('/api/v1/admin/settings/models', {
        llm_provider: settings.llm_provider,
        llm_api_url: settings.llm_api_url,
        llm_api_key: settings.llm_api_key,
      })
      if (res.data.ok) {
        setAvailableModels(res.data.models || [])
        setMessage(lang === 'vi' 
          ? `🔌 Kết nối thành công! Tải được ${res.data.models.length} model.` 
          : `🔌 Connection successful! Loaded ${res.data.models.length} models.`)
        if (res.data.models.length > 0 && (!settings.llm_model_name || !res.data.models.includes(settings.llm_model_name))) {
          set('llm_model_name', res.data.models[0])
        }
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Connection failed')
    } finally {
      setTesting(false)
    }
  }

  const set = (k, v) => setSettings(prev => ({ ...prev, [k]: v }))

  if (loading) return <p className="text-gray-400">Loading...</p>

  // Prepare models list to include currently selected model if it is not present in fetched availableModels list
  const modelsList = [...availableModels]
  if (settings.llm_model_name && !modelsList.includes(settings.llm_model_name)) {
    modelsList.unshift(settings.llm_model_name)
  }

  return (
    <form onSubmit={save} className="space-y-4 max-w-2xl bg-white p-6 border rounded-xl shadow-sm">
      <h3 className="font-bold text-gray-900 text-base border-b pb-2">
        {lang === 'vi' ? '⚙️ Cấu hình AI Model (Inference Backend)' : '⚙️ AI Model Configuration'}
      </h3>

      {message && <div className="p-3 bg-green-50 text-green-700 rounded-lg text-sm font-medium">{message}</div>}
      {error && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm font-medium">{error}</div>}

      <div className="space-y-3">
        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">
            {lang === 'vi' ? 'Nhà cung cấp (Provider)' : 'Provider'}
          </label>
          <select
            value={settings.llm_provider}
            onChange={e => {
              const p = e.target.value
              set('llm_provider', p)
              setAvailableModels([]) // Reset list on provider change
              if (p === 'cliproxy') {
                set('llm_api_url', 'http://152.67.112.145:8317/v1/chat/completions')
                set('llm_model_name', 'gpt-5.5')
              } else if (p === 'openai') {
                set('llm_api_url', 'https://api.openai.com/v1/chat/completions')
                set('llm_model_name', 'gpt-4o')
              } else if (p === 'google') {
                set('llm_api_url', '')
                set('llm_model_name', 'gemini-1.5-flash')
              }
            }}
            className="w-full px-3 py-2 border rounded-lg text-sm bg-white focus:ring-2 focus:ring-green-500 focus:outline-none"
          >
            <option value="cliproxy">Cliproxy (Mặc định)</option>
            <option value="openai">OpenAI API</option>
            <option value="google">Google Gemini API</option>
          </select>
        </div>

        {settings.llm_provider !== 'google' && (
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              {lang === 'vi' ? 'Đường dẫn API (API Endpoint URL)' : 'API Endpoint URL'}
            </label>
            <input
              type="text"
              required
              value={settings.llm_api_url || ''}
              onChange={e => {
                set('llm_api_url', e.target.value)
                setAvailableModels([])
              }}
              placeholder="https://..."
              className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:outline-none"
            />
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">
            API Key
          </label>
          <input
            type="password"
            value={settings.llm_api_key || ''}
            onChange={e => {
              set('llm_api_key', e.target.value)
              setAvailableModels([])
            }}
            placeholder={lang === 'vi' ? 'Nhập API key mới hoặc để nguyên' : 'Enter new API key or keep existing'}
            className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:outline-none"
          />
          <p className="text-gray-400 text-[10px] mt-1">
            {lang === 'vi' 
              ? 'Lưu ý: API key được ẩn đi để bảo mật. Chỉ điền khi cần thay đổi.'
              : 'Note: API key is masked for security. Only fill if you want to change it.'}
          </p>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">
            {lang === 'vi' ? 'Tên Model (Model Name)' : 'Model Name'}
          </label>
          {modelsList.length > 0 ? (
            <div className="flex gap-2">
              <select
                value={settings.llm_model_name || ''}
                onChange={e => set('llm_model_name', e.target.value)}
                className="flex-1 px-3 py-2 border rounded-lg text-sm bg-white focus:ring-2 focus:ring-green-500 focus:outline-none"
              >
                {modelsList.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => {
                  const custom = prompt(
                    lang === 'vi' ? 'Nhập tên model thủ công:' : 'Enter custom model name:', 
                    settings.llm_model_name
                  )
                  if (custom) {
                    set('llm_model_name', custom)
                    setAvailableModels(prev => [...prev, custom])
                  }
                }}
                className="px-3 py-2 border rounded-lg text-sm bg-gray-50 text-gray-700 hover:bg-gray-100 font-medium whitespace-nowrap"
              >
                {lang === 'vi' ? 'Khác...' : 'Other...'}
              </button>
            </div>
          ) : (
            <input
              type="text"
              required
              value={settings.llm_model_name || ''}
              onChange={e => set('llm_model_name', e.target.value)}
              placeholder={settings.llm_provider === 'google' ? 'gemini-1.5-flash' : 'gpt-5.5'}
              className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:outline-none"
            />
          )}
        </div>
      </div>

      <div className="flex gap-3 pt-2">
        <button
          type="button"
          disabled={testing}
          onClick={testConnection}
          className="flex-1 py-2.5 border border-green-600 text-green-700 font-semibold rounded-lg text-sm hover:bg-green-50 transition disabled:opacity-50"
        >
          {testing 
            ? (lang === 'vi' ? 'Đang kết nối...' : 'Connecting...') 
            : (lang === 'vi' ? '🔌 Thử kết nối & Tải model' : '🔌 Test Connection & Load Models')}
        </button>

        <button
          type="submit"
          disabled={saving}
          className="flex-1 py-2.5 bg-green-600 text-white rounded-lg text-sm font-semibold hover:bg-green-700 transition disabled:opacity-50"
        >
          {saving 
            ? (lang === 'vi' ? 'Đang lưu...' : 'Saving...') 
            : (lang === 'vi' ? 'Lưu cấu hình Model' : 'Save Model Settings')}
        </button>
      </div>
    </form>
  )
}

function MobileAppsAdmin({ token, lang, onConfigUpdated }) {
  const [iosUrl, setIosUrl] = useState('')
  const [androidUrl, setAndroidUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const fetchMobileSettings = () => {
    setLoading(true)
    api(token).get('/api/v1/admin/settings')
      .then(r => {
        setIosUrl(r.data.app_ios_url || '')
        setAndroidUrl(r.data.app_android_url || '')
      })
      .catch(e => setError(e.response?.data?.detail || 'Failed to fetch settings'))
      .finally(() => setLoading(false))
  }

  useEffect(fetchMobileSettings, [])

  const save = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    setError('')
    try {
      await api(token).put('/api/v1/admin/settings', {
        app_ios_url: iosUrl.trim(),
        app_android_url: androidUrl.trim(),
      })
      setMessage(lang === 'vi' ? '✅ Đã lưu cấu hình link Mobile App thành công!' : '✅ Mobile app download links saved successfully!')
      if (onConfigUpdated) {
        onConfigUpdated()
      }
      fetchMobileSettings()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save mobile settings')
    } finally {
      setSaving(false)
    }
  }

  const resetToDefaults = () => {
    setIosUrl('https://apps.apple.com/app/plantdoctor')
    setAndroidUrl('https://benhcay.tuaf.edu.vn/plantdoctor.apk')
  }

  const testOpenLink = (url) => {
    const trimmed = (url || '').trim()
    if (!trimmed || trimmed === '#') {
      alert(lang === 'vi' ? 'Chưa có link hoặc link đang để #' : 'No valid URL configured or set to #')
      return
    }
    window.open(trimmed.startsWith('http') ? trimmed : `https://${trimmed}`, '_blank')
  }

  if (loading) return <p className="text-gray-400">Loading...</p>

  const hasIos = iosUrl && iosUrl.trim() !== '#' && iosUrl.trim() !== ''
  const hasAndroid = androidUrl && androidUrl.trim() !== '#' && androidUrl.trim() !== ''

  return (
    <form onSubmit={save} className="space-y-5 max-w-2xl bg-white p-6 border rounded-xl shadow-sm">
      <div className="flex justify-between items-center border-b pb-3">
        <div>
          <h3 className="font-bold text-gray-900 text-base">
            📱 {lang === 'vi' ? 'Quản lý Link Tải Ứng Dụng Di Động' : 'Mobile App Download Links'}
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {lang === 'vi' 
              ? 'Tùy chỉnh link tải App Store và Android hiển thị ở chân trang (Footer)'
              : 'Configure App Store and Android download links displayed in the web footer'}
          </p>
        </div>
        <button
          type="button"
          onClick={resetToDefaults}
          className="text-xs text-blue-600 hover:text-blue-800 font-medium underline"
        >
          {lang === 'vi' ? 'Mặc định' : 'Reset default'}
        </button>
      </div>

      {message && <div className="p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm font-medium">{message}</div>}
      {error && <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm font-medium">{error}</div>}

      <div className="space-y-4">
        {/* iOS */}
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100 space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-bold text-gray-800 flex items-center gap-1.5">
              🍎 {lang === 'vi' ? 'Link Apple App Store (iOS)' : 'Apple App Store URL (iOS)'}
            </label>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${hasIos ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'}`}>
              {hasIos ? (lang === 'vi' ? 'Đang hoạt động' : 'Active') : (lang === 'vi' ? 'Chưa có (Sắp có)' : 'Pending')}
            </span>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={iosUrl}
              onChange={e => setIosUrl(e.target.value)}
              placeholder="https://apps.apple.com/app/plantdoctor"
              className="flex-1 px-3 py-2 border rounded-lg text-sm bg-white focus:ring-2 focus:ring-green-500 focus:outline-none"
            />
            <button
              type="button"
              onClick={() => testOpenLink(iosUrl)}
              className="px-3 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg text-xs hover:bg-gray-100 font-medium whitespace-nowrap"
            >
              🔗 {lang === 'vi' ? 'Mở thử' : 'Test Link'}
            </button>
          </div>
          <p className="text-gray-500 text-[11px]">
            {lang === 'vi'
              ? '💡 Link trên Apple App Store hoặc TestFlight. Để trống hoặc nhập # nếu chưa phát hành.'
              : '💡 Apple App Store or TestFlight link. Leave blank or # if not yet published.'}
          </p>
        </div>

        {/* Android */}
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100 space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-bold text-gray-800 flex items-center gap-1.5">
              🤖 {lang === 'vi' ? 'Link Android (Google Play / File APK)' : 'Android URL (Google Play / APK)'}
            </label>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${hasAndroid ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'}`}>
              {hasAndroid ? (lang === 'vi' ? 'Đang hoạt động' : 'Active') : (lang === 'vi' ? 'Chưa có (Sắp có)' : 'Pending')}
            </span>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={androidUrl}
              onChange={e => setAndroidUrl(e.target.value)}
              placeholder="https://benhcay.tuaf.edu.vn/plantdoctor.apk"
              className="flex-1 px-3 py-2 border rounded-lg text-sm bg-white focus:ring-2 focus:ring-green-500 focus:outline-none"
            />
            <button
              type="button"
              onClick={() => testOpenLink(androidUrl)}
              className="px-3 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg text-xs hover:bg-gray-100 font-medium whitespace-nowrap"
            >
              🔗 {lang === 'vi' ? 'Mở thử' : 'Test Link'}
            </button>
          </div>
          <p className="text-gray-500 text-[11px]">
            {lang === 'vi'
              ? '💡 Đường dẫn tải trực tiếp file .apk hoặc link ứng dụng trên Google Play Store.'
              : '💡 Direct .apk download URL or Google Play Store application link.'}
          </p>
        </div>

        {/* Live Preview of Web Footer */}
        <div className="p-4 bg-white border border-dashed border-gray-300 rounded-xl space-y-2">
          <p className="text-xs font-bold text-gray-700">
            👁️ {lang === 'vi' ? 'Xem trước hiển thị nút tải ở Footer Web:' : 'Live Preview (Web Footer Buttons):'}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2.5 p-3 bg-gray-50 rounded-lg border">
            {hasIos ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-black text-white rounded-lg text-xs font-medium shadow-sm">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
                App Store
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 text-gray-400 rounded-lg text-xs font-medium cursor-not-allowed">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
                App Store (Sắp có)
              </span>
            )}

            {hasAndroid ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-700 text-white rounded-lg text-xs font-medium shadow-sm">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M17.523 2.226l1.392-2.415a.4.4 0 00-.692-.4l-1.41 2.446C15.742 1.312 14.58.96 13.32.96c-1.26 0-2.422.352-3.493.897L8.417-.589a.4.4 0 00-.692.4l1.392 2.415C6.82 3.528 5.28 5.748 5.28 8.32h16.08c0-2.572-1.54-4.792-3.837-6.094zM9.6 6.4a.8.8 0 110-1.6.8.8 0 010 1.6zm7.44 0a.8.8 0 110-1.6.8.8 0 010 1.6zM5.28 9.6v7.92a1.2 1.2 0 001.2 1.2h1.2v3.36a1.2 1.2 0 002.4 0v-3.36h3.48v3.36a1.2 1.2 0 002.4 0v-3.36h1.2a1.2 1.2 0 001.2-1.2V9.6H5.28zM3.12 9.6a1.2 1.2 0 00-1.2 1.2v5.76a1.2 1.2 0 002.4 0V10.8a1.2 1.2 0 00-1.2-1.2zm20.4 0a1.2 1.2 0 00-1.2 1.2v5.76a1.2 1.2 0 002.4 0V10.8a1.2 1.2 0 00-1.2-1.2z"/></svg>
                Android (APK / CH Play)
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 text-gray-400 rounded-lg text-xs font-medium cursor-not-allowed">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M17.523 2.226l1.392-2.415a.4.4 0 00-.692-.4l-1.41 2.446C15.742 1.312 14.58.96 13.32.96c-1.26 0-2.422.352-3.493.897L8.417-.589a.4.4 0 00-.692.4l1.392 2.415C6.82 3.528 5.28 5.748 5.28 8.32h16.08c0-2.572-1.54-4.792-3.837-6.094zM9.6 6.4a.8.8 0 110-1.6.8.8 0 010 1.6zm7.44 0a.8.8 0 110-1.6.8.8 0 010 1.6zM5.28 9.6v7.92a1.2 1.2 0 001.2 1.2h1.2v3.36a1.2 1.2 0 002.4 0v-3.36h3.48v3.36a1.2 1.2 0 002.4 0v-3.36h1.2a1.2 1.2 0 001.2-1.2V9.6H5.28zM3.12 9.6a1.2 1.2 0 00-1.2 1.2v5.76a1.2 1.2 0 002.4 0V10.8a1.2 1.2 0 00-1.2-1.2zm20.4 0a1.2 1.2 0 00-1.2 1.2v5.76a1.2 1.2 0 002.4 0V10.8a1.2 1.2 0 00-1.2-1.2z"/></svg>
                Android (Sắp có)
              </span>
            )}
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={saving}
        className="w-full py-3 bg-green-600 text-white rounded-xl text-sm font-bold hover:bg-green-700 transition disabled:opacity-50 shadow-sm"
      >
        {saving 
          ? (lang === 'vi' ? 'Đang lưu...' : 'Saving...') 
          : (lang === 'vi' ? '💾 Lưu cấu hình link Mobile App' : '💾 Save Mobile App Links')}
      </button>
    </form>
  )
}
