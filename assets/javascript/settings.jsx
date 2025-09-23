import React from 'react'
import { createRoot } from 'react-dom/client'
import SettingsPage from './components/settings/SettingsPage'

// Initialize settings page when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const settingsContainer = document.getElementById('settings-container')

  if (settingsContainer) {
    // Get data from the container's data attributes
    const initialFacebookToken = JSON.parse(settingsContainer.dataset.facebookToken || 'null')
    const csrfToken = settingsContainer.dataset.csrfToken

    const root = createRoot(settingsContainer)
    root.render(
      <SettingsPage
        initialFacebookToken={initialFacebookToken}
        csrfToken={csrfToken}
      />
    )
  }
})