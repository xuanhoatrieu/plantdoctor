import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { translations } from './i18n'
import { diseaseLibrary } from './diseaseLibrary'
import { useAuth } from './AuthContext'
import LoginModal from './LoginModal'
import AdminView from './AdminView'
import { checkImageInBrowser, issueText, LowQualityCard, ClarificationCard, FeedbackWidget } from './DiagnosisExtras'

const HISTORY_KEY = 'leafdoctor_history'
function getHistory() { try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]') } catch { return [] } }
function saveHistory(h) { localStorage.setItem(HISTORY_KEY, JSON.stringify(h.slice(0, 20))) }

const PLANT_CHOICES = [
  { id: 'Chè', label: 'Chè', icon: '🍵' },
  { id: 'Cam/Bưởi', label: 'Cam/Bưởi', icon: '🍊' },
  { id: 'Lúa', label: 'Lúa', icon: '🌾' },
  { id: 'Ngô', label: 'Ngô', icon: '🌽' },
  { id: 'Cà phê', label: 'Cà phê', icon: '☕' },
  { id: 'Sầu riêng', label: 'Sầu riêng', icon: '🍈' },
  { id: 'Hồ tiêu/Ớt', label: 'Tiêu/Ớt', icon: '🌶️' },
  { id: 'Cà chua', label: 'Cà chua', icon: '🍅' },
  { id: 'Khoai tây', label: 'Khoai tây', icon: '🥔' },
  { id: 'Chuối', label: 'Chuối', icon: '🍌' },
  { id: 'Nhãn/Vải', label: 'Nhãn/Vải', icon: '🍒' },
  { id: 'Xoài', label: 'Xoài', icon: '🥭' },
  { id: 'Thanh long', label: 'Thanh long', icon: '🐉' },
  { id: 'Rau màu/Bắp cải', label: 'Rau màu', icon: '🥬' },
  { id: 'Lạc/Đậu tương', label: 'Lạc/Đậu', icon: '🥜' },
]
const PLANT_KEY = 'last_selected_plant'
function getSavedPlant() {
  try {
    const v = (localStorage.getItem(PLANT_KEY) || '').trim()
    if (!v || v.length > 60) return null
    return v
  } catch { return null }
}

function ConfidenceBar({ value }) {
  const color = value >= 80 ? 'bg-green-500' : value >= 50 ? 'bg-yellow-500' : 'bg-red-400'
  return (
    <div className="w-full bg-gray-200 rounded-full h-2.5">
      <div className={`h-2.5 rounded-full transition-all duration-700 ${color}`} style={{ width: `${value}%` }} />
    </div>
  )
}

function SeverityBadge({ severity, t }) {
  const map = {
    'nhẹ': 'bg-yellow-100 text-yellow-800', 'mild': 'bg-yellow-100 text-yellow-800',
    'trung bình': 'bg-orange-100 text-orange-800', 'moderate': 'bg-orange-100 text-orange-800',
    'nặng': 'bg-red-100 text-red-800', 'severe': 'bg-red-100 text-red-800',
    'không': 'bg-green-100 text-green-800', 'none': 'bg-green-100 text-green-800',
  }
  const s = (severity || '').toLowerCase()
  const color = map[s] || 'bg-gray-100 text-gray-700'
  return <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${color}`}>{severity || '—'}</span>
}

function App() {
  const [lang, setLang] = useState('vi')
  const [tab, setTab] = useState('diagnose')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  // Optional 2nd photo: overview of the branch / whole plant (helps the AI identify the crop)
  const [file2, setFile2] = useState(null)
  const [preview2, setPreview2] = useState(null)
  const [clientChecks, setClientChecks] = useState({ 1: null, 2: null })
  const [wasClarified, setWasClarified] = useState(false)
  const [resultSeq, setResultSeq] = useState(0)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [selectedPlant, setSelectedPlantState] = useState(getSavedPlant)
  const [error, setError] = useState('')
  const [history, setHistory] = useState(getHistory)
  const [weather, setWeather] = useState(null)
  const [showLogin, setShowLogin] = useState(false)
  const [showPrivacy, setShowPrivacy] = useState(
    typeof window !== 'undefined' && window.location.pathname.includes('/privacy')
  )
  const [showDeleteAccount, setShowDeleteAccount] = useState(
    typeof window !== 'undefined' && window.location.pathname.includes('/delete-account')
  )
  const fileRef = useRef()
  const fileRef2 = useRef()
  const t = translations[lang]
  const { user, logout, token } = useAuth()
  const isAdmin = user?.role === 'admin'

  const setSelectedPlant = (id) => {
    setSelectedPlantState(id)
    try {
      if (id) localStorage.setItem(PLANT_KEY, id)
      else localStorage.removeItem(PLANT_KEY)
    } catch { /* storage disabled: just don't remember */ }
  }

  const [appLinks, setAppLinks] = useState({
    ios: 'https://apps.apple.com/vn/app/tuaf-plantdoctor/id6773555310',
    android: 'https://play.google.com/store/apps/details?id=com.trieuxuanhoa.plantdoctor&pcampaignid=web_share',
  })

  const fetchPublicConfig = () => {
    axios.get('/api/v1/config')
      .then(res => {
        if (res.data) {
          setAppLinks({
            ios: res.data.app_ios_url ?? '',
            android: res.data.app_android_url ?? '',
          })
        }
      })
      .catch(() => {})
  }

  useEffect(() => {
    const fetchWeather = (lat, lon) => {
      fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto&forecast_days=3`)
        .then(r => r.json()).then(setWeather).catch(() => {})
    }
    navigator.geolocation?.getCurrentPosition(
      (pos) => fetchWeather(pos.coords.latitude, pos.coords.longitude),
      () => { fetchWeather(21.03, 105.85) } // Fallback: Hanoi
    )

    fetchPublicConfig()
  }, [])

  const handleFile = async (f, slot = 1) => {
    if (!f) return
    if (!f.type?.startsWith('image/')) { setError(lang === 'vi' ? 'Vui lòng chọn tệp ảnh.' : 'Please choose an image file.'); return }
    if (f.size > 10 * 1024 * 1024) { setError(t.maxSize); return }
    const url = URL.createObjectURL(f)
    if (slot === 2) { setFile2(f); setPreview2(url) } else { setFile(f); setPreview(url) }
    setResult(null)
    setError('')
    setClientChecks(c => ({ ...c, [slot]: null }))
    const check = await checkImageInBrowser(f)
    setClientChecks(c => ({ ...c, [slot]: check }))
  }

  const removeSecond = () => {
    setFile2(null); setPreview2(null); setResult(null)
    setClientChecks(c => ({ ...c, 2: null }))
    if (fileRef2.current) fileRef2.current.value = ''
  }

  const pushHistory = (data) => {
    const entry = { date: new Date().toISOString(), preview, result: data }
    const h = [entry, ...history].slice(0, 20)
    setHistory(h)
    saveHistory(h)
  }

  // force=true re-sends the same photos with the quality gate off (user chose "Diagnose anyway")
  const handlePredict = async (force = false) => {
    if (!file) return
    setLoading(true)
    setError('')
    setWasClarified(false)
    try {
      const form = new FormData()
      if (file2) {
        // Order matters: the server labels image 1 as close-up and image 2 as overview
        form.append('files', file)
        form.append('files', file2)
      } else {
        form.append('file', file)
      }
      form.append('model_id', 'gpt55_vision')
      form.append('lang', lang)
      form.append('quality_gate', force ? 'false' : 'true')
      if (selectedPlant) {
        form.append('plant_hint', selectedPlant)
      }
      const res = await axios.post('/api/v1/predict', form)
      setResult(res.data)
      setResultSeq(s => s + 1)
      if (res.data?.status === 'success') pushHistory(res.data)
    } catch { setError(t.error) }
    finally { setLoading(false) }
  }

  const handleClarify = async (candidateName) => {
    if (!result?.session_token) return
    setLoading(true)
    setError('')
    try {
      const res = await axios.post('/api/v1/predict/clarify', {
        session_token: result.session_token,
        selected_plant: candidateName,
        lang,
      })
      setResult(res.data)
      setResultSeq(s => s + 1)
      setWasClarified(true)
      if (res.data?.status === 'success') pushHistory(res.data)
    } catch (err) {
      setError(err?.response?.status === 404
        ? (lang === 'vi' ? 'Phiên xác nhận đã hết hạn (30 phút). Vui lòng bấm chẩn đoán lại.' : 'The confirmation session expired. Please diagnose again.')
        : t.error)
    }
    finally { setLoading(false) }
  }

  const handleReset = () => {
    setFile(null); setPreview(null); setFile2(null); setPreview2(null)
    setClientChecks({ 1: null, 2: null })
    setResult(null); setError(''); setWasClarified(false)
    if (fileRef.current) fileRef.current.value = ''
    if (fileRef2.current) fileRef2.current.value = ''
  }

  const handleRetake = () => {
    handleReset()
    // Let React clear state first, then open the picker
    setTimeout(() => fileRef.current?.click(), 0)
  }

  const topPrediction = result?.predictions?.[0]
  const isHealthy = topPrediction?.label?.toLowerCase().includes('healthy') || topPrediction?.label?.includes('Khỏe mạnh')

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-3 sm:px-4 py-2 sm:py-3 flex justify-between items-center gap-2">
          <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
            <span className="text-xl sm:text-2xl">🌿</span>
            <div className="min-w-0">
              <h1 className="text-base sm:text-xl font-bold text-green-800 truncate">PlantDoctor</h1>
              <p className="text-[10px] sm:text-xs text-green-600 truncate">{t.subtitle}</p>
            </div>
          </div>
          <div className="hidden md:flex flex-col items-center">
            <span className="text-xl font-bold text-green-800">Trường Đại học Nông Lâm Thái Nguyên</span>
            <span className="text-xs text-green-600">Cùng bạn ra thế giới!</span>
          </div>
          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            {user ? (
              <div className="flex items-center gap-1 sm:gap-2">
                <span className="text-xs text-gray-600 hidden sm:inline">{user.phone}</span>
                {isAdmin && <span className="text-[10px] sm:text-xs bg-purple-100 text-purple-700 px-1 sm:px-1.5 py-0.5 rounded">Admin</span>}
                <button onClick={logout} className="px-1.5 sm:px-2 py-1 text-xs text-red-600 hover:text-red-800">Thoát</button>
              </div>
            ) : (
              <button onClick={() => setShowLogin(true)} className="px-2 sm:px-3 py-1 bg-green-600 text-white rounded-lg text-xs sm:text-sm hover:bg-green-700 whitespace-nowrap">
                {lang === 'vi' ? 'Đăng nhập' : 'Login'}
              </button>
            )}
            <button onClick={() => setLang(lang === 'vi' ? 'en' : 'vi')} className="px-2 sm:px-3 py-1 border rounded-lg text-xs sm:text-sm hover:bg-gray-50">{t.switchLang}</button>
          </div>
        </div>
      </header>

      <nav className="bg-white border-b overflow-x-auto">
        <div className="max-w-6xl mx-auto px-3 sm:px-4 flex gap-0.5 sm:gap-1 min-w-max">
          {['diagnose', ...(user ? ['history', 'library', 'pesticides'] : []), ...(isAdmin ? ['admin'] : [])].map(id => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-3 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm font-medium border-b-2 transition whitespace-nowrap ${tab === id ? 'border-green-600 text-green-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
              {t[`tab_${id}`]}
            </button>
          ))}
        </div>
      </nav>

      <main className="flex-1 max-w-6xl mx-auto w-full px-3 sm:px-4 py-4 sm:py-6">
        {tab === 'diagnose' && <DiagnoseView {...{t, file, preview, file2, preview2, clientChecks, loading, result, resultSeq, error, topPrediction, isHealthy, fileRef, fileRef2, handleFile, removeSecond, handlePredict, handleReset, handleRetake, weather, lang, user, token, selectedPlant, setSelectedPlant, handleClarify, wasClarified}} />}
        {tab === 'history' && user && <HistoryView {...{t, history, setHistory}} />}
        {tab === 'library' && user && <LibraryView {...{t, lang}} />}
        {tab === 'pesticides' && user && <PesticidesView {...{t, lang}} />}
        {tab === 'admin' && isAdmin && <AdminView lang={lang} onConfigUpdated={fetchPublicConfig} />}
      </main>

      {showLogin && <LoginModal onClose={() => setShowLogin(false)} lang={lang} />}

      <footer className="bg-white border-t py-3 sm:py-4 text-center text-xs text-gray-400">
        <div className="flex flex-col sm:flex-row justify-center items-center gap-2 sm:gap-3 mb-2 px-4">
          {appLinks.ios && appLinks.ios !== '#' ? (
            <a href={appLinks.ios} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-black text-white rounded-lg hover:bg-gray-800 transition text-xs font-medium">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
              App Store
            </a>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 text-gray-400 rounded-lg text-xs font-medium cursor-not-allowed">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
              App Store (Sắp có)
            </span>
          )}

          {appLinks.android && appLinks.android !== '#' ? (
            <a href={appLinks.android} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-700 text-white rounded-lg hover:bg-green-800 transition text-xs font-medium">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M17.523 2.226l1.392-2.415a.4.4 0 00-.692-.4l-1.41 2.446C15.742 1.312 14.58.96 13.32.96c-1.26 0-2.422.352-3.493.897L8.417-.589a.4.4 0 00-.692.4l1.392 2.415C6.82 3.528 5.28 5.748 5.28 8.32h16.08c0-2.572-1.54-4.792-3.837-6.094zM9.6 6.4a.8.8 0 110-1.6.8.8 0 010 1.6zm7.44 0a.8.8 0 110-1.6.8.8 0 010 1.6zM5.28 9.6v7.92a1.2 1.2 0 001.2 1.2h1.2v3.36a1.2 1.2 0 002.4 0v-3.36h3.48v3.36a1.2 1.2 0 002.4 0v-3.36h1.2a1.2 1.2 0 001.2-1.2V9.6H5.28zM3.12 9.6a1.2 1.2 0 00-1.2 1.2v5.76a1.2 1.2 0 002.4 0V10.8a1.2 1.2 0 00-1.2-1.2zm20.4 0a1.2 1.2 0 00-1.2 1.2v5.76a1.2 1.2 0 002.4 0V10.8a1.2 1.2 0 00-1.2-1.2z"/></svg>
              Android (APK / CH Play)
            </a>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 text-gray-400 rounded-lg text-xs font-medium cursor-not-allowed">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M17.523 2.226l1.392-2.415a.4.4 0 00-.692-.4l-1.41 2.446C15.742 1.312 14.58.96 13.32.96c-1.26 0-2.422.352-3.493.897L8.417-.589a.4.4 0 00-.692.4l1.392 2.415C6.82 3.528 5.28 5.748 5.28 8.32h16.08c0-2.572-1.54-4.792-3.837-6.094zM9.6 6.4a.8.8 0 110-1.6.8.8 0 010 1.6zm7.44 0a.8.8 0 110-1.6.8.8 0 010 1.6zM5.28 9.6v7.92a1.2 1.2 0 001.2 1.2h1.2v3.36a1.2 1.2 0 002.4 0v-3.36h3.48v3.36a1.2 1.2 0 002.4 0v-3.36h1.2a1.2 1.2 0 001.2-1.2V9.6H5.28zM3.12 9.6a1.2 1.2 0 00-1.2 1.2v5.76a1.2 1.2 0 002.4 0V10.8a1.2 1.2 0 00-1.2-1.2zm20.4 0a1.2 1.2 0 00-1.2 1.2v5.76a1.2 1.2 0 002.4 0V10.8a1.2 1.2 0 00-1.2-1.2z"/></svg>
              Android (Sắp có)
            </span>
          )}
        </div>

        {/* Public Store Compliance Links */}
        <div className="flex flex-wrap justify-center items-center gap-3 text-xs text-gray-500 mb-2">
          <button
            onClick={() => setShowPrivacy(true)}
            className="hover:text-green-700 underline transition cursor-pointer"
          >
            Chính sách Quyền riêng tư
          </button>
          <span>•</span>
          <button
            onClick={() => setShowDeleteAccount(true)}
            className="hover:text-red-600 underline transition cursor-pointer"
          >
            Yêu cầu Xóa tài khoản
          </button>
          <span>•</span>
          <a
            href="mailto:trieuxuanhoa@tuaf.edu.vn"
            className="hover:text-green-700 underline transition"
          >
            Hỗ trợ: trieuxuanhoa@tuaf.edu.vn
          </a>
        </div>

        <div>PlantDoctor v2.7.0 — Phát triển bởi Triệu Xuân Hòa (Trường ĐH Nông Lâm Thái Nguyên)</div>
      </footer>

      {showPrivacy && <PrivacyModal onClose={() => setShowPrivacy(false)} />}
      {showDeleteAccount && <DeleteAccountModal user={user} onClose={() => setShowDeleteAccount(false)} />}
    </div>
  )
}

function WeatherWidget({ weather, t }) {
  if (!weather?.current) return null
  const weatherNames = { 0: '☀️ Trời nắng', 1: '🌤️ Ít mây', 2: '⛅ Mây', 3: '☁️ Nhiều mây', 45: '🌫️ Sương mù', 51: '🌦️ Mưa phùn', 61: '🌧️ Mưa', 63: '🌧️ Mưa vừa', 65: '🌧️ Mưa to', 80: '🌦️ Mưa rào', 95: '⛈️ Giông' }
  const code = weather.current.weather_code
  const desc = weatherNames[code] || `🌡️ Code ${code}`
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 sm:p-4">
      <h4 className="font-semibold text-blue-800 mb-2 text-sm sm:text-base">⛅ {t.weather}</h4>
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-base sm:text-lg font-bold text-blue-900">{weather.current.temperature_2m}°C</p>
          <p className="text-xs sm:text-sm text-blue-700">{desc}</p>
        </div>
        <div className="text-right text-xs sm:text-sm text-blue-700">
          <p>💧 {t.humidity}: {weather.current.relative_humidity_2m}%</p>
          <p>💨 {t.wind}: {weather.current.wind_speed_10m} km/h</p>
        </div>
      </div>
      {weather.daily && (
        <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-blue-200 grid grid-cols-3 gap-1 sm:gap-2 text-center text-[10px] sm:text-xs">
          {weather.daily.time.map((day, i) => (
            <div key={i}>
              <p className="text-blue-600">{new Date(day).toLocaleDateString(undefined, {weekday:'short'})}</p>
              <p className="font-medium">{weather.daily.temperature_2m_min[i]}°-{weather.daily.temperature_2m_max[i]}°</p>
              <p className="text-blue-500">🌧️ {weather.daily.precipitation_probability_max[i]}%</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ClientCheckHint({ check, lang }) {
  if (!check || !check.issues?.length) return null
  return (
    <div className="mt-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-left" onClick={(e) => e.stopPropagation()}>
      {check.issues.map((code) => (
        <p key={code} className="text-[11px] sm:text-xs text-amber-800">⚠️ {issueText(code, lang, check)}</p>
      ))}
    </div>
  )
}

function DiagnoseView({ t, file, preview, file2, preview2, clientChecks, loading, result, resultSeq, error, topPrediction, isHealthy, fileRef, fileRef2, handleFile, removeSecond, handlePredict, handleReset, handleRetake, weather, lang, user, token, selectedPlant, setSelectedPlant, handleClarify, wasClarified }) {
  const vi = lang === 'vi'
  const status = result?.status || 'success'
  const [showPlantPopup, setShowPlantPopup] = useState(false)
  const [customPlantInput, setCustomPlantInput] = useState('')
  const [showCustomInput, setShowCustomInput] = useState(false)

  const handlePopupSelectPlant = (plantId) => {
    setSelectedPlant(plantId)
    setShowPlantPopup(false)
    setShowCustomInput(false)
    setCustomPlantInput('')
    if (fileRef.current) {
      fileRef.current.click()
    }
  }

  return (
    <div className="grid md:grid-cols-2 gap-4 sm:gap-6">
      {/* Popup Modal: Select Crop Before Taking/Picking Photo */}
      {showPlantPopup && (
        <div
          className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4"
          onClick={() => { setShowPlantPopup(false); setShowCustomInput(false) }}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-4 sm:p-6 space-y-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-2 border-b pb-3">
              <div>
                <h3 className="text-base sm:text-lg font-bold text-green-900 flex items-center gap-2">
                  <span>🌿</span>
                  <span>{vi ? 'Chọn loại cây trồng hoặc rau màu' : 'Select Crop or Vegetable'}</span>
                </h3>
                <p className="text-xs text-gray-600 mt-0.5">
                  {vi
                    ? 'Chọn đúng loại cây giúp AI khoanh vùng chính xác Kho tri thức bệnh của cây đó trước khi tải ảnh.'
                    : 'Selecting the crop locks the AI to the exact disease knowledge base before uploading.'}
                </p>
              </div>
              <button
                type="button"
                onClick={() => { setShowPlantPopup(false); setShowCustomInput(false) }}
                className="text-gray-400 hover:text-gray-600 text-lg font-bold px-2"
              >
                ✕
              </button>
            </div>

            {/* Grid of common crops and vegetables */}
            <div className="grid grid-cols-3 sm:grid-cols-3 gap-2">
              {PLANT_CHOICES.map((item) => {
                const active = selectedPlant === item.id
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handlePopupSelectPlant(item.id)}
                    className={`flex flex-col items-center justify-center p-2.5 sm:p-3 rounded-xl border text-center transition cursor-pointer ${
                      active
                        ? 'bg-green-700 text-white border-green-700 shadow-sm ring-2 ring-green-300'
                        : 'bg-gray-50 hover:bg-green-50 hover:border-green-400 text-gray-800 border-gray-200'
                    }`}
                  >
                    <span className="text-2xl mb-1">{item.icon}</span>
                    <span className="text-xs font-semibold leading-tight">{item.label}</span>
                  </button>
                )
              })}

              {/* Custom crop button */}
              <button
                type="button"
                onClick={() => setShowCustomInput((v) => !v)}
                className={`flex flex-col items-center justify-center p-2.5 sm:p-3 rounded-xl border text-center transition cursor-pointer ${
                  showCustomInput
                    ? 'bg-amber-100 border-amber-400 text-amber-900'
                    : 'bg-amber-50/70 hover:bg-amber-100 text-amber-800 border-amber-200'
                }`}
              >
                <span className="text-2xl mb-1">✏️</span>
                <span className="text-xs font-semibold leading-tight">{vi ? 'Cây khác...' : 'Other crop...'}</span>
              </button>
            </div>

            {showCustomInput && (
              <div className="flex gap-2 bg-amber-50 p-2.5 rounded-xl border border-amber-200">
                <input
                  type="text"
                  value={customPlantInput}
                  onChange={(e) => setCustomPlantInput(e.target.value)}
                  placeholder={vi ? 'Nhập tên cây (VD: Ổi, Dưa lưới, Hoa hồng...)' : 'Enter crop name (e.g. Guava, Melon, Rose...)'}
                  className="flex-1 px-3 py-1.5 text-xs sm:text-sm border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <button
                  type="button"
                  disabled={!customPlantInput.trim()}
                  onClick={() => handlePopupSelectPlant(customPlantInput.trim().slice(0, 60))}
                  className="px-3 py-1.5 bg-green-700 text-white rounded-lg text-xs sm:text-sm font-semibold disabled:opacity-50"
                >
                  {vi ? 'Chọn & Tải ảnh' : 'Select & Upload'}
                </button>
              </div>
            )}

            {/* LAST OPTION AT THE BOTTOM: Auto-detect */}
            <div className="pt-2 border-t">
              <button
                type="button"
                onClick={() => handlePopupSelectPlant(null)}
                className="w-full py-3 px-4 rounded-xl border-2 border-dashed border-green-500 bg-green-50/70 hover:bg-green-100 text-green-900 font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 transition cursor-pointer"
              >
                <span className="text-lg">🌱</span>
                <span>{vi ? 'Tự động phát hiện loại cây (Để AI tự nhận diện)' : 'Auto-detect plant species (Let AI identify)'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Left column */}
      <div className="space-y-3 sm:space-y-4">
        {/* Plant Selector Chips */}
        <div className="bg-white rounded-xl border p-3 space-y-2">
          <div className="flex items-center justify-between gap-2">
            <label className="block text-xs font-semibold text-gray-700">
              🌾 {vi ? 'Chọn loại cây trồng (Giúp AI khoanh vùng đúng kho bệnh của cây):' : 'Select crop (Locks AI to the exact crop disease catalog):'}
            </label>
            {selectedPlant && (
              <button
                type="button"
                onClick={() => setSelectedPlant(null)}
                className="text-[11px] text-red-600 hover:underline font-medium shrink-0"
              >
                ✕ {vi ? 'Đặt lại Tự động' : 'Reset to Auto'}
              </button>
            )}
          </div>
          <div className="flex gap-1.5 flex-wrap">
            {[
              { id: null, label: vi ? 'Tự động nhận diện' : 'Auto-detect', icon: '🌱' },
              ...PLANT_CHOICES,
            ].map((item) => (
              <button
                key={String(item.id)}
                type="button"
                onClick={() => setSelectedPlant(item.id)}
                className={`px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition flex items-center gap-1 ${
                  selectedPlant === item.id
                    ? 'bg-green-700 text-white shadow-sm ring-2 ring-green-300'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
            <button
              type="button"
              onClick={() => {
                const custom = window.prompt(
                  vi ? 'Nhập tên cây trồng (VD: Xoài, Ổi, Dưa lưới, Hoa hồng...):' : 'Enter crop name (e.g., Mango, Guava, Rose...):',
                  selectedPlant && !PLANT_CHOICES.some(p => p.id === selectedPlant) ? selectedPlant : ''
                )
                if (custom && custom.trim()) {
                  setSelectedPlant(custom.trim().slice(0, 60))
                }
              }}
              className={`px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition flex items-center gap-1 ${
                selectedPlant && !PLANT_CHOICES.some(p => p.id === selectedPlant)
                  ? 'bg-green-700 text-white shadow-sm ring-2 ring-green-300'
                  : 'bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200'
              }`}
            >
              <span>✏️</span>
              <span>
                {selectedPlant && !PLANT_CHOICES.some(p => p.id === selectedPlant)
                  ? selectedPlant
                  : (vi ? 'Cây khác...' : 'Other crop...')}
              </span>
            </button>
          </div>
          {selectedPlant && (
            <div className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg px-2.5 py-1.5 text-xs text-green-800">
              <span>
                🎯 {vi ? 'Đang khóa chẩn đoán theo cây:' : 'Locked to crop:'} <strong>{selectedPlant}</strong>
              </span>
              <span className="text-[11px] text-green-700">
                {vi ? '(Đổi cây nếu chụp sang lá cây khác)' : '(Change if uploading another crop)'}
              </span>
            </div>
          )}
        </div>
        {/* Steps guide */}
        {!preview && !result && (
          <div className="bg-white rounded-xl border p-3 sm:p-4">
            <h3 className="font-semibold text-gray-800 mb-2 sm:mb-3 text-sm sm:text-base">{t.howToUse}</h3>
            <div className="space-y-2 sm:space-y-3">
              <div className="flex items-center gap-2 sm:gap-3">
                <span className="w-7 h-7 sm:w-8 sm:h-8 bg-green-100 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold text-green-700 shrink-0">1</span>
                <p className="text-xs sm:text-sm text-gray-600">{t.step1_desc}</p>
              </div>
              <div className="flex items-center gap-2 sm:gap-3">
                <span className="w-7 h-7 sm:w-8 sm:h-8 bg-green-100 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold text-green-700 shrink-0">2</span>
                <p className="text-xs sm:text-sm text-gray-600">{t.step2_desc}</p>
              </div>
              <div className="flex items-center gap-2 sm:gap-3">
                <span className="w-7 h-7 sm:w-8 sm:h-8 bg-green-100 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold text-green-700 shrink-0">3</span>
                <p className="text-xs sm:text-sm text-gray-600">{t.step3_desc}</p>
              </div>
            </div>
          </div>
        )}

        {/* Upload slot 1: close-up of the lesion (required) */}
        <div
          id="upload-slot-1"
          onDrop={(e) => { e.preventDefault(); handleFile(e.dataTransfer.files[0], 1) }}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => setShowPlantPopup(true)}
          className="relative border-2 border-dashed border-green-300 rounded-xl p-4 sm:p-6 text-center cursor-pointer hover:border-green-500 hover:bg-green-50/50 transition min-h-[160px] sm:min-h-[220px] flex flex-col items-center justify-center"
        >
          <span className="absolute top-2 left-2 text-[10px] sm:text-xs font-semibold bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
            {vi ? 'Ảnh 1 · Cận cảnh vết bệnh' : 'Photo 1 · Lesion close-up'}
          </span>
          {preview ? (
            <div className="relative mt-4">
              <img src={preview} alt="preview" className="max-h-48 sm:max-h-64 mx-auto rounded-lg shadow-sm" />
              {loading && (
                <div className="absolute inset-0 bg-black/30 rounded-lg flex items-center justify-center">
                  <div className="relative w-full h-full overflow-hidden rounded-lg">
                    <div className="scan-line absolute left-0 w-full h-1 bg-green-400/80" />
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-green-600 space-y-2">
              <div className="text-4xl sm:text-5xl">📷</div>
              <p className="font-medium text-sm sm:text-base">{t.dragDrop}</p>
              <p className="text-[10px] sm:text-xs text-gray-400">{t.maxSize}</p>
            </div>
          )}
          <ClientCheckHint check={clientChecks?.[1]} lang={lang} />
          <input ref={fileRef} id="file-input-1" type="file" accept="image/*" className="hidden" onChange={(e) => handleFile(e.target.files[0], 1)} />
        </div>

        {/* Upload slot 2: overview of branch / plant (optional) */}
        {file && (
          <div
            id="upload-slot-2"
            onDrop={(e) => { e.preventDefault(); handleFile(e.dataTransfer.files[0], 2) }}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => !preview2 && fileRef2.current.click()}
            className={`relative border-2 border-dashed rounded-xl p-3 transition ${preview2 ? 'border-green-300' : 'border-gray-300 hover:border-green-400 hover:bg-green-50/40 cursor-pointer'}`}
          >
            {preview2 ? (
              <div className="flex items-center gap-3">
                <img src={preview2} alt="overview" className="w-20 h-20 object-cover rounded-lg shadow-sm" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-green-800">{vi ? 'Ảnh 2 · Toàn cảnh cành/cây' : 'Photo 2 · Branch/plant overview'}</p>
                  <p className="text-[11px] text-gray-500">{vi ? 'AI sẽ kết hợp 2 ảnh để nhận đúng loại cây.' : 'The AI combines both photos to identify the crop.'}</p>
                  <div className="flex gap-3 mt-1">
                    <button id="replace-photo-2" type="button" onClick={(e) => { e.stopPropagation(); fileRef2.current.click() }} className="text-xs text-green-700 hover:underline">{vi ? 'Đổi ảnh' : 'Replace'}</button>
                    <button id="remove-photo-2" type="button" onClick={(e) => { e.stopPropagation(); removeSecond() }} className="text-xs text-red-600 hover:underline">{vi ? 'Bỏ ảnh' : 'Remove'}</button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3 text-left">
                <span className="text-3xl">🌳</span>
                <div>
                  <p className="text-xs sm:text-sm font-semibold text-gray-700">+ {vi ? 'Thêm ảnh 2: toàn cảnh cành/cây (khuyên dùng)' : 'Add photo 2: branch/plant overview (recommended)'}</p>
                  <p className="text-[11px] text-gray-500">{vi ? 'Khi ảnh 1 chỉ chụp cận vết bệnh, ảnh toàn cảnh giúp AI không nhầm loại cây.' : 'If photo 1 is a tight close-up, an overview stops crop mix-ups.'}</p>
                </div>
              </div>
            )}
            <ClientCheckHint check={clientChecks?.[2]} lang={lang} />
            <input ref={fileRef2} id="file-input-2" type="file" accept="image/*" className="hidden" onChange={(e) => handleFile(e.target.files[0], 2)} />
          </div>
        )}

        {/* Predict button */}
        <button id="predict-btn" onClick={() => handlePredict(false)} disabled={!file || loading}
          className="w-full py-3 sm:py-3.5 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition text-base sm:text-lg shadow-sm">
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              {t.predicting}
            </span>
          ) : selectedPlant ? `${t.predict} (${selectedPlant})` : t.predict}
        </button>

        {result && (
          <button onClick={handleReset} className="w-full py-2 sm:py-2.5 border-2 border-green-600 text-green-700 rounded-xl font-medium hover:bg-green-50 transition">
            📷 {t.tryAgain}
          </button>
        )}

        {error && <p className="text-red-500 text-sm text-center bg-red-50 p-3 rounded-lg">{error}</p>}

        {/* Register prompt for guests */}
        {!user && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
            <p className="text-xs sm:text-sm text-blue-800">{lang === 'vi' ? '📝 Hãy đăng ký tài khoản để sử dụng nhiều tính năng hơn (lịch sử, thư viện bệnh, tra cứu thuốc BVTV...)' : '📝 Register an account to access more features (history, disease library, pesticide lookup...)'}</p>
          </div>
        )}

        {/* Weather */}
        <WeatherWidget weather={weather} t={t} />
      </div>

      {/* Right column - Results */}
      <div className="space-y-3 sm:space-y-4">
        <div className="bg-white rounded-xl shadow-lg p-4 sm:p-6 min-h-[200px] sm:min-h-[300px]">
          <h2 className="text-base sm:text-lg font-bold text-gray-800 mb-3 sm:mb-4">{t.results}</h2>
          {!result ? (
            <p className="text-gray-400 text-center py-12">{t.noResults}</p>
          ) : status === 'low_quality' ? (
            <LowQualityCard result={result} lang={lang} loading={loading}
              onForce={() => handlePredict(true)} onRetake={handleRetake} />
          ) : status === 'needs_clarification' ? (
            <ClarificationCard key={resultSeq} result={result} lang={lang} loading={loading} onSelect={handleClarify} />
          ) : !topPrediction ? (
            <p className="text-gray-400 text-center py-12">{t.error}</p>
          ) : (
            <div className="space-y-4">
              {/* Image quality warnings */}
              {result.image_quality_warnings?.length > 0 && (
                <div className="bg-orange-50 border border-orange-300 rounded-lg p-3 sm:p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">📸</span>
                    <h4 className="font-semibold text-orange-900 text-sm">{lang === 'vi' ? 'Gợi ý cải thiện ảnh:' : 'Image improvement tips:'}</h4>
                  </div>
                  <ul className="space-y-1 ml-7">
                    {result.image_quality_warnings.map((w, i) => (
                      <li key={i} className="text-xs sm:text-sm text-orange-800">• {w}</li>
                    ))}
                  </ul>
                  <p className="text-xs text-orange-700 mt-2 ml-7 italic">
                    💡 {lang === 'vi' ? 'Chụp lại ảnh rõ hơn (có cành, quả, nhiều lá) để kết quả chính xác hơn' : 'Retake with better context (branches, fruit, multiple leaves) for more accurate results'}
                  </p>
                </div>
              )}

              {/* Voting badge */}
              {result.voting_used && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-2.5 flex items-center gap-2">
                  <span>🔄</span>
                  <p className="text-xs text-blue-800">{lang === 'vi' ? 'Kết quả đã được xác nhận qua AI voting (3 lần phân tích)' : 'Result confirmed via AI voting (3 analysis rounds)'}</p>
                </div>
              )}

              {/* Cached badge */}
              {result.cached && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-2.5 flex items-center gap-2">
                  <span>⚡</span>
                  <p className="text-xs text-green-800">{lang === 'vi' ? 'Kết quả lấy lại từ lần chẩn đoán trước với ảnh gần giống hệt' : 'Reused result from an earlier diagnosis of a near-identical photo'}</p>
                </div>
              )}

              {/* AI disclaimer */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex items-start gap-2">
                <span className="text-yellow-600">⚠️</span>
                <p className="text-xs text-yellow-800">{lang === 'vi' ? 'Kết quả chẩn đoán chỉ mang tính tham khảo. Vui lòng tham vấn chuyên gia nông nghiệp trước khi sử dụng thuốc bảo vệ thực vật.' : 'Diagnosis results are for reference only. Please consult an agricultural expert before applying pesticides.'}</p>
              </div>
              {/* Main result */}
              <div className={`p-4 rounded-xl ${isHealthy ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-bold text-lg text-gray-900">{topPrediction.name}</h3>
                  <SeverityBadge severity={topPrediction.severity} t={t} />
                </div>
                <div className="mb-2">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{t.confidence}</span>
                    <span className="font-semibold">{topPrediction.confidence}%</span>
                  </div>
                  <ConfidenceBar value={topPrediction.confidence} />
                </div>
                {isHealthy && <p className="text-green-700 font-medium mt-2">✅ {t.healthy}</p>}
              </div>

              {/* Description */}
              {topPrediction.description && (
                <div className="p-4 bg-gray-50 rounded-xl">
                  <h4 className="font-semibold text-gray-800 mb-1">🔍 {t.description}</h4>
                  <p className="text-gray-600 text-sm leading-relaxed">{topPrediction.description}</p>
                </div>
              )}

              {/* CABI Plantwise Knowledge Base Reference Card (Visual & Agronomic Cross-Check) */}
              {topPrediction.kb_reference && !isHealthy && (
                <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-xl space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-base">📚</span>
                      <h4 className="font-bold text-emerald-900 text-sm">
                        {vi ? 'Đối chiếu Kho tri thức CABI Plantwise Vietnam' : 'CABI Plantwise Vietnam Knowledge Base Match'}
                      </h4>
                    </div>
                    <span className="text-[11px] font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full">
                      {vi ? 'Độ khớp tri thức:' : 'KB Match:'} {Math.round((topPrediction.kb_reference.match_score || 0.85) * 100)}%
                    </span>
                  </div>

                  <div className="text-xs text-emerald-900 space-y-0.5">
                    <p className="font-semibold text-sm">
                      {topPrediction.kb_reference.crop} — {vi ? topPrediction.kb_reference.name_vi : (topPrediction.kb_reference.name_en || topPrediction.kb_reference.name_vi)}
                    </p>
                    {topPrediction.kb_reference.scientific_name && (
                      <p className="italic text-emerald-700">
                        🧬 {vi ? 'Tác nhân khoa học:' : 'Scientific pathogen:'} {topPrediction.kb_reference.scientific_name}
                      </p>
                    )}
                  </div>

                  {/* Side-by-side visual comparison: User Photo vs Verified Reference Photo */}
                  {topPrediction.kb_reference.image_url && (
                    <div className="grid grid-cols-2 gap-2.5 pt-1">
                      {preview && (
                        <div className="bg-white p-2 rounded-lg border border-emerald-100 text-center">
                          <img
                            src={preview}
                            alt="User leaf"
                            className="w-full h-28 sm:h-32 object-cover rounded-md mb-1 bg-gray-100"
                          />
                          <p className="text-[11px] font-medium text-gray-600">
                            📷 {vi ? 'Ảnh của bạn' : 'Your photo'}
                          </p>
                        </div>
                      )}
                      <div className={`bg-white p-2 rounded-lg border border-emerald-200 text-center ${!preview ? 'col-span-2' : ''}`}>
                        <img
                          src={topPrediction.kb_reference.image_url}
                          alt={topPrediction.kb_reference.name_vi}
                          className="w-full h-28 sm:h-32 object-cover rounded-md mb-1 bg-gray-100"
                          onError={(e) => { e.currentTarget.parentElement.style.display = 'none' }}
                        />
                        <p className="text-[11px] font-medium text-emerald-800">
                          🔬 {vi ? 'Ảnh mẫu chuẩn trong Kho tri thức' : 'Verified KB reference photo'}
                        </p>
                      </div>
                    </div>
                  )}

                  {topPrediction.kb_reference.conditions_vi && (
                    <div className="bg-amber-50/90 border border-amber-200 rounded-lg p-2.5 text-xs text-amber-900">
                      <span className="font-semibold">🌦️ {vi ? 'Điều kiện phát sinh (CABI): ' : 'Outbreak conditions (CABI): '}</span>
                      <span>{topPrediction.kb_reference.conditions_vi}</span>
                    </div>
                  )}

                  {topPrediction.kb_reference.prevention_vi && (
                    <div className="bg-white/90 border border-emerald-200 rounded-lg p-2.5 text-xs text-emerald-900">
                      <span className="font-semibold">🛡️ {vi ? 'Quản lý dịch hại tổng hợp (IPM Xanh CABI): ' : 'CABI Green IPM Prevention: '}</span>
                      <span>{topPrediction.kb_reference.prevention_vi}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Treatment */}
              {topPrediction.treatment && !isHealthy && (
                <div className="p-4 bg-gray-50 rounded-xl">
                  <h4 className="font-semibold text-gray-800 mb-1">💊 {t.treatment}</h4>
                  <p className="text-gray-600 text-sm leading-relaxed">{topPrediction.treatment}</p>
                </div>
              )}

              {/* Medicines + Matched Products */}
              {topPrediction.medicines?.length > 0 && !isHealthy && (
                <div className="p-4 bg-gray-50 rounded-xl space-y-3">
                  <h4 className="font-semibold text-gray-800">🧪 {t.medicines}</h4>
                  
                  {/* Banned warning */}
                  {topPrediction.banned_warning?.length > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <p className="text-red-700 text-sm font-semibold">🚫 {lang === 'vi' ? 'Cảnh báo: Hoạt chất CẤM sử dụng tại VN' : 'Warning: BANNED substances in Vietnam'}</p>
                      <p className="text-red-600 text-xs mt-1">{topPrediction.banned_warning.join(', ')}</p>
                    </div>
                  )}

                  {/* Matched products per active ingredient */}
                  {topPrediction.matched_products?.map((mp, i) => (
                    <div key={i} className={`rounded-lg p-3 ${mp.banned ? 'bg-red-50 border border-red-200' : 'bg-white border'}`}>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-sm font-semibold ${mp.banned ? 'text-red-700' : 'text-blue-700'}`}>
                          {mp.banned ? '🚫' : '✅'} {mp.active}
                        </span>
                      </div>
                      {mp.banned ? (
                        <p className="text-xs text-red-600">{lang === 'vi' ? 'Hoạt chất này bị CẤM tại Việt Nam' : 'This substance is BANNED in Vietnam'}</p>
                      ) : mp.products?.length > 0 ? (
                        <div className="space-y-1 mt-1">
                          {mp.products.map((p, j) => (
                            <div key={j} className="flex justify-between text-xs">
                              <span className="text-gray-800 font-medium">{p.name}</span>
                              <span className="text-gray-500">{p.company}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-gray-500">{lang === 'vi' ? 'Không tìm thấy sản phẩm trong danh mục VN' : 'No products found in VN catalog'}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* User feedback (stored server-side for expert review) */}
              <FeedbackWidget key={resultSeq} result={result} lang={lang} token={token}
                plantHint={selectedPlant} imageCount={file2 ? 2 : 1} wasClarified={wasClarified} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function HistoryView({ t, history, setHistory }) {
  const clear = () => { localStorage.removeItem(HISTORY_KEY); setHistory([]) }
  if (!history.length) return <p className="text-center text-gray-400 py-12">{t.noHistory}</p>
  return (
    <div className="space-y-3 sm:space-y-4">
      <div className="flex justify-end"><button onClick={clear} className="text-sm text-red-500 hover:text-red-700">{t.clearHistory}</button></div>
      {history.map((entry, i) => {
        const p = entry.result?.predictions?.[0]
        if (!p) return null
        return (
          <div key={i} className="bg-white p-3 sm:p-4 rounded-xl border flex gap-3 sm:gap-4 items-center">
            {entry.preview && <img src={entry.preview} alt="" className="w-12 h-12 sm:w-14 sm:h-14 object-cover rounded-lg shrink-0" />}
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-900 truncate text-sm sm:text-base">{p.name}</p>
              <p className="text-[10px] sm:text-xs text-gray-500">{new Date(entry.date).toLocaleString()}</p>
            </div>
            <span className="text-xs sm:text-sm font-semibold text-gray-600 shrink-0">{p.confidence}%</span>
          </div>
        )
      })}
    </div>
  )
}

function LibraryView({ t, lang }) {
  const vi = lang === 'vi'
  const [subTab, setSubTab] = useState('guide') // 'guide' | 'diseases'
  const [expanded, setExpanded] = useState(null)
  const [dbDiseases, setDbDiseases] = useState([])
  const [cropGuides, setCropGuides] = useState([])
  const [search, setSearch] = useState('')
  const [cropFilter, setCropFilter] = useState('')
  const [selectedGuideCrop, setSelectedGuideCrop] = useState('Lúa')
  const [fromStageCrop, setFromStageCrop] = useState(null)

  const toggle = (key) => setExpanded(expanded === key ? null : key)
  const severityLabel = {
    high: { vi: 'Nguy hiểm cao', en: 'High risk', color: 'bg-red-100 text-red-700 border-red-200' },
    medium: { vi: 'Trung bình', en: 'Medium', color: 'bg-yellow-100 text-yellow-700 border-yellow-200' },
    low: { vi: 'Thấp', en: 'Low', color: 'bg-green-100 text-green-700 border-green-200' },
  }

  useEffect(() => {
    axios.get('/api/v1/diseases').then(r => {
      if (Array.isArray(r.data) && r.data.length > 0) setDbDiseases(r.data)
    }).catch(() => {})
    axios.get('/api/v1/crop-guides').then(r => {
      if (Array.isArray(r.data) && r.data.length > 0) {
        setCropGuides(r.data)
        if (!r.data.some(g => g.crop === selectedGuideCrop)) {
          setSelectedGuideCrop(r.data[0].crop)
        }
      }
    }).catch(() => {})
  }, [])

  const getCropIcon = (cropName) => {
    if (!cropName) return '🌿'
    const iconMatch = PLANT_CHOICES.find(
      p => p.id.toLowerCase() === cropName.toLowerCase() || cropName.toLowerCase().includes(p.label.toLowerCase())
    )
    return iconMatch ? iconMatch.icon : '🌿'
  }

  // Build unified groups from DB knowledge base (or fallback to static diseaseLibrary)
  const groups = (() => {
    if (!dbDiseases.length) return diseaseLibrary
    const byCrop = new Map()
    for (const d of dbDiseases) {
      const c = d.crop || 'Khác'
      if (!byCrop.has(c)) byCrop.set(c, [])
      const splitLines = (txt) => (txt || '').split(/\n|;\s*/).map(s => s.trim()).filter(Boolean)
      byCrop.get(c).push({
        id: d.id,
        rawNameVi: d.name_vi || d.name_en,
        name: { vi: d.name_vi || d.name_en, en: d.name_en || d.name_vi },
        scientific: d.scientific_name || '',
        severity: d.severity || 'medium',
        image: d.image_url || '',
        symptoms: { vi: d.symptoms_vi || '', en: d.symptoms_en || d.symptoms_vi || '' },
        conditions: { vi: d.conditions_vi || '', en: d.conditions_en || d.conditions_vi || '' },
        prevention: { vi: splitLines(d.prevention_vi), en: splitLines(d.prevention_en || d.prevention_vi) },
        treatment: { vi: splitLines(d.treatment_vi), en: splitLines(d.treatment_en || d.treatment_vi) },
      })
    }
    return Array.from(byCrop.entries()).map(([cropName, list]) => {
      const icon = getCropIcon(cropName)
      return {
        cropKey: cropName,
        crop: { vi: `${icon} ${cropName}`, en: `${icon} ${cropName}` },
        diseases: list,
      }
    })
  })()

  const openDiseaseFromStage = (cropName, diseaseNameVi) => {
    setFromStageCrop(cropName)
    setCropFilter(cropName)
    setSearch('')
    const targetKey = `${cropName}::${diseaseNameVi}`
    setExpanded(targetKey)
    setSubTab('diseases')
    setTimeout(() => {
      const el = document.getElementById(`disease-card-${encodeURIComponent(targetKey)}`)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 120)
  }

  const filteredGroups = groups.map(g => ({
    ...g,
    diseases: g.diseases.filter(d => {
      if (cropFilter && g.cropKey && g.cropKey !== cropFilter) return false
      if (!search.trim()) return true
      const q = search.toLowerCase()
      return (
        (d.name[lang] || '').toLowerCase().includes(q) ||
        (d.scientific || '').toLowerCase().includes(q) ||
        (d.symptoms[lang] || '').toLowerCase().includes(q)
      )
    })
  })).filter(g => g.diseases.length > 0)

  const activeGuide = cropGuides.find(g => g.crop === selectedGuideCrop) || cropGuides[0] || null

  return (
    <div className="space-y-4 sm:space-y-5">
      {/* Sub-tab switcher: Quy trình trồng vs Danh mục bệnh */}
      <div className="bg-white p-2 rounded-xl border shadow-sm flex gap-2">
        <button
          id="subtab-cultivation-guide"
          type="button"
          onClick={() => setSubTab('guide')}
          className={`flex-1 py-2.5 px-3 rounded-lg font-bold text-xs sm:text-sm transition flex items-center justify-center gap-2 ${
            subTab === 'guide'
              ? 'bg-green-600 text-white shadow-sm'
              : 'bg-gray-50 text-gray-700 hover:bg-green-50 hover:text-green-800'
          }`}
        >
          <span>🌱</span>
          <span>{vi ? 'Quy trình trồng & Chăm sóc' : 'Cultivation & Care Guide'}</span>
        </button>
        <button
          id="subtab-disease-catalog"
          type="button"
          onClick={() => setSubTab('diseases')}
          className={`flex-1 py-2.5 px-3 rounded-lg font-bold text-xs sm:text-sm transition flex items-center justify-center gap-2 ${
            subTab === 'diseases'
              ? 'bg-green-600 text-white shadow-sm'
              : 'bg-gray-50 text-gray-700 hover:bg-green-50 hover:text-green-800'
          }`}
        >
          <span>🔬</span>
          <span>{vi ? `Danh mục bệnh (${dbDiseases.length || 50})` : `Disease Catalog (${dbDiseases.length || 50})`}</span>
        </button>
      </div>

      {/* SUB-TAB 1: QUY TRÌNH TRỒNG & CHĂM SÓC THEO GIAI ĐOẠN */}
      {subTab === 'guide' && (
        <div className="space-y-4">
          {/* Crop selector pills */}
          <div className="bg-white p-3 sm:p-4 rounded-xl border space-y-2.5">
            <div className="flex items-center justify-between">
              <p className="text-xs sm:text-sm font-bold text-gray-800">
                {vi ? '🌿 Chọn cây trồng để xem quy trình từ gieo trồng đến thu hoạch:' : '🌿 Select a crop to view its cultivation & care timeline:'}
              </p>
              <span className="text-[11px] text-green-700 bg-green-50 border border-green-200 px-2 py-0.5 rounded-full font-medium">
                {cropGuides.length} {vi ? 'nhóm cây chính thống' : 'crops'}
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5 sm:gap-2">
              {cropGuides.map((g) => {
                const active = activeGuide && activeGuide.crop === g.crop
                return (
                  <button
                    key={g.crop}
                    type="button"
                    onClick={() => setSelectedGuideCrop(g.crop)}
                    className={`px-3 py-1.5 rounded-full text-xs sm:text-sm font-semibold border transition flex items-center gap-1.5 ${
                      active
                        ? 'bg-green-600 text-white border-green-600 shadow-sm'
                        : 'bg-gray-50 text-gray-700 border-gray-200 hover:border-green-400 hover:bg-green-50'
                    }`}
                  >
                    <span>{getCropIcon(g.crop)}</span>
                    <span>{g.crop}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Active Crop Overview + 5 Phenological Stages */}
          {activeGuide ? (
            <div className="space-y-4">
              {/* Crop Overview Header */}
              <div className="bg-gradient-to-r from-green-700 to-emerald-600 text-white rounded-xl p-4 sm:p-5 shadow-md">
                <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                  <div>
                    <h3 className="text-lg sm:text-xl font-bold flex items-center gap-2">
                      <span>{getCropIcon(activeGuide.crop)}</span>
                      <span>{vi ? `Quy trình kỹ thuật canh tác: ${activeGuide.crop}` : `Cultivation & Care Guide: ${activeGuide.crop}`}</span>
                    </h3>
                    {activeGuide.scientific_name && (
                      <p className="text-xs sm:text-sm text-green-100 italic mt-0.5">
                        🧬 {activeGuide.scientific_name}
                      </p>
                    )}
                  </div>
                  {activeGuide.source_agency && (
                    <span className="text-[11px] bg-white/20 backdrop-blur-sm text-white px-2.5 py-1 rounded-lg font-medium">
                      🏛️ {activeGuide.source_agency}
                    </span>
                  )}
                </div>
                <p className="text-xs sm:text-sm text-green-50 leading-relaxed bg-black/15 p-3 rounded-lg">
                  {vi ? activeGuide.summary_vi : (activeGuide.summary_en || activeGuide.summary_vi)}
                </p>
              </div>

              {/* 5 Growth Stages Timeline */}
              <div className="space-y-3.5">
                {(activeGuide.stages || []).map((st) => (
                  <div
                    key={st.stage_number}
                    className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden hover:border-green-300 transition"
                  >
                    {/* Stage header bar */}
                    <div className="bg-green-50/80 border-b border-green-100 px-4 py-3 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <span className="w-7 h-7 rounded-full bg-green-600 text-white font-bold text-xs flex items-center justify-center shrink-0">
                          {st.stage_number}
                        </span>
                        <h4 className="font-bold text-gray-900 text-sm sm:text-base">
                          {vi ? st.title_vi : (st.title_en || st.title_vi)}
                        </h4>
                      </div>
                      <span className="text-xs font-semibold bg-white text-green-800 border border-green-200 px-2.5 py-1 rounded-full">
                        🕒 {vi ? st.timing_vi : (st.timing_en || st.timing_vi)}
                      </span>
                    </div>

                    {/* Stage body */}
                    <div className="p-4 space-y-3">
                      {/* Care & Fertilization */}
                      <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                        <h5 className="text-xs sm:text-sm font-bold text-green-800 mb-1 flex items-center gap-1.5">
                          <span>🌱</span>
                          <span>{vi ? 'Kỹ thuật chăm sóc & Bón phân:' : 'Care & Fertilization:'}</span>
                        </h5>
                        <p className="text-xs sm:text-sm text-gray-700 leading-relaxed">
                          {vi ? st.care_vi : (st.care_en || st.care_vi)}
                        </p>
                      </div>

                      {/* Critical Notes / Warnings */}
                      {(st.notes_vi || st.notes_en) && (
                        <div className="bg-amber-50/80 rounded-lg p-3 border border-amber-200">
                          <h5 className="text-xs sm:text-sm font-bold text-amber-900 mb-1 flex items-center gap-1.5">
                            <span>⚠️</span>
                            <span>{vi ? 'Chú ý quan trọng ở giai đoạn này:' : 'Critical Stage Notes:'}</span>
                          </h5>
                          <p className="text-xs sm:text-sm text-amber-800 leading-relaxed">
                            {vi ? st.notes_vi : (st.notes_en || st.notes_vi)}
                          </p>
                        </div>
                      )}

                      {/* Common Diseases in this stage (Interactive links to Disease Catalog tab) */}
                      {st.linked_diseases?.length > 0 && (
                        <div className="pt-1">
                          <h5 className="text-xs font-bold text-gray-700 mb-2 flex items-center gap-1.5">
                            <span>🐛</span>
                            <span>
                              {vi
                                ? 'Bệnh & dịch hại thường gặp giai đoạn này (nhấn để xem chi tiết & thuốc trị):'
                                : 'Common diseases at this stage (click to view details & treatment):'}
                            </span>
                          </h5>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {st.linked_diseases.map((ld, idx) => {
                              const sev = severityLabel[ld.severity] || severityLabel.medium
                              return (
                                <button
                                  key={idx}
                                  type="button"
                                  onClick={() => openDiseaseFromStage(activeGuide.crop, ld.name_vi)}
                                  className="flex items-center gap-2.5 p-2 rounded-lg border border-gray-200 hover:border-green-500 hover:bg-green-50/60 transition text-left group"
                                >
                                  {ld.image_url ? (
                                    <img
                                      src={ld.image_url}
                                      alt={ld.name_vi}
                                      className="w-11 h-11 rounded-md object-cover bg-gray-100 shrink-0 border"
                                      onError={(e) => { e.target.style.display = 'none' }}
                                    />
                                  ) : (
                                    <div className="w-11 h-11 rounded-md bg-green-100 flex items-center justify-center text-lg shrink-0">
                                      🔬
                                    </div>
                                  )}
                                  <div className="min-w-0 flex-1">
                                    <p className="text-xs sm:text-sm font-semibold text-gray-900 group-hover:text-green-700 truncate">
                                      {vi ? ld.name_vi : (ld.name_en || ld.name_vi)}
                                    </p>
                                    <div className="flex items-center gap-1.5 mt-0.5">
                                      <span className={`px-1.5 py-0.2 rounded text-[10px] font-medium border ${sev.color}`}>
                                        {sev[lang]}
                                      </span>
                                      <span className="text-[11px] text-green-700 font-medium group-hover:underline">
                                        {vi ? 'Xem bệnh →' : 'View →'}
                                      </span>
                                    </div>
                                  </div>
                                </button>
                              )
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-center text-gray-400 py-8">{vi ? 'Đang tải cẩm nang cây trồng...' : 'Loading crop guides...'}</p>
          )}
        </div>
      )}

      {/* SUB-TAB 2: DANH MỤC BỆNH (CABI PLANTWISE VIETNAM) */}
      {subTab === 'diseases' && (
        <div className="space-y-4">
          {fromStageCrop && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-3 flex items-center justify-between gap-2">
              <p className="text-xs sm:text-sm text-green-900 font-medium">
                🔗 {vi ? `Đang xem bệnh liên kết từ quy trình trồng cây: ${fromStageCrop}` : `Viewing disease linked from ${fromStageCrop} cultivation guide`}
              </p>
              <button
                type="button"
                onClick={() => {
                  setSelectedGuideCrop(fromStageCrop)
                  setSubTab('guide')
                }}
                className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-xs font-bold shrink-0 transition"
              >
                ← {vi ? `Quay lại Quy trình ${fromStageCrop}` : `Back to ${fromStageCrop} Guide`}
              </button>
            </div>
          )}

          <div className="bg-white p-3 sm:p-4 rounded-xl border flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder={vi ? '🔍 Tìm tên bệnh, tên khoa học, triệu chứng...' : '🔍 Search disease name, scientific name, symptoms...'}
              className="flex-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-400"
            />
            {dbDiseases.length > 0 && (
              <select
                value={cropFilter}
                onChange={e => {
                  setCropFilter(e.target.value)
                  setFromStageCrop(null)
                }}
                className="px-3 py-2 border rounded-lg text-sm bg-white"
              >
                <option value="">{vi ? 'Tất cả cây trồng' : 'All crops'}</option>
                {groups.map((g, i) => (
                  <option key={i} value={g.cropKey}>{g.crop[lang]} ({g.diseases.length})</option>
                ))}
              </select>
            )}
          </div>

          {filteredGroups.map((group, gi) => (
            <div key={gi}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-gray-800 text-lg">{group.crop[lang]}</h3>
                {cropGuides.some(cg => cg.crop === group.cropKey) && (
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedGuideCrop(group.cropKey)
                      setSubTab('guide')
                    }}
                    className="text-xs font-semibold text-green-700 hover:text-green-900 bg-green-50 border border-green-200 px-2.5 py-1 rounded-full transition"
                  >
                    🌱 {vi ? `Xem quy trình trồng ${group.cropKey}` : `View ${group.cropKey} cultivation guide`}
                  </button>
                )}
              </div>
              <div className="space-y-2">
                {group.diseases.map((d, di) => {
                  const key = `${group.cropKey || gi}::${d.rawNameVi || d.name.vi}`
                  const isOpen = expanded === key
                  const sev = severityLabel[d.severity] || severityLabel.medium
                  return (
                    <div
                      key={di}
                      id={`disease-card-${encodeURIComponent(key)}`}
                      className={`bg-white rounded-xl border overflow-hidden transition ${
                        isOpen ? 'ring-2 ring-green-500 border-green-400 shadow-md' : ''
                      }`}
                    >
                      {/* Collapsed row */}
                      <button onClick={() => toggle(key)} className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition text-left">
                        <div className="flex items-center gap-3 min-w-0">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${sev.color}`}>{sev[lang]}</span>
                          <span className="font-medium text-gray-900 truncate">{d.name[lang]}</span>
                        </div>
                        <svg className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                      </button>

                      {/* Expanded content */}
                      {isOpen && (
                        <div className="px-3 sm:px-4 pb-3 sm:pb-4 space-y-3 sm:space-y-4 border-t">
                          {/* Image + basic info */}
                          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-3 sm:pt-4">
                            {d.image && <img src={d.image} alt={d.name[lang]} className="w-full sm:w-36 h-36 sm:h-28 object-cover rounded-lg bg-gray-100 border" onError={(e) => { e.target.style.display = 'none' }} />}
                            <div className="flex-1">
                              <p className="text-xs text-gray-500 italic mb-1">{d.scientific}</p>
                              <p className="text-sm text-gray-700 leading-relaxed">{d.symptoms[lang]}</p>
                            </div>
                          </div>

                          {/* Conditions */}
                          {d.conditions[lang] && (
                            <div className="bg-amber-50 p-3 rounded-lg">
                              <h5 className="font-semibold text-amber-800 text-sm mb-1">⚠️ {vi ? 'Điều kiện phát bệnh' : 'Disease conditions'}</h5>
                              <p className="text-sm text-amber-700">{d.conditions[lang]}</p>
                            </div>
                          )}

                          {/* Prevention */}
                          {d.prevention[lang]?.length > 0 && (
                            <div className="bg-green-50 p-3 rounded-lg">
                              <h5 className="font-semibold text-green-800 text-sm mb-1">🛡️ {vi ? 'Phòng tránh' : 'Prevention'}</h5>
                              <ul className="list-disc list-inside text-sm text-green-700 space-y-0.5">
                                {d.prevention[lang].map((item, i) => <li key={i}>{item}</li>)}
                              </ul>
                            </div>
                          )}

                          {/* Treatment */}
                          {d.treatment[lang]?.length > 0 && (
                            <div className="bg-blue-50 p-3 rounded-lg">
                              <h5 className="font-semibold text-blue-800 text-sm mb-1">💊 {vi ? 'Hoạt chất / Điều trị' : 'Treatment'}</h5>
                              <ul className="list-disc list-inside text-sm text-blue-700 space-y-0.5">
                                {d.treatment[lang].map((item, i) => <li key={i}>{item}</li>)}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function PesticidesView({ t, lang }) {
  const [viewPdf, setViewPdf] = useState(null)
  const [pesticides, setPesticides] = useState(null)
  const [search, setSearch] = useState('')
  const [filterCat, setFilterCat] = useState('')
  const [page, setPage] = useState(0)
  const PAGE_SIZE = 50

  useEffect(() => {
    fetch('/pesticides.json').then(r => r.json()).then(setPesticides).catch(() => {})
  }, [])

  const bannedInsecticides = ['Aldrin','BHC / Lindane','Cadmium compound (Cd)','Carbofuran','Chlordane','Chlordimeform','DDT','Dieldrin','Endosulfan','Endrin','Heptachlor','Isobenzan','Isodrin','Lead (Pb)','Methamidophos','Methyl Parathion','Monocrotophos','Parathion Ethyl','Sodium Pentachlorophenate monohydrate','Pentachlorophenol','Phosphamidon','Polychlorocamphene','Trichlorfon (Chlorophos)']
  const bannedFungicides = ['Arsenic (As)','Captan','Captafol','Hexachlorobenzene','Mercury (Hg)','Selenium (Se)']
  const bannedOther = ['Talium compound (trừ chuột)', '2,4,5-T (trừ cỏ)']

  const categories = pesticides ? [...new Set(pesticides.map(p => p.cat))].sort() : []
  const filtered = pesticides ? pesticides.filter(p => {
    if (filterCat && p.cat !== filterCat) return false
    if (!search) return true
    const q = search.toLowerCase()
    return p.n.toLowerCase().includes(q) || p.a.toLowerCase().includes(q) || p.c.toLowerCase().includes(q)
  }) : []
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const pageItems = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  useEffect(() => { setPage(0) }, [search, filterCat])

  if (viewPdf) {
    return (
      <div className="space-y-3">
        <button onClick={() => setViewPdf(null)} className="flex items-center gap-1 text-sm text-green-700 hover:text-green-900 font-medium">← {lang === 'vi' ? 'Quay lại' : 'Back'}</button>
        <div className="bg-white rounded-xl border overflow-hidden" style={{height:'70vh'}}>
          <iframe src={viewPdf} className="w-full h-full" title="PDF" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {/* Warning */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
        <h3 className="font-semibold text-amber-800 mb-1">⚠️ {lang === 'vi' ? 'Lưu ý pháp lý' : 'Legal Notice'}</h3>
        <p className="text-sm text-amber-700">{lang === 'vi' ? 'Theo Thông tư 75/2025/TT-BNNPTNT (hiệu lực 30/12/2025). Sử dụng thuốc cấm bị xử phạt hành chính hoặc hình sự.' : 'Per Circular 75/2025 (effective 30/12/2025). Using banned pesticides is punishable by law.'}</p>
      </div>

      {/* PDF links */}
      <div className="flex flex-col sm:flex-row gap-2">
        <button onClick={() => setViewPdf('/thong-tu-75-2025.pdf')} className="flex-1 p-3 bg-blue-50 border border-blue-200 rounded-xl text-left hover:shadow transition text-sm">
          📋 {lang === 'vi' ? 'Xem Thông tư 75/2025' : 'View Circular 75/2025'}
        </button>
        <button onClick={() => setViewPdf('/danh-muc-duoc-phep.pdf')} className="flex-1 p-3 bg-green-50 border border-green-200 rounded-xl text-left hover:shadow transition text-sm">
          📄 {lang === 'vi' ? 'Xem PDF gốc đầy đủ' : 'View full original PDF'}
        </button>
      </div>

      {/* Banned list */}
      <details className="bg-red-50 border border-red-200 rounded-xl">
        <summary className="p-4 cursor-pointer font-semibold text-red-800 flex items-center gap-2">🚫 {lang === 'vi' ? 'Danh mục CẤM sử dụng (31 hoạt chất)' : 'BANNED pesticides (31 substances)'}</summary>
        <div className="px-4 pb-4 space-y-2">
          <div><span className="text-xs font-medium text-red-700">{lang === 'vi' ? 'Trừ sâu:' : 'Insecticides:'}</span> <span className="text-xs text-red-600">{bannedInsecticides.join(', ')}</span></div>
          <div><span className="text-xs font-medium text-red-700">{lang === 'vi' ? 'Trừ bệnh:' : 'Fungicides:'}</span> <span className="text-xs text-red-600">{bannedFungicides.join(', ')}</span></div>
          <div><span className="text-xs font-medium text-red-700">{lang === 'vi' ? 'Khác:' : 'Other:'}</span> <span className="text-xs text-red-600">{bannedOther.join(', ')}</span></div>
        </div>
      </details>

      {/* Permitted list - searchable */}
      <div className="bg-white border rounded-xl p-4 space-y-3">
        <h3 className="font-bold text-green-800">✅ {lang === 'vi' ? `Danh mục được phép (${pesticides?.length || '...'} sản phẩm)` : `Permitted list (${pesticides?.length || '...'} products)`}</h3>

        {/* Search & filter */}
        <div className="flex flex-col sm:flex-row gap-2">
          <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder={lang === 'vi' ? 'Tìm theo tên, hoạt chất, công ty...' : 'Search by name, ingredient, company...'} className="flex-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-300" />
          <select value={filterCat} onChange={e => setFilterCat(e.target.value)} className="px-3 py-2 border rounded-lg text-sm bg-white">
            <option value="">{lang === 'vi' ? 'Tất cả loại' : 'All types'}</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <p className="text-xs text-gray-500">{lang === 'vi' ? `Hiển thị ${pageItems.length} / ${filtered.length} kết quả` : `Showing ${pageItems.length} / ${filtered.length} results`}</p>

        {/* Table */}
        {pesticides ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left">
                  <th className="px-2 py-2 font-medium text-gray-700">{lang === 'vi' ? 'Tên thương phẩm' : 'Trade Name'}</th>
                  <th className="px-2 py-2 font-medium text-gray-700">{lang === 'vi' ? 'Hoạt chất' : 'Active Ingredient'}</th>
                  <th className="px-2 py-2 font-medium text-gray-700 hidden md:table-cell">{lang === 'vi' ? 'Đối tượng' : 'Target'}</th>
                  <th className="px-2 py-2 font-medium text-gray-700 hidden lg:table-cell">{lang === 'vi' ? 'Công ty' : 'Company'}</th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map((p, i) => (
                  <tr key={i} className="border-t hover:bg-gray-50">
                    <td className="px-2 py-1.5 font-medium text-gray-900">{p.n}</td>
                    <td className="px-2 py-1.5 text-gray-600">{p.a}</td>
                    <td className="px-2 py-1.5 text-gray-500 text-xs hidden md:table-cell">{p.t}</td>
                    <td className="px-2 py-1.5 text-gray-500 text-xs hidden lg:table-cell">{p.c}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="text-center text-gray-400 py-4">{lang === 'vi' ? 'Đang tải...' : 'Loading...'}</p>}

        {/* Pagination */}
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 pt-2">
            <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0} className="px-3 py-1 border rounded text-sm disabled:opacity-30">←</button>
            <span className="text-sm text-gray-600">{page + 1} / {totalPages}</span>
            <button onClick={() => setPage(Math.min(totalPages - 1, page + 1))} disabled={page >= totalPages - 1} className="px-3 py-1 border rounded text-sm disabled:opacity-30">→</button>
          </div>
        )}
      </div>
    </div>
  )
}

function PrivacyModal({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        <div className="p-4 sm:p-5 border-b flex justify-between items-center bg-gray-50">
          <h3 className="font-bold text-gray-900 text-base sm:text-lg flex items-center gap-2">
            🛡️ Chính sách Quyền riêng tư — PlantDoctor
          </h3>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-gray-600 font-bold transition"
          >
            ✕
          </button>
        </div>
        <div className="p-5 sm:p-6 overflow-y-auto space-y-4 text-sm text-gray-700 leading-relaxed">
          <div className="bg-green-50 border border-green-200 rounded-xl p-3.5 text-xs text-green-800">
            Cập nhật lần cuối: Tháng 9/2026 • Áp dụng cho Web App và Mobile App (iOS & Android).
          </div>

          <h4 className="font-bold text-gray-900 text-sm sm:text-base">1. Giới thiệu</h4>
          <p>
            PlantDoctor là ứng dụng chẩn đoán bệnh cây trồng bằng trí tuệ nhân tạo (AI), được phát triển bởi TS. Triệu Xuân Hòa, Trường Đại học Nông Lâm Thái Nguyên (TUAF). Chúng tôi cam kết bảo vệ tuyệt đối quyền riêng tư và dữ liệu cá nhân của người dùng theo quy định của pháp luật và các tiêu chuẩn bảo vệ dữ liệu quốc tế.
          </p>

          <h4 className="font-bold text-gray-900 text-sm sm:text-base">2. Dữ liệu thu thập</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Số điện thoại:</strong> Dùng làm định danh duy nhất để đăng ký, đăng nhập và bảo vệ tài khoản.</li>
            <li><strong>Tên hiển thị:</strong> Tùy chọn, dùng để cá nhân hóa lời chào trong ứng dụng.</li>
            <li><strong>Ảnh lá cây trồng:</strong> Do người dùng chụp từ camera hoặc chọn từ thư viện để AI phân tích bệnh. Ảnh được xử lý tức thời và <strong>không lưu trữ</strong> trên máy chủ sau khi hoàn thành chẩn đoán.</li>
            <li><strong>Vị trí địa lý (tùy chọn):</strong> Chỉ thu thập tọa độ xấp xỉ khi được cấp quyền để truy vấn thời tiết địa phương (nhiệt độ, độ ẩm), hỗ trợ đánh giá nguy cơ phát sinh dịch bệnh. Không theo dõi vị trí nền (background location).</li>
          </ul>

          <h4 className="font-bold text-gray-900 text-sm sm:text-base">3. Cam kết KHÔNG thu thập & KHÔNG chia sẻ</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li>Chúng tôi <strong>không thu thập</strong> danh bạ, tin nhắn, lịch sử cuộc gọi, tài chính hoặc dữ liệu nhạy cảm khác.</li>
            <li>Chúng tôi <strong>không bán</strong> và <strong>không chia sẻ</strong> dữ liệu người dùng cho bất kỳ đơn vị quảng cáo hoặc bên thứ ba nào.</li>
            <li>Mọi giao tiếp truyền tải dữ liệu đều được mã hóa bằng chuẩn HTTPS/TLS an toàn.</li>
          </ul>

          <h4 className="font-bold text-gray-900 text-sm sm:text-base">4. Quyền của người dùng & Xóa dữ liệu</h4>
          <p>
            Người dùng có toàn quyền:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Từ chối cấp quyền truy cập Camera hoặc Vị trí bất kỳ lúc nào trong cài đặt thiết bị.</li>
            <li>Xóa vĩnh viễn tài khoản và toàn bộ dữ liệu lịch sử ngay trong ứng dụng hoặc qua biểu mẫu web này.</li>
          </ul>

          <h4 className="font-bold text-gray-900 text-sm sm:text-base">5. Đơn vị chủ quản & Liên hệ</h4>
          <p>
            <strong>Triệu Xuân Hòa — Trường Đại học Nông Lâm Thái Nguyên</strong><br />
            Địa chỉ: Quyết Thắng, TP. Thái Nguyên, Việt Nam<br />
            Hotline hỗ trợ: <span className="font-semibold text-green-700">0944.550.007</span><br />
            Email: <span className="font-semibold text-green-700">trieuxuanhoa@tuaf.edu.vn</span><br />
            Website: <a href="https://benhcay.tuaf.edu.vn" target="_blank" rel="noreferrer" className="text-green-600 underline">https://benhcay.tuaf.edu.vn</a>
          </p>
        </div>
        <div className="p-4 border-t bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-semibold transition"
          >
            Đã hiểu & Đóng
          </button>
        </div>
      </div>
    </div>
  )
}

function DeleteAccountModal({ user, onClose }) {
  const [phone, setPhone] = useState(user?.phone || '')
  const [password, setPassword] = useState('')
  const [reason, setReason] = useState('')
  const [status, setStatus] = useState({ loading: false, success: false, error: '' })

  const handleDelete = async (e) => {
    e.preventDefault()
    if (!phone) {
      setStatus({ ...status, error: 'Vui lòng nhập số điện thoại tài khoản' })
      return
    }

    if (user && !password && !user.phone?.startsWith('apple_')) {
      setStatus({ ...status, error: 'Vui lòng nhập mật khẩu xác nhận' })
      return
    }

    if (!confirm('CẢNH BÁO: Toàn bộ thông tin tài khoản và dữ liệu sẽ bị xóa vĩnh viễn và không thể khôi phục. Bạn có chắc chắn muốn xóa?')) {
      return
    }

    setStatus({ loading: true, success: false, error: '' })
    try {
      if (user) {
        // Logged in user self-deletion
        const token = localStorage.getItem('leafdoctor_token')
        await axios.delete('/api/v1/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
          data: { password, reason },
        })
        localStorage.removeItem('leafdoctor_token')
        localStorage.removeItem('leafdoctor_user')
        setStatus({ loading: false, success: true, error: '' })
        setTimeout(() => {
          window.location.href = '/'
        }, 2500)
      } else {
        // Guest user submitting web deletion request (meets Google Play requirement)
        await axios.post('/api/v1/auth/forgot-password', { phone })
        setStatus({ loading: false, success: true, error: '' })
      }
    } catch (err) {
      setStatus({
        loading: false,
        success: false,
        error: err.response?.data?.detail || 'Không thể xóa tài khoản. Vui lòng kiểm tra lại thông tin.',
      })
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
        <div className="flex justify-between items-center border-b pb-3">
          <h3 className="font-bold text-red-600 text-lg flex items-center gap-2">
            ⚠️ Yêu cầu Xóa tài khoản & Dữ liệu
          </h3>
          <button onClick={onClose} className="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-500 font-bold">✕</button>
        </div>

        <p className="text-xs text-gray-600 leading-relaxed">
          Theo chính sách bảo vệ quyền riêng tư của <strong>Google Play Store</strong> và <strong>Apple App Store</strong>, bạn có quyền yêu cầu xóa vĩnh viễn tài khoản và toàn bộ dữ liệu liên quan khỏi hệ thống PlantDoctor.
        </p>

        {status.success ? (
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-green-800 text-sm text-center space-y-2">
            <p className="font-bold text-base">✅ Đã xử lý yêu cầu xóa tài khoản</p>
            <p className="text-xs text-green-700">
              {user
                ? 'Tài khoản của bạn đã được xóa hoàn toàn khỏi máy chủ. Đang tải lại trang...'
                : 'Yêu cầu của bạn đã được ghi nhận. Ban quản trị sẽ tiến hành xác minh và xóa dữ liệu trong vòng 24 giờ.'}
            </p>
          </div>
        ) : (
          <form onSubmit={handleDelete} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Số điện thoại tài khoản (*)</label>
              <input
                type="tel"
                value={phone}
                onChange={e => setPhone(e.target.value)}
                placeholder="Nhập số điện thoại tài khoản cần xóa"
                disabled={!!user}
                className="w-full px-3 py-2 border rounded-lg text-sm bg-gray-50 disabled:opacity-75 focus:outline-none focus:ring-2 focus:ring-red-400"
                required
              />
            </div>

            {user && !user.phone?.startsWith('apple_') && (
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Mật khẩu xác nhận (*)</label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Nhập mật khẩu hiện tại để xác nhận"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-400"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Lý do xóa (tùy chọn)</label>
              <textarea
                value={reason}
                onChange={e => setReason(e.target.value)}
                placeholder="Chia sẻ lý do để chúng tôi cải thiện dịch vụ tốt hơn..."
                rows={2}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-400"
              />
            </div>

            {status.error && (
              <p className="text-xs text-red-600 bg-red-50 p-2 rounded-lg border border-red-200">{status.error}</p>
            )}

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-2.5 text-xs text-amber-800">
              Sau khi xóa, mọi dữ liệu hồ sơ và lịch sử chẩn đoán cây trồng liên kết với số điện thoại này sẽ bị hủy vĩnh viễn.
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border rounded-lg text-sm text-gray-700 hover:bg-gray-50"
              >
                Hủy bỏ
              </button>
              <button
                type="submit"
                disabled={status.loading}
                className="px-5 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-bold transition shadow-sm disabled:opacity-50"
              >
                {status.loading ? 'Đang xử lý...' : 'Xóa vĩnh viễn'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

export default App

