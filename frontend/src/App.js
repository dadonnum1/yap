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
import { PlusCircle, Twitter, Copy, RefreshCw, Trash2, LogOut, User, Calendar, Hash } from 'lucide-react';
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
            Generate engaging tweets for crypto airdrops
          </CardDescription>
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
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState('companies');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [companiesRes, tweetsRes] = await Promise.all([
        axios.get(`${API}/companies`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/tweets`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setCompanies(companiesRes.data);
      setTweets(tweetsRes.data);
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
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
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
                  <p className="text-sm text-muted-foreground">Copied Tweets</p>
                  <p className="text-3xl font-bold" data-testid="copied-count">
                    {tweets.filter(t => t.copied_at).length}
                  </p>
                </div>
                <Copy className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mb-6">
          <Button 
            onClick={generateDailyTweets} 
            disabled={generating || companies.length === 0}
            className="flex items-center gap-2"
            data-testid="generate-daily-button"
          >
            <RefreshCw className={`h-4 w-4 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'Generating...' : 'Generate Daily Tweets'}
          </Button>
          <AddCompanyDialog onCompanyAdded={loadData} />
        </div>

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
    </div>
  );
};

// Main App
function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="App">
      {user ? <Dashboard /> : <AuthForm />}
      <Toaster position="top-right" />
    </div>
  );
}

// Admin Login Component
const AdminLogin = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [adminToken, setAdminToken] = useState(localStorage.getItem('adminToken'));

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/admin/login`, { username, password });
      const { access_token } = response.data;
      localStorage.setItem('adminToken', access_token);
      setAdminToken(access_token);
      toast.success('Admin login successful!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Admin login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    setAdminToken(null);
    toast.success('Logged out successfully');
  };

  if (adminToken) {
    return <AdminDashboard token={adminToken} onLogout={handleLogout} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-950 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
      <Card className=\"w-full max-w-md\">
        <CardHeader className=\"text-center\">
          <CardTitle className=\"text-2xl font-bold flex items-center justify-center gap-2\">
            <User className=\"h-8 w-8 text-red-500\" />
            Admin Panel
          </CardTitle>
          <CardDescription>
            Access system administration
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAdminLogin} className=\"space-y-4\">
            <div className=\"space-y-2\">
              <Label htmlFor=\"username\">Username</Label>
              <Input
                id=\"username\"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder=\"Enter admin username\"
                required
                data-testid=\"admin-username-input\"
              />
            </div>
            <div className=\"space-y-2\">
              <Label htmlFor=\"password\">Password</Label>
              <Input
                id=\"password\"
                type=\"password\"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder=\"Enter admin password\"
                required
                data-testid=\"admin-password-input\"
              />
            </div>
            <Button type=\"submit\" className=\"w-full\" disabled={loading} data-testid=\"admin-login-button\">
              {loading ? 'Logging in...' : 'Admin Login'}
            </Button>
          </form>
          <div className=\"mt-4 text-center\">
            <Button variant=\"link\" onClick={() => window.location.href = '/'}>
              ← Back to User Login
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Admin Dashboard Component
const AdminDashboard = ({ token, onLogout }) => {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [tweets, setTweets] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      const [statsRes, usersRes, companiesRes, tweetsRes] = await Promise.all([
        axios.get(`${API}/admin/stats`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/users`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/companies`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/tweets`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setStats(statsRes.data);
      setUsers(usersRes.data);
      setCompanies(companiesRes.data);
      setTweets(tweetsRes.data);
    } catch (error) {
      toast.error('Failed to load admin data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const toggleUserStatus = async (userId) => {
    try {
      await axios.post(`${API}/admin/users/${userId}/toggle`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('User status updated');
      loadAdminData();
    } catch (error) {
      toast.error('Failed to update user status');
    }
  };

  const deleteCompany = async (companyId) => {
    try {
      await axios.delete(`${API}/admin/companies/${companyId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Company deactivated');
      loadAdminData();
    } catch (error) {
      toast.error('Failed to deactivate company');
    }
  };

  if (loading) {
    return (
      <div className=\"min-h-screen flex items-center justify-center\">
        <div className=\"animate-spin rounded-full h-8 w-8 border-b-2 border-red-500\"></div>
      </div>
    );
  }

  return (
    <div className=\"min-h-screen bg-gray-50\">
      {/* Header */}
      <header className=\"bg-white border-b border-gray-200 px-6 py-4\">
        <div className=\"flex justify-between items-center\">
          <div className=\"flex items-center gap-3\">
            <User className=\"h-8 w-8 text-red-500\" />
            <h1 className=\"text-2xl font-bold text-gray-900\">Admin Dashboard</h1>
          </div>
          <Button variant=\"outline\" onClick={onLogout} size=\"sm\" data-testid=\"admin-logout-button\">
            <LogOut className=\"h-4 w-4 mr-2\" />
            Logout
          </Button>
        </div>
      </header>

      <div className=\"p-6\">
        {/* Stats Cards */}
        {stats && (
          <div className=\"grid grid-cols-1 md:grid-cols-5 gap-6 mb-8\">
            <Card>
              <CardContent className=\"p-6 text-center\">
                <div className=\"text-2xl font-bold text-blue-600\">{stats.total_users}</div>
                <div className=\"text-sm text-muted-foreground\">Total Users</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className=\"p-6 text-center\">
                <div className=\"text-2xl font-bold text-green-600\">{stats.total_companies}</div>
                <div className=\"text-sm text-muted-foreground\">Companies</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className=\"p-6 text-center\">
                <div className=\"text-2xl font-bold text-purple-600\">{stats.total_tweets}</div>
                <div className=\"text-sm text-muted-foreground\">Total Tweets</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className=\"p-6 text-center\">
                <div className=\"text-2xl font-bold text-orange-600\">{stats.active_users}</div>
                <div className=\"text-sm text-muted-foreground\">Active Users</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className=\"p-6 text-center\">
                <div className=\"text-2xl font-bold text-red-600\">{stats.tweets_today}</div>
                <div className=\"text-sm text-muted-foreground\">Tweets Today</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className=\"mb-6\">
            <TabsTrigger value=\"overview\">Overview</TabsTrigger>
            <TabsTrigger value=\"users\">Users</TabsTrigger>
            <TabsTrigger value=\"companies\">Companies</TabsTrigger>
            <TabsTrigger value=\"tweets\">Tweets</TabsTrigger>
          </TabsList>

          <TabsContent value=\"users\">
            <Card>
              <CardHeader>
                <CardTitle>User Management</CardTitle>
              </CardHeader>
              <CardContent>
                <div className=\"space-y-4\">
                  {users.map((user) => (
                    <div key={user.id} className=\"flex items-center justify-between p-4 border rounded-lg\">
                      <div>
                        <div className=\"font-medium\">{user.email}</div>
                        <div className=\"text-sm text-muted-foreground\">
                          {user.company_count} companies • {user.tweet_count} tweets
                        </div>
                      </div>
                      <div className=\"flex items-center gap-2\">
                        <Badge variant={user.is_active ? 'default' : 'secondary'}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                        <Button 
                          size=\"sm\" 
                          variant=\"outline\"
                          onClick={() => toggleUserStatus(user.id)}
                        >
                          {user.is_active ? 'Deactivate' : 'Activate'}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value=\"companies\">
            <Card>
              <CardHeader>
                <CardTitle>Company Management</CardTitle>
              </CardHeader>
              <CardContent>
                <div className=\"space-y-4\">
                  {companies.map((company) => (
                    <div key={company.id} className=\"flex items-center justify-between p-4 border rounded-lg\">
                      <div>
                        <div className=\"font-medium\">{company.company_name}</div>
                        <div className=\"text-sm text-muted-foreground\">
                          {company.twitter_handle} • {company.user_email} • {company.tweet_count} tweets
                        </div>
                      </div>
                      <div className=\"flex items-center gap-2\">
                        <Badge variant={company.is_active ? 'default' : 'secondary'}>
                          {company.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                        {company.is_active && (
                          <Button 
                            size=\"sm\" 
                            variant=\"destructive\"
                            onClick={() => deleteCompany(company.id)}
                          >
                            Deactivate
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value=\"tweets\">
            <Card>
              <CardHeader>
                <CardTitle>Recent Tweets</CardTitle>
              </CardHeader>
              <CardContent>
                <div className=\"space-y-4\">
                  {tweets.map((tweet) => (
                    <div key={tweet.id} className=\"p-4 border rounded-lg\">
                      <div className=\"flex items-start justify-between mb-2\">
                        <div className=\"text-sm text-muted-foreground\">
                          {tweet.company_name} ({tweet.twitter_handle}) • {tweet.user_email}
                        </div>
                        <div className=\"text-xs text-muted-foreground\">
                          {new Date(tweet.generated_at).toLocaleString()}
                        </div>
                      </div>
                      <div className=\"text-sm bg-muted/50 p-3 rounded\">
                        {tweet.content}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

function App() {
  const { user, loading } = useAuth();
  const [showAdmin, setShowAdmin] = useState(false);

  if (loading) {
    return (
      <div className=\"min-h-screen flex items-center justify-center bg-gray-50\">
        <div className=\"animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500\"></div>
      </div>
    );
  }

  // Check if URL has admin path
  if (window.location.pathname.includes('/admin') || showAdmin) {
    return <AdminLogin />;
  }

  return (
    <div className=\"App\">
      {user ? <Dashboard /> : <AuthForm />}
      <Toaster position=\"top-right\" />
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