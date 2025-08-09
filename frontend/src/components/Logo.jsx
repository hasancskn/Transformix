import React from 'react'

export default function Logo({ className = 'h-8 w-8' }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#a78bfa" />
          <stop offset="100%" stopColor="#7c3aed" />
        </linearGradient>
      </defs>
      <rect rx="14" ry="14" width="64" height="64" fill="url(#g)" />
      <path d="M20 34c0-6.627 5.373-12 12-12h2v-6l10 9-10 9v-6h-2c-3.314 0-6 2.686-6 6 0 3.314 2.686 6 6 6h6v6h-6c-6.627 0-12-5.373-12-12z" fill="white"/>
    </svg>
  )
} 