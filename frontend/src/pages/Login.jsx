import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, useTenant } from '../App';
import { useState as useLockState, useEffect as useLockEffect } from 'react';
import { Button } from '../components/ui/button';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '../components/ui/dialog';
import {
  Delete, CornerDownLeft, User, Lock, Eye, EyeOff,
  AlertTriangle, CreditCard, Phone,
  ShoppingCart, Package, BarChart3, Users, Boxes, Store,
  Keyboard,
} from 'lucide-react';
import '../login-design.css';

const SERVICES = [
  { icon: ShoppingCart, label: 'Arka POS' },
  { icon: Package,      label: 'Produkte' },
  { icon: BarChart3,    label: 'Raporte' },
  { icon: Users,        label: 'Klientët' },
  { icon: Boxes,        label: 'Stoku' },
];

const QWERTY_ROWS = [
  ['1','2','3','4','5','6','7','8','9','0'],
  ['q','w','e','r','t','y','u','i','o','p'],
  ['a','s','d','f','g','h','j','k','l'],
  ['z','x','c','v','b','n','m'],
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

  // Virtual Keyboard state
  const [vkOpen, setVkOpen] = useState(false);
  const [vkTarget, setVkTarget] = useState('pin');
  const [vkShift, setVkShift] = useState(false);

  const { login, deviceLock } = useAuth();

  // Firma e kycur ne kete PC (device lock)
  const [lockedCompany, setLockedCompany] = useLockState(null);
  useLockEffect(() => {
    let active = true;
    (async () => {
      try {
        const lock = await deviceLock?.getLock?.();
        if (active && lock) {
          setLockedCompany(lock.company_name || lock.tenant_name || null);
        }
      } catch (e) {
        /* ignore */
      }
    })();
    return () => {
      active = false;
    };
  }, [deviceLock]);
  const navigate = useNavigate();
  const tenantContext = useTenant();
  const tenant = tenantContext?.tenant;
  const tenantLoading = tenantContext?.tenantLoading;

  const brandName = tenant?.company_name || tenant?.name || 'DataPOS';
  const [logoFailed, setLogoFailed] = useState(false);
  useEffect(() => { setLogoFailed(false); }, [tenant?.logo_url]);

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
    if (e && e.preventDefault) e.preventDefault();
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

  // Virtual Keyboard handlers
  const openVK = (target) => { setVkTarget(target); setVkShift(false); setVkOpen(true); };

  const vkKeyPress = (key) => {
    if (vkTarget === 'pin') {
      if (/^[0-9]$/.test(key) && pin.length < 6) setPin(prev => prev + key);
    } else if (vkTarget === 'username') {
      setUsername(prev => prev + key);
    } else if (vkTarget === 'password') {
      setPassword(prev => prev + key);
    }
  };

  const vkBackspace = () => {
    if (vkTarget === 'pin') setPin(prev => prev.slice(0, -1));
    else if (vkTarget === 'username') setUsername(prev => prev.slice(0, -1));
    else if (vkTarget === 'password') setPassword(prev => prev.slice(0, -1));
  };

  const vkClear = () => {
    if (vkTarget === 'pin') setPin('');
    else if (vkTarget === 'username') setUsername('');
    else if (vkTarget === 'password') setPassword('');
  };

  const vkEnter = () => {
    setVkOpen(false);
    setTimeout(() => {
      if (vkTarget === 'pin') handlePinLogin();
      else handleAdminLogin();
    }, 50);
  };

  useEffect(() => {
    if (showAdminLogin || vkOpen) return;
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
    // eslint-disable-next-line
  }, [showAdminLogin, vkOpen, pin, addDigit, removeDigit]);

  const numpadButtons = ['1','2','3','4','5','6','7','8','9','clear','0','delete'];

  const vkFieldValue =
    vkTarget === 'pin' ? '\u2022'.repeat(pin.length)
    : vkTarget === 'username' ? username
    : '\u2022'.repeat(password.length);
  const vkFieldEmpty =
    (vkTarget === 'pin' ? pin.length
     : vkTarget === 'username' ? username.length
     : password.length) === 0;

  return (
    <div className="dp-login-page dp-login-v3">
      <div className="dp-login-container">
        <main className="dp-login-card" aria-label="Hyrja në DataPOS">
          <div className="dp-login-grid">
            <section className="dp-login-brand" aria-label="Firma">
              <div className="dp-brand-identity">
                <div className="dp-login-logo">
                  {tenant?.logo_url && !logoFailed ? (
                    <img src={tenant.logo_url} alt={`Logo e ${brandName}`} onError={() => setLogoFailed(true)} />
                  ) : <Store aria-hidden="true" strokeWidth={1.5} />}
                </div>
                <div className="dp-brand-name">
                  <h1>{brandName}</h1>
                  <p>Hapësira juaj e punës</p>
                </div>
              </div>
              <div className="dp-brand-intro">
                <span className="dp-brand-eyebrow">ME DATAPOS</span>
                <h2>Punë më e thjeshtë.<br />Kontroll më i plotë.</h2>
                <p>Shitjet, produktet dhe raportet — në një hapësirë të vetme për biznesin tuaj.</p>
                <div className="dp-brand-services" aria-label="Modulet e sistemit">
                  {SERVICES.map(({icon: Icon, label}) => (
                    <div key={label}><Icon aria-hidden="true" /><span>{label}</span></div>
                  ))}
                </div>
              </div>
              <div className="dp-brand-signature"><span>Powered by</span> <strong>DataPOS</strong></div>
            </section>

            <section className="dp-login-form" aria-labelledby="dp-login-heading">
              <div className="dp-auth-heading">
                <h2 id="dp-login-heading">Hyni në sistem</h2>
                <p>Zgjidhni mënyrën e hyrjes për të vazhduar.</p>
              </div>
              <div className="dp-auth-switch" role="group" aria-label="Mënyra e hyrjes">
                <button type="button" aria-pressed={!showAdminLogin} disabled={loading}
                  onClick={() => { setShowAdminLogin(false); setUsername(''); setPassword(''); setError(''); }}>
                  <ShoppingCart aria-hidden="true" />Hyrje me PIN
                </button>
                <button type="button" aria-pressed={showAdminLogin} disabled={loading}
                  onClick={() => { setShowAdminLogin(true); setError(''); }}>
                  <User aria-hidden="true" />Administrator
                </button>
              </div>

              {tenantLoading ? (
                <div className="dp-auth-loading" role="status"><span className="dp-auth-spinner" />Duke ngarkuar firmën…</div>
              ) : !showAdminLogin ? (
                <div className="dp-auth-content">
                  <label className="dp-auth-label" id="dp-pin-label">Kodi PIN</label>
                  <div className="dp-pin-field" aria-labelledby="dp-pin-label">
                    <div className={pin ? 'dp-pin-value' : 'dp-pin-placeholder'} role="status"
                      aria-label={pin ? `Kodi PIN: ${pin.length} shifra të vendosura` : 'Vendosni kodin PIN'}>
                      {pin ? '\u2022'.repeat(pin.length) : 'Vendosni PIN-in'}
                    </div>
                    <button type="button" className="dp-auth-icon-button" onClick={() => openVK('pin')}
                      title="Hap tastierën virtuale" aria-label="Hap tastierën virtuale për PIN-in"><Keyboard aria-hidden="true" /></button>
                  </div>
                  <div className="dp-pin-keypad" aria-label="Tastiera numerike">
                    {numpadButtons.map(btn => (
                      <button type="button" key={btn} disabled={loading}
                        className={btn === 'clear' || btn === 'delete' ? 'dp-pin-secondary' : ''}
                        aria-label={btn === 'clear' ? 'Pastro PIN-in' : btn === 'delete' ? 'Fshi shifrën e fundit' : `Shifra ${btn}`}
                        onClick={() => btn === 'clear' ? clearPin() : btn === 'delete' ? removeDigit() : addDigit(btn)}>
                        {btn === 'clear' ? 'C' : btn === 'delete' ? <Delete aria-hidden="true" /> : btn}
                      </button>
                    ))}
                  </div>
                  {error && <div className="dp-auth-error" role="alert">{error}</div>}
                  <Button className="dp-auth-primary" onClick={handlePinLogin} disabled={pin.length < 1 || loading}>
                    {loading ? <><span className="dp-auth-spinner" />Duke u kyçur…</> : <>Hyr në POS<CornerDownLeft aria-hidden="true" /></>}
                  </Button>
                  <p className="dp-auth-keyboard-hint">Mund të përdorni edhe tastierën: <kbd>0–9</kbd> dhe <kbd>Enter</kbd></p>
                </div>
              ) : (
                <form onSubmit={handleAdminLogin} className="dp-auth-content dp-admin-form">
                  {lockedCompany && <div className="dp-auth-notice">Ky kompjuter është i rezervuar për <strong>{lockedCompany}</strong>.</div>}
                  <div className="dp-auth-field">
                    <label className="dp-auth-label" htmlFor="dp-username">Emri i përdoruesit</label>
                    <div className="dp-auth-input-wrap">
                      <User className="dp-auth-field-icon" aria-hidden="true" />
                      <input id="dp-username" name="username" autoComplete="username" type="text" placeholder="Emri i përdoruesit"
                        value={username} onChange={e => setUsername(e.target.value)} required autoFocus />
                      <button type="button" className="dp-auth-icon-button" onClick={() => openVK('username')}
                        title="Hap tastierën virtuale" aria-label="Hap tastierën virtuale për emrin e përdoruesit"><Keyboard aria-hidden="true" /></button>
                    </div>
                  </div>
                  <div className="dp-auth-field">
                    <label className="dp-auth-label" htmlFor="dp-password">Fjalëkalimi</label>
                    <div className="dp-auth-input-wrap dp-auth-password-wrap">
                      <Lock className="dp-auth-field-icon" aria-hidden="true" />
                      <input id="dp-password" name="password" autoComplete="current-password" type={showPassword ? 'text' : 'password'}
                        placeholder="Fjalëkalimi juaj" value={password} onChange={e => setPassword(e.target.value)} required />
                      <button type="button" className="dp-auth-icon-button dp-password-toggle" onClick={() => setShowPassword(!showPassword)}
                        aria-label={showPassword ? 'Fshih fjalëkalimin' : 'Shfaq fjalëkalimin'} aria-pressed={showPassword}>
                        {showPassword ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}
                      </button>
                      <button type="button" className="dp-auth-icon-button" onClick={() => openVK('password')}
                        title="Hap tastierën virtuale" aria-label="Hap tastierën virtuale për fjalëkalimin"><Keyboard aria-hidden="true" /></button>
                    </div>
                  </div>
                  {error && <div className="dp-auth-error" role="alert">{error}</div>}
                  <Button type="submit" className="dp-auth-primary" disabled={loading}>
                    {loading ? <><span className="dp-auth-spinner" />Duke u kyçur…</> : <>Hyr si administrator<CornerDownLeft aria-hidden="true" /></>}
                  </Button>
                  <p className="dp-auth-admin-help">Përdorni llogarinë e administratorit të firmës suaj.</p>
                </form>
              )}
            </section>
          </div>
        </main>
        <footer className="dp-login-footer">
          <span>© {new Date().getFullYear()} DataPOS</span>
          <div><a href="https://www.datapos.pro" target="_blank" rel="noopener noreferrer">www.datapos.pro</a><span aria-hidden="true">·</span><a href="tel:+38345278279">+383 45 278 279</a></div>
        </footer>
      </div>

      {/* Virtual Keyboard Modal */}
      <Dialog open={vkOpen} onOpenChange={setVkOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-[#0E4B49]">
              <Keyboard className="h-5 w-5" />
              Tastiera Virtuale
            </DialogTitle>
          </DialogHeader>

          <div className="mb-3">
            <p className="text-xs text-gray-500 mb-1.5 font-medium">
              {vkTarget === 'pin' ? 'Kodi PIN' : vkTarget === 'username' ? 'Emri i perdoruesit' : 'Fjalekalimi'}
            </p>
            <div className="p-3 bg-gray-100 rounded-lg text-lg font-mono min-h-[48px] break-all border border-gray-200">
              {vkFieldEmpty ? <span className="text-gray-400 text-sm">Fillo te shkruash...</span> : vkFieldValue}
            </div>
          </div>

          {vkTarget === 'pin' ? (
            <div className="grid grid-cols-3 gap-2">
              {['1','2','3','4','5','6','7','8','9'].map(k => (
                <button
                  key={k}
                  onClick={() => vkKeyPress(k)}
                  className="h-14 bg-gray-100 hover:bg-emerald-100 active:bg-emerald-200 rounded-lg text-xl font-bold transition-colors"
                >{k}</button>
              ))}
              <button onClick={vkClear} className="h-14 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg font-medium transition-colors">C</button>
              <button onClick={() => vkKeyPress('0')} className="h-14 bg-gray-100 hover:bg-emerald-100 active:bg-emerald-200 rounded-lg text-xl font-bold transition-colors">0</button>
              <button onClick={vkBackspace} className="h-14 bg-gray-100 hover:bg-emerald-100 rounded-lg flex items-center justify-center transition-colors">
                <Delete className="h-5 w-5" />
              </button>
              <button onClick={vkEnter} className="col-span-3 h-12 bg-[#0E4B49] hover:bg-[#0A3634] text-white rounded-lg font-bold tracking-wider transition-colors">KYCU</button>
            </div>
          ) : (
            <div className="space-y-1.5">
              {QWERTY_ROWS.map((row, i) => (
                <div key={i} className="dp-vk-row flex gap-1 justify-center">
                  {row.map(k => {
                    const isLetter = /[a-z]/.test(k);
                    const display = isLetter && vkShift ? k.toUpperCase() : k;
                    return (
                      <button
                        key={k}
                        onClick={() => vkKeyPress(display)}
                        className="w-9 h-11 sm:w-10 sm:h-12 bg-gray-100 hover:bg-emerald-100 active:bg-emerald-200 rounded-md font-medium text-sm transition-colors"
                      >{display}</button>
                    );
                  })}
                </div>
              ))}
              <div className="flex gap-1 justify-center pt-1 flex-wrap">
                <button
                  onClick={() => setVkShift(!vkShift)}
                  className={"px-3 h-11 rounded-md font-medium text-xs transition-colors " + (vkShift ? "bg-[#0E4B49] text-white" : "bg-gray-100 hover:bg-emerald-100")}
                >Shift</button>
                <button onClick={() => vkKeyPress('@')} className="px-3 h-11 bg-gray-100 hover:bg-emerald-100 rounded-md text-sm transition-colors">@</button>
                <button onClick={() => vkKeyPress('.')} className="px-3 h-11 bg-gray-100 hover:bg-emerald-100 rounded-md text-sm transition-colors">.</button>
                <button onClick={() => vkKeyPress('_')} className="px-3 h-11 bg-gray-100 hover:bg-emerald-100 rounded-md text-sm transition-colors">_</button>
                <button onClick={() => vkKeyPress('-')} className="px-3 h-11 bg-gray-100 hover:bg-emerald-100 rounded-md text-sm transition-colors">-</button>
                <button onClick={() => vkKeyPress(' ')} className="flex-1 min-w-[100px] max-w-[200px] h-11 bg-gray-100 hover:bg-emerald-100 rounded-md text-xs transition-colors">Space</button>
                <button onClick={vkBackspace} className="px-3 h-11 bg-gray-100 hover:bg-emerald-100 rounded-md flex items-center transition-colors"><Delete className="h-4 w-4" /></button>
                <button onClick={vkClear} className="px-3 h-11 bg-red-50 hover:bg-red-100 text-red-600 rounded-md text-xs font-medium transition-colors">Clear</button>
                <button onClick={vkEnter} className="px-4 h-11 bg-[#0E4B49] hover:bg-[#0A3634] text-white rounded-md text-sm font-bold transition-colors">Enter</button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Subscription Expired Modal */}
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
                {expiredDays > 0 ? "Abonimi juaj ka skaduar para " + expiredDays + " ditesh." : 'Abonimi juaj ka skaduar sot.'}
              </p>
              <p className="text-sm text-gray-500">Per te vazhduar perdorimin e sistemit, kontaktoni administratorin per te rinovuar abonimin.</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 space-y-2">
              <p className="text-sm font-medium text-gray-700 text-center">Kontaktoni per rinovim:</p>
              <div className="flex items-center justify-center gap-2 text-[#0E4B49]">
                <Phone className="h-4 w-4" />
                <span className="font-medium">+383 45 278 279</span>
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
