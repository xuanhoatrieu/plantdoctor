// Diagnosis UX helpers for the web app (US-021):
//  - checkImageInBrowser: fast local resolution/brightness check before upload (non-blocking hint)
//  - LowQualityCard: server quality gate rejected the photo -> retake or "diagnose anyway"
//  - ClarificationCard: AI is unsure about the crop -> user picks one (or types it)
//  - FeedbackWidget: 👍/👎 on a result, stored server-side for expert review
// All text is rendered through React (no innerHTML) and no alert()/prompt() is used.
import { useState } from 'react'
import axios from 'axios'

// Keep in sync with backend/app/models/vlm.py (QUALITY_MIN_SIDE_PX / DARK / BRIGHT thresholds).
const MIN_SIDE_PX = 300
const DARK_THRESHOLD = 45
const BRIGHT_THRESHOLD = 235

export const MAX_FEEDBACK_COMMENT = 1000

/**
 * Decode the image locally and measure size + mean brightness.
 * Blur is NOT measured in the browser (too slow/unreliable on phones); the server does that.
 * Resolves to { width, height, brightness, issues: string[] }. Never rejects.
 */
export function checkImageInBrowser(file) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      try {
        const width = img.naturalWidth
        const height = img.naturalHeight
        const scale = Math.min(1, 256 / Math.max(width, height))
        const cw = Math.max(1, Math.round(width * scale))
        const ch = Math.max(1, Math.round(height * scale))
        const canvas = document.createElement('canvas')
        canvas.width = cw
        canvas.height = ch
        const ctx = canvas.getContext('2d', { willReadFrequently: true })
        ctx.drawImage(img, 0, 0, cw, ch)
        const data = ctx.getImageData(0, 0, cw, ch).data
        let sum = 0
        for (let i = 0; i < data.length; i += 4) {
          // ITU-R 601 luma, same as PIL's convert("L")
          sum += 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]
        }
        const brightness = sum / (data.length / 4)
        const issues = []
        if (Math.min(width, height) < MIN_SIDE_PX) issues.push('low_resolution')
        if (brightness < DARK_THRESHOLD) issues.push('too_dark')
        else if (brightness > BRIGHT_THRESHOLD) issues.push('overexposed')
        resolve({ width, height, brightness: Math.round(brightness), issues })
      } catch {
        resolve({ width: 0, height: 0, brightness: null, issues: [] })
      } finally {
        URL.revokeObjectURL(url)
      }
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      resolve({ width: 0, height: 0, brightness: null, issues: ['unreadable'] })
    }
    img.src = url
  })
}

export function issueText(code, lang, info = {}) {
  const vi = {
    low_resolution: `Ảnh nhỏ (${info.width || '?'}x${info.height || '?'}px) — nên chụp gần hơn hoặc dùng ảnh gốc.`,
    too_dark: 'Ảnh khá tối — AI có thể không thấy rõ màu vết bệnh.',
    overexposed: 'Ảnh bị chói/cháy sáng — tránh nắng chiếu thẳng.',
    blurry: 'Ảnh bị mờ/nhòe — giữ chắc tay và lấy nét vào vết bệnh.',
    unreadable: 'Không đọc được tệp ảnh này.',
  }
  const en = {
    low_resolution: `Small image (${info.width || '?'}x${info.height || '?'}px) — move closer or use the original photo.`,
    too_dark: 'Image is quite dark — lesion colours may be hard to see.',
    overexposed: 'Image is overexposed — avoid direct sunlight.',
    blurry: 'Image is blurry — hold steady and focus on the lesion.',
    unreadable: 'This image file cannot be read.',
  }
  return (lang === 'vi' ? vi : en)[code] || code
}

export function LowQualityCard({ result, lang, loading, onForce, onRetake }) {
  const vi = lang === 'vi'
  return (
    <div className="space-y-3" id="low-quality-card">
      <div className="bg-amber-50 border border-amber-300 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">📸</span>
          <h3 className="font-bold text-amber-900">{vi ? 'Ảnh chưa đủ tốt để chẩn đoán chính xác' : 'Photo quality is too low for a reliable diagnosis'}</h3>
        </div>
        <ul className="space-y-1 ml-1">
          {(result.image_quality_warnings || []).map((w, i) => (
            <li key={i} className="text-sm text-amber-800">• {w}</li>
          ))}
        </ul>
        <p className="text-xs text-amber-700 mt-3">
          {vi
            ? 'Ảnh này chưa được gửi cho AI nên không tốn lượt chẩn đoán. Chụp lại sẽ cho kết quả đáng tin hơn.'
            : 'This photo was not sent to the AI yet. Retaking it will give a more reliable result.'}
        </p>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button id="lowq-retake-btn" type="button" onClick={onRetake} disabled={loading}
          className="py-2.5 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 disabled:opacity-50 transition">
          📷 {vi ? 'Chọn ảnh khác' : 'Choose another photo'}
        </button>
        <button id="lowq-force-btn" type="button" onClick={onForce} disabled={loading}
          className="py-2.5 border-2 border-amber-500 text-amber-800 rounded-xl font-semibold hover:bg-amber-50 disabled:opacity-50 transition">
          {vi ? 'Vẫn chẩn đoán' : 'Diagnose anyway'}
        </button>
      </div>
    </div>
  )
}

export function ClarificationCard({ result, lang, loading, onSelect }) {
  const vi = lang === 'vi'
  const [customOpen, setCustomOpen] = useState(false)
  const [custom, setCustom] = useState('')
  const candidates = result.candidate_plants || []

  const submitCustom = (e) => {
    e.preventDefault()
    const name = custom.trim().slice(0, 100)
    if (name) onSelect(name)
  }

  return (
    <div className="space-y-3" id="clarification-card">
      <div className="bg-sky-50 border border-sky-300 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">🤔</span>
          <h3 className="font-bold text-sky-900">{vi ? 'Cần bạn xác nhận loại cây' : 'Please confirm the crop'}</h3>
        </div>
        <p className="text-sm text-sky-800">{result.clarification_message}</p>
        {result.preliminary_symptoms && (
          <div className="mt-3 bg-white/70 rounded-lg p-3">
            <p className="text-xs font-semibold text-gray-700 mb-1">{vi ? 'Triệu chứng AI quan sát được (sơ bộ):' : 'Preliminary symptoms observed:'}</p>
            <p className="text-xs text-gray-600 leading-relaxed">{result.preliminary_symptoms}</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        {candidates.map((c) => (
          <button key={c.id} id={`clarify-${c.id}`} type="button" disabled={loading}
            onClick={() => (c.id === 'other' ? setCustomOpen(true) : onSelect(c.name))}
            className={`flex items-center gap-2 px-3 py-2.5 rounded-xl border-2 text-sm font-medium transition disabled:opacity-50 ${
              c.id === 'other' ? 'border-gray-300 text-gray-700 hover:bg-gray-50 col-span-2' : 'border-sky-300 text-sky-900 hover:bg-sky-50'
            }`}>
            <span className="text-xl">{c.icon}</span>
            <span className="text-left">{c.name}</span>
          </button>
        ))}
      </div>

      {customOpen && (
        <form onSubmit={submitCustom} className="flex gap-2">
          <input id="clarify-custom-input" value={custom} maxLength={100} autoFocus
            onChange={(e) => setCustom(e.target.value)}
            placeholder={vi ? 'Nhập tên cây (vd: Thanh long)' : 'Type the crop name'}
            className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400" />
          <button id="clarify-custom-submit" type="submit" disabled={loading || !custom.trim()}
            className="px-4 py-2 bg-sky-600 text-white rounded-lg text-sm font-semibold hover:bg-sky-700 disabled:opacity-50">
            {vi ? 'Xác nhận' : 'Confirm'}
          </button>
        </form>
      )}
      {loading && <p className="text-xs text-center text-gray-500">{vi ? 'Đang phân tích lại theo loại cây bạn chọn…' : 'Re-analysing for the selected crop…'}</p>}
    </div>
  )
}

const REASONS = [
  { id: 'wrong_plant', vi: 'Sai loại cây', en: 'Wrong crop' },
  { id: 'wrong_disease', vi: 'Sai bệnh', en: 'Wrong disease' },
  { id: 'wrong_severity', vi: 'Sai mức độ', en: 'Wrong severity' },
  { id: 'wrong_treatment', vi: 'Cách trị không phù hợp', en: 'Unsuitable treatment' },
  { id: 'other', vi: 'Khác', en: 'Other' },
]

export function FeedbackWidget({ result, lang, token, plantHint, imageCount, wasClarified }) {
  const vi = lang === 'vi'
  const [state, setState] = useState('idle') // idle | sending | done | error
  const [modalOpen, setModalOpen] = useState(false)
  const [reason, setReason] = useState('wrong_disease')
  const [correctPlant, setCorrectPlant] = useState('')
  const [correctDisease, setCorrectDisease] = useState('')
  const [comment, setComment] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const top = result?.predictions?.[0]
  if (!top) return null

  const send = async (isCorrect) => {
    setState('sending')
    setErrorMsg('')
    const payload = {
      is_correct: isCorrect,
      reason: isCorrect ? '' : reason,
      correct_plant: isCorrect ? '' : correctPlant.trim().slice(0, 100),
      correct_disease: isCorrect ? '' : correctDisease.trim().slice(0, 200),
      comment: isCorrect ? '' : comment.trim().slice(0, MAX_FEEDBACK_COMMENT),
      platform: 'web',
      predicted_name: String(top.name || '').slice(0, 300),
      predicted_label: String(top.label || '').slice(0, 200),
      predicted_confidence: Math.max(0, Math.min(100, Number(top.confidence) || 0)),
      plant_hint: String(plantHint || '').slice(0, 100),
      image_count: Math.max(1, Math.min(3, imageCount || 1)),
      was_clarified: !!wasClarified,
    }
    try {
      await axios.post('/api/v1/feedback', payload, token ? { headers: { Authorization: `Bearer ${token}` } } : undefined)
      setState('done')
      setModalOpen(false)
    } catch (err) {
      setState('error')
      setErrorMsg(err?.response?.status === 429
        ? (vi ? 'Bạn gửi phản hồi quá nhanh, vui lòng thử lại sau ít phút.' : 'Too many submissions, please try again later.')
        : (vi ? 'Không gửi được phản hồi. Vui lòng thử lại.' : 'Could not send feedback. Please try again.'))
    }
  }

  if (state === 'done') {
    return (
      <div id="feedback-thanks" className="bg-green-50 border border-green-200 rounded-xl p-3 text-center text-sm text-green-800">
        🙏 {vi ? 'Cảm ơn bạn! Phản hồi sẽ được chuyên gia xem xét để cải thiện độ chính xác.' : 'Thank you! Experts will review your feedback to improve accuracy.'}
      </div>
    )
  }

  return (
    <div className="bg-white border rounded-xl p-3" id="feedback-widget">
      <p className="text-sm font-medium text-gray-700 text-center mb-2">{vi ? 'Kết quả này có đúng không?' : 'Is this diagnosis correct?'}</p>
      <div className="flex gap-2 justify-center">
        <button id="feedback-up-btn" type="button" disabled={state === 'sending'} onClick={() => send(true)}
          className="px-4 py-2 rounded-lg border-2 border-green-500 text-green-700 font-medium hover:bg-green-50 disabled:opacity-50 transition">
          👍 {vi ? 'Đúng' : 'Correct'}
        </button>
        <button id="feedback-down-btn" type="button" disabled={state === 'sending'} onClick={() => { setModalOpen(true); setState('idle') }}
          className="px-4 py-2 rounded-lg border-2 border-red-400 text-red-600 font-medium hover:bg-red-50 disabled:opacity-50 transition">
          👎 {vi ? 'Chưa đúng' : 'Not correct'}
        </button>
      </div>
      {state === 'error' && !modalOpen && <p className="text-xs text-red-600 text-center mt-2">{errorMsg}</p>}

      {modalOpen && (
        <div className="fixed inset-0 z-[100] bg-black/50 flex items-end sm:items-center justify-center p-0 sm:p-4" role="dialog" aria-modal="true"
          onClick={(e) => { if (e.target === e.currentTarget && state !== 'sending') setModalOpen(false) }}>
          <div className="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-5 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center">
              <h3 className="font-bold text-gray-900">{vi ? 'Góp ý kết quả chẩn đoán' : 'Report an incorrect diagnosis'}</h3>
              <button type="button" aria-label="close" onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
            </div>
            <p className="text-xs text-gray-500">{vi ? 'AI trả lời:' : 'AI answered:'} <span className="font-medium text-gray-700">{top.name}</span></p>

            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">{vi ? 'Sai ở điểm nào?' : 'What is wrong?'}</p>
              <div className="flex flex-wrap gap-2">
                {REASONS.map((r) => (
                  <button key={r.id} id={`fb-reason-${r.id}`} type="button" onClick={() => setReason(r.id)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition ${reason === r.id ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>
                    {vi ? r.vi : r.en}
                  </button>
                ))}
              </div>
            </div>

            {(reason === 'wrong_plant' || reason === 'other') && (
              <label className="block">
                <span className="text-xs text-gray-600">{vi ? 'Cây đúng là (nếu biết):' : 'Correct crop (if known):'}</span>
                <input id="fb-correct-plant" value={correctPlant} maxLength={100} onChange={(e) => setCorrectPlant(e.target.value)}
                  className="mt-1 w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-400" />
              </label>
            )}
            {reason !== 'wrong_treatment' && (
              <label className="block">
                <span className="text-xs text-gray-600">{vi ? 'Bệnh đúng là (nếu biết):' : 'Correct disease (if known):'}</span>
                <input id="fb-correct-disease" value={correctDisease} maxLength={200} onChange={(e) => setCorrectDisease(e.target.value)}
                  className="mt-1 w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-400" />
              </label>
            )}
            <label className="block">
              <span className="text-xs text-gray-600">{vi ? 'Ghi chú thêm:' : 'Comment:'}</span>
              <textarea id="fb-comment" value={comment} maxLength={MAX_FEEDBACK_COMMENT} rows={3} onChange={(e) => setComment(e.target.value)}
                className="mt-1 w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-400" />
              <span className="block text-right text-[10px] text-gray-400">{comment.length}/{MAX_FEEDBACK_COMMENT}</span>
            </label>
            {state === 'error' && <p className="text-xs text-red-600">{errorMsg}</p>}
            <div className="flex gap-2">
              <button type="button" onClick={() => setModalOpen(false)} disabled={state === 'sending'}
                className="flex-1 py-2.5 border rounded-xl text-gray-700 hover:bg-gray-50 disabled:opacity-50">{vi ? 'Hủy' : 'Cancel'}</button>
              <button id="fb-submit-btn" type="button" onClick={() => send(false)} disabled={state === 'sending'}
                className="flex-1 py-2.5 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 disabled:opacity-50">
                {state === 'sending' ? (vi ? 'Đang gửi…' : 'Sending…') : (vi ? 'Gửi góp ý' : 'Send')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
