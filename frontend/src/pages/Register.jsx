import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { 
  Building2, User, Mail, Phone, Lock, Eye, EyeOff, 
  Loader2, CheckCircle, ArrowLeft, Shield, Clock, Gift
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const Register = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [success, setSuccess] = useState(false);
  
  const [formData, setFormData] = useState({
    company_name: '',
    full_name: '',
    username: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: ''
  });

  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.company_name.trim()) {
      newErrors.company_name = 'Emri i kompanisë është i detyrueshëm';
    }
    
    if (!formData.full_name.trim()) {
      newErrors.full_name = 'Emri i plotë është i detyrueshëm';
    }
    
    if (!formData.username.trim()) {
      newErrors.username = 'Username është i detyrueshëm';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username duhet të ketë të paktën 3 karaktere';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = 'Username mund të përmbajë vetëm shkronja, numra dhe _';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email-i është i detyrueshëm';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email-i nuk është i vlefshëm';
    }
    
    if (!formData.phone.trim()) {
      newErrors.phone = 'Numri i telefonit është i detyrueshëm';
    }
    
    if (!formData.password) {
      newErrors.password = 'Fjalëkalimi është i detyrueshëm';
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Fjalëkalimet nuk përputhen';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/api/register`, {
        company_name: formData.company_name,
        full_name: formData.full_name,
        username: formData.username,
        email: formData.email,
        phone: formData.phone,
        password: formData.password
      });
      
      setSuccess(true);
      toast.success('Regjistrimi u krye me sukses!');
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
      
    } catch (error) {
      const message = error.response?.data?.detail || 'Ka ndodhur një gabim gjatë regjistrimit';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-[#0a1628] flex items-center justify-center p-4 relative overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-[#00a79d]/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-[#00a79d]/5 rounded-full blur-3xl"></div>
        </div>

        <div className="relative w-full max-w-md">
          <div className="bg-[#0f1f35]/80 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl p-8 text-center">
            <div className="w-20 h-20 bg-[#00a79d]/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-10 h-10 text-[#00a79d]" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-4">Regjistrimi u Krye!</h2>
            <p className="text-gray-400 mb-4">
              Llogaria juaj u krijua me sukses. Keni <span className="text-[#00a79d] font-semibold">30 ditë provë falas</span> për të testuar sistemin.
            </p>
            
            {/* Login Credentials */}
            <div className="bg-[#0a1628] border border-white/10 rounded-xl p-4 mb-6 text-left">
              <p className="text-sm text-gray-400 mb-3 text-center">Të dhënat tuaja për kyçje:</p>
              <div className="space-y-2">
                <div className="flex items-center justify-between bg-white/5 rounded-lg px-3 py-2">
                  <span className="text-gray-400 text-sm">Username:</span>
                  <span className="text-[#00a79d] font-semibold">{formData.username}</span>
                </div>
                <div className="flex items-center justify-between bg-white/5 rounded-lg px-3 py-2">
                  <span className="text-gray-400 text-sm">Fjalëkalimi:</span>
                  <span className="text-gray-300">••••••••</span>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-3 text-center">
                Përdorni këto kredenciale për t'u kyçur në panel
              </p>
            </div>
            
            <div className="bg-[#00a79d]/10 border border-[#00a79d]/20 rounded-xl p-3 mb-6">
              <p className="text-sm text-gray-300">
                Duke u ridrejtuar te faqja e kyçjes...
              </p>
            </div>
            <Button
              onClick={() => navigate('/login')}
              className="w-full h-12 bg-[#00a79d] hover:bg-[#008f86] text-white font-semibold rounded-xl"
            >
              Kyçu Tani
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a1628] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-[#00a79d]/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-[#00a79d]/5 rounded-full blur-3xl"></div>
      </div>

      {/* Grid Pattern */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23ffffff%22%20fill-opacity%3D%220.02%22%3E%3Cpath%20d%3D%22M36%2034v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6%2034v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6%204V0H4v4H0v2h4v4h2V6h4V4H6z%22%2F%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fsvg%3E')] opacity-50"></div>

      <div className="relative w-full max-w-lg">
        {/* Back Button */}
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm">Kthehu në Faqen Kryesore</span>
        </Link>

        <div className="bg-[#0f1f35]/80 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-[#00a79d]/20 to-transparent p-6 border-b border-white/10">
            <div className="flex items-center gap-3 mb-2">
              <img 
                src="https://customer-assets.emergentagent.com/job_retailsys-1/artifacts/9i1h1bxb_logo%20icon.png" 
                alt="DataPOS" 
                className="h-10 object-contain"
              />
              <h1 className="text-2xl font-bold text-white">Regjistrohu në DataPOS</h1>
            </div>
            <p className="text-gray-400 text-sm">Krijoni llogarinë tuaj dhe filloni me 30 ditë provë falas</p>
          </div>

          {/* Trial Benefits */}
          <div className="grid grid-cols-3 gap-3 p-4 bg-[#00a79d]/5 border-b border-white/10">
            <div className="flex items-center gap-2 text-center">
              <Gift className="w-4 h-4 text-[#00a79d]" />
              <span className="text-xs text-gray-300">30 Ditë Falas</span>
            </div>
            <div className="flex items-center gap-2 text-center">
              <Shield className="w-4 h-4 text-[#00a79d]" />
              <span className="text-xs text-gray-300">Pa Kartë Krediti</span>
            </div>
            <div className="flex items-center gap-2 text-center">
              <Clock className="w-4 h-4 text-[#00a79d]" />
              <span className="text-xs text-gray-300">Anulo Kurdo</span>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* Company Name */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Emri i Kompanisë *</label>
              <div className="relative">
                <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  type="text"
                  name="company_name"
                  placeholder="p.sh. Mobileri Urimi"
                  value={formData.company_name}
                  onChange={handleChange}
                  className={`pl-12 h-12 bg-white/5 border-white/10 text-white placeholder:text-gray-500 rounded-xl focus:border-[#00a79d] focus:ring-[#00a79d]/20 ${errors.company_name ? 'border-red-500' : ''}`}
                />
              </div>
              {errors.company_name && <p className="text-red-400 text-xs">{errors.company_name}</p>}
            </div>

            {/* Full Name */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Emri i Plotë *</label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  type="text"
                  name="full_name"
                  placeholder="p.sh. Urim Krasniqi"
                  value={formData.full_name}
                  onChange={handleChange}
                  className={`pl-12 h-12 bg-white/5 border-white/10 text-white placeholder:text-gray-500 rounded-xl focus:border-[#00a79d] focus:ring-[#00a79d]/20 ${errors.full_name ? 'border-red-500' : ''}`}
                />
              </div>
              {errors.full_name && <p className="text-red-400 text-xs">{errors.full_name}</p>}
            </div>

            {/* Username */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Username (për kyçje) *</label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  type="text"
                  name="username"
                  placeholder="p.sh. urimi123"
                  value={formData.username}
                  onChange={handleChange}
                  className={`pl-12 h-12 bg-white/5 border-white/10 text-white placeholder:text-gray-500 rounded-xl focus:border-[#00a79d] focus:ring-[#00a79d]/20 ${errors.username ? 'border-red-500' : ''}`}
                />
              </div>
              {errors.username && <p className="text-red-400 text-xs">{errors.username}</p>}
            </div>

            {/* Email */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Email *</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  type="email"
                  name="email"
                  placeholder="email@kompania.com"
                  value={formData.email}
                  onChange={handleChange}
                  className={`pl-12 h-12 bg-white/5 border-white/10 text-white placeholder:text-gray-500 rounded-xl focus:border-[#00a79d] focus:ring-[#00a79d]/20 ${errors.email ? 'border-red-500' : ''}`}
                />
              </div>
              {errors.email && <p className="text-red-400 text-xs">{errors.email}</p>}
            </div>

            {/* Phone */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Numri i Telefonit *</label>
              <div className="relative">
                <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  type="tel"
                  name="phone"
                  placeholder="+383 44 123 456"
                  value={formData.phone}
                  onChange={handleChange}
                  className={`pl-12 h-12 bg-white/5 border-white/10 text-white placeholder:text-gray-500 rounded-xl focus:border-[#00a79d] focus:ring-[#00a79d]/20 ${errors.phone ? 'border-red-500' : ''}`}
                />
              </div>
              {errors.phone && <p className="text-red-400 text-xs">{errors.phone}</p>}
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Fjalëkalimi *</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  placeholder="Shkruani fjalëkalimin"
                  value={formData.password}
                  onChange={handleChange}
                  className={`pl-12 pr-12 h-12 bg-white/5 border-white/10 text-white placeholder:text-gray-500 rounded-xl focus:border-[#00a79d] focus:ring-[#00a79d]/20 ${errors.password ? 'border-red-500' : ''}`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && <p className="text-red-400 text-xs">{errors.password}</p>}
            </div>

            {/* Confirm Password */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Konfirmo Fjalëkalimin *</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  type={showPassword ? 'text' : 'password'}
                  name="confirmPassword"
                  placeholder="Shkruani fjalëkalimin përsëri"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={`pl-12 h-12 bg-white/5 border-white/10 text-white placeholder:text-gray-500 rounded-xl focus:border-[#00a79d] focus:ring-[#00a79d]/20 ${errors.confirmPassword ? 'border-red-500' : ''}`}
                />
              </div>
              {errors.confirmPassword && <p className="text-red-400 text-xs">{errors.confirmPassword}</p>}
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-[#00a79d] hover:bg-[#008f86] text-white font-semibold rounded-xl transition-all duration-200 mt-6"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                'Regjistrohu Falas'
              )}
            </Button>

            {/* Login Link */}
            <div className="text-center pt-4 border-t border-white/10">
              <p className="text-gray-400 text-sm">
                Keni tashmë llogari?{' '}
                <Link to="/login" className="text-[#00a79d] hover:text-[#00c9b7] font-medium">
                  Kyçuni këtu
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Register;
