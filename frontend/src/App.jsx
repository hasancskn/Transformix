import React, { useEffect, useState } from 'react'
import axios from 'axios'
import Logo from './components/Logo'
import { FileDown, FileUp, Image as ImageIcon, FileType, Shield, Scissors, RotateCw, Link as LinkIcon, FileArchive } from 'lucide-react'

const CARD_GRID = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6'

function Header() {
  return (
    <header className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-gray-200">
      <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Logo className="h-8 w-8" />
          <span className="text-xl font-semibold">Transformix</span>
        </div>
        <a href="https://github.com/hasancskn/Transformix" target="_blank" className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-brand-700">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5"><path d="M12 .5C5.73.5.77 5.46.77 11.74c0 4.93 3.2 9.12 7.64 10.6.56.1.77-.24.77-.54 0-.27-.01-1.16-.02-2.1-3.11.68-3.76-1.32-3.76-1.32-.51-1.28-1.25-1.62-1.25-1.62-1.02-.7.08-.68.08-.68 1.13.08 1.72 1.16 1.72 1.16 1 .1 1.78-.75 2.2-1.15-.89-.1-1.82-.45-1.82-2 0-.44.16-.8.42-1.09-.04-.1-.18-.52.04-1.08 0 0 .34-.11 1.12.41.33-.09.68-.13 1.03-.13.35 0 .7.05 1.03.13.78-.52 1.12-.41 1.12-.41.22.56.08.98.04 1.08.26.29.42.65.42 1.09 0 1.56-.93 1.9-1.82 2 .49.42.94 1.24.94 2.5 0 1.81-.02 3.27-.02 3.72 0 .3.2.64.78.53 4.43-1.49 7.63-5.67 7.63-10.6C23.23 5.46 18.27.5 12 .5z"/></svg>
          GitHub
        </a>
      </div>
    </header>
  )
}

function iconFor(cap) {
  const n = (cap.name || '').toLowerCase()
  if (n.includes('merge')) return FileArchive
  if (n.includes('split')) return Scissors
  if (n.includes('rotate')) return RotateCw
  if (n.includes('protect')) return Shield
  if (n.includes('jpg') || n.includes('image')) return ImageIcon
  if (n.includes('html')) return LinkIcon
  if (n.includes('compress')) return FileDown
  if (n.includes('pdf') && n.includes('word')) return FileType
  return FileUp
}

function CapabilityCard({ cap, onSelect }) {
  const Icon = iconFor(cap)
  return (
    <button onClick={() => onSelect(cap)} className="text-left group rounded-2xl p-6 shadow-sm ring-1 ring-gray-200 bg-white hover:shadow-md hover:ring-brand-300 transition relative overflow-hidden">
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition bg-gradient-to-br from-brand-50/60 to-transparent pointer-events-none"/>
      <div className="relative z-10">
        <div className="h-12 w-12 rounded-xl bg-brand-100 text-brand-700 flex items-center justify-center">
          <Icon className="h-6 w-6" />
        </div>
        <div className="mt-4 font-semibold text-gray-900">{cap.name}</div>
        <div className="mt-1 text-sm text-gray-500">{cap.from_type} → {cap.to_type}</div>
      </div>
    </button>
  )
}

function Uploader({ selected, onClose }) {
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    const requiresFile = !selected.endpoint.includes('/html-to-pdf') && !selected.endpoint.includes('/merge')
    if (requiresFile && !file) {
      setMessage('Lütfen dosya seçin')
      return
    }
    setBusy(true)
    setMessage('')
    try {
      const form = new FormData()
      if (selected.endpoint.includes('/html-to-pdf')) {
        const url = e.target.url?.value?.trim()
        const html = e.target.html?.value
        if (!url && !html) {
          setMessage('URL veya HTML içeriği girin')
          setBusy(false)
          return
        }
        if (url) form.append('url', url)
        if (html) form.append('html', html)
      } else if (selected.endpoint.includes('/merge')) {
        for (const f of e.target.files.files) form.append('files', f)
      } else {
        form.append('file', file)
      }

      // extra params
      if (selected.endpoint.includes('/compress')) {
        form.append('quality', e.target.quality?.value || 85)
      }
      if (selected.endpoint.includes('/split')) {
        form.append('from_page', e.target.from_page?.value || 1)
        form.append('to_page', e.target.to_page?.value || '')
      }
      if (selected.endpoint.includes('/rotate')) {
        form.append('degrees', e.target.degrees?.value || 90)
      }
      if (selected.endpoint.includes('/protect')) {
        form.append('password', e.target.password?.value || '')
      }

      const url = `/api${selected.endpoint}`
      const response = await axios.post(url, form, { responseType: 'blob', timeout: 600000 })
      const blob = new Blob([response.data])
      const a = document.createElement('a')
      const contentDisposition = response.headers['content-disposition'] || ''
      const match = /filename=([^;]+)/i.exec(contentDisposition)
      const name = match ? match[1] : 'download'
      a.href = URL.createObjectURL(blob)
      a.download = name
      a.click()
      setMessage('İndirme başladı')
    } catch (err) {
      if (err.response && err.response.data instanceof Blob) {
        try {
          const text = await err.response.data.text()
          try {
            const j = JSON.parse(text)
            setMessage('Hata: ' + (j.detail || text))
          } catch {
            setMessage('Hata: ' + text)
          }
        } catch {
          setMessage('Hata: ' + err.message)
        }
      } else {
        setMessage('Hata: ' + (err.response?.data || err.message))
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg">
        <div className="p-5 border-b flex items-center justify-between">
          <div>
            <div className="text-lg font-semibold">{selected.name}</div>
            <div className="text-xs text-gray-500">{selected.from_type} → {selected.to_type}</div>
          </div>
          <button onClick={onClose} className="px-3 py-1 text-sm rounded-md bg-gray-100 hover:bg-gray-200">Kapat</button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4">
          {!selected.endpoint.includes('/html-to-pdf') && !selected.endpoint.includes('/merge') && (
            <div>
              <label className="block text-sm text-gray-600 mb-1">Dosya yükle</label>
              <input type="file" className="block w-full" onChange={(e)=> setFile(e.target.files?.[0] || null)} required />
            </div>
          )}

          {selected.endpoint.includes('/merge') && (
            <div>
              <label className="block text-sm text-gray-600 mb-1">Birden fazla PDF seçin</label>
              <input name="files" type="file" accept="application/pdf" multiple className="block w-full" required />
            </div>
          )}

          {selected.endpoint.includes('/compress') && (
            <div>
              <label className="block text-sm text-gray-600 mb-1">Kalite (0-100)</label>
              <input name="quality" type="number" min="0" max="100" defaultValue={85} className="w-full rounded-md border px-3 py-2" />
            </div>
          )}

          {selected.endpoint.includes('/split') && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Başlangıç</label>
                <input name="from_page" type="number" min="1" defaultValue={1} className="w-full rounded-md border px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Bitiş</label>
                <input name="to_page" type="number" min="1" className="w-full rounded-md border px-3 py-2" />
              </div>
            </div>
          )}

          {selected.endpoint.includes('/rotate') && (
            <div>
              <label className="block text-sm text-gray-600 mb-1">Derece</label>
              <input name="degrees" type="number" defaultValue={90} className="w-full rounded-md border px-3 py-2" />
            </div>
          )}

          {selected.endpoint.includes('/protect') && (
            <div>
              <label className="block text-sm text-gray-600 mb-1">Şifre</label>
              <input name="password" type="password" className="w-full rounded-md border px-3 py-2" required />
            </div>
          )}

          {selected.endpoint.includes('/html-to-pdf') && (
            <div className="space-y-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">URL</label>
                <input name="url" type="url" placeholder="https://..." className="w-full rounded-md border px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">veya HTML</label>
                <textarea name="html" rows="4" className="w-full rounded-md border px-3 py-2" placeholder="<h1>Merhaba</h1>"></textarea>
              </div>
            </div>
          )}

          <div className="pt-2 flex items-center justify-between">
            <div className="text-sm text-gray-500">Endpoint: <code className="bg-gray-100 px-2 py-0.5 rounded">{selected.endpoint}</code></div>
            <button disabled={busy} className="inline-flex items-center gap-2 rounded-lg bg-brand-600 text-white px-4 py-2 hover:bg-brand-700 disabled:opacity-60">
              {busy ? 'İşleniyor...' : 'Dönüştür'}
            </button>
          </div>
          {message && <div className="text-sm text-red-600">{message}</div>}
        </form>
      </div>
    </div>
  )
}

export default function App() {
  const [caps, setCaps] = useState([])
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    axios.get('/api/').then(r => setCaps(r.data)).catch(() => setCaps([]))
  }, [])

  const grouped = caps.reduce((acc, c) => {
    const key = c.to_type
    acc[key] = acc[key] || []
    acc[key].push(c)
    return acc
  }, {})

  return (
    <div>
      <Header />
      <main className="mx-auto max-w-7xl px-6 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Dönüştürme ve PDF Araçları</h1>
          <p className="text-gray-600 mt-2">Aşağıdaki araçlardan birini seçin ve dosyanızı yükleyin.</p>
        </div>

        <div className={CARD_GRID}>
          {caps.map((c, i) => (
            <CapabilityCard key={i} cap={c} onSelect={setSelected} />
          ))}
        </div>

        <footer className="mt-16 text-center text-sm text-gray-500">© {new Date().getFullYear()} Transformix</footer>
      </main>

      {selected && <Uploader selected={selected} onClose={() => setSelected(null)} />}
    </div>
  )
} 