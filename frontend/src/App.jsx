import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { translations } from './i18n'
import { diseaseLibrary } from './diseaseLibrary'
import { useAuth } from './AuthContext'
import LoginModal from './LoginModal'
import AdminView from './AdminView'

const HISTORY_KEY = 'leafdoctor_history'
function getHistory() { try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]') } catch { return [] } }
function saveHistory(h) { localStorage.setItem(HISTORY_KEY, JSON.stringify(h.slice(0, 20))) }

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
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [history, setHistory] = useState(getHistory)
  const [weather, setWeather] = useState(null)
  const [showLogin, setShowLogin] = useState(false)
  const fileRef = useRef()
  const t = translations[lang]
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [appLinks, setAppLinks] = useState({
    ios: 'https://apps.apple.com/app/plantdoctor',
    android: 'https://benhcay.tuaf.edu.vn/plantdoctor.apk',
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

  const handleFile = (f) => {
    if (!f) return
    if (f.size > 10 * 1024 * 1024) { setError(t.maxSize); return }
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
    setError('')
  }

  const handlePredict = async () => {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('file', file)
      form.append('model_id', 'gpt55_vision')
      form.append('lang', lang)
      const res = await axios.post('/api/v1/predict', form)
      setResult(res.data)
      const entry = { date: new Date().toISOString(), preview, result: res.data }
      const h = [entry, ...history].slice(0, 20)
      setHistory(h)
      saveHistory(h)
    } catch { setError(t.error) }
    finally { setLoading(false) }
  }

  const handleReset = () => { setFile(null); setPreview(null); setResult(null); setError('') }

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
        {tab === 'diagnose' && <DiagnoseView {...{t, file, preview, loading, result, error, topPrediction, isHealthy, fileRef, handleFile, handlePredict, handleReset, weather, lang, user}} />}
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
        PlantDoctor v2.0 — Powered by Triệu Xuân Hòa
      </footer>
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

function DiagnoseView({ t, file, preview, loading, result, error, topPrediction, isHealthy, fileRef, handleFile, handlePredict, handleReset, weather, lang, user }) {
  return (
    <div className="grid md:grid-cols-2 gap-4 sm:gap-6">
      {/* Left column */}
      <div className="space-y-3 sm:space-y-4">
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

        {/* Upload */}
        <div
          onDrop={(e) => { e.preventDefault(); handleFile(e.dataTransfer.files[0]) }}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileRef.current.click()}
          className="relative border-2 border-dashed border-green-300 rounded-xl p-4 sm:p-6 text-center cursor-pointer hover:border-green-500 hover:bg-green-50/50 transition min-h-[160px] sm:min-h-[220px] flex items-center justify-center"
        >
          {preview ? (
            <div className="relative">
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
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
        </div>

        {/* Predict button */}
        <button onClick={handlePredict} disabled={!file || loading}
          className="w-full py-3 sm:py-3.5 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition text-base sm:text-lg shadow-sm">
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              {t.predicting}
            </span>
          ) : t.predict}
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
                  <p className="text-xs text-green-800">{lang === 'vi' ? 'Kết quả từ bộ nhớ đệm (nhất quán 100%)' : 'Cached result (100% consistent)'}</p>
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
  const [expanded, setExpanded] = useState(null)
  const toggle = (key) => setExpanded(expanded === key ? null : key)
  const severityLabel = { high: { vi: 'Nguy hiểm cao', en: 'High risk', color: 'bg-red-100 text-red-700' }, medium: { vi: 'Trung bình', en: 'Medium', color: 'bg-yellow-100 text-yellow-700' }, low: { vi: 'Thấp', en: 'Low', color: 'bg-green-100 text-green-700' } }

  return (
    <div className="space-y-6">
      {diseaseLibrary.map((group, gi) => (
        <div key={gi}>
          <h3 className="font-bold text-gray-800 mb-3 text-lg">{group.crop[lang]}</h3>
          <div className="space-y-2">
            {group.diseases.map((d, di) => {
              const key = `${gi}-${di}`
              const isOpen = expanded === key
              const sev = severityLabel[d.severity] || severityLabel.medium
              return (
                <div key={di} className="bg-white rounded-xl border overflow-hidden">
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
                        <img src={d.image} alt={d.name[lang]} className="w-full sm:w-32 h-32 sm:h-24 object-cover rounded-lg bg-gray-100" onError={(e) => { e.target.style.display = 'none' }} />
                        <div className="flex-1">
                          <p className="text-xs text-gray-500 italic mb-1">{d.scientific}</p>
                          <p className="text-sm text-gray-700 leading-relaxed">{d.symptoms[lang]}</p>
                        </div>
                      </div>

                      {/* Conditions */}
                      <div className="bg-amber-50 p-3 rounded-lg">
                        <h5 className="font-semibold text-amber-800 text-sm mb-1">⚠️ {lang === 'vi' ? 'Điều kiện phát bệnh' : 'Disease conditions'}</h5>
                        <p className="text-sm text-amber-700">{d.conditions[lang]}</p>
                      </div>

                      {/* Prevention */}
                      <div className="bg-green-50 p-3 rounded-lg">
                        <h5 className="font-semibold text-green-800 text-sm mb-1">🛡️ {lang === 'vi' ? 'Phòng tránh' : 'Prevention'}</h5>
                        <ul className="list-disc list-inside text-sm text-green-700 space-y-0.5">
                          {d.prevention[lang].map((item, i) => <li key={i}>{item}</li>)}
                        </ul>
                      </div>

                      {/* Treatment */}
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <h5 className="font-semibold text-blue-800 text-sm mb-1">💊 {lang === 'vi' ? 'Điều trị' : 'Treatment'}</h5>
                        <ul className="list-disc list-inside text-sm text-blue-700 space-y-0.5">
                          {d.treatment[lang].map((item, i) => <li key={i}>{item}</li>)}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      ))}
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

export default App
