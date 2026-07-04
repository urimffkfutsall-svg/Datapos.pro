import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, useTenant } from '../App';
import { Button } from '../components/ui/button';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '../components/ui/dialog';
import {
  Delete, CornerDownLeft, User, Lock, Eye, EyeOff,
  ArrowLeft, AlertTriangle, CreditCard, Phone,
  ShoppingCart, Package, BarChart3, Users, Boxes, Ticket,
} from 'lucide-react';

const SERVICES = [
  { icon: ShoppingCart, label: 'Arka POS' },
  { icon: Package,      label: 'Produkte' },
  { icon: BarChart3,    label: 'Raporte' },
  { icon: Users,        label: 'Klientet' },
  { icon: Boxes,        label: 'Stoku' },
  { icon: Ticket,       label: 'Kuponja' },
];

const Login = () => {
  const [pin, setPin] = useState('');
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showExpiredModal, setShowExpiredModal] = useState(false);
  const [expiredDays, setExpiredDays] = useState(0);
  const [rememberMe, setRememberMe] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const tenantContext = useTenant();
  const tenant = tenantContext?.tenant;
  const tenantLoading = tenantContext?.tenantLoading;

  const logoSrc = tenant?.logo_url || '/logo-icon.png';
  const brandName = tenant?.company_name || tenant?.name || 'DataPOS';

  const handleSubscriptionExpired = (errorDetail) => {
    if (errorDetail && errorDetail.startsWith('SUBSCRIPTION_EXPIRED|')) {
      const days = parseInt(errorDetail.split('|')[1]) || 0;
      setExpiredDays(days);
      setShowExpiredModal(true);
      return true;
    }
    return false;
  };

  const handlePinLogin = async () => {
    if (pin.length < 1) return;
    setLoading(true);
    setError('');
    const result = await login(pin, pin);
    setLoading(false);
    if (result.success) {
      navigate('/pos');
    } else {
      if (result.status === 402 && handleSubscriptionExpired(result.error)) {
        setPin('');
        return;
      }
      setPin('');
      setError('PIN i gabuar. Provoni perseri.');
    }
  };

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const result = await login(username, password);
    setLoading(false);
    if (result.success) {
      navigate('/dashboard');
    } else {
      if (result.status === 402 && handleSubscriptionExpired(result.error)) {
        return;
      }
      setError(result.error || 'Username ose fjalekalimi i gabuar');
    }
  };

  const addDigit = useCallback((digit) => {
    if (pin.length < 6) setPin(prev => prev + digit);
  }, [pin]);

  const removeDigit = useCallback(() => {
    setPin(prev => prev.slice(0, -1));
  }, []);

  const clearPin = () => setPin('');

  useEffect(() => {
    if (showAdminLogin) return;
    const handleKeyDown = (e) => {
      const ae = document.activeElement;
      if (ae && (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA')) return;
      if (e.key >= '0' && e.key <= '9') addDigit(e.key);
      else if (e.key === 'Backspace') { e.preventDefault(); removeDigit(); }
      else if (e.key === 'Enter' && pin.length >= 1) handlePinLogin();
      else if (e.key === 'Escape') clearPin();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showAdminLogin, pin, addDigit, removeDigit]);

  const numpadButtons = ['1','2','3','4','5','6','7','8','9','clear','0','delete'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center p-4">
      <div className="w-full max-w-5xl">
        <div className="relative bg-white rounded-3xl shadow-2xl overflow-hidden min-h-[600px]">
          <div className="absolute inset-0 bg-[#2563EB] [clip-path:polygon(48%_0,100%_0,100%_100%,32%_100%)]" />

          <div className="relative grid grid-cols-1 lg:grid-cols-2 min-h-[600px]">
            {/* LEFT: e bardhe - logo blu + brand + sherbimet */}
            <div className="flex items-center h-full p-8 lg:pl-14 lg:pr-8 relative z-10">
              <div className="w-full max-w-[240px] mx-auto lg:mx-0 flex flex-col items-center">
                {/* Logo ne kontejner blu */}
                <div className="w-24 h-24 bg-[#2563EB] rounded-3xl shadow-lg flex items-center justify-center mb-4">
                  <img
                    src={logoSrc}
                    alt={brandName}
                    className="w-16 h-16 object-contain"
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                </div>

                {/* Emri firmes */}
                <h1 className="text-2xl font-bold text-[#2563EB] tracking-tight text-center leading-tight break-words w-full">
                  {brandName}
                </h1>
                <p className="text-[11px] text-gray-500 text-center mt-1 mb-5">Sistemi POS Moderne</p>

                {/* Sherbimet - grid 2 kolonash */}
                <div className="grid grid-cols-2 gap-2 w-full">
                  {SERVICES.map((s, i) => {
                    const Icon = s.icon;
                    return (
                      <div key={i} className="flex items-center gap-1.5 bg-gray-50 rounded-lg px-2 py-1.5 border border-gray-100">
                        <div className="w-6 h-6 bg-blue-50 rounded-md flex items-center justify-center flex-shrink-0">
                          <Icon className="w-3.5 h-3.5 text-[#2563EB]" />
                        </div>
                        <span className="text-[11px] text-gray-700 font-medium truncate">{s.label}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* RIGHT: forma blu */}
            <div className="flex flex-col justify-center p-8 lg:p-12 text-white relative z-10">
              {tenantLoading && (
                <div className="flex items-center justify-center py-10">
                  <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin" />
                </div>
              )}

              {!tenantLoading && !showAdminLogin && (
                <>
                  <h2 className="text-2xl lg:text-3xl font-bold mb-1">Kycje e Shpejte</h2>
                  <p className="text-blue-100 text-sm mb-5">Shkruaj kodin PIN per te hyre</p>

                  <div className="mb-4">
                    <div className="w-full h-14 rounded-xl bg-white/10 backdrop-blur-sm border border-white/25 flex items-center justify-center text-2xl font-bold tracking-[0.5em] text-white">
                      {pin ? '\u2022'.repeat(pin.length) : <span className="text-blue-200 text-base tracking-normal">PIN</span>}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2.5 mb-4">
                    {numpadButtons.map((btn) => {
                      if (btn === 'clear') return (
                        <button key={btn} onClick={clearPin} className="h-12 rounded-xl bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/25 text-white font-medium transition-all">C</button>
                      );
                      if (btn === 'delete') return (
                        <button key={btn} onClick={removeDigit} className="h-12 rounded-xl bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/25 flex items-center justify-center transition-all">
                          <Delete className="h-5 w-5 text-white" />
                        </button>
                      );
                      return (
                        <button key={btn} onClick={() => addDigit(btn)} className="h-12 rounded-xl bg-white hover:bg-blue-50 text-[#2563EB] text-xl font-bold transition-all shadow-sm">{btn}</button>
                      );
                    })}
                  </div>

                  {error && (
                    <div className="bg-red-500/20 border border-red-300/40 text-red-100 px-3 py-2 rounded-xl text-sm text-center mb-3">{error}</div>
                  )}

                  <Button
                    onClick={handlePinLogin}
                    disabled={pin.length < 1 || loading}
                    className="w-full h-12 bg-white hover:bg-blue-50 text-[#2563EB] font-bold rounded-xl shadow-lg tracking-wider transition-all flex items-center justify-center gap-2"
                  >
                    {loading ? <div className="w-5 h-5 border-2 border-[#2563EB] border-t-transparent rounded-full animate-spin" /> : (<><CornerDownLeft className="h-4 w-4" /> KYCU</>)}
                  </Button>

                  <button
                    onClick={() => { setShowAdminLogin(true); setError(''); }}
                    className="mt-5 text-center w-full text-blue-100 hover:text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    <User className="h-4 w-4" />
                    Kycu si Administrator
                  </button>

                  <p className="text-blue-200/70 text-xs text-center mt-3">
                    Perdor tastet 0-9, Backspace, Enter
                  </p>
                </>
              )}

              {!tenantLoading && showAdminLogin && (
                <>
                  <button
                    onClick={() => { setShowAdminLogin(false); setUsername(''); setPassword(''); setError(''); }}
                    className="flex items-center gap-1 text-blue-100 hover:text-white text-sm mb-3 self-start transition-colors"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    Kthehu
                  </button>
                  <h2 className="text-2xl lg:text-3xl font-bold mb-1">Administrator</h2>
                  <p className="text-blue-100 text-sm mb-5">Vendos kredencialet per te vazhduar</p>

                  <form onSubmit={handleAdminLogin} className="space-y-4">
                    <div>
                      <label className="block text-blue-100 text-xs font-medium mb-1.5">Username</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <User className="h-4 w-4 text-gray-400" />
                        </div>
                        <input
                          type="text"
                          placeholder="Enter your username"
                          value={username}
                          onChange={(e) => setUsername(e.target.value)}
                          className="w-full pl-10 h-11 bg-white text-gray-900 placeholder-gray-400 border-0 rounded-lg focus:ring-2 focus:ring-white outline-none transition-all"
                          required
                          autoFocus
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-blue-100 text-xs font-medium mb-1.5">Password</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <Lock className="h-4 w-4 text-gray-400" />
                        </div>
                        <input
                          type={showPassword ? 'text' : 'password'}
                          placeholder="Enter your password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          className="w-full pl-10 pr-10 h-11 bg-white text-gray-900 placeholder-gray-400 border-0 rounded-lg focus:ring-2 focus:ring-white outline-none transition-all"
                          required
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute inset-y-0 right-0 pr-3 flex items-center"
                        >
                          {showPassword ? <EyeOff className="h-4 w-4 text-gray-400" /> : <Eye className="h-4 w-4 text-gray-400" />}
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <label className="flex items-center gap-2 cursor-pointer text-blue-100 select-none">
                        <input
                          type="checkbox"
                          checked={rememberMe}
                          onChange={(e) => setRememberMe(e.target.checked)}
                          className="w-4 h-4 rounded border-white/40 bg-white/10 accent-white"
                        />
                        Remember me
                      </label>
                      <button type="button" className="text-white hover:underline text-sm">Recover password</button>
                    </div>

                    {error && (
                      <div className="bg-red-500/20 border border-red-300/40 text-red-100 px-3 py-2 rounded-lg text-sm text-center">{error}</div>
                    )}

                    <Button
                      type="submit"
                      disabled={loading}
                      className="w-full h-12 bg-[#3B82F6] hover:bg-[#60A5FA] text-white font-bold rounded-lg shadow-lg tracking-widest transition-all"
                    >
                      {loading ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : 'SIGN IN'}
                    </Button>
                  </form>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      <Dialog open={showExpiredModal} onOpenChange={setShowExpiredModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-6 w-6" />
              Abonimi Ka Skaduar
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex justify-center">
              <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center">
                <CreditCard className="h-10 w-10 text-red-500" />
              </div>
            </div>
            <div className="text-center space-y-2">
              <p className="text-lg font-semibold text-gray-900">Abonimi juaj ka skaduar!</p>
              <p className="text-sm text-gray-600">
                {expiredDays > 0 ? `Abonimi juaj ka skaduar para ${expiredDays} ditesh.` : 'Abonimi juaj ka skaduar sot.'}
              </p>
              <p className="text-sm text-gray-500">Per te vazhduar perdorimin e sistemit, kontaktoni administratorin per te rinovuar abonimin.</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 space-y-2">
              <p className="text-sm font-medium text-gray-700 text-center">Kontaktoni per rinovim:</p>
              <div className="flex items-center justify-center gap-2 text-[#2563EB]">
                <Phone className="h-4 w-4" />
                <span className="font-medium">+383 44 123 456</span>
              </div>
            </div>
            <Button onClick={() => setShowExpiredModal(false)} variant="outline" className="w-full">Mbyll</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Login;