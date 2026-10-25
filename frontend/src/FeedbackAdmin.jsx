// Admin tab: review user feedback (👍/👎) on diagnosis results.
// Data comes from /api/v1/admin/feedback (admin-only, phone numbers already masked server-side).
import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const PAGE_SIZE = 20

const REASON_LABELS = {
  vi: {
    wrong_plant: 'Sai loại cây', wrong_disease: 'Sai bệnh', wrong_severity: 'Sai mức độ',
    wrong_treatment: 'Cách trị không phù hợp', other: 'Khác', unspecified: 'Không nêu',
  },
  en: {
    wrong_plant: 'Wrong crop', wrong_disease: 'Wrong disease', wrong_severity: 'Wrong severity',
    wrong_treatment: 'Unsuitable treatment', other: 'Other', unspecified: 'Unspecified',
  },
}

const PLATFORM_ICON = { web: '🌐', ios: '📱', android: '🤖' }

function StatCard({ label, value, sub, tone = 'gray' }) {
  const tones = {
    gray: 'bg-gray-50 border-gray-200 text-gray-900',
    green: 'bg-green-50 border-green-200 text-green-900',
    red: 'bg-red-50 border-red-200 text-red-900',
    amber: 'bg-amber-50 border-amber-200 text-amber-900',
  }
  return (
    <div className={`border rounded-xl p-3 ${tones[tone]}`}>
      <p className="text-xs opacity-75">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
      {sub && <p className="text-[11px] opacity-70">{sub}</p>}
    </div>
  )
}

function ReviewEditor({ item, lang, onSave, saving }) {
  const vi = lang === 'vi'
  const [note, setNote] = useState(item.expert_note || '')
  return (
    <div className="mt-3 space-y-2">
      <textarea value={note} maxLength={2000} rows={2} onChange={(e) => setNote(e.target.value)}
        id={`fb-note-${item.id}`}
        placeholder={vi ? 'Ghi chú chuyên gia (chẩn đoán đúng là gì, cần sửa prompt/dữ liệu ra sao...)' : 'Expert note'}
        className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-400" />
      <div className="flex gap-2 justify-end">
        {item.reviewed && (
          <button type="button" disabled={saving} onClick={() => onSave(item, false, note)}
            className="px-3 py-1.5 text-xs border rounded-lg text-gray-600 hover:bg-gray-50 disabled:opacity-50">
            {vi ? 'Đánh dấu chưa xem' : 'Mark unreviewed'}
          </button>
        )}
        <button type="button" id={`fb-save-${item.id}`} disabled={saving} onClick={() => onSave(item, true, note)}
          className="px-3 py-1.5 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50">
          {saving ? '…' : item.reviewed ? (vi ? 'Cập nhật ghi chú' : 'Update note') : (vi ? '✓ Đã xem xét' : '✓ Mark reviewed')}
        </button>
      </div>
    </div>
  )
}

export default function FeedbackAdmin({ token, lang }) {
  const vi = lang === 'vi'
  const reasons = REASON_LABELS[vi ? 'vi' : 'en']
  const [stats, setStats] = useState(null)
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [verdict, setVerdict] = useState('incorrect')
  const [reviewed, setReviewed] = useState('no')
  const [loading, setLoading] = useState(false)
  const [savingId, setSavingId] = useState(null)
  const [expanded, setExpanded] = useState(null)
  const [error, setError] = useState('')

  const client = useCallback(() => axios.create({ headers: { Authorization: `Bearer ${token}` } }), [token])

  const loadStats = useCallback(() => {
    client().get('/api/v1/admin/feedback/stats').then((r) => setStats(r.data)).catch(() => {})
  }, [client])

  const loadList = useCallback(() => {
    setLoading(true)
    setError('')
    client()
      .get('/api/v1/admin/feedback', { params: { verdict, reviewed, page, page_size: PAGE_SIZE } })
      .then((r) => { setItems(r.data.items || []); setTotal(r.data.total || 0) })
      .catch(() => setError(vi ? 'Không tải được danh sách phản hồi.' : 'Could not load feedback.'))
      .finally(() => setLoading(false))
  }, [client, verdict, reviewed, page, vi])

  useEffect(() => { loadStats() }, [loadStats])
  useEffect(() => { loadList() }, [loadList])

  const changeFilter = (setter) => (e) => { setter(e.target.value); setPage(1) }

  const save = async (item, isReviewed, note) => {
    setSavingId(item.id)
    try {
      const r = await client().put(`/api/v1/admin/feedback/${item.id}`, { reviewed: isReviewed, expert_note: note })
      setItems((prev) => prev.map((x) => (x.id === item.id ? r.data : x)))
      loadStats()
    } catch {
      setError(vi ? 'Lưu thất bại, vui lòng thử lại.' : 'Save failed, please retry.')
    } finally {
      setSavingId(null)
    }
  }

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const fmtPct = (v) => (v === null || v === undefined ? '—' : `${v}%`)

  return (
    <div className="space-y-4" id="feedback-admin">
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-xs text-blue-900">
        {vi
          ? 'ℹ️ "Tỷ lệ đúng theo người dùng" chỉ phản ánh những người chủ động bấm 👍/👎 — không phải độ chính xác đo bằng bộ dữ liệu chuẩn. Hãy ưu tiên xem các phản hồi 👎 chưa xem xét.'
          : 'ℹ️ "User-reported accuracy" only reflects users who chose to vote — it is not a benchmark accuracy.'}
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label={vi ? 'Tổng phản hồi' : 'Total feedback'} value={stats.total} sub={`${vi ? '30 ngày' : '30 days'}: ${stats.last_30_days?.total ?? 0}`} />
          <StatCard tone="green" label={vi ? 'Tỷ lệ đúng (người dùng)' : 'User-reported accuracy'} value={fmtPct(stats.user_reported_accuracy)}
            sub={`${vi ? '30 ngày' : '30 days'}: ${fmtPct(stats.last_30_days?.user_reported_accuracy)}`} />
          <StatCard tone="red" label={vi ? 'Báo sai' : 'Reported wrong'} value={stats.incorrect} />
          <StatCard tone="amber" label={vi ? 'Báo sai chưa xem xét' : 'Unreviewed wrong'} value={stats.unreviewed_incorrect} />
        </div>
      )}

      {stats && Object.keys(stats.by_reason || {}).length > 0 && (
        <div className="bg-white border rounded-xl p-3">
          <p className="text-xs font-semibold text-gray-700 mb-2">{vi ? 'Lý do báo sai' : 'Reasons'}</p>
          <div className="space-y-1.5">
            {Object.entries(stats.by_reason).sort((a, b) => b[1] - a[1]).map(([k, v]) => (
              <div key={k} className="flex items-center gap-2 text-xs">
                <span className="w-40 text-gray-700 truncate">{reasons[k] || k}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-2">
                  <div className="bg-red-400 h-2 rounded-full" style={{ width: `${stats.incorrect ? (v * 100) / stats.incorrect : 0}%` }} />
                </div>
                <span className="w-8 text-right text-gray-600">{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-2 items-center">
        <select id="fb-filter-verdict" value={verdict} onChange={changeFilter(setVerdict)} className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="incorrect">👎 {vi ? 'Báo sai' : 'Wrong'}</option>
          <option value="correct">👍 {vi ? 'Báo đúng' : 'Correct'}</option>
          <option value="all">{vi ? 'Tất cả' : 'All'}</option>
        </select>
        <select id="fb-filter-reviewed" value={reviewed} onChange={changeFilter(setReviewed)} className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="no">{vi ? 'Chưa xem xét' : 'Unreviewed'}</option>
          <option value="yes">{vi ? 'Đã xem xét' : 'Reviewed'}</option>
          <option value="all">{vi ? 'Tất cả' : 'All'}</option>
        </select>
        <button type="button" onClick={() => { loadList(); loadStats() }} className="px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50">↻ {vi ? 'Tải lại' : 'Reload'}</button>
        <span className="text-xs text-gray-500 ml-auto">{total} {vi ? 'phản hồi' : 'items'}</span>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 rounded-lg p-2">{error}</p>}

      {loading ? (
        <p className="text-center text-gray-400 py-8">{vi ? 'Đang tải…' : 'Loading…'}</p>
      ) : items.length === 0 ? (
        <p className="text-center text-gray-400 py-8">{vi ? 'Không có phản hồi nào khớp bộ lọc.' : 'No feedback matches the filter.'}</p>
      ) : (
        <div className="space-y-2">
          {items.map((it) => (
            <div key={it.id} className={`bg-white border rounded-xl p-3 ${it.reviewed ? 'opacity-80' : ''}`}>
              <div className="flex items-start gap-3 cursor-pointer" onClick={() => setExpanded(expanded === it.id ? null : it.id)}>
                <span className="text-xl">{it.is_correct ? '👍' : '👎'}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-900 truncate">{it.predicted_name || '—'}
                    <span className="ml-2 text-xs font-normal text-gray-500">{it.predicted_confidence}%</span>
                  </p>
                  <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-gray-500 mt-0.5">
                    <span>{it.created_at ? new Date(it.created_at + (it.created_at.endsWith('Z') ? '' : 'Z')).toLocaleString() : ''}</span>
                    <span>{PLATFORM_ICON[it.platform] || ''} {it.platform || '?'}</span>
                    <span>📷 {it.image_count}</span>
                    {it.plant_hint && <span>🌾 {it.plant_hint}</span>}
                    {it.was_clarified && <span>🤔 {vi ? 'đã hỏi lại loại cây' : 'clarified'}</span>}
                    <span>👤 {it.user ? `${it.user.name || ''} ${it.user.phone}`.trim() : (vi ? 'Khách' : 'Guest')}</span>
                  </div>
                  {!it.is_correct && (
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      {it.reason && <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-[11px]">{reasons[it.reason] || it.reason}</span>}
                      {it.correct_plant && <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded-full text-[11px]">{vi ? 'Cây đúng' : 'Crop'}: {it.correct_plant}</span>}
                      {it.correct_disease && <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded-full text-[11px]">{vi ? 'Bệnh đúng' : 'Disease'}: {it.correct_disease}</span>}
                    </div>
                  )}
                </div>
                <span className={`shrink-0 text-[11px] px-2 py-0.5 rounded-full ${it.reviewed ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                  {it.reviewed ? (vi ? 'Đã xem' : 'Reviewed') : (vi ? 'Chưa xem' : 'New')}
                </span>
              </div>
              {expanded === it.id && (
                <div className="mt-2 pl-9">
                  {it.comment && <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-2 whitespace-pre-wrap break-words">💬 {it.comment}</p>}
                  {it.reviewed_at && <p className="text-[11px] text-gray-400 mt-1">{vi ? 'Xem xét lúc' : 'Reviewed at'}: {new Date(it.reviewed_at + (it.reviewed_at.endsWith('Z') ? '' : 'Z')).toLocaleString()}</p>}
                  <ReviewEditor item={it} lang={lang} onSave={save} saving={savingId === it.id} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {pages > 1 && (
        <div className="flex justify-center items-center gap-2">
          <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1 border rounded-lg text-sm disabled:opacity-40">‹</button>
          <span className="text-sm text-gray-600">{page} / {pages}</span>
          <button type="button" disabled={page >= pages} onClick={() => setPage(page + 1)} className="px-3 py-1 border rounded-lg text-sm disabled:opacity-40">›</button>
        </div>
      )}
    </div>
  )
}
