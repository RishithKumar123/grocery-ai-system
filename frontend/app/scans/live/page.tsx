"use client"

import React, { useState, useRef, useEffect } from 'react'

export default function LiveScannerPage() {
  const [source, setSource] = useState('')
  const [skipFrames, setSkipFrames] = useState(5)
  const [streamId, setStreamId] = useState<string | null>(null)
  const [status, setStatus] = useState<any>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const apiBase = (process.env.NEXT_PUBLIC_API_BASE as string) || ''

  const startStream = async () => {
    const res = await fetch(`${apiBase}/api/v1/barcode/live/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source, skip_frames: Number(skipFrames) })
    })
    const body = await res.json()
    setStreamId(body.stream_id)
  }

  const stopStream = async () => {
    if (!streamId) return
    await fetch('/api/v1/barcode/live/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stream_id: streamId })
    })
    setStreamId(null)
    setStatus(null)
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }

  useEffect(() => {
    if (!streamId) return
    const api = (process.env.NEXT_PUBLIC_API_BASE as string) || ''
    // build websocket url from apiBase; if empty, use current host
    let wsUrl = ''
    if (api) {
      const url = new URL(api)
      const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl = `${protocol}//${url.host}/api/v1/barcode/live/ws?stream_id=${streamId}`
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const host = window.location.host
      wsUrl = `${protocol}://${host}/api/v1/barcode/live/ws?stream_id=${streamId}`
    }
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data)
        setStatus(data)
      } catch (e) {
        // ignore
      }
    }
    ws.onclose = () => {
      wsRef.current = null
    }
    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [streamId])

  return (
    <div style={{ padding: 20 }}>
      <h1>Live Scanner</h1>
      <div style={{ marginBottom: 12 }}>
        <label>Camera Source (RTSP/URL/Device):</label>
        <input style={{ width: '100%' }} value={source} onChange={e => setSource(e.target.value)} placeholder="rtsp://... or /dev/video0" />
      </div>
      <div style={{ marginBottom: 12 }}>
        <label>Skip Frames:</label>
        <input type="number" value={skipFrames} onChange={e => setSkipFrames(Number(e.target.value))} />
      </div>
      <div style={{ marginBottom: 12 }}>
        {!streamId ? (
          <button onClick={startStream}>Start Stream</button>
        ) : (
          <button onClick={stopStream}>Stop Stream</button>
        )}
      </div>
      {streamId && <div style={{ marginBottom: 12 }}>Stream ID: {streamId}</div>}
      {status && (
        <div>
          <h3>Stream Status</h3>
          <pre>{JSON.stringify(status, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
