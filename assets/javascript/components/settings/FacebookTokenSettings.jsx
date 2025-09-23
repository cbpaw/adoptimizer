import * as React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Form, FormField, FormLabel, FormDescription } from "@/components/ui/form"
import { usePageNotifications } from "@/components/ui/page-notifications"
import { cn } from "@/utilities/shadcn"

function FacebookTokenStatus({ token, onUpdate, onRevoke }) {
  if (!token || !token.has_token) {
    return (
      <Alert variant="warning" className="mb-6">
        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <circle cx="12" cy="17" r="1" fill="currentColor"/>
        </svg>
        <AlertDescription>
          <strong>Facebook Token Required</strong><br />
          Please provide your Facebook access token to connect your account.
        </AlertDescription>
      </Alert>
    )
  }

  const isExpired = token.token_expired
  const expiresSoon = token.token_expires_soon
  let variant = "success"
  let title = "Token Active"

  if (isExpired) {
    variant = "error"
    title = "Token Expired"
  } else if (expiresSoon) {
    variant = "warning"
    title = "Token Expires Soon"
  }

  return (
    <div className="space-y-6">
      <Alert variant={variant}>
        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <polyline points="22,4 12,14.01 9,11.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <AlertDescription>
          <strong>{title}</strong><br />
          Connected to: {token.facebook_user_name}
          {token.facebook_user_email && (
            <span className="text-xs opacity-70"> ({token.facebook_user_email})</span>
          )}
          {expiresSoon && !isExpired && (
            <div className="mt-1 text-sm">Token expires soon. Consider refreshing.</div>
          )}
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Facebook ID</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm font-mono">{token.facebook_user_id}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Last Used</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{new Date(token.last_used_at).toLocaleDateString()}</p>
          </CardContent>
        </Card>
      </div>

      {token.scopes && token.scopes.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Granted Permissions</h3>
          <div className="flex flex-wrap gap-2">
            {token.scopes.map((scope, index) => (
              <Badge key={index} variant="default">{scope}</Badge>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <Button onClick={onUpdate} variant="default">
          <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M23 4v6h-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M1 20v-6h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Update Token
        </Button>
        <Button onClick={onRevoke} variant="destructive">
          <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polyline points="3,6 5,6 21,6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6h14z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Revoke Token
        </Button>
      </div>
    </div>
  )
}

function FacebookTokenForm({ onSubmit, isLoading }) {
  const [token, setToken] = React.useState("")

  const handleSubmit = (e) => {
    e.preventDefault()
    if (token.trim()) {
      onSubmit(token.trim())
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Facebook Access Token</CardTitle>
        <CardDescription>
          Enter your Facebook access token to connect your account.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form onSubmit={handleSubmit}>
          <FormField>
            <div className="flex justify-between items-center">
              <FormLabel htmlFor="access_token">Access Token</FormLabel>
              <a
                href="https://developers.facebook.com/tools/explorer/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Get Token
              </a>
            </div>
            <Textarea
              id="access_token"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Paste your Facebook access token here..."
              rows={4}
              required
            />
            <FormDescription>
              Get a User Access Token from Facebook Graph API Explorer
            </FormDescription>
          </FormField>

          <Button type="submit" disabled={isLoading || !token.trim()}>
            {isLoading && (
              <svg className="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.25"/>
                <path d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 0 1 4 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" fill="currentColor"/>
              </svg>
            )}
            <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" fill="currentColor"/>
            </svg>
            {isLoading ? "Validating..." : "Validate & Save Token"}
          </Button>
        </Form>
      </CardContent>
    </Card>
  )
}

function FacebookTokenInstructions() {
  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="text-base">How to get a Facebook Access Token</CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="list-decimal list-inside space-y-2 text-sm">
          <li>
            Visit the{" "}
            <a
              href="https://developers.facebook.com/tools/explorer/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800"
            >
              Facebook Graph API Explorer
            </a>
          </li>
          <li>Select your app or create a new one</li>
          <li>
            Generate a User Access Token with required permissions:
            <ul className="list-disc list-inside ml-4 mt-1">
              <li>ads_management</li>
              <li>ads_read</li>
              <li>business_management</li>
              <li>pages_read_engagement</li>
            </ul>
          </li>
          <li>Copy the generated token and paste it above</li>
          <li>Click 'Validate & Save Token' to test and store it</li>
        </ol>
      </CardContent>
    </Card>
  )
}

export function FacebookTokenSettings({ initialToken, csrfToken }) {
  const [token, setToken] = React.useState(initialToken)
  const [isLoading, setIsLoading] = React.useState(false)
  const [showForm, setShowForm] = React.useState(!initialToken?.has_token)
  const notifications = usePageNotifications()

  const handleTokenSubmit = async (accessToken) => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/v1/facebook/token/validate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ access_token: accessToken })
      })

      const data = await response.json()

      if (response.ok && data.success) {
        setToken(data)
        setShowForm(false)
        notifications.success(
          'Token validated successfully!',
          `Connected to: ${data.user_info.name}`
        )
      } else {
        notifications.error(
          'Validation Error',
          `${data.error}${data.details ? '. ' + data.details : ''}`
        )
      }
    } catch (error) {
      notifications.error(
        'Network Error',
        'Please check your internet connection and try again.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleTokenRevoke = async () => {
    if (!confirm('Are you sure you want to revoke your Facebook token?')) {
      return
    }

    try {
      const response = await fetch('/api/v1/facebook/token/revoke/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken
        }
      })

      const data = await response.json()

      if (response.ok && data.success) {
        setToken(null)
        setShowForm(true)
        notifications.success(
          'Token Revoked',
          'Your Facebook token has been successfully revoked.'
        )
      } else {
        notifications.error(
          'Revocation Error',
          data.error
        )
      }
    } catch (error) {
      notifications.error(
        'Network Error',
        'Please check your internet connection and try again.'
      )
    }
  }

  const handleTokenUpdate = () => {
    setShowForm(true)
  }

  return (
    <div className="space-y-6">
      {!showForm && token?.has_token ? (
        <FacebookTokenStatus
          token={token}
          onUpdate={handleTokenUpdate}
          onRevoke={handleTokenRevoke}
        />
      ) : (
        <>
          <FacebookTokenForm
            onSubmit={handleTokenSubmit}
            isLoading={isLoading}
          />
          <FacebookTokenInstructions />
        </>
      )}
    </div>
  )
}

export default FacebookTokenSettings