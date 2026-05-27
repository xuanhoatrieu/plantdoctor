import { useState, useEffect } from 'react'
import { useAuth } from './AuthContext'
import axios from 'axios'

function api(token) {
  return axios.create({ headers: { Authorization: `Bearer ${token}` } })
}

export default function AdminView({ lang }) {
  const { token } = useAuth()
  const [tab, setTab] = useState('diseases')

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold text-gray-900">⚙️ {lang === 'vi' ? 'Quản trị hệ thống' : 'Admin Panel'}</h2>
      <div className="flex gap-2 flex-wrap">
        {[
          { id: 'diseases', label: '📚 Thư viện bệnh' },
          { id: 'pesticides', label: '🧪 Thuốc BVTV' },
          { id: 'users', label: '👥 Người dùng' },
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
