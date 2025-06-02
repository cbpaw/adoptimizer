import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function FacebookDashboard({ 
  facebookAccounts, 
  facebookAds, 
  selectedCampaignsCount,
  onShowFacebookSetup,
  onSyncFacebookAds 
}) {
  const activeAdsCount = facebookAds.filter(ad => ad.status === 'ACTIVE').length;

  const getStatusBadgeVariant = (status) => {
    switch (status) {
      case 'ACTIVE':
        return 'default';
      case 'PAUSED':
        return 'secondary';
      default:
        return 'destructive';
    }
  };

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Welcome to AdOptimizer!</CardTitle>
          <CardDescription>Your Facebook Ads Management Dashboard</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Manage and optimize your Facebook advertising campaigns from here.
          </p>
          <div className="flex items-center gap-3">
            <img className="h-24 w-auto" src="/static/images/web/rocket-laptop.svg" alt="Fly Away!" />
          </div>
        </CardContent>
      </Card>

      {/* Facebook Ads Section */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-xl">Facebook Ads</CardTitle>
            <div className="flex items-center gap-2">
              {!facebookAccounts?.length ? (
                <Button onClick={onShowFacebookSetup}>
                  Connect Facebook Account
                </Button>
              ) : (
                <>
                  <Button variant="outline" onClick={onSyncFacebookAds}>
                    Sync Ads
                  </Button>
                  <Button variant="outline" asChild>
                    <a href="/facebook-ads/manage-accounts/">Manage Accounts</a>
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {facebookAccounts?.length ? (
            <>
              {/* Campaign Selection Info */}
              <Alert className="mb-6">
                <AlertDescription>
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="font-medium">Campagne Monitoring</h4>
                      <p className="text-sm">
                        {selectedCampaignsCount > 0 
                          ? `${selectedCampaignsCount} campagne${selectedCampaignsCount > 1 ? 's' : ''} geselecteerd voor monitoring`
                          : 'Geen campagnes geselecteerd voor monitoring'
                        }
                      </p>
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <a href="/facebook-ads/campaigns/">
                        <i className="fa fa-bullhorn mr-2"></i>
                        Selecteer Campagnes
                      </a>
                    </Button>
                  </div>
                </AlertDescription>
              </Alert>
              
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <Card>
                  <CardContent className="p-6">
                    <div className="text-2xl font-bold text-blue-600">{facebookAds.length}</div>
                    <div className="text-sm text-muted-foreground">Total Ads</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <div className="text-2xl font-bold text-green-600">{activeAdsCount}</div>
                    <div className="text-sm text-muted-foreground">Active Ads</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <div className="text-2xl font-bold text-purple-600">$0.00</div>
                    <div className="text-sm text-muted-foreground">Total Spend</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <div className="text-2xl font-bold text-orange-600">0</div>
                    <div className="text-sm text-muted-foreground">Impressions</div>
                  </CardContent>
                </Card>
              </div>
              
              {/* Ads Table */}
              <Card>
                <CardHeader>
                  <CardTitle>
                    Recent Ads
                    {selectedCampaignsCount > 0 && (
                      <span className="text-sm font-normal text-muted-foreground ml-2">
                        (van geselecteerde campagnes)
                      </span>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Ad Name</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Campaign</TableHead>
                        <TableHead>Spend</TableHead>
                        <TableHead>Impressions</TableHead>
                        <TableHead>Clicks</TableHead>
                        <TableHead>CTR</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {facebookAds.length > 0 ? (
                        facebookAds.map((ad, index) => (
                          <TableRow key={index}>
                            <TableCell className="font-medium">
                              {ad.ad_name.length > 30 ? ad.ad_name.substring(0, 30) + '...' : ad.ad_name}
                            </TableCell>
                            <TableCell>
                              <Badge variant={getStatusBadgeVariant(ad.status)}>
                                {ad.status}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-muted-foreground">
                              {ad.campaign_name.length > 25 ? ad.campaign_name.substring(0, 25) + '...' : ad.campaign_name}
                            </TableCell>
                            <TableCell>${ad.spend}</TableCell>
                            <TableCell>{Math.floor(ad.impressions)}</TableCell>
                            <TableCell>{ad.clicks}</TableCell>
                            <TableCell>{parseFloat(ad.ctr).toFixed(2)}%</TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan="7" className="text-center py-8 text-muted-foreground">
                            {selectedCampaignsCount === 0 ? (
                              <>
                                No campaigns selected for monitoring.{' '}
                                <a href="/facebook-ads/campaigns/" className="text-primary hover:underline">
                                  Select campaigns
                                </a>
                              </>
                            ) : (
                              'No ads found for selected campaigns.'
                            )}
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          ) : (
            <div className="text-center py-12">
              <div className="text-muted-foreground mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium mb-2">No Facebook Ad Accounts Connected</h3>
              <p className="text-muted-foreground mb-4">
                Connect your Facebook ad account to view and manage your ads from this dashboard.
              </p>
              <Button onClick={onShowFacebookSetup}>
                Connect Facebook Account
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 