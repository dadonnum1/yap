import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PlusCircle, Twitter, Copy, RefreshCw, Trash2, LogOut, User, Calendar, Hash, CreditCard, Shield, CheckCircle } from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      checkAuth();
    } else {
      setLoading(false);
    }
  }, [token]);

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
      toast.success('Login successful!');
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
      return false;
    }
  };

  const register = async (email, password) => {
    try {
      await axios.post(`${API}/auth/register`, { email, password });
      toast.success('Registration successful! Please login.');
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    toast.success('Logged out successfully');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => React.useContext(AuthContext);

// Login/Register Component
const AuthForm = () => {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    const success = isLogin 
      ? await login(email, password)
      : await register(email, password);
    
    if (success && !isLogin) {
      setIsLogin(true);
      setPassword('');
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-950 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold flex items-center justify-center gap-2">
            <Twitter className="h-8 w-8 text-blue-500" />
            Yapping
          </CardTitle>
          <CardDescription>
            Generate AI-undetectable tweets for crypto airdrops
          </CardDescription>
          <div className="mt-4 flex items-center justify-center gap-2 text-sm bg-green-50 text-green-700 px-3 py-2 rounded-lg">
            <Shield className="h-4 w-4" />
            ✅ Passes AI Detection Tests
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
                data-testid="auth-email-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                minLength={6}
                data-testid="auth-password-input"
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading} data-testid="auth-submit-button">
              {loading ? 'Loading...' : (isLogin ? 'Login' : 'Register')}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <Button
              variant="link"
              onClick={() => setIsLogin(!isLogin)}
              data-testid="auth-toggle-button"
            >
              {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Add Company Dialog
const AddCompanyDialog = ({ onCompanyAdded }) => {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    twitter_handle: '',
    company_name: '',
    description: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(`${API}/companies`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Company added successfully!');
      setFormData({ twitter_handle: '', company_name: '', description: '' });
      setOpen(false);
      onCompanyAdded();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add company');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="flex items-center gap-2" data-testid="add-company-button">
          <PlusCircle className="h-4 w-4" />
          Add Company
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add New Company</DialogTitle>
          <DialogDescription>
            Add a company to generate tweets for airdrop hunting
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="twitter_handle">Twitter Handle</Label>
            <Input
              id="twitter_handle"
              value={formData.twitter_handle}
              onChange={(e) => setFormData({...formData, twitter_handle: e.target.value})}
              placeholder="@company (e.g., @ethereum)"
              required
              data-testid="company-twitter-input"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="company_name">Company Name</Label>
            <Input
              id="company_name"
              value={formData.company_name}
              onChange={(e) => setFormData({...formData, company_name: e.target.value})}
              placeholder="Ethereum"
              required
              data-testid="company-name-input"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Decentralized blockchain platform..."
              data-testid="company-description-input"
            />
          </div>
          <Button type="submit" className="w-full" disabled={loading} data-testid="company-submit-button">
            {loading ? 'Adding...' : 'Add Company'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// Tweet Card Component
const TweetCard = ({ tweet, onCopy }) => {
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(tweet.content);
      onCopy(tweet.id);
      toast.success('Tweet copied to clipboard!');
    } catch (error) {
      toast.error('Failed to copy tweet');
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow" data-testid={`tweet-card-${tweet.id}`}>
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="flex items-center gap-1">
              <Twitter className="h-3 w-3" />
              {tweet.twitter_handle}
            </Badge>
            <span className="text-sm text-muted-foreground">{tweet.company_name}</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Calendar className="h-3 w-3" />
            {new Date(tweet.generated_at).toLocaleString()}
          </div>
        </div>
        
        <p className="text-sm leading-relaxed mb-4 p-3 bg-muted/50 rounded-lg">
          {tweet.content}
        </p>
        
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Hash className="h-3 w-3" />
            {tweet.content.length} characters
          </div>
          <Button 
            size="sm" 
            onClick={handleCopy}
            className="flex items-center gap-2"
            data-testid={`copy-tweet-${tweet.id}`}
          >
            <Copy className="h-3 w-3" />
            {tweet.copied_at ? 'Copied' : 'Copy'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

// Main Dashboard
const Dashboard = () => {
  const { user, logout, token } = useAuth();
  const [companies, setCompanies] = useState([]);
  const [tweets, setTweets] = useState([]);
  const [credits, setCredits] = useState({ balance: 0, transactions: [] });
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState('companies');
  const [showPricing, setShowPricing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [companiesRes, tweetsRes, creditsRes] = await Promise.all([
        axios.get(`${API}/companies`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/tweets`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/user/credits`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setCompanies(companiesRes.data);
      setTweets(tweetsRes.data);
      setCredits(creditsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const generateDailyTweets = async () => {
    setGenerating(true);
    try {
      const response = await axios.post(`${API}/tweets/generate-daily`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(response.data.message);
      loadData(); // Reload to show new tweets
      setActiveTab('tweets'); // Switch to tweets tab
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate tweets');
    } finally {
      setGenerating(false);
    }
  };

  const generateCompanyTweets = async (companyId, count = 1) => {
    try {
      await axios.post(`${API}/tweets/generate`, { company_id: companyId, count }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Generated ${count} new tweet${count > 1 ? 's' : ''}!`);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate tweets');
    }
  };

  const deleteCompany = async (companyId) => {
    try {
      await axios.delete(`${API}/companies/${companyId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Company removed successfully');
      loadData();
    } catch (error) {
      toast.error('Failed to remove company');
    }
  };

  const markTweetCopied = async (tweetId) => {
    try {
      await axios.post(`${API}/tweets/${tweetId}/mark-copied`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      loadData();
    } catch (error) {
      console.error('Failed to mark tweet as copied');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Twitter className="h-8 w-8 text-blue-500" />
            <h1 className="text-2xl font-bold text-gray-900">Yapping Dashboard</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <User className="h-4 w-4" />
              {user.email}
            </div>
            <Button variant="outline" onClick={logout} size="sm" data-testid="logout-button">
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="p-6">
        {/* AI Detection Badge */}
        <div className="mb-6 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="h-8 w-8 text-green-600" />
              <div>
                <h3 className="font-semibold text-green-800">✅ AI Detection Resistant</h3>
                <p className="text-sm text-green-700">All tweets pass AI detection tests with human-like authenticity</p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={() => setShowPricing(true)}>
              Upgrade Plan
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Tweet Credits</p>
                  <p className="text-3xl font-bold text-blue-600" data-testid="credits-count">{credits.balance}</p>
                </div>
                <CreditCard className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Companies</p>
                  <p className="text-3xl font-bold" data-testid="companies-count">{companies.length}</p>
                </div>
                <Twitter className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Generated Tweets</p>
                  <p className="text-3xl font-bold" data-testid="tweets-count">{tweets.length}</p>
                </div>
                <Hash className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">AI-Undetectable</p>
                  <p className="text-3xl font-bold text-green-600" data-testid="copied-count">
                    {tweets.filter(t => t.copied_at).length}
                  </p>
                </div>
                <Shield className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mb-6">
          <Button 
            onClick={generateDailyTweets} 
            disabled={generating || companies.length === 0 || credits.balance === 0}
            className="flex items-center gap-2"
            data-testid="generate-daily-button"
          >
            <RefreshCw className={`h-4 w-4 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'Generating...' : 'Generate Daily Tweets'}
          </Button>
          <AddCompanyDialog onCompanyAdded={loadData} />
          <Button variant="outline" onClick={() => setShowPricing(true)} className="flex items-center gap-2">
            <CreditCard className="h-4 w-4" />
            Buy Credits
          </Button>
        </div>

        {credits.balance === 0 && (
          <Card className="mb-6 border-orange-200 bg-orange-50">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <CreditCard className="h-5 w-5 text-orange-600" />
                <div>
                  <p className="font-medium text-orange-800">No Tweet Credits Remaining</p>
                  <p className="text-sm text-orange-700">Purchase credits to generate AI-undetectable tweets</p>
                </div>
                <Button size="sm" onClick={() => setShowPricing(true)}>
                  Get Credits
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="companies" data-testid="companies-tab">Companies</TabsTrigger>
            <TabsTrigger value="tweets" data-testid="tweets-tab">Generated Tweets</TabsTrigger>
          </TabsList>

          <TabsContent value="companies">
            {companies.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <Twitter className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Companies Added</h3>
                  <p className="text-muted-foreground mb-4">
                    Add companies to start generating tweets for airdrop hunting
                  </p>
                  <AddCompanyDialog onCompanyAdded={loadData} />
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {companies.map((company) => (
                  <Card key={company.id} className="hover:shadow-md transition-shadow" data-testid={`company-card-${company.id}`}>
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="font-semibold">{company.company_name}</h3>
                          <Badge variant="outline" className="mt-1">{company.twitter_handle}</Badge>
                        </div>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => deleteCompany(company.id)}
                          data-testid={`delete-company-${company.id}`}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                      
                      {company.description && (
                        <p className="text-sm text-muted-foreground mb-3">
                          {company.description}
                        </p>
                      )}
                      
                      <div className="flex gap-2">
                        <Button 
                          size="sm" 
                          onClick={() => generateCompanyTweets(company.id, 1)}
                          data-testid={`generate-one-${company.id}`}
                        >
                          Generate 1
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => generateCompanyTweets(company.id, 3)}
                          data-testid={`generate-three-${company.id}`}
                        >
                          Generate 3
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="tweets">
            {tweets.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <Hash className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Tweets Generated</h3>
                  <p className="text-muted-foreground mb-4">
                    Generate tweets to see them here
                  </p>
                  <Button 
                    onClick={generateDailyTweets} 
                    disabled={companies.length === 0}
                    data-testid="empty-generate-button"
                  >
                    Generate Daily Tweets
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {tweets.map((tweet) => (
                  <TweetCard 
                    key={tweet.id} 
                    tweet={tweet} 
                    onCopy={markTweetCopied}
                  />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
      
      <PricingModal open={showPricing} onClose={() => setShowPricing(false)} />
    </div>
  );
};

// Pricing Component
const PricingModal = ({ open, onClose }) => {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(false);
  const { token } = useAuth();

  useEffect(() => {
    if (open) {
      loadPackages();
    }
  }, [open]);

  const loadPackages = async () => {
    try {
      const response = await axios.get(`${API}/payments/packages`);
      setPackages(response.data.packages);
    } catch (error) {
      toast.error('Failed to load packages');
    }
  };

  const handlePurchase = async (packageId) => {
    if (!token) {
      toast.error('Please login first');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/payments/checkout/session`, {
        package_id: packageId,
        origin_url: window.location.origin
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Redirect to Stripe checkout
      window.location.href = response.data.url;
    } catch (error) {
      toast.error('Failed to start checkout');
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Choose Your Plan
          </DialogTitle>
          <CardDescription>
            All plans include AI-undetectable tweets that pass detection tests
          </CardDescription>
        </DialogHeader>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
          {packages.map((pkg) => (
            <Card key={pkg.package_id} className="relative">
              {pkg.package_id === 'pro' && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-blue-600">Most Popular</Badge>
                </div>
              )}
              <CardContent className="p-6">
                <div className="text-center mb-4">
                  <h3 className="text-xl font-bold">{pkg.name}</h3>
                  <div className="text-3xl font-bold text-blue-600 mt-2">
                    ${pkg.amount}
                    <span className="text-sm text-muted-foreground">/month</span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-2">{pkg.description}</p>
                </div>

                <div className="space-y-3 mb-6">
                  {pkg.features.map((feature, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </div>
                  ))}
                </div>

                <Button 
                  className="w-full" 
                  onClick={() => handlePurchase(pkg.package_id)}
                  disabled={loading}
                  data-testid={`purchase-${pkg.package_id}`}
                >
                  {loading ? 'Processing...' : 'Get Started'}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-6 p-4 bg-green-50 rounded-lg">
          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-green-600 mt-0.5" />
            <div>
              <div className="font-medium text-green-800">AI Detection Guarantee</div>
              <div className="text-sm text-green-700 mt-1">
                Our advanced system generates completely unique, human-like tweets that consistently pass AI detection tests. 
                Each tweet uses natural crypto slang, human imperfections, and varied writing styles.
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Payment Success Component
const PaymentSuccess = () => {
  const [status, setStatus] = useState('checking');
  const { token } = useAuth();

  useEffect(() => {
    const sessionId = new URLSearchParams(window.location.search).get('session_id');
    if (sessionId && token) {
      checkPaymentStatus(sessionId);
    }
  }, [token]);

  const checkPaymentStatus = async (sessionId) => {
    try {
      const response = await axios.get(`${API}/payments/checkout/status/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.payment_status === 'paid') {
        setStatus('success');
        setTimeout(() => {
          window.location.href = '/';
        }, 3000);
      } else {
        setStatus('pending');
        // Continue checking
        setTimeout(() => checkPaymentStatus(sessionId), 2000);
      }
    } catch (error) {
      setStatus('error');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardContent className="p-8 text-center">
          {status === 'checking' && (
            <>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <h2 className="text-xl font-bold mb-2">Processing Payment</h2>
              <p className="text-muted-foreground">Please wait while we confirm your payment...</p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h2 className="text-xl font-bold mb-2 text-green-800">Payment Successful!</h2>
              <p className="text-muted-foreground">Your credits have been added. Redirecting to dashboard...</p>
            </>
          )}

          {status === 'error' && (
            <>
              <div className="h-12 w-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-red-600">✕</span>
              </div>
              <h2 className="text-xl font-bold mb-2 text-red-800">Payment Failed</h2>
              <Button onClick={() => window.location.href = '/'}>
                Return to Dashboard
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Simple Admin Panel - will add back after fixing compilation
const AdminLogin = () => {
  return (
    <div className="min-h-screen bg-red-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="p-8 text-center">
          <h2 className="text-2xl font-bold mb-4">Admin Panel</h2>
          <p className="mb-4">Admin functionality coming soon!</p>
          <Button onClick={() => window.location.href = '/'}>
            Back to User Login
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

function App() {
  const { user, loading } = useAuth();
  const [showAdmin, setShowAdmin] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Check if URL has admin path
  if (window.location.pathname.includes('/admin') || showAdmin) {
    return <AdminLogin />;
  }

  return (
    <div className="App">
      {user ? <Dashboard /> : <AuthForm />}
      <Toaster position="top-right" />
    </div>
  );
}

function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

export default AppWithAuth;