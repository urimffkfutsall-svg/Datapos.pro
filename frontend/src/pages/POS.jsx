import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, useAuth } from '../App';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { ScrollArea } from '../components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  Search,
  Plus,
  Minus,
  Trash2,
  CreditCard,
  Banknote, Sparkles, Wallet, Zap, ArrowRight,
  Receipt,
  FileText,
  Package,
  User,
  Percent,
  Ticket,
  Calculator,
  X,
  Delete,
  Settings,
  Printer,
  List,
  XCircle,
  LogOut,
  FileDown,
  Save,
  Shield,
  Calendar,
  Phone,
  MapPin
} from 'lucide-react';
import InvoiceA4 from '../components/InvoiceA4';
import ThermalReceipt from '../components/ThermalReceipt';
import { Checkbox } from '../components/ui/checkbox';

const POS = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [search, setSearch] = useState('');
  const [dialogSearch, setDialogSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [cashDrawer, setCashDrawer] = useState(null);
  const [showOpenDrawer, setShowOpenDrawer] = useState(false);
  const [showPayment, setShowPayment] = useState(false);
  const [showProductSearch, setShowProductSearch] = useState(false);
  const [showCustomer, setShowCustomer] = useState(false);
  const [showParams, setShowParams] = useState(false);
  const [showDocuments, setShowDocuments] = useState(false);
  const [openingBalance, setOpeningBalance] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [cashAmount, setCashAmount] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [customerNote, setCustomerNote] = useState('');
  const [selectedItemIndex, setSelectedItemIndex] = useState(null);
  const [recentSales, setRecentSales] = useState([]);
  const [applyNoVat, setApplyNoVat] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [showInvoiceA4, setShowInvoiceA4] = useState(false);
  const [showBuyerForm, setShowBuyerForm] = useState(false);
  const [currentSaleForPrint, setCurrentSaleForPrint] = useState(null);
  const [companySettings, setCompanySettings] = useState(null);
  const [printReceipt, setPrintReceipt] = useState(false); // Default: pa kupon, arkëtari zgjedh
  const [screenSize, setScreenSize] = useState('large'); // Për responsive scaling
  const [currentTime, setCurrentTime] = useState(new Date()); // For clock display
  // Debt (Borgj) state
  const [isDebt, setIsDebt] = useState(false);
  const [couponEnabled, setCouponEnabled] = useState(false);
  const [couponCode, setCouponCode] = useState('');
  const [couponData, setCouponData] = useState(null);
  const [couponLoading, setCouponLoading] = useState(false);
  const [debtorName, setDebtorName] = useState('');
  const [buyerInfo, setBuyerInfo] = useState({
    name: '',
    address: '',
    phone: '',
    nui: '',
    nf: ''
  });
  
  // Warranty (Garancioni) state
  const [showWarranty, setShowWarranty] = useState(false);
  const [showWarrantyList, setShowWarrantyList] = useState(false);
  const [savedWarranties, setSavedWarranties] = useState([]);
  const [loadingWarranties, setLoadingWarranties] = useState(false);
  const [warrantySearch, setWarrantySearch] = useState('');
  const [warrantyData, setWarrantyData] = useState({
    customerName: '',
    customerPhone: '',
    customerAddress: '',
    productName: '',
    productBrand: '',
    productModel: '',
    serialNumber: '',
    imei: '',
    purchaseDate: new Date().toISOString().split('T')[0],
    warrantyPeriod: '12', // muaj
    productCondition: 'I ri',
    notes: '',
    accessories: ''
  });
  const warrantyRef = useRef(null);
  
  const searchRef = useRef(null);
  const invoiceRef = useRef(null);
  const thermalReceiptRef = useRef(null);

  // Clock update every minute
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute
    return () => clearInterval(timer);
  }, []);

  // Auto-scaling based on screen resolution
  const [scale, setScale] = useState(1);
  const [fontSize, setFontSize] = useState('base');
  
  // Responsive screen size detection with auto-scaling
  useEffect(() => {
    const updateScreenSize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      // Calculate optimal scale based on resolution
      // Base resolution: 1920x1080
      const baseWidth = 1920;
      const baseHeight = 1080;
      
      const scaleX = width / baseWidth;
      const scaleY = height / baseHeight;
      const optimalScale = Math.min(scaleX, scaleY, 1.2); // Cap at 1.2x
      
      // Set scale for CSS transform
      setScale(Math.max(optimalScale, 0.7)); // Min 0.7x
      
      // Determine screen size category
      if (width < 1280 || height < 700) {
        setScreenSize('small');
        setFontSize('sm');
      } else if (width < 1536 || height < 800) {
        setScreenSize('medium');
        setFontSize('base');
      } else if (width >= 1920) {
        setScreenSize('xlarge');
        setFontSize('lg');
      } else {
        setScreenSize('large');
        setFontSize('base');
      }
      
      // Apply CSS custom properties for dynamic sizing
      document.documentElement.style.setProperty('--pos-scale', optimalScale.toString());
      document.documentElement.style.setProperty('--pos-font-scale', `${Math.max(optimalScale, 0.85)}rem`);
    };
    
    updateScreenSize();
    window.addEventListener('resize', updateScreenSize);
    return () => window.removeEventListener('resize', updateScreenSize);
  }, []);

  // Get dynamic classes based on screen size
  const getResponsiveClasses = () => {
    switch(screenSize) {
      case 'small':
        return {
          container: 'p-2 gap-2',
          header: 'text-xs',
          productCard: 'p-2',
          productName: 'text-xs',
          productPrice: 'text-sm',
          cartItem: 'py-1 text-xs',
          button: 'text-xs px-2 py-1',
          total: 'text-lg',
          input: 'h-8 text-sm'
        };
      case 'medium':
        return {
          container: 'p-3 gap-3',
          header: 'text-sm',
          productCard: 'p-3',
          productName: 'text-sm',
          productPrice: 'text-base',
          cartItem: 'py-2 text-sm',
          button: 'text-sm px-3 py-2',
          total: 'text-xl',
          input: 'h-9 text-base'
        };
      case 'xlarge':
        return {
          container: 'p-6 gap-4',
          header: 'text-base',
          productCard: 'p-4',
          productName: 'text-base',
          productPrice: 'text-xl',
          cartItem: 'py-3 text-base',
          button: 'text-base px-4 py-3',
          total: 'text-3xl',
          input: 'h-12 text-lg'
        };
      default: // large
        return {
          container: 'p-4 gap-4',
          header: 'text-sm',
          productCard: 'p-3',
          productName: 'text-sm',
          productPrice: 'text-lg',
          cartItem: 'py-2 text-sm',
          button: 'text-sm px-3 py-2',
          total: 'text-2xl',
          input: 'h-10 text-base'
        };
    }
  };
  
  const responsiveClasses = getResponsiveClasses();

  // Initial data load
  useEffect(() => {
    loadData();
    loadCompanySettings();
  }, []);

  const loadCompanySettings = async () => {
    try {
      const response = await api.get('/settings/company');
      setCompanySettings(response.data);
    } catch (error) {
      console.error('Error loading company settings:', error);
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [productsRes, drawerRes, salesRes] = await Promise.all([
        api.get('/products'),
        api.get('/cashier/current').catch(() => ({ data: null })),
        api.get('/sales?limit=10').catch(() => ({ data: [] }))
      ]);
      setProducts(productsRes.data);
      setCashDrawer(drawerRes.data);
      setRecentSales(salesRes.data || []);
    } catch (error) {
      console.error('Error loading POS data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    if (cashDrawer) {
      if (!window.confirm('Keni arkë të hapur. Jeni të sigurt që doni të çkyçeni pa e mbyllur arkën?')) {
        return;
      }
    }
    logout();
    navigate('/login');
  };

  const handleOpenDrawer = async () => {
    try {
      const response = await api.post('/cashier/open', {
        opening_balance: parseFloat(openingBalance) || 0,
        branch_id: user?.branch_id
      });
      setCashDrawer(response.data);
      setShowOpenDrawer(false);
      setOpeningBalance('');
      toast.success('Arka u hap me sukses');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë hapjes së arkës');
    }
  };

  const handleCloseDrawer = async () => {
    if (!window.confirm('Jeni të sigurt që doni të mbyllni arkën?')) return;
    
    const actualBalance = prompt('Vendosni bilancin aktual në arkë (€):');
    if (actualBalance === null) return;

    try {
      const response = await api.post('/cashier/close', { actual_balance: parseFloat(actualBalance) || 0 });
      setCashDrawer(null);
      toast.success(`Arka u mbyll. Diferenca: €${response.data.discrepancy.toFixed(2)}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë mbylljes së arkës');
    }
  };

  // Filter products for dialog - show all products, highlight zero stock
  const filteredProducts = products.filter(p => {
    const searchTerm = (showProductSearch ? dialogSearch : search).toLowerCase().trim();
    if (!searchTerm) return true; // Show all products when no search
    return (
      p.name?.toLowerCase().includes(searchTerm) ||
      p.barcode?.toLowerCase().includes(searchTerm) ||
      p.barcode?.includes(searchTerm)
    );
  });

  // Products for main search (showing dropdown) - show all products including zero stock
  const mainSearchResults = search.trim() ? products.filter(p => 
    (p.name?.toLowerCase().includes(search.toLowerCase().trim()) ||
    p.barcode?.toLowerCase().includes(search.toLowerCase().trim()) ||
    p.barcode?.includes(search.trim()))
  ) : [];

  const addToCart = useCallback((product) => {
    setCart(prevCart => {
      const existing = prevCart.find(item => item.product_id === product.id);
      if (existing) {
        return prevCart.map(item =>
          item.product_id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }
      return [...prevCart, {
        product_id: product.id,
        product_name: product.name,
        quantity: 1,
        unit_price: product.sale_price || 0,
        discount_percent: 0,
        vat_percent: applyNoVat ? 0 : (product.vat_rate || 0),
        current_stock: product.current_stock, image_url: product.metadata?.image_url || null
      }];
    });
    setShowProductSearch(false);
    setSearch('');
    setShowSearchResults(false);
    
    // Show warning if product has no stock
    if (product.current_stock <= 0) {
      toast.warning(`Kujdes: "${product.name}" nuk ka stok!`);
    }
  }, [applyNoVat]);

  const updateQuantity = (productId, delta) => {
    setCart(prevCart =>
      prevCart.map(item => {
        if (item.product_id === productId) {
          const newQty = item.quantity + delta;
          if (newQty <= 0) return item;
          // Allow selling without stock limit - just show warning
          if (item.current_stock > 0 && newQty > item.current_stock) {
            toast.warning('Kujdes: Po shisni mbi stokun e disponueshëm!');
          }
          return { ...item, quantity: newQty };
        }
        return item;
      })
    );
  };

  const updateDiscount = (productId, discount) => {
    setCart(prevCart =>
      prevCart.map(item =>
        item.product_id === productId
          ? { ...item, discount_percent: Math.min(100, Math.max(0, parseFloat(discount) || 0)) }
          : item
      )
    );
  };

  const removeFromCart = (productId) => {
    setCart(prevCart => prevCart.filter(item => item.product_id !== productId));
    setSelectedItemIndex(null);
  };

  const deleteSelectedItem = () => {
    if (selectedItemIndex !== null && cart[selectedItemIndex]) {
      removeFromCart(cart[selectedItemIndex].product_id);
      toast.success('Artikulli u fshi');
    } else {
      toast.error('Zgjidhni një artikull për ta fshirë');
    }
  };

  const clearCart = () => {
    if (cart.length > 0 && window.confirm('Jeni të sigurt që doni të pastroni shportën?')) {
      setCart([]);
      setSelectedItemIndex(null);
      setCustomerName('');
      setCustomerNote('');
      toast.success('Shporta u pastrua');
    }
  };

  // Calculate totals
  const calculateItemTotal = (item) => {
    const subtotal = item.quantity * item.unit_price;
    const discount = subtotal * (item.discount_percent / 100);
    const afterDiscount = subtotal - discount;
    const vat = afterDiscount * (item.vat_percent / 100);
    return { subtotal, discount, vat, total: afterDiscount + vat };
  };

  const cartTotals = cart.reduce((acc, item) => {
    const { subtotal, discount, vat, total } = calculateItemTotal(item);
    return {
      subtotal: acc.subtotal + subtotal,
      discount: acc.discount + discount,
      vat: acc.vat + vat,
      total: acc.total + total
    };
  }, { subtotal: 0, discount: 0, vat: 0, total: 0 });

  const changeAmount = Math.max(0, (parseFloat(cashAmount) || 0) - (cartTotals.total - (couponData?.discount_amount || 0)));

  // State for receipt preview
  const [showReceiptPreview, setShowReceiptPreview] = useState(false);
  const [receiptDataForPrint, setReceiptDataForPrint] = useState(null);
  const [receiptComment, setReceiptComment] = useState(''); // Extra comment for receipt
  const [showCommentOnReceipt, setShowCommentOnReceipt] = useState(true); // Toggle to show comment
  const [savedReceiptComment, setSavedReceiptComment] = useState(''); // Saved comment from settings
  const [directPrintEnabled, setDirectPrintEnabled] = useState(false); // Direct print without dialog
  const [commentTemplates, setCommentTemplates] = useState([]); // Comment templates from backend

  // Load saved preferences from localStorage and comment templates
  useEffect(() => {
    const savedComment = localStorage.getItem('receiptDefaultComment');
    if (savedComment) {
      setSavedReceiptComment(savedComment);
    }
    const savedDirectPrint = localStorage.getItem('directPrintEnabled');
    if (savedDirectPrint === 'true') {
      setDirectPrintEnabled(true);
    }
    
    // Load comment templates from backend
    const loadCommentTemplates = async () => {
      try {
        const response = await api.get('/comment-templates');
        setCommentTemplates(response.data || []);
        // Set default comment if exists
        const defaultTemplate = response.data?.find(t => t.is_default && t.is_active);
        if (defaultTemplate && !savedComment) {
          setSavedReceiptComment(defaultTemplate.content);
        }
      } catch (error) {
        console.log('Comment templates not loaded:', error);
      }
    };
    loadCommentTemplates();
  }, []);

  // Load saved warranties
  const loadWarranties = async (searchTerm = '') => {
    try {
      setLoadingWarranties(true);
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      params.append('limit', '50');
      const response = await api.get(`/warranties?${params.toString()}`);
      setSavedWarranties(response.data || []);
    } catch (error) {
      console.error('Error loading warranties:', error);
      toast.error('Gabim gjatë ngarkimit të garancioneve');
    } finally {
      setLoadingWarranties(false);
    }
  };

  // Save warranty to database
  const saveWarranty = async () => {
    try {
      const warrantyPayload = {
        customer_name: warrantyData.customerName || null,
        customer_phone: warrantyData.customerPhone || null,
        customer_address: warrantyData.customerAddress || null,
        product_name: warrantyData.productName || null,
        product_brand: warrantyData.productBrand || null,
        product_model: warrantyData.productModel || null,
        serial_number: warrantyData.serialNumber || null,
        imei: warrantyData.imei || null,
        purchase_date: warrantyData.purchaseDate || null,
        warranty_period: parseInt(warrantyData.warrantyPeriod) || 12,
        product_condition: warrantyData.productCondition || 'I ri',
        accessories: warrantyData.accessories || null,
        notes: warrantyData.notes || null
      };
      
      const response = await api.post('/warranties', warrantyPayload);
      toast.success(`Garancioni u ruajt me sukses! Nr: ${response.data.warranty_number}`);
      return response.data;
    } catch (error) {
      console.error('Error saving warranty:', error);
      toast.error('Gabim gjatë ruajtjes së garancionit');
      return null;
    }
  };

  // Load warranty into form for viewing/printing
  const loadWarrantyToForm = (warranty) => {
    setWarrantyData({
      customerName: warranty.customer_name || '',
      customerPhone: warranty.customer_phone || '',
      customerAddress: warranty.customer_address || '',
      productName: warranty.product_name || '',
      productBrand: warranty.product_brand || '',
      productModel: warranty.product_model || '',
      serialNumber: warranty.serial_number || '',
      imei: warranty.imei || '',
      purchaseDate: warranty.purchase_date || new Date().toISOString().split('T')[0],
      warrantyPeriod: String(warranty.warranty_period || '12'),
      productCondition: warranty.product_condition || 'I ri',
      notes: warranty.notes || '',
      accessories: warranty.accessories || ''
    });
    setShowWarrantyList(false);
    setShowWarranty(true);
  };

  // Delete warranty
  const deleteWarranty = async (warrantyId) => {
    if (!window.confirm('Jeni të sigurt që doni të fshini këtë garancioni?')) return;
    try {
      await api.delete(`/warranties/${warrantyId}`);
      toast.success('Garancioni u fshi me sukses');
      loadWarranties(warrantySearch);
    } catch (error) {
      toast.error('Gabim gjatë fshirjes së garancionit');
    }
  };

  // Check if running in Electron
  const isElectron = window.electronAPI?.isElectron === true;

  // Toggle direct print and save preference
  const toggleDirectPrint = (enabled) => {
    setDirectPrintEnabled(enabled);
    localStorage.setItem('directPrintEnabled', enabled ? 'true' : 'false');
    if (enabled) {
      if (isElectron) {
        toast.success('Printimi direkt aktivizuar! Kuponi do të printohet automatikisht pa dialog.');
      } else {
        toast.success('Printimi direkt aktivizuar! Kuponi do të printohet automatikisht.');
      }
    } else {
      toast.info('Printimi direkt çaktivizuar. Do të hapet dialogu i printerit.');
    }
  };

  // Print thermal receipt - show preview dialog or print directly based on preference
  const printThermalReceipt = (saleData) => {
    setReceiptDataForPrint(saleData);
    setReceiptComment(savedReceiptComment); // Load saved comment as default
    setShowCommentOnReceipt(!!savedReceiptComment);
    
    // If direct print is enabled, print immediately without showing preview dialog
    if (directPrintEnabled) {
      // Print directly without showing preview dialog
      executeThermalPrintDirect(saleData);
    } else {
      setShowReceiptPreview(true);
    }
  };
  
  // Direct print function - creates and prints receipt without showing dialog
  const executeThermalPrintDirect = async (saleData) => {
    // Build receipt HTML directly
    const receiptHTML = buildReceiptHTML(saleData);
    
    // If running in Electron, use silent print
    if (isElectron && window.electronAPI?.silentPrint) {
      try {
        // Create a temporary window content for printing
        const fullHTML = `
          <!DOCTYPE html>
          <html>
            <head>
              <title>Kupon Shitje</title>
              <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                  font-family: 'Courier New', 'Consolas', monospace; 
                  font-size: 11px; 
                  line-height: 1.4;
                  width: 80mm;
                  max-width: 80mm;
                  padding: 4mm;
                  background: white;
                  color: #000;
                }
                img { max-width: 100%; height: auto; }
                @media print {
                  @page { size: 80mm auto; margin: 0; }
                  html, body { width: 80mm !important; max-width: 80mm !important; }
                }
              </style>
            </head>
            <body>
              ${receiptHTML}
            </body>
          </html>
        `;
        
        // Use Electron's silent print
        const result = await window.electronAPI.silentPrint({
          pageSize: { width: 80000, height: 297000 }, // 80mm width in microns
          printOptions: {
            silent: true,
            printBackground: true
          }
        });
        
        if (result.success) {
          toast.success(`Kuponi u printua në: ${result.printer}`);
        } else {
          // Fallback to browser print if Electron silent print fails
          console.warn('Electron silent print failed, falling back to browser print:', result.error);
          executeBrowserPrint(receiptHTML);
        }
      } catch (error) {
        console.error('Electron print error:', error);
        // Fallback to browser print
        executeBrowserPrint(receiptHTML);
      }
    } else {
      // Use browser print (iframe method)
      executeBrowserPrint(receiptHTML);
    }
  };
  
  // Browser print using iframe method
  const executeBrowserPrint = (receiptHTML) => {
    // Create hidden iframe for printing
    const printFrame = document.createElement('iframe');
    printFrame.id = 'thermal-print-frame-direct';
    printFrame.style.position = 'absolute';
    printFrame.style.top = '-10000px';
    printFrame.style.left = '-10000px';
    printFrame.style.width = '80mm';
    printFrame.style.height = '0';
    
    // Remove any existing print frame
    const existingFrame = document.getElementById('thermal-print-frame-direct');
    if (existingFrame) {
      existingFrame.remove();
    }
    
    document.body.appendChild(printFrame);
    
    const printDocument = printFrame.contentDocument || printFrame.contentWindow.document;
    
    printDocument.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Kupon Shitje</title>
          <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
              font-family: 'Courier New', 'Consolas', monospace; 
              font-size: 11px; 
              line-height: 1.4;
              width: 80mm;
              max-width: 80mm;
              padding: 4mm;
              background: white;
              color: #000;
            }
            img { max-width: 100%; height: auto; }
            @media print {
              @page { size: 80mm auto; margin: 0; }
              html, body { width: 80mm !important; max-width: 80mm !important; }
            }
          </style>
        </head>
        <body>
          ${receiptHTML}
        </body>
      </html>
    `);
    
    printDocument.close();
    
    // Wait for content and images to load, then print
    setTimeout(() => {
      try {
        printFrame.contentWindow.focus();
        printFrame.contentWindow.print();
        toast.success('Kuponi u dërgua në printer!');
      } catch (e) {
        console.error('Print error:', e);
        toast.error('Gabim gjatë printimit.');
      }
      // Remove iframe after printing
      setTimeout(() => {
        const frame = document.getElementById('thermal-print-frame-direct');
        if (frame) frame.remove();
      }, 2000);
    }, 500);
  };
  
  // Build receipt HTML for direct printing
  const buildReceiptHTML = (saleData) => {
    const items = saleData.items || [];
    const itemsHTML = items.map(item => `
      <div style="margin-bottom: 6px;">
        <div style="font-weight: 500;">${(item.product_name || 'Produkt').substring(0, 30)}</div>
        <div style="display: flex;">
          <span style="flex: 1;"></span>
          <span style="width: 30px; text-align: center;">${item.quantity}</span>
          <span style="width: 45px; text-align: right;">${(item.unit_price || 0).toFixed(2)}</span>
          <span style="width: 50px; text-align: right; font-weight: bold;">${(item.total || (item.quantity * item.unit_price)).toFixed(2)}</span>
        </div>
        ${item.discount_percent > 0 ? `<div style="font-size: 8px; color: #b91c1c; text-align: right; padding-right: 50px; margin-top: 1px;">Zbritja: ${item.discount_percent}% (-${((item.unit_price || 0) * (item.quantity || 0) * (item.discount_percent || 0) / 100).toFixed(2)} EUR)</div>` : ''}
      </div>
    `).join('');
    
    // Use company logo if available from tenant settings
    const logoUrl = companySettings?.logo_url || '';
    const companyName = companySettings?.company_name || 'DataPOS';
    const companyAddress = companySettings?.address || '';
    const companyCity = companySettings?.city || '';
    const companyPhone = companySettings?.phone || '';
    const companyEmail = companySettings?.email || '';
    const companyNUI = companySettings?.nui || '';
    const companyNF = companySettings?.nf || '';
    const whatsappQrUrl = companySettings?.whatsapp_qr_url || '';
    
    // Debt information
    const isDebtSale = saleData.is_debt;
    const paidAmount = saleData.paid_amount || saleData.cash_amount || 0;
    const remainingDebt = saleData.remaining_debt || 0;
    
    return `
      <div style="text-align: center; margin-bottom: 8px;">
        ${logoUrl ? `<img src="${logoUrl}" alt="Logo" style="height: 45px; max-width: 60mm;" onerror="this.style.display='none'" />` : ''}
        <div style="font-size: 14px; font-weight: bold;">${companyName}</div>
        ${companyAddress ? `<div style="font-size: 9px;">${companyAddress}${companyCity ? ', ' + companyCity : ''}</div>` : ''}
        ${companyPhone ? `<div style="font-size: 9px;">Tel: ${companyPhone}</div>` : ''}
        ${companyEmail ? `<div style="font-size: 9px;">${companyEmail}</div>` : ''}
        ${companyNUI ? `<div style="font-size: 9px;">NUI: ${companyNUI}</div>` : ''}
        ${companyNF ? `<div style="font-size: 9px;">NF: ${companyNF}</div>` : ''}
      </div>
      <div style="border-top: 2px dashed #000; margin: 8px 0;"></div>
      <div style="text-align: center; margin: 8px 0;">
        <span style="border: 1px solid #000; padding: 4px 8px; font-weight: bold;">${isDebtSale ? 'KUPON BORGJ' : 'KUPON SHITJE'}</span>
      </div>
      ${isDebtSale ? `
        <div style="text-align: center; margin: 8px 0; padding: 6px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px;">
          <div style="font-size: 10px; font-weight: bold; color: #856404;">⚠ SHITJE ME BORXH</div>
        </div>
      ` : ''}
      <div style="font-size: 10px; margin: 8px 0;">
        <div style="display: flex; justify-content: space-between;"><span>Nr:</span><span style="font-weight: bold;">${saleData.receipt_number}</span></div>
        <div style="display: flex; justify-content: space-between;"><span>Data:</span><span>${new Date(saleData.created_at).toLocaleDateString('sq-AL')}</span></div>
        <div style="display: flex; justify-content: space-between;"><span>Ora:</span><span>${new Date(saleData.created_at).toLocaleTimeString('sq-AL')}</span></div>
        <div style="display: flex; justify-content: space-between;"><span>Arkëtar:</span><span>${user?.full_name || '-'}</span></div>
        ${saleData.customer_name ? `<div style="display: flex; justify-content: space-between; margin-top: 4px; padding-top: 4px; border-top: 1px dashed #ccc;"><span>${isDebtSale ? 'Debitori:' : 'Klienti:'}</span><span style="font-weight: bold;">${saleData.customer_name}</span></div>` : ''}
      </div>
      <div style="border-top: 1px dashed #000; margin: 8px 0;"></div>
      <div style="font-size: 9px; font-weight: bold; display: flex; border-bottom: 1px solid #000; padding-bottom: 4px;">
        <span style="flex: 1;">ARTIKULLI</span>
        <span style="width: 30px; text-align: center;">SAS</span>
        <span style="width: 45px; text-align: right;">ÇMIMI</span>
        <span style="width: 50px; text-align: right;">VLERA</span>
      </div>
      <div style="font-size: 9px; margin: 8px 0;">${itemsHTML}</div>
      <div style="border-top: 1px dashed #000; margin: 8px 0;"></div>
      <div style="font-size: 10px;">
        <div style="display: flex; justify-content: space-between;"><span>Nëntotali:</span><span>${(saleData.subtotal || 0).toFixed(2)} EUR</span></div>
        ${(saleData.total_discount || 0) > 0 ? `<div style="display: flex; justify-content: space-between; color: #b91c1c;"><span>Zbritja totale:</span><span>-${(saleData.total_discount || 0).toFixed(2)} EUR</span></div>` : ''}
        ${(saleData.total_vat || 0) > 0 ? `<div style="display: flex; justify-content: space-between;"><span>TVSH:</span><span>${(saleData.total_vat || 0).toFixed(2)} EUR</span></div>` : ''}
      </div>
      <div style="border-top: 2px solid #000; border-bottom: 2px solid #000; padding: 8px 0; margin: 8px 0; display: flex; justify-content: space-between;">
        <span style="font-size: 14px; font-weight: bold;">TOTALI:</span>
        <span style="font-size: 18px; font-weight: bold;">${(saleData.grand_total || 0).toFixed(2)} EUR</span>
      </div>
      
      ${isDebtSale ? `
        <!-- DEBT SECTION -->
        <div style="margin: 8px 0; padding: 8px; background: #fff3cd; border: 2px solid #ffc107; border-radius: 4px;">
          <div style="font-size: 11px; font-weight: bold; text-align: center; margin-bottom: 6px; color: #856404;">INFORMACION BORGJI</div>
          <div style="font-size: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span>Total Fatura:</span>
              <span style="font-weight: bold;">${(saleData.grand_total || 0).toFixed(2)} EUR</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span>Paguar Tani:</span>
              <span style="font-weight: bold; color: #28a745;">${paidAmount.toFixed(2)} EUR</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding-top: 4px; border-top: 1px dashed #856404;">
              <span style="font-weight: bold;">BORGJ I MBETUR:</span>
              <span style="font-size: 14px; font-weight: bold; color: #dc3545;">${remainingDebt.toFixed(2)} EUR</span>
            </div>
          </div>
        </div>
      ` : `
        <div style="font-size: 10px; margin: 8px 0;">
          <div style="display: flex; justify-content: space-between;"><span>Mënyra:</span><span style="font-weight: bold;">${saleData.payment_method === 'cash' ? 'CASH' : 'KARTË'}</span></div>
          ${saleData.payment_method === 'cash' ? `
            <div style="display: flex; justify-content: space-between;"><span>Paguar:</span><span>${(saleData.cash_amount || 0).toFixed(2)} EUR</span></div>
            <div style="display: flex; justify-content: space-between; font-weight: bold;"><span>Kusuri:</span><span>${(saleData.change_amount || 0).toFixed(2)} EUR</span></div>
          ` : ''}
        </div>
      `}
      
      <div style="border-top: 1px dashed #000; margin: 8px 0;"></div>
      <div style="text-align: center; margin: 10px 0;">
        <div style="font-size: 12px; font-weight: bold;">FALEMINDERIT!</div>
        <div style="font-size: 9px;">Ju mirëpresim përsëri!</div>
      </div>
      ${isDebtSale ? `
        <div style="text-align: center; margin: 8px 0; padding: 8px; border: 2px dashed #dc3545; background: #fff5f5;">
          <div style="font-size: 9px; color: #666;">Borgj i mbetur për tu paguar:</div>
          <div style="font-size: 16px; font-weight: bold; color: #dc3545;">${remainingDebt.toFixed(2)} EUR</div>
        </div>
      ` : ''}
      <div style="text-align: center; font-size: 8px; color: #666; border-top: 1px dashed #000; padding-top: 8px;">
        <div>Ky kupon shërben vetëm për evidencë</div>
        <div>${new Date().toLocaleString('sq-AL')}</div>
      </div>
      
      <!-- ═══════════ ZONA E SHKYÇJES PËR ARKËTARIN ═══════════ -->
      <div style="margin-top: 15px; border-top: 2px dashed #000; padding-top: 8px;">
        <div style="text-align: center; margin-bottom: 8px;">
          <span style="font-size: 8px; background: #000; color: #fff; padding: 2px 8px; letter-spacing: 1px;">✂ SHKYÇ KËTU ✂</span>
        </div>
        <div style="border: 1px solid #000; padding: 8px; border-radius: 4px; background: ${isDebtSale ? '#fff3cd' : '#fafafa'};">
          <div style="text-align: center; font-size: 10px; font-weight: bold; margin-bottom: 6px; text-transform: uppercase; border-bottom: 1px solid #ddd; padding-bottom: 4px;">
            Kopje për Arkëtarin ${isDebtSale ? '⚠ BORGJ' : ''}
          </div>
          <div style="font-size: 9px;">
            <div style="margin-bottom: 4px;"><strong>Data:</strong> ${new Date(saleData.created_at).toLocaleDateString('sq-AL')} <strong>Ora:</strong> ${new Date(saleData.created_at).toLocaleTimeString('sq-AL', { hour: '2-digit', minute: '2-digit' })}</div>
            <div style="margin-bottom: 4px;"><strong>Nr:</strong> ${saleData.receipt_number}</div>
            ${isDebtSale && saleData.debtor_name ? `<div style="margin-bottom: 4px; padding: 3px; background: #ffe0b2; border-radius: 2px;"><strong>Debitori:</strong> <span style="font-size: 10px; font-weight: bold;">${saleData.debtor_name}</span></div>` : ''}
            <div style="border-top: 1px dashed #ccc; margin: 6px 0; padding-top: 6px;">
              ${items.map(item => `<div style="display: flex; justify-content: space-between; margin-bottom: 2px;"><span>${(item.product_name || 'Produkt').substring(0, 20)} x${item.quantity}${item.discount_percent > 0 ? ' (-' + item.discount_percent + '%)' : ''}</span><span style="font-weight: bold;">${(item.total || (item.quantity * item.unit_price)).toFixed(2)}€</span></div>`).join('')}
            </div>
            <div style="border-top: 1px solid #000; margin-top: 6px; padding-top: 6px; display: flex; justify-content: space-between; font-weight: bold;">
              <span>TOTAL:</span>
              <span style="font-size: 12px;">${(saleData.grand_total || 0).toFixed(2)} EUR</span>
            </div>
            ${isDebtSale ? `
              <div style="margin-top: 8px; padding: 6px; background: #ffebee; border: 1px solid #ef5350; border-radius: 4px;">
                <div style="font-size: 8px; text-align: center; color: #c62828; margin-bottom: 4px; font-weight: bold;">INFORMACION BORGJI</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                  <span>Total Fatura:</span>
                  <span style="font-weight: bold;">${(saleData.grand_total || 0).toFixed(2)}€</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                  <span>Paguar Tani:</span>
                  <span style="font-weight: bold; color: #2e7d32;">${paidAmount.toFixed(2)}€</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding-top: 4px; border-top: 1px dashed #ef5350; font-weight: bold;">
                  <span style="color: #c62828;">BORGJ MBETUR:</span>
                  <span style="font-size: 12px; color: #c62828;">${remainingDebt.toFixed(2)}€</span>
                </div>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  };

  // Save comment as default for future receipts
  const saveCommentAsDefault = () => {
    localStorage.setItem('receiptDefaultComment', receiptComment);
    setSavedReceiptComment(receiptComment);
    toast.success('Komenti u ruajt si default!');
  };

  // Clear saved comment
  const clearSavedComment = () => {
    localStorage.removeItem('receiptDefaultComment');
    setSavedReceiptComment('');
    toast.success('Komenti default u fshi!');
  };

  // Execute the actual print using iframe (more reliable, no popup blockers)
  const executeThermalPrint = (showDialog = true) => {
    const printArea = document.getElementById('thermal-receipt-print');
    if (!printArea) {
      toast.error('Gabim: Kuponi nuk u gjet');
      return;
    }

    // Create hidden iframe for printing
    const printFrame = document.createElement('iframe');
    printFrame.id = 'thermal-print-frame';
    printFrame.style.position = 'absolute';
    printFrame.style.top = '-10000px';
    printFrame.style.left = '-10000px';
    printFrame.style.width = '80mm';
    printFrame.style.height = '0';
    
    // Remove any existing print frame
    const existingFrame = document.getElementById('thermal-print-frame');
    if (existingFrame) {
      existingFrame.remove();
    }
    
    document.body.appendChild(printFrame);

    const printDocument = printFrame.contentDocument || printFrame.contentWindow.document;
    
    printDocument.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Kupon Shitje</title>
          <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
              font-family: 'Courier New', 'Consolas', monospace; 
              font-size: 11px; 
              line-height: 1.4;
              width: 80mm;
              max-width: 80mm;
              min-height: 180mm;
              padding: 4mm;
              background: white;
              color: #000;
            }
            div { box-sizing: border-box; }
            img { max-width: 100%; height: auto; }
            @media print {
              @page { 
                size: 80mm auto; 
                margin: 0; 
              }
              html, body { 
                width: 80mm !important;
                max-width: 80mm !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
              }
            }
          </style>
        </head>
        <body>
          ${printArea.innerHTML}
        </body>
      </html>
    `);
    
    printDocument.close();
    
    // Wait for content to load, then print
    setTimeout(() => {
      try {
        printFrame.contentWindow.focus();
        
        // Check if running in Electron with silent print support
        if (window.electron && window.electron.print) {
          // Electron silent print
          window.electron.print({ silent: !showDialog });
          toast.success('Kuponi u printua!');
        } else {
          // Standard browser print
          printFrame.contentWindow.print();
        }
      } catch (e) {
        console.error('Print error:', e);
        toast.error('Gabim gjatë printimit. Provoni përsëri.');
      }
      // Remove iframe after a delay
      setTimeout(() => {
        const frame = document.getElementById('thermal-print-frame');
        if (frame) {
          frame.remove();
        }
      }, 2000);
    }, 300);
    
    if (showDialog) {
      toast.success('Kuponi po dërgohet për printim...');
    } else {
      toast.success('Kuponi u dërgua direkt në printer!');
    }
  };

  // Direct print function (prints and closes dialog)
  const executeDirectPrint = () => {
    executeThermalPrint(false);
  };

  const handlePayment = async () => {
    if (cart.length === 0) {
      toast.error('Shporta është bosh');
      return;
    }

    // Validate debtor name for debt sales
    if (isDebt && !debtorName.trim()) {
      toast.error('Ju lutem shkruani emrin e debitorit');
      return;
    }

    // Calculate paid amount and remaining debt
    const paidAmount = parseFloat(cashAmount) || 0;
    const couponDiscount = couponData?.discount_amount || 0;
    const finalTotal = Math.max(0, cartTotals.total - couponDiscount);
    const remainingDebt = isDebt ? Math.max(0, finalTotal - paidAmount) : 0;

    try {
      const saleData = {
        items: cart.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity,
          unit_price: item.unit_price,
          discount_percent: item.discount_percent,
          vat_percent: item.vat_percent
        })),
        payment_method: paymentMethod,
        cash_amount: paidAmount,
        bank_amount: !isDebt && paymentMethod === 'bank' ? finalTotal : 0,
        customer_name: isDebt ? debtorName : (customerName || null),
        notes: customerNote || null,
        // Debt fields
        is_debt: isDebt,
        debtor_name: isDebt ? debtorName : null,
        remaining_debt: remainingDebt,
        coupon_code: couponData?.code || null
      };

      const response = await api.post('/sales', saleData);
      
      if (isDebt) {
        if (remainingDebt > 0) {
          toast.success(`Borgj i regjistruar: ${response.data.receipt_number} - ${debtorName} (Mbetur: €${remainingDebt.toFixed(2)})`);
        } else {
          toast.success(`Shitja u regjistrua plotësisht: ${response.data.receipt_number}`);
        }
      } else {
        toast.success(`Shitja u regjistrua: ${response.data.receipt_number}`);
      }
      
      // Print thermal receipt if option is checked
      if (printReceipt) {
        const receiptData = {
          ...response.data,
          items: cart.map(item => ({
            ...item,
            total: calculateItemTotal(item).total
          })),
          subtotal: cartTotals.subtotal,
          total_discount: cartTotals.discount,
          total_vat: cartTotals.vat,
          grand_total: cartTotals.total,
          cash_amount: paidAmount,
          change_amount: !isDebt ? Math.max(0, paidAmount - cartTotals.total) : 0,
          customer_name: isDebt ? debtorName : (customerName || null),
          is_debt: isDebt,
          debtor_name: isDebt ? debtorName : null,
          remaining_debt: remainingDebt,
        coupon_code: couponData?.code || null,
          paid_amount: paidAmount
        };
        printThermalReceipt(receiptData);
      }
      
      setCart([]);
      setShowPayment(false);
      setCashAmount('');
      setCustomerName('');
      setCustomerNote('');
      setSelectedItemIndex(null);
      // Reset debt state
      setIsDebt(false);
      setDebtorName('');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë regjistrimit të shitjes');
    }
  };

  // Print note (simulation)
  const handlePrintNote = () => {
    if (cart.length === 0) {
      toast.error('Shporta është bosh');
      return;
    }
    // Create printable content with tenant company name
    const companyName = companySettings?.company_name || 'DataPOS';
    const printContent = `
      =====================================
      ${companyName} - NOTË
      =====================================
      Data: ${new Date().toLocaleString('sq-AL')}
      Arkëtar: ${user?.full_name}
      -------------------------------------
      ${cart.map((item, i) => `${i+1}. ${item.product_name || 'Produkt'} x${item.quantity} = €${calculateItemTotal(item).total.toFixed(2)}`).join('\n')}
      -------------------------------------
      TOTAL: €${cartTotals.total.toFixed(2)}
      =====================================
    `;
    console.log(printContent);
    toast.success('Nota u dërgua për printim');
  };

  // Open buyer form before printing A4
  const handlePrintA4 = (sale = null) => {
    if (!sale && cart.length === 0) {
      toast.error('Shporta është bosh');
      return;
    }
    
    // If sale is provided (from documents), go directly to print
    if (sale) {
      setCurrentSaleForPrint(sale);
      setShowInvoiceA4(true);
      return;
    }
    
    // Otherwise show buyer form first
    setBuyerInfo({
      name: customerName || '',
      address: '',
      phone: '',
      nui: '',
      nf: ''
    });
    setShowBuyerForm(true);
  };

  // Proceed to print after filling buyer info
  const proceedToPrintA4 = () => {
    const saleData = {
      receipt_number: 'PREVIEW',
      items: cart.map(item => ({
        ...item,
        total: calculateItemTotal(item).total
      })),
      subtotal: cartTotals.subtotal,
      total_discount: cartTotals.discount,
      total_vat: cartTotals.vat,
      grand_total: cartTotals.total,
      payment_method: paymentMethod,
      cash_amount: parseFloat(cashAmount) || 0,
      bank_amount: paymentMethod === 'bank' ? cartTotals.total : 0,
      change_amount: changeAmount,
      customer_name: buyerInfo.name,
      buyer_info: buyerInfo,
      notes: customerNote,
      created_at: new Date().toISOString()
    };
    
    setCurrentSaleForPrint(saleData);
    setShowBuyerForm(false);
    setShowInvoiceA4(true);
  };

  // Print the invoice
  const executePrint = () => {
    const printContent = invoiceRef.current;
    if (!printContent) {
      toast.error('Gabim: Fatura nuk u gjet');
      return;
    }

    // Create hidden iframe for printing (more reliable than window.open)
    const printFrame = document.createElement('iframe');
    printFrame.id = 'a4-print-frame';
    printFrame.style.position = 'absolute';
    printFrame.style.top = '-10000px';
    printFrame.style.left = '-10000px';
    printFrame.style.width = '210mm';
    printFrame.style.height = '0';
    
    // Remove any existing print frame
    const existingFrame = document.getElementById('a4-print-frame');
    if (existingFrame) {
      existingFrame.remove();
    }
    
    document.body.appendChild(printFrame);

    const printDocument = printFrame.contentDocument || printFrame.contentWindow.document;
    
    printDocument.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Faturë - ${currentSaleForPrint?.receipt_number || 'Preview'}</title>
          <script src="https://cdn.tailwindcss.com"></script>
          <style>
            @media print {
              body { margin: 0; padding: 0; }
              @page { size: A4; margin: 0; }
            }
            body { font-family: Arial, sans-serif; }
          </style>
        </head>
        <body>
          ${printContent.outerHTML}
        </body>
      </html>
    `);
    
    printDocument.close();
    
    // Wait for content and Tailwind to load, then print
    setTimeout(() => {
      try {
        printFrame.contentWindow.focus();
        printFrame.contentWindow.print();
      } catch (e) {
        console.error('Print error:', e);
        toast.error('Gabim gjatë printimit. Provoni përsëri.');
      }
      // Remove iframe after print dialog closes
      setTimeout(() => {
        const frame = document.getElementById('a4-print-frame');
        if (frame) {
          frame.remove();
        }
      }, 2000);
    }, 800);
    
    toast.success('Fatura po dërgohet për printim...');
  };

  // View and print recent sale A4
  const handleViewSaleA4 = async (saleId) => {
    try {
      const response = await api.get(`/sales/${saleId}`);
      setCurrentSaleForPrint(response.data);
      setShowInvoiceA4(true);
      setShowDocuments(false);
    } catch (error) {
      toast.error('Gabim gjatë ngarkimit të faturës');
    }
  };

  // Apply no VAT to all items
  const handleNoVat = () => {
    setApplyNoVat(!applyNoVat);
    setCart(prevCart => 
      prevCart.map(item => ({
        ...item,
        vat_percent: applyNoVat ? (products.find(p => p.id === item.product_id)?.vat_rate || 0) : 0
      }))
    );
    toast.success(applyNoVat ? 'TVSH u aktivizua' : 'TVSH u çaktivizua');
  };

  // Numpad handler
  const handleNumpad = (value) => {
    if (value === 'clear') {
      setCashAmount('');
    } else if (value === 'backspace') {
      setCashAmount(prev => prev.slice(0, -1));
    } else {
      setCashAmount(prev => prev + value);
    }
  };

  // Reference for cash input
  const cashInputRef = useRef(null);

  // Focus on cash input when payment dialog opens
  useEffect(() => {
    if (showPayment && paymentMethod === 'cash' && cashInputRef.current) {
      setTimeout(() => {
        cashInputRef.current?.focus();
        cashInputRef.current?.select();
      }, 100);
    }
  }, [showPayment, paymentMethod]);

  // Keyboard shortcuts for POS operations
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger shortcuts when typing in input fields (except specific shortcuts)
      const isInputActive = document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA';
      
      // F1 - Ndihma (Help)
      if (e.key === 'F1') {
        e.preventDefault();
        toast.info(
          <div className="text-sm">
            <strong>Shkurtesat e Tastierës:</strong><br/>
            F1 - Ndihma<br/>
            F2 - Shtyp & Përfundo<br/>
            F4 - Shtyp A4<br/>
            F6 - Lista e shitjeve<br/>
            {companySettings?.show_warranty_in_pos !== false && <>F7 - Garancioni<br/></>}
            F9 - Dritarja për pagesë<br/>
            F10 - Pagesë direkte<br/>
            F12 - Lista e artikujve<br/>
            Ctrl+1 - Zgjidh artikullin<br/>
            Ctrl+* - Ndrysho çmimin<br/>
            Ctrl++ - Shto sasinë<br/>
            Ctrl+- - Zbrit sasinë<br/>
            Delete - Fshij artikullin
          </div>,
          { duration: 8000 }
        );
        return;
      }
      
      // F2 - Shtyp & Përfundo (Open payment dialog) - EXISTING
      if (e.key === 'F2' && cart.length > 0 && !showPayment && cashDrawer) {
        e.preventDefault();
        setCashAmount('');
        setPaymentMethod('cash');
        setShowPayment(true);
        return;
      }
      
      // F4 - Shtyp A4
      if (e.key === 'F4') {
        e.preventDefault();
        if (cart.length > 0) {
          setShowInvoiceA4(true);
        } else {
          toast.error('Shporta është bosh');
        }
        return;
      }
      
      // F6 - Lista e shitjeve
      if (e.key === 'F6') {
        e.preventDefault();
        setShowDocuments(true);
        return;
      }
      
      // F7 - Garancioni (Warranty document) - only if warranty is enabled
      if (e.key === 'F7' && companySettings?.show_warranty_in_pos !== false) {
        e.preventDefault();
        setShowWarranty(true);
        return;
      }
      
      // F9 - Dritarja për pagesë
      if (e.key === 'F9' && cart.length > 0 && cashDrawer) {
        e.preventDefault();
        setCashAmount('');
        setPaymentMethod('cash');
        setShowPayment(true);
        return;
      }
      
      // F10 - Pagesë direkte (me kartë)
      if (e.key === 'F10' && cart.length > 0 && cashDrawer) {
        e.preventDefault();
        setPaymentMethod('bank');
        setCashAmount('');
        setShowPayment(true);
        // Auto-submit after a short delay
        setTimeout(() => {
          handlePayment();
        }, 100);
        return;
      }
      
      // F12 - Lista e artikujve
      if (e.key === 'F12') {
        e.preventDefault();
        setShowProductSearch(true);
        return;
      }
      
      // Enter in payment dialog - complete sale
      if (e.key === 'Enter' && showPayment) {
        e.preventDefault();
        if (paymentMethod === 'bank' || (paymentMethod === 'cash' && parseFloat(cashAmount) >= (cartTotals.total - (couponData?.discount_amount || 0)))) {
          handlePayment();
        }
        return;
      }
      
      // Enter for barcode/search (when not in payment dialog)
      if (e.key === 'Enter' && search && !showPayment && !showProductSearch) {
        e.preventDefault();
        const productByBarcode = products.find(p => p.barcode === search.trim());
        if (productByBarcode) {
          addToCart(productByBarcode);
          setSearch('');
          setShowSearchResults(false);
          return;
        }
        if (mainSearchResults.length > 0) {
          addToCart(mainSearchResults[0]);
          setSearch('');
          setShowSearchResults(false);
        }
        return;
      }
      
      // Delete - Fshij artikullin e zgjedhur
      if (e.key === 'Delete' && !isInputActive) {
        e.preventDefault();
        deleteSelectedItem();
        return;
      }
      
      // Ctrl+1 - Zgjidh artikullin e parë në shportë
      if (e.ctrlKey && e.key === '1') {
        e.preventDefault();
        if (cart.length > 0) {
          setSelectedItemIndex(0);
          toast.info('Artikulli i parë u zgjodh');
        }
        return;
      }
      
      // Ctrl+* - Ndrysho çmimin e artikullit të zgjedhur
      if (e.ctrlKey && (e.key === '*' || e.key === '8')) {
        e.preventDefault();
        if (selectedItemIndex !== null && cart[selectedItemIndex]) {
          const newPrice = prompt('Shkruaj çmimin e ri:', cart[selectedItemIndex].unit_price);
          if (newPrice !== null && !isNaN(parseFloat(newPrice))) {
            setCart(prevCart => prevCart.map((item, idx) => 
              idx === selectedItemIndex 
                ? { ...item, unit_price: parseFloat(newPrice) }
                : item
            ));
            toast.success('Çmimi u ndryshua');
          }
        } else {
          toast.error('Zgjidhni një artikull së pari (Ctrl+1)');
        }
        return;
      }
      
      // Ctrl++ - Shto sasinë
      if (e.ctrlKey && (e.key === '+' || e.key === '=')) {
        e.preventDefault();
        if (selectedItemIndex !== null && cart[selectedItemIndex]) {
          updateQuantity(cart[selectedItemIndex].product_id, cart[selectedItemIndex].quantity + 1);
          toast.success('Sasia u shtua');
        } else {
          toast.error('Zgjidhni një artikull së pari (Ctrl+1)');
        }
        return;
      }
      
      // Ctrl+- - Zbrit sasinë
      if (e.ctrlKey && e.key === '-') {
        e.preventDefault();
        if (selectedItemIndex !== null && cart[selectedItemIndex]) {
          if (cart[selectedItemIndex].quantity > 1) {
            updateQuantity(cart[selectedItemIndex].product_id, cart[selectedItemIndex].quantity - 1);
            toast.success('Sasia u zbrit');
          } else {
            toast.error('Sasia minimale është 1');
          }
        } else {
          toast.error('Zgjidhni një artikull së pari (Ctrl+1)');
        }
        return;
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [search, products, addToCart, showPayment, showProductSearch, mainSearchResults, cart, cashDrawer, paymentMethod, cashAmount, cartTotals.total, selectedItemIndex, deleteSelectedItem, updateQuantity]);

  // Check if cashier should see full POS mode (no sidebar)
  const isCashierFullscreen = user?.role === 'cashier';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="spinner" />
      </div>
    );
  }

  // Check if drawer is open - show fullscreen for cashier
  if (!cashDrawer) {
    // For cashier - fullscreen view with header
    if (isCashierFullscreen) {
      return (
        <div className="min-h-screen bg-[#F8FAFC]">
          {/* Cashier Header */}
          <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Company Logo */}
              {companySettings?.logo_url ? (
                <img 
                  src={companySettings.logo_url} 
                  alt="Logo" 
                  className="h-8 w-auto object-contain"
                  onError={(e) => e.target.style.display = 'none'}
                />
              ) : (
                <span className="text-2xl font-bold text-[#00a79d]">→</span>
              )}
              {/* Company Name */}
              <span className="text-xl font-bold text-[#00a79d]">
                {companySettings?.company_name || 'DataPOS'}
              </span>
              <span className="text-gray-400 mx-2">|</span>
              <span className="text-gray-600">Arka</span>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                <p className="text-xs text-gray-500">Arkëtar</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                className="gap-2 text-red-600 border-red-200 hover:bg-red-50"
                data-testid="logout-btn"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Çkyçu</span>
              </Button>
            </div>
          </header>

          {/* Open Drawer Content */}
          <div className="flex flex-col items-center justify-center h-[calc(100vh-5rem)]" data-testid="pos-open-drawer">
            <div className="text-center space-y-6">
              <div className="h-24 w-24 mx-auto bg-[#00a79d]/10 rounded-full flex items-center justify-center">
                <Calculator className="h-12 w-12 text-[#00a79d]" />
              </div>
              <div>
                <h2 className="text-3xl font-bold text-gray-900">Arka është e Mbyllur</h2>
                <p className="text-gray-500 mt-2">Hapni arkën për të filluar shitjen</p>
              </div>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button
                  onClick={() => setShowOpenDrawer(true)}
                  className="bg-[#00a79d] hover:bg-[#008f86] text-white px-8 py-6 text-lg"
                  data-testid="open-drawer-btn"
                >
                  <Calculator className="h-5 w-5 mr-2" />
                  Hap Arkën
                </Button>
                <Button
                  variant="outline"
                  onClick={handleLogout}
                  className="px-8 py-6 text-lg text-red-600 border-red-200 hover:bg-red-50"
                  data-testid="logout-main-btn"
                >
                  <LogOut className="h-5 w-5 mr-2" />
                  Çkyçu
                </Button>
              </div>
            </div>

            {/* Open Drawer Dialog */}
            <Dialog open={showOpenDrawer} onOpenChange={setShowOpenDrawer}>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Hap Arkën</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 pt-4">
                  <div>
                    <Label>Bilanci Fillestar (€)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={openingBalance}
                      onChange={(e) => setOpeningBalance(e.target.value)}
                      placeholder="0.00"
                      className="mt-1"
                      data-testid="opening-balance-input"
                    />
                  </div>
                  <Button
                    onClick={handleOpenDrawer}
                    className="w-full bg-[#00a79d] hover:bg-[#008f86]"
                    data-testid="confirm-open-drawer"
                  >
                    Konfirmo
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      );
    }

    // For admin/manager - normal view
    return (
      <div className="flex flex-col items-center justify-center h-[70vh]" data-testid="pos-open-drawer">
        <div className="text-center space-y-4">
          <div className="h-20 w-20 mx-auto bg-[#00a79d]/10 rounded-full flex items-center justify-center">
            <Calculator className="h-10 w-10 text-[#00a79d]" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Arka është e Mbyllur</h2>
          <p className="text-gray-500">Hapni arkën për të filluar shitjen</p>
          <Button
            onClick={() => setShowOpenDrawer(true)}
            className="bg-[#00a79d] hover:bg-[#008f86] text-white px-8 py-6 text-lg"
            data-testid="open-drawer-btn"
          >
            Hap Arkën
          </Button>
        </div>

        {/* Open Drawer Dialog */}
        <Dialog open={showOpenDrawer} onOpenChange={setShowOpenDrawer}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Hap Arkën</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-4">
              <div>
                <Label>Bilanci Fillestar (€)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={openingBalance}
                  onChange={(e) => setOpeningBalance(e.target.value)}
                  placeholder="0.00"
                  className="mt-1"
                  data-testid="opening-balance-input"
                />
              </div>
              <Button
                onClick={handleOpenDrawer}
                className="w-full bg-[#00a79d] hover:bg-[#008f86]"
                data-testid="confirm-open-drawer"
              >
                Konfirmo
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    );
  }

  // Full screen POS layout for cashier
  const posContent = (
    <div
      className={`${isCashierFullscreen ? 'h-[calc(100vh-5rem)]' : 'h-[calc(100vh-8rem)]'} flex flex-col lg:flex-row gap-3 ${responsiveClasses.container}`}
      style={{
        fontSize: `calc(1rem * ${scale})`,
        '--dynamic-scale': scale
      }}
      data-testid="pos-page"
    >
      {/* Left Side - Product Search & Cart */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header with search */}
        <div className="flex items-center gap-3 mb-3 lg:mb-4">
          <div className="hidden sm:flex items-center gap-2.5 px-3 py-2 rounded-2xl bg-white/70 backdrop-blur-md border border-gray-200/60 shadow-sm">
            <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-[#00a79d] to-[#007a73] flex items-center justify-center text-white text-sm font-semibold">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="hidden md:flex flex-col leading-tight">
              <span className="text-xs font-semibold text-gray-800">{user?.full_name}</span>
              <span className="text-[10px] text-gray-400">{currentTime.toLocaleTimeString('sq-AL', { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
          </div>

          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-[#00a79d]" />
            <Input
              ref={searchRef}
              type="text"
              placeholder={'K\u00EBrko produkt ose skano barkod...'}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setShowSearchResults(e.target.value.trim().length > 0);
              }}
              onFocus={() => search.trim() && setShowSearchResults(true)}
              onBlur={() => setTimeout(() => setShowSearchResults(false), 200)}
              className="pl-12 h-12 text-base rounded-2xl border-gray-200/80 bg-white/80 backdrop-blur-md shadow-sm focus-visible:ring-2 focus-visible:ring-[#00a79d]/40 focus-visible:border-[#00a79d]"
              data-testid="pos-search-input"
            />

            {showSearchResults && mainSearchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white/95 backdrop-blur-xl border border-gray-200/70 rounded-2xl shadow-xl z-50 max-h-72 overflow-auto p-1.5">
                {mainSearchResults.map((product) => (
                  <div
                    key={product.id}
                    className={`p-3 rounded-xl cursor-pointer transition-colors ${product.current_stock > 0 ? 'hover:bg-[#00a79d]/10' : 'bg-gray-50 opacity-70'}`}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      addToCart(product);
                    }}
                  >
                    <div className="flex justify-between items-center gap-3">
                      <div className="min-w-0">
                        <p className="font-semibold text-gray-900 truncate">{product.name || 'Pa em\u00EBr'}</p>
                        <p className="text-xs text-gray-400">Barkod: {product.barcode || '-'}</p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="font-bold text-[#00a79d]">{`\u20AC${(product.sale_price || 0).toFixed(2)}`}</p>
                        <p className={`text-xs ${product.current_stock > 0 ? 'text-emerald-600' : 'text-red-500 font-semibold'}`}>
                          {product.current_stock > 0 ? `Stok: ${product.current_stock}` : 'Pa stok!'}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {showSearchResults && search.trim() && mainSearchResults.length === 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white/95 backdrop-blur-xl border border-gray-200/70 rounded-2xl shadow-xl z-50 p-4 text-center text-gray-500">
                {`Nuk u gjet asnj\u00EB produkt p\u00EBr "${search}"`}
              </div>
            )}
          </div>
          {customerName && (
            <div className="flex items-center gap-2 px-3 py-2 bg-[#00a79d]/10 rounded-2xl border border-[#00a79d]/20">
              <User className="h-4 w-4 text-[#00a79d]" />
              <span className="text-sm font-semibold text-[#00a79d]">{customerName}</span>
            </div>
          )}
        </div>

        {/* Cart Table */}
        <Card className="flex-1 border border-gray-200/60 rounded-3xl shadow-sm overflow-hidden bg-white/80 backdrop-blur-md flex flex-col">
          <div className="bg-gradient-to-r from-[#00a79d]/15 to-[#00c4b8]/10 px-4 py-3 border-b border-[#00a79d]/15">
            <div className="grid grid-cols-12 gap-2 text-[11px] font-bold text-gray-600 uppercase tracking-wide">
              <div className="col-span-1">Nr</div>
              <div className="col-span-3">{'Em\u00EBrtimi'}</div>
              <div className="col-span-1 text-center">Sasia</div>
              <div className="col-span-2 text-right">{'\u00C7mimi'}</div>
              <div className="col-span-1 text-center">Zbritja %</div>
              <div className="col-span-1 text-center">Tvsh %</div>
              <div className="col-span-2 text-right">{'\u00C7mimi me tvsh'}</div>
              <div className="col-span-1 text-right">Total</div>
            </div>
          </div>
          <div className="overflow-auto flex-1" style={{ maxHeight: 'calc(100vh - 24rem)' }}>
            <Table>
              <TableBody>
                {cart.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={12} className="text-center py-16 text-gray-400">
                      <div className="h-16 w-16 mx-auto mb-3 rounded-2xl bg-gray-100 flex items-center justify-center">
                        <Package className="h-8 w-8 opacity-40" />
                      </div>
                      <p className="font-medium">{'Shtoni produkte n\u00EB shport\u00EB'}</p>
                    </TableCell>
                  </TableRow>
                ) : (
                  cart.map((item, index) => {
                    const { subtotal, total } = calculateItemTotal(item);
                    const canEdit = user?.role === 'admin' || user?.role === 'manager' || user?.role === 'super_admin';
                    return (
                      <TableRow
                        key={item.product_id}
                        className={`cursor-pointer transition-colors ${selectedItemIndex === index ? 'bg-[#00a79d]/10' : 'hover:bg-gray-50'}`}
                        onClick={() => setSelectedItemIndex(index)}
                      >
                        <TableCell className="w-12 text-gray-400 font-medium">{index + 1}</TableCell>
                        <TableCell>
                          {canEdit ? (
                            <Select
                              value={item.product_id}
                              onValueChange={(value) => {
                                const product = products.find(p => p.id === value);
                                if (product) {
                                  setCart(prev => prev.map((it, i) =>
                                    i === index ? {
                                      ...it,
                                      product_id: product.id,
                                      product_name: product.name,
                                      unit_price: product.sale_price || 0,
                                      vat_percent: applyNoVat ? 0 : (product.vat_rate || 0),
                                      max_stock: product.current_stock, image_url: product.metadata?.image_url || null
                                    } : it
                                  ));
                                }
                              }}
                            >
                              <SelectTrigger className="border-gray-200 rounded-xl">
                                <SelectValue><span className="inline-flex items-center gap-2">{item.image_url ? <img src={item.image_url} alt="" className="h-6 w-6 rounded object-cover" /> : null}<span>{item.product_name || 'Zgjidh'}</span></span></SelectValue>
                              </SelectTrigger>
                              <SelectContent>
                                {products.filter(p => p.current_stock > 0).map(p => (
                                  <SelectItem key={p.id} value={p.id}>
                                    {p.name || p.barcode || p.id}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          ) : (
                            <div className="flex items-center gap-2">{item.image_url ? <img src={item.image_url} alt="" className="h-8 w-8 rounded-md object-cover border border-gray-200" /> : null}<span className="font-semibold text-gray-800">{item.product_name || 'Produkt'}</span></div>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center justify-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 rounded-lg hover:bg-[#00a79d]/10 hover:text-[#00a79d]"
                              onClick={(e) => { e.stopPropagation(); updateQuantity(item.product_id, -1); }}
                            >
                              <Minus className="h-3 w-3" />
                            </Button>
                            <span className="w-8 text-center font-bold text-gray-800">{item.quantity}</span>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 rounded-lg hover:bg-[#00a79d]/10 hover:text-[#00a79d]"
                              onClick={(e) => { e.stopPropagation(); updateQuantity(item.product_id, 1); }}
                            >
                              <Plus className="h-3 w-3" />
                            </Button>
                          </div>
                        </TableCell>
                        <TableCell className="text-right text-gray-600">{`\u20AC${item.unit_price.toFixed(2)}`}</TableCell>
                        <TableCell>
                          <div className="flex items-center justify-center gap-1">
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              step="1"
                              value={item.discount_percent}
                              onChange={(e) => updateDiscount(item.product_id, e.target.value)}
                              onClick={(e) => e.stopPropagation()}
                              className="w-16 h-8 text-center rounded-lg border-[#00a79d]/30 focus:border-[#00a79d]"
                              title="Zbritja ne perqindje"
                            />
                            <span className="text-xs text-gray-500 font-semibold">%</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-center text-gray-600">{item.vat_percent}</TableCell>
                        <TableCell className="text-right text-gray-600">{`\u20AC${(item.unit_price * (1 - item.discount_percent / 100) * (1 + item.vat_percent / 100)).toFixed(2)}`}</TableCell>
                        <TableCell className="text-right font-bold text-gray-900">{`\u20AC${total.toFixed(2)}`}</TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 rounded-lg text-red-400 hover:text-red-600 hover:bg-red-50"
                            onClick={(e) => { e.stopPropagation(); removeFromCart(item.product_id); }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>

          {/* Cart Totals */}
          <div className="mt-auto border-t border-[#00a79d]/15 bg-gradient-to-r from-[#00a79d] to-[#007a73] p-4">
            <div className="flex justify-between items-center gap-4 flex-wrap">
              <div className="flex gap-5 text-sm text-white/85">
                <span>Subtotal: <span className="font-semibold text-white">{`\u20AC${cartTotals.subtotal.toFixed(2)}`}</span></span>
                <span>Zbritja: <span className="font-semibold text-amber-200">{`-\u20AC${cartTotals.discount.toFixed(2)}`}</span></span>
                <span>TVSH: <span className="font-semibold text-white">{`\u20AC${cartTotals.vat.toFixed(2)}`}</span></span>
              </div>
              <div className="text-right">
                <div className="text-[10px] uppercase tracking-widest text-white/70 font-semibold">Totali</div>
                <div className="text-4xl font-extrabold text-white leading-none">{`\u20AC${Math.max(0, cartTotals.total - (couponData?.discount_amount || 0)).toFixed(2)}`}</div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Right Side - Action Buttons */}
      <div className="w-full lg:w-52 flex flex-row lg:flex-col gap-2 flex-wrap lg:flex-nowrap lg:overflow-y-auto">
        <Button
          className="flex-1 lg:h-16 flex items-center justify-center gap-2 bg-gradient-to-br from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold shadow-lg shadow-emerald-500/25 rounded-2xl text-base"
          onClick={() => cart.length > 0 && setShowPayment(true)}
          disabled={cart.length === 0}
          data-testid="pos-print-btn"
        >
          <Printer className="h-5 w-5" />
          <span className="hidden lg:inline">Shtyp</span>
          <span className="text-xs bg-white/20 px-2 py-0.5 rounded-md ml-1">F2</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-blue-200 text-blue-600 hover:bg-blue-50 hover:border-blue-300"
          onClick={() => handlePrintA4()}
          disabled={cart.length === 0}
          data-testid="pos-print-a4-btn"
        >
          <FileDown className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">Printo A4</span>
          <span className="text-xs bg-blue-100 px-1.5 py-0.5 rounded-md ml-1">F4</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300"
          onClick={() => setShowProductSearch(true)}
          data-testid="pos-add-product-btn"
        >
          <Package className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">{'K\u00EBrko artikullin'}</span>
          <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded-md ml-1">F12</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300"
          onClick={() => setShowDocuments(true)}
          data-testid="pos-documents-btn"
        >
          <FileText className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">Dokumentin</span>
          <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded-md ml-1">F6</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300"
          onClick={handlePrintNote}
          data-testid="pos-print-note-btn"
        >
          <Receipt className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">Shtyp Noten</span>
        </Button>

        {companySettings?.show_warranty_in_pos !== false && (
          <>
            <Button
              variant="outline"
              className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-emerald-200 text-emerald-600 hover:bg-emerald-50 hover:border-emerald-300"
              onClick={() => setShowWarranty(true)}
              data-testid="pos-warranty-btn"
            >
              <Shield className="h-5 w-5" strokeWidth={1.75} />
              <span className="hidden lg:inline">Garancioni</span>
              <span className="text-xs bg-emerald-100 px-1.5 py-0.5 rounded-md ml-1">F7</span>
            </Button>

            <Button
              variant="outline"
              className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-emerald-200 text-emerald-500 hover:bg-emerald-50 hover:border-emerald-300"
              onClick={() => {
                loadWarranties();
                setShowWarrantyList(true);
              }}
              data-testid="pos-warranty-list-btn"
            >
              <List className="h-5 w-5" strokeWidth={1.75} />
              <span className="hidden lg:inline">Garancione</span>
            </Button>
          </>
        )}

        <Button
          variant="outline"
          className={`flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300 ${customerName ? 'border-[#00a79d] text-[#00a79d] bg-[#00a79d]/5' : ''}`}
          onClick={() => setShowCustomer(true)}
          data-testid="pos-customer-btn"
        >
          <User className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">Konsumatori</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300"
          onClick={() => setShowParams(true)}
          data-testid="pos-params-btn"
        >
          <Settings className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">Parametrat</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300"
          onClick={deleteSelectedItem}
          data-testid="pos-delete-btn"
        >
          <Trash2 className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">{'Fshij artikullin'}</span>
          <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded-md ml-1">Del</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-red-200 text-red-500 hover:bg-red-50 hover:border-red-300"
          onClick={clearCart}
          data-testid="pos-clear-btn"
        >
          <Trash2 className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">Pastro</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300"
          onClick={handleCloseDrawer}
          data-testid="pos-close-drawer-btn"
        >
          <XCircle className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">{'Mbyll Ark\u00EBn'}</span>
        </Button>

        {(user?.role === 'admin' || user?.role === 'manager') && (
          <Button
            className={`flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl text-white ${applyNoVat ? 'bg-orange-500 hover:bg-orange-600' : 'bg-[#00a79d] hover:bg-[#008f86]'}`}
            onClick={handleNoVat}
            data-testid="pos-no-vat-btn"
          >
            <Percent className="h-5 w-5" strokeWidth={1.75} />
            <span className="hidden lg:inline">{applyNoVat ? 'Me TVSH' : 'Pa TVSH'}</span>
          </Button>
        )}

        {/* Zbritje me kupon */}
        {!couponEnabled && !couponData && (
          <Button
            variant="outline"
            className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-amber-300 text-amber-700 hover:bg-amber-50 hover:border-amber-400"
            onClick={() => setCouponEnabled(true)}
            data-testid="pos-coupon-btn"
          >
            <Ticket className="h-5 w-5" strokeWidth={1.75} />
            <span className="hidden lg:inline">Zbritje me kupon</span>
          </Button>
        )}
        {couponEnabled && !couponData && (
          <div className="flex-1 lg:h-14 flex items-center gap-1 rounded-2xl border border-amber-400 bg-amber-50 px-2 py-1">
            <input
              type="text"
              value={couponCode}
              onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleApplyCoupon(); } else if (e.key === 'Escape') { setCouponEnabled(false); setCouponCode(''); } }}
              placeholder="Kodi"
              autoFocus
              className="flex-1 min-w-0 px-2 h-9 rounded-lg bg-white border border-amber-200 text-gray-900 placeholder-gray-400 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-amber-300"
              data-testid="pos-coupon-input"
            />
            <button
              type="button"
              onClick={handleApplyCoupon}
              disabled={!couponCode.trim() || couponLoading}
              className="px-2 h-9 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs uppercase disabled:opacity-50"
              title="Apliko (Enter)"
            >
              {couponLoading ? '...' : 'OK'}
            </button>
            <button
              type="button"
              onClick={() => { setCouponEnabled(false); setCouponCode(''); }}
              className="h-9 w-9 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 flex items-center justify-center"
              title="Anulo (Esc)"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}
        {couponData && (
          <Button
            variant="outline"
            className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-amber-400 bg-amber-100 hover:bg-amber-200 text-amber-900"
            onClick={handleRemoveCoupon}
            data-testid="pos-coupon-active-btn"
            title="Kliko per ta hequr kuponin"
          >
            <Ticket className="h-5 w-5" strokeWidth={1.75} />
            <span className="hidden lg:inline text-xs leading-tight text-left">
              <span className="font-mono font-bold block">{couponData.code}</span>
              <span className="text-amber-700">{`-\u20AC${(couponData.discount_amount || 0).toFixed(2)}`}</span>
            </span>
          </Button>
        )}
      </div>

      {/* Payment Dialog */}
      <Dialog open={showPayment} onOpenChange={setShowPayment}>
        <DialogContent className="sm:max-w-md p-0 overflow-hidden border-0 bg-transparent shadow-none">
          <div className="relative rounded-3xl overflow-hidden bg-[#faf9f4] border border-[#00a79d]/15 shadow-xl shadow-[#00a79d]/10">
            <div className="relative p-6 space-y-5">
              <DialogHeader className="flex flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-1 rounded-full bg-[#00a79d]"></div>
                  <div className="text-left">
                    <DialogTitle className="text-lg font-bold text-gray-900 tracking-tight m-0">{'P\u00EBrfundimi i Pages\u00EBs'}</DialogTitle>
                    <p className="text-xs text-gray-400 font-medium mt-0.5">{'Zgjidh m\u00EBnyr\u00EBn e pages\u00EBs'}</p>
                  </div>
                </div>
                <button type="button" onClick={() => setShowPayment(false)} className="h-9 w-9 rounded-xl bg-gray-100 hover:bg-gray-200 border border-gray-200 text-gray-600 hover:text-gray-900 flex items-center justify-center transition">
                  <X className="h-4 w-4" />
                </button>
              </DialogHeader>
              <div className="relative rounded-2xl bg-[#00a79d]/8 border border-[#00a79d]/15 p-5 text-center">
                <div className="text-[10px] uppercase tracking-[0.3em] text-[#00a79d]/80 font-semibold mb-1">{'Totali p\u00EBr Pages\u00EB'}</div>
                <div className="text-5xl font-extrabold tabular-nums text-[#00a79d]">{`\u20AC${Math.max(0, cartTotals.total - (couponData?.discount_amount || 0)).toFixed(2)}`}</div>
                <Zap className="absolute top-3 right-3 h-4 w-4 text-[#00a79d]/60" />
              </div>
              <div className="grid grid-cols-2 gap-2 p-1 rounded-2xl bg-gray-50 border border-gray-200">
                <button type="button" onClick={() => setPaymentMethod('cash')} data-testid="payment-cash-btn" className={`relative h-11 rounded-xl flex items-center justify-center gap-2 font-semibold text-sm transition-all ${paymentMethod === 'cash' ? 'bg-[#00a79d] text-white shadow-md shadow-[#00a79d]/30' : 'text-gray-500 hover:text-gray-900'}`}>
                  <Banknote className="h-4 w-4" /> Cash
                </button>
                <button type="button" onClick={() => setPaymentMethod('bank')} data-testid="payment-bank-btn" className={`relative h-11 rounded-xl flex items-center justify-center gap-2 font-semibold text-sm transition-all ${paymentMethod === 'bank' ? 'bg-[#00a79d] text-white shadow-md shadow-[#00a79d]/30' : 'text-gray-500 hover:text-gray-900'}`}>
                  <CreditCard className="h-4 w-4" /> Bank
                </button>
              </div>
              {paymentMethod === 'cash' && (
                <div className="space-y-4">
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#00a79d] font-bold text-lg pointer-events-none">{'\u20AC'}</span>
                    <input ref={cashInputRef} type="text" value={cashAmount} onChange={(e) => setCashAmount(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && parseFloat(cashAmount) >= (cartTotals.total - (couponData?.discount_amount || 0))) { e.preventDefault(); handlePayment(); } }} placeholder={'Shkruaj shum\u00EBn e paguar...'} autoFocus data-testid="cash-amount-input" className="w-full h-14 pl-10 pr-4 rounded-2xl bg-white border border-gray-200 text-xl font-bold text-gray-900 tabular-nums placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#00a79d]/40 focus:border-[#00a79d]/40 transition" />
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="rounded-xl bg-gray-50 border border-gray-200 p-3">
                      <div className="text-[9px] uppercase tracking-widest text-gray-500 font-semibold">Total</div>
                      <div className="text-base font-bold text-gray-900 tabular-nums mt-0.5">{`\u20AC${Math.max(0, cartTotals.total - (couponData?.discount_amount || 0)).toFixed(2)}`}</div>
                    </div>
                    <div className="rounded-xl bg-gray-50 border border-gray-200 p-3">
                      <div className="text-[9px] uppercase tracking-widest text-gray-500 font-semibold">Paguar</div>
                      <div className="text-base font-bold text-[#00a79d] tabular-nums mt-0.5">{`\u20AC${(parseFloat(cashAmount) || 0).toFixed(2)}`}</div>
                    </div>
                    <div className={`rounded-xl border p-3 transition ${changeAmount > 0 ? 'bg-emerald-50 border-emerald-300 shadow-lg shadow-emerald-500/30' : 'bg-gray-50 border-gray-200'}`}>
                      <div className="text-[9px] uppercase tracking-widest text-gray-500 font-semibold">Kusuri</div>
                      <div className={`text-base font-bold tabular-nums mt-0.5 ${changeAmount > 0 ? 'text-emerald-600' : 'text-gray-600'}`}>{`\u20AC${changeAmount.toFixed(2)}`}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {['7','8','9','4','5','6','1','2','3','.','0'].map((num) => (
                      <button key={num} type="button" onClick={() => handleNumpad(num)} className="h-12 rounded-xl bg-white hover:bg-gray-50 border border-gray-200 text-gray-900 text-lg font-bold tabular-nums transition active:scale-95">{num}</button>
                    ))}
                    <button type="button" onClick={() => handleNumpad('backspace')} className="h-12 rounded-xl bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-600 transition active:scale-95 flex items-center justify-center">
                      <Delete className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              )}
              {paymentMethod === 'bank' && (
                <div className="rounded-2xl bg-[#00a79d]/8 border border-[#00a79d]/20 p-6 text-center">
                  <CreditCard className="h-8 w-8 mx-auto text-[#00a79d] mb-2" />
                  <p className="text-xs uppercase tracking-widest text-[#00a79d] font-semibold mb-1">{'Pagesa me Kart\u00EB / Bank'}</p>
                  <p className="text-3xl font-extrabold text-gray-900 tabular-nums">{`\u20AC${cartTotals.total.toFixed(2)}`}</p>
                </div>
              )}
              <div className="space-y-2">
                <button type="button" onClick={() => setPrintReceipt(!printReceipt)} data-testid="print-receipt-checkbox" className={`w-full flex items-center gap-3 p-3 rounded-2xl border transition ${printReceipt ? 'bg-[#00a79d]/10 border-[#00a79d]/30' : 'bg-gray-50 border-gray-200 hover:bg-white'}`}>
                  <div className={`relative h-5 w-9 rounded-full transition ${printReceipt ? 'bg-[#00a79d]' : 'bg-gray-300'}`}>
                    <div className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${printReceipt ? 'left-4' : 'left-0.5'}`}></div>
                  </div>
                  <span className={`text-sm font-medium flex-1 text-left ${printReceipt ? 'text-[#00a79d]' : 'text-gray-600'}`}>{'Shtyp kupon p\u00EBr klientin'}</span>
                  <Printer className={`h-4 w-4 ${printReceipt ? 'text-[#00a79d]' : 'text-gray-400'}`} />
                </button>
                <button type="button" onClick={() => { const next = !isDebt; setIsDebt(next); if (!next) setDebtorName(''); }} data-testid="debt-checkbox" className={`w-full flex items-center gap-3 p-3 rounded-2xl border transition ${isDebt ? 'bg-amber-50 border-amber-300' : 'bg-gray-50 border-gray-200 hover:bg-white'}`}>
                  <div className={`relative h-5 w-9 rounded-full transition ${isDebt ? 'bg-amber-500' : 'bg-gray-300'}`}>
                    <div className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${isDebt ? 'left-4' : 'left-0.5'}`}></div>
                  </div>
                  <span className={`text-sm font-medium flex-1 text-left ${isDebt ? 'text-amber-700' : 'text-gray-600'}`}>Borgj (Shitje me Borxh)</span>
                  <Wallet className={`h-4 w-4 ${isDebt ? 'text-amber-600' : 'text-gray-400'}`} />
                </button>
                {isDebt && (
                  <div className="rounded-2xl bg-amber-50/60 border border-amber-300 p-4 space-y-3">
                    <div>
                      <label className="text-[10px] font-bold text-amber-700 uppercase tracking-wider">Emri i Debitorit <span className="text-rose-400">*</span></label>
                      <input type="text" value={debtorName} onChange={(e) => setDebtorName(e.target.value)} placeholder="Shkruaj emrin e debitorit..." autoFocus data-testid="debtor-name-input" className="mt-1.5 w-full h-10 px-3 rounded-xl bg-white border border-amber-300 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-400/50 transition" />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold text-amber-700 uppercase tracking-wider">Paguar Tani (opsional)</label>
                      <div className="relative mt-1.5">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-amber-600 font-bold pointer-events-none">{'\u20AC'}</span>
                        <input type="number" step="0.01" min="0" max={cartTotals.total} value={cashAmount} onChange={(e) => setCashAmount(e.target.value)} placeholder="0.00" data-testid="debt-paid-amount-input" className="w-full h-10 pl-8 pr-3 rounded-xl bg-white border border-amber-300 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-400/50 transition" />
                      </div>
                    </div>
                    <div className="rounded-xl bg-gray-50 border border-amber-200 p-3 space-y-1.5">
                      <div className="flex justify-between text-xs"><span className="text-gray-500">Total Fatura:</span><span className="font-bold text-gray-900 tabular-nums">{`\u20AC${cartTotals.total.toFixed(2)}`}</span></div>
                      <div className="flex justify-between text-xs"><span className="text-gray-500">Paguar Tani:</span><span className="font-bold text-emerald-600 tabular-nums">{`\u20AC${(parseFloat(cashAmount) || 0).toFixed(2)}`}</span></div>
                      <div className="flex justify-between text-sm font-bold border-t border-amber-200 pt-1.5 mt-1"><span className="text-amber-700">Borgj i Mbetur:</span><span className="text-amber-600 tabular-nums">{`\u20AC${Math.max(0, cartTotals.total - (parseFloat(cashAmount) || 0)).toFixed(2)}`}</span></div>
                    </div>
                  </div>
                )}
                {printReceipt && !isDebt && (
                  <div className="rounded-2xl bg-gray-50 border border-gray-200 p-3">
                    <label className="text-[10px] font-bold text-gray-600 uppercase tracking-wider">Emri i Klientit (opsional)</label>
                    <input type="text" value={customerName} onChange={(e) => setCustomerName(e.target.value)} placeholder="Shkruaj emrin e klientit..." data-testid="receipt-customer-name-input" className="mt-1.5 w-full h-9 px-3 rounded-xl bg-white border border-gray-200 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#00a79d]/40 transition" />
                  </div>
                )}
                {printReceipt && !isDebt && (
                  <button type="button" onClick={() => toggleDirectPrint(!directPrintEnabled)} data-testid="direct-print-checkbox" className={`w-full flex items-center gap-3 p-3 rounded-2xl border transition ${directPrintEnabled ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'}`}>
                    <div className={`relative h-5 w-9 rounded-full transition ${directPrintEnabled ? 'bg-blue-500' : 'bg-gray-300'}`}>
                      <div className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${directPrintEnabled ? 'left-4' : 'left-0.5'}`}></div>
                    </div>
                    <span className={`text-sm font-medium flex-1 text-left ${directPrintEnabled ? 'text-blue-700' : 'text-gray-600'}`}>Printim direkt (pa parapamje)</span>
                  </button>
                )}
              </div>
              <button type="button" onClick={handlePayment} disabled={isDebt && !debtorName.trim()} data-testid="confirm-payment-btn" className={`group relative w-full h-14 rounded-2xl font-bold text-base text-white shadow-2xl transition-all overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.01] active:scale-[0.99] ${isDebt ? 'bg-amber-500 shadow-amber-500/40 hover:shadow-amber-500/60' : 'bg-[#00a79d] shadow-[#00a79d]/40 hover:shadow-[#00a79d]/60'}`}>
                
                <span className="relative flex items-center justify-center gap-2">
                  
                  {isDebt ? 'Regjistro Borgj' : (printReceipt ? 'Shtyp & P\u00EBrfundo' : 'P\u00EBrfundo pa Shtypur')}
                  <ArrowRight className="h-4 w-4" />
                </span>
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Product Search Dialog */}
      <Dialog open={showProductSearch} onOpenChange={(open) => {
        setShowProductSearch(open);
        if (!open) setDialogSearch('');
      }}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Kërko Artikullin</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Kërko sipas emrit ose barkodit..."
                className="pl-10"
                autoFocus
                value={dialogSearch}
                onChange={(e) => setDialogSearch(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && filteredProducts.length > 0) {
                    addToCart(filteredProducts[0]);
                    setDialogSearch('');
                  }
                }}
              />
            </div>
            <ScrollArea className="h-64">
              <div className="space-y-2">
                {filteredProducts.map((product) => (
                  <div
                    key={product.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      product.current_stock > 0 ? 'hover:bg-[#E0F7FA]' : 'bg-gray-100 opacity-70'
                    }`}
                    onClick={() => {
                      addToCart(product);
                      setDialogSearch('');
                    }}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium">{product.name || 'Pa emër'}</p>
                        <p className="text-sm text-gray-500">Barkod: {product.barcode || '-'}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-[#00a79d]">€{(product.sale_price || 0).toFixed(2)}</p>
                        <p className={`text-xs ${product.current_stock > 0 ? 'text-green-600' : 'text-red-500 font-semibold'}`}>
                          {product.current_stock > 0 ? `Stok: ${product.current_stock}` : 'Pa stok!'}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
                {filteredProducts.length === 0 && dialogSearch.trim() && (
                  <p className="text-center text-gray-400 py-8">Nuk u gjet asnjë produkt për &quot;{dialogSearch}&quot;</p>
                )}
                {filteredProducts.length === 0 && !dialogSearch.trim() && (
                  <p className="text-center text-gray-400 py-8">Shkruani emrin ose barkod-in e produktit</p>
                )}
              </div>
            </ScrollArea>
          </div>
        </DialogContent>
      </Dialog>

      {/* Customer Dialog */}
      <Dialog open={showCustomer} onOpenChange={setShowCustomer}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Informacioni i Konsumatorit</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Emri i Konsumatorit</Label>
              <Input
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="Emri (opsional)"
                data-testid="customer-name-input"
              />
            </div>
            <div className="space-y-2">
              <Label>Shënime</Label>
              <Textarea
                value={customerNote}
                onChange={(e) => setCustomerNote(e.target.value)}
                placeholder="Shënime shtesë..."
                data-testid="customer-note-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setCustomerName(''); setCustomerNote(''); }}>
              Pastro
            </Button>
            <Button onClick={() => setShowCustomer(false)} className="bg-[#00a79d] hover:bg-[#008f86]">
              Ruaj
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Parameters Dialog */}
      <Dialog open={showParams} onOpenChange={setShowParams}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Parametrat e Arkës</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex justify-between mb-2">
                <span className="text-gray-500">Bilanci Fillestar:</span>
                <span className="font-semibold">€{cashDrawer?.opening_balance?.toFixed(2) || '0.00'}</span>
              </div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-500">Bilanci Aktual:</span>
                <span className="font-semibold">€{cashDrawer?.current_balance?.toFixed(2) || '0.00'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Bilanci i Pritshëm:</span>
                <span className="font-semibold text-[#00a79d]">€{cashDrawer?.expected_balance?.toFixed(2) || '0.00'}</span>
              </div>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex justify-between mb-2">
                <span className="text-gray-500">Hapur më:</span>
                <span className="font-semibold">{cashDrawer?.opened_at ? new Date(cashDrawer.opened_at).toLocaleString('sq-AL') : '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Arkëtari:</span>
                <span className="font-semibold">{user?.full_name}</span>
              </div>
            </div>
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <span className="text-gray-500">Pa TVSH:</span>
              <Button
                variant={applyNoVat ? 'default' : 'outline'}
                size="sm"
                onClick={handleNoVat}
                className={applyNoVat ? 'bg-orange-500' : ''}
              >
                {applyNoVat ? 'Aktiv' : 'Joaktiv'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Documents Dialog */}
      <Dialog open={showDocuments} onOpenChange={setShowDocuments}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Dokumentet e Fundit</DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-80">
            <div className="space-y-2">
              {recentSales.map((sale) => (
                <div key={sale.id} className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer" onClick={() => handleViewSaleA4(sale.id)}>
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">{sale.receipt_number}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(sale.created_at).toLocaleString('sq-AL')}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p className="font-bold text-[#00a79d]">€{sale.grand_total?.toFixed(2)}</p>
                        <p className="text-xs text-gray-400 capitalize">{sale.payment_method}</p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-blue-600"
                        onClick={(e) => { e.stopPropagation(); handleViewSaleA4(sale.id); }}
                        title="Printo A4"
                      >
                        <FileDown className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
              {recentSales.length === 0 && (
                <p className="text-center text-gray-400 py-8">Nuk ka dokumente</p>
              )}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Thermal Receipt Preview Dialog - Fiscal Style */}
      <Dialog open={showReceiptPreview} onOpenChange={setShowReceiptPreview}>
        <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader className="pb-2">
            <DialogTitle className="flex items-center justify-between">
              <span>Kupon Shitje</span>
              <Button
                onClick={executeThermalPrint}
                className="bg-[#00a79d] hover:bg-[#008f86]"
                size="sm"
              >
                <Printer className="h-4 w-4 mr-2" />
                Printo
              </Button>
            </DialogTitle>
          </DialogHeader>
          
          {/* Comment Section with Save Option */}
          <div className="space-y-3 border-b pb-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="receiptComment" className="text-sm font-medium">
                Koment për kuponin
              </Label>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="showComment"
                  checked={showCommentOnReceipt}
                  onChange={(e) => setShowCommentOnReceipt(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <label htmlFor="showComment" className="text-xs text-gray-600">Shfaq në kupon</label>
              </div>
            </div>
            
            {/* Comment Templates from Backend + Fallback hardcoded */}
            <div className="flex flex-wrap gap-1.5">
              <span className="text-xs text-gray-500 mr-1">Shabllonet:</span>
              {commentTemplates.filter(t => t.is_active).length > 0 ? (
                // Use templates from backend
                commentTemplates.filter(t => t.is_active).map((template) => (
                  <button
                    key={template.id}
                    type="button"
                    onClick={() => {
                      setReceiptComment(template.content);
                      setShowCommentOnReceipt(true);
                    }}
                    className={`px-2 py-0.5 text-xs rounded border transition-colors ${
                      template.is_default 
                        ? 'bg-[#00a79d]/10 border-[#00a79d] text-[#00a79d] hover:bg-[#00a79d]/20' 
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                    }`}
                  >
                    {template.is_default && '★ '}{template.title}
                  </button>
                ))
              ) : (
                // Fallback to hardcoded templates if backend is empty
                [
                  'Garanci 12 muaj',
                  'Pa kthim',
                  'Zbritje speciale',
                  'Kthim brenda 14 ditëve',
                  'Produkt i ri',
                  'Artikull në zbritje'
                ].map((template) => (
                  <button
                    key={template}
                    type="button"
                    onClick={() => {
                      setReceiptComment(prev => prev ? `${prev}, ${template}` : template);
                      setShowCommentOnReceipt(true);
                    }}
                    className="px-2 py-0.5 text-xs bg-gray-100 hover:bg-gray-200 rounded border text-gray-700 transition-colors"
                  >
                    + {template}
                  </button>
                ))
              )}
            </div>
            
            <Textarea
              id="receiptComment"
              placeholder="Klikoni shabllonet ose shkruani manualisht..."
              value={receiptComment}
              onChange={(e) => setReceiptComment(e.target.value)}
              className="h-14 text-sm resize-none"
              maxLength={200}
            />
            <div className="flex items-center justify-between">
              <p className="text-xs text-gray-500">{receiptComment.length}/200 karaktere</p>
              <div className="flex gap-2">
                {receiptComment && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-7 text-xs text-gray-500"
                    onClick={() => setReceiptComment('')}
                  >
                    Pastro
                  </Button>
                )}
                {savedReceiptComment && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-7 text-xs text-red-500 hover:text-red-700"
                    onClick={clearSavedComment}
                  >
                    Fshi Default
                  </Button>
                )}
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="h-7 text-xs"
                  onClick={saveCommentAsDefault}
                  disabled={!receiptComment}
                >
                  <Save className="h-3 w-3 mr-1" />
                  Ruaj si Default
                </Button>
              </div>
            </div>
            {savedReceiptComment && (
              <p className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
                ✓ Koment default: &quot;{savedReceiptComment.substring(0, 50)}{savedReceiptComment.length > 50 ? '...' : ''}&quot;
              </p>
            )}
          </div>

          <div className="border rounded-lg overflow-auto flex-1 bg-gray-100 p-3">
            {receiptDataForPrint && (
              <div id="thermal-receipt-print" style={{ 
                fontFamily: "'Courier New', 'Consolas', monospace", 
                fontSize: '10px', 
                width: '80mm', 
                maxWidth: '80mm',
                minHeight: '250mm',
                maxHeight: '250mm',
                margin: '0 auto',
                padding: '3mm',
                backgroundColor: '#fff',
                color: '#000',
                lineHeight: '1.4'
              }}>
                {/* === FISCAL RECEIPT HEADER === */}
                <div style={{ textAlign: 'center', marginBottom: '8px' }}>
                  {/* Logo - uses tenant's logo if available */}
                  {companySettings?.logo_url && (
                    <div style={{ marginBottom: '8px' }}>
                      <img 
                        src={companySettings.logo_url} 
                        alt="Logo" 
                        style={{ height: '45px', maxWidth: '60mm', objectFit: 'contain' }} 
                        onError={(e) => e.target.style.display = 'none'}
                      />
                    </div>
                  )}
                  <div style={{ fontSize: '14px', fontWeight: 'bold', letterSpacing: '1px' }}>
                    {companySettings?.company_name || 'DataPOS'}
                  </div>
                  <div style={{ fontSize: '9px', marginTop: '4px' }}>
                    {companySettings?.address || 'Adresa e Biznesit'}
                  </div>
                  {companySettings?.city && (
                    <div style={{ fontSize: '9px' }}>{companySettings.city}</div>
                  )}
                  <div style={{ fontSize: '9px', marginTop: '2px' }}>
                    Tel: {companySettings?.phone || '+383 XX XXX XXX'}
                  </div>
                  {(companySettings?.nui || companySettings?.nf) && (
                    <div style={{ fontSize: '8px', marginTop: '4px' }}>
                      {companySettings?.nui && `NUI: ${companySettings.nui}`}
                      {companySettings?.nui && companySettings?.nf && ' | '}
                      {companySettings?.nf && `NF: ${companySettings.nf}`}
                    </div>
                  )}
                </div>

                {/* Separator */}
                <div style={{ borderTop: '2px dashed #000', margin: '6px 0' }}></div>

                {/* Receipt Type */}
                <div style={{ textAlign: 'center', margin: '6px 0' }}>
                  <div style={{ 
                    fontSize: '12px', 
                    fontWeight: 'bold',
                    border: '1px solid #000',
                    padding: '4px 8px',
                    display: 'inline-block',
                    background: receiptDataForPrint.is_debt ? '#fff3cd' : 'transparent'
                  }}>
                    {receiptDataForPrint.is_debt ? '⚠ KUPON BORGJ' : 'KUPON SHITJE'}
                  </div>
                </div>

                {/* Debt Warning Banner */}
                {receiptDataForPrint.is_debt && (
                  <div style={{ 
                    textAlign: 'center', 
                    margin: '6px 0', 
                    padding: '5px', 
                    background: '#fff3cd', 
                    border: '1px solid #ffc107', 
                    borderRadius: '3px' 
                  }}>
                    <div style={{ fontSize: '10px', fontWeight: 'bold', color: '#856404' }}>⚠ SHITJE ME BORXH</div>
                  </div>
                )}

                {/* Receipt Info */}
                <div style={{ fontSize: '9px', margin: '6px 0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                    <span>Nr:</span>
                    <span style={{ fontWeight: 'bold' }}>{receiptDataForPrint.receipt_number}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                    <span>Data:</span>
                    <span>{new Date(receiptDataForPrint.created_at).toLocaleDateString('sq-AL')}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                    <span>Ora:</span>
                    <span>{new Date(receiptDataForPrint.created_at).toLocaleTimeString('sq-AL', { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                    <span>Arkëtar:</span>
                    <span>{user?.full_name || '-'}</span>
                  </div>
                  {receiptDataForPrint.customer_name && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold', marginTop: '4px', paddingTop: '4px', borderTop: '1px dashed #ccc' }}>
                      <span>{receiptDataForPrint.is_debt ? 'DEBITORI:' : 'Klienti:'}</span>
                      <span>{receiptDataForPrint.customer_name}</span>
                    </div>
                  )}
                </div>

                {/* Separator */}
                <div style={{ borderTop: '1px dashed #000', margin: '6px 0' }}></div>

                {/* Items Header */}
                <div style={{ 
                  fontSize: '8px', 
                  fontWeight: 'bold',
                  display: 'flex',
                  borderBottom: '1px solid #000',
                  paddingBottom: '3px',
                  marginBottom: '4px'
                }}>
                  <span style={{ flex: 1 }}>ARTIKULLI</span>
                  <span style={{ width: '25px', textAlign: 'center' }}>SAS</span>
                  <span style={{ width: '40px', textAlign: 'right' }}>ÇMIMI</span>
                  <span style={{ width: '45px', textAlign: 'right' }}>VLERA</span>
                </div>

                {/* Items */}
                {receiptDataForPrint.items?.map((item, index) => (
                  <div key={index} style={{ fontSize: '9px', marginBottom: '5px' }}>
                    <div style={{ fontWeight: '500' }}>
                      {(item.product_name || 'Produkt').substring(0, 28)}
                    </div>
                    <div style={{ display: 'flex' }}>
                      <span style={{ flex: 1 }}></span>
                      <span style={{ width: '25px', textAlign: 'center' }}>{item.quantity}</span>
                      <span style={{ width: '40px', textAlign: 'right' }}>{(item.unit_price || 0).toFixed(2)}</span>
                      <span style={{ width: '45px', textAlign: 'right', fontWeight: 'bold' }}>
                        {(item.total || (item.quantity * item.unit_price)).toFixed(2)}
                      </span>
                    </div>
            {item.discount_percent > 0 && (
              <div style={ { fontSize: '8px', color: '#b91c1c', textAlign: 'right', marginTop: '1px' } }>
                Zbritja: {item.discount_percent}% (-{((item.unit_price || 0) * (item.quantity || 0) * (item.discount_percent || 0) / 100).toFixed(2)} EUR)
              </div>
            )}
          </div>
                ))}

                {/* Separator */}
                <div style={{ borderTop: '1px dashed #000', margin: '6px 0' }}></div>

                {/* Totals */}
                <div style={{ fontSize: '9px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Nëntotali:</span>
                    <span>{(receiptDataForPrint.subtotal || 0).toFixed(2)} EUR</span>
                  </div>
          {receiptDataForPrint.total_discount > 0 && (
            <div style={ { display: 'flex', justifyContent: 'space-between', color: '#b91c1c' } }>
              <span>Zbritja totale:</span>
              <span>-{(receiptDataForPrint.total_discount || 0).toFixed(2)} EUR</span>
            </div>
          )}
          {receiptDataForPrint.total_vat > 0 && (
            <div style={ { display: 'flex', justifyContent: 'space-between' } }>
              <span>TVSH:</span>
              <span>{(receiptDataForPrint.total_vat || 0).toFixed(2)} EUR</span>
            </div>
          )}
        </div>

                {/* Grand Total */}
                <div style={{ 
                  borderTop: '2px solid #000',
                  borderBottom: '2px solid #000',
                  padding: '6px 0',
                  margin: '6px 0',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span style={{ fontSize: '14px', fontWeight: 'bold' }}>TOTALI:</span>
                  <span style={{ fontSize: '16px', fontWeight: 'bold' }}>{(receiptDataForPrint.grand_total || 0).toFixed(2)} EUR</span>
                </div>

                {/* DEBT INFORMATION SECTION */}
                {receiptDataForPrint.is_debt && (
                  <div style={{ 
                    margin: '6px 0', 
                    padding: '6px', 
                    background: '#fff3cd', 
                    border: '1px solid #ffc107', 
                    borderRadius: '3px' 
                  }}>
                    <div style={{ fontSize: '10px', fontWeight: 'bold', textAlign: 'center', marginBottom: '5px', color: '#856404' }}>
                      INFORMACION BORGJI
                    </div>
                    <div style={{ fontSize: '9px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                        <span>Total Fatura:</span>
                        <span style={{ fontWeight: 'bold' }}>{(receiptDataForPrint.grand_total || 0).toFixed(2)} EUR</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                        <span>Paguar Tani:</span>
                        <span style={{ fontWeight: 'bold', color: '#28a745' }}>{(receiptDataForPrint.paid_amount || receiptDataForPrint.cash_amount || 0).toFixed(2)} EUR</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '4px', borderTop: '1px dashed #856404' }}>
                        <span style={{ fontWeight: 'bold' }}>BORGJ MBETUR:</span>
                        <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#dc3545' }}>{(receiptDataForPrint.remaining_debt || 0).toFixed(2)} EUR</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Payment Info - Only show for non-debt sales */}
                {!receiptDataForPrint.is_debt && (
                  <div style={{ fontSize: '9px', margin: '6px 0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                      <span>Mënyra:</span>
                      <span style={{ fontWeight: 'bold' }}>{receiptDataForPrint.payment_method === 'cash' ? 'CASH' : 'KARTË'}</span>
                    </div>
                    {receiptDataForPrint.payment_method === 'cash' && (
                      <>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                          <span>Paguar:</span>
                          <span>{(receiptDataForPrint.cash_amount || 0).toFixed(2)} EUR</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold' }}>
                          <span>Kusuri:</span>
                          <span>{(receiptDataForPrint.change_amount || 0).toFixed(2)} EUR</span>
                        </div>
                      </>
                    )}
                  </div>
                )}

                {/* Comment Section */}
                {showCommentOnReceipt && receiptComment && (
                  <div style={{ 
                    margin: '6px 0',
                    padding: '5px',
                    border: '1px dashed #000',
                    fontSize: '8px'
                  }}>
                    <div style={{ fontWeight: 'bold' }}>SHËNIM:</div>
                    <div style={{ whiteSpace: 'pre-wrap' }}>{receiptComment}</div>
                  </div>
                )}

                {/* Separator */}
                <div style={{ borderTop: '1px dashed #000', margin: '6px 0' }}></div>

                {/* Debt Reminder Box for Customer */}
                {receiptDataForPrint.is_debt && receiptDataForPrint.remaining_debt > 0 && (
                  <div style={{ 
                    textAlign: 'center', 
                    margin: '6px 0', 
                    padding: '8px', 
                    border: '2px dashed #dc3545', 
                    background: '#fff5f5' 
                  }}>
                    <div style={{ fontSize: '8px', color: '#666' }}>Borgj i mbetur:</div>
                    <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#dc3545' }}>
                      {(receiptDataForPrint.remaining_debt || 0).toFixed(2)} EUR
                    </div>
                  </div>
                )}

                {/* Thank You Message */}
                <div style={{ textAlign: 'center', margin: '6px 0' }}>
                  <div style={{ fontSize: '11px', fontWeight: 'bold' }}>FALEMINDERIT!</div>
                  <div style={{ fontSize: '8px' }}>Ju mirëpresim përsëri!</div>
                </div>

                {/* Footer */}
                <div style={{ 
                  textAlign: 'center', 
                  fontSize: '7px', 
                  color: '#666',
                  marginTop: '4px',
                  paddingTop: '4px',
                  borderTop: '1px dashed #000'
                }}>
                  <div>{companySettings?.company_name || 'DataPOS'} • {new Date().toLocaleString('sq-AL')}</div>
                </div>

                {/* ═══════════ ZONA E SHKYÇJES PËR ARKËTARIN ═══════════ */}
                <div style={{ 
                  marginTop: '12px', 
                  borderTop: '2px dashed #000', 
                  paddingTop: '6px'
                }}>
                  <div style={{ textAlign: 'center', marginBottom: '6px' }}>
                    <span style={{ 
                      fontSize: '7px', 
                      background: '#000', 
                      color: '#fff', 
                      padding: '2px 8px', 
                      letterSpacing: '1px'
                    }}>✂ SHKYÇ KËTU ✂</span>
                  </div>
                  <div style={{ 
                    border: '1px solid #000', 
                    padding: '6px', 
                    borderRadius: '3px', 
                    background: receiptDataForPrint.is_debt ? '#fff3cd' : '#fafafa'
                  }}>
                    <div style={{ 
                      textAlign: 'center', 
                      fontSize: '9px', 
                      fontWeight: 'bold', 
                      marginBottom: '5px', 
                      borderBottom: '1px solid #ddd', 
                      paddingBottom: '4px'
                    }}>
                      KOPJE ARKËTAR {receiptDataForPrint.is_debt ? '⚠ BORGJ' : ''}
                    </div>
                    <div style={{ fontSize: '8px' }}>
                      <div style={{ marginBottom: '2px' }}>
                        <strong>Nr:</strong> {receiptDataForPrint.receipt_number} | {new Date(receiptDataForPrint.created_at).toLocaleDateString('sq-AL')} {new Date(receiptDataForPrint.created_at).toLocaleTimeString('sq-AL', { hour: '2-digit', minute: '2-digit' })}
                      </div>
                      {receiptDataForPrint.is_debt && receiptDataForPrint.debtor_name && (
                        <div style={{ marginBottom: '4px', padding: '2px', background: '#ffe0b2', borderRadius: '2px' }}>
                          <strong>DEBITORI:</strong> {receiptDataForPrint.debtor_name}
                        </div>
                      )}
                      <div style={{ borderTop: '1px dashed #ccc', margin: '4px 0', paddingTop: '4px' }}>
                        {receiptDataForPrint.items?.map((item, idx) => (
                          <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                            <span>{(item.product_name || 'Produkt').substring(0, 20)} x{item.quantity}</span>
                            <span style={{ fontWeight: 'bold' }}>{(item.total || (item.quantity * item.unit_price)).toFixed(2)}€</span>
                          </div>
                        ))}
                      </div>
                      <div style={{ 
                        borderTop: '1px solid #000', 
                        marginTop: '4px', 
                        paddingTop: '4px', 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        fontWeight: 'bold'
                      }}>
                        <span>TOTAL:</span>
                        <span style={{ fontSize: '11px' }}>{(receiptDataForPrint.grand_total || 0).toFixed(2)} EUR</span>
                      </div>
                      {receiptDataForPrint.is_debt && (
                        <div style={{ 
                          marginTop: '5px', 
                          padding: '4px', 
                          background: '#ffebee', 
                          border: '1px solid #ef5350', 
                          borderRadius: '2px' 
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                            <span>Paguar:</span>
                            <span style={{ fontWeight: 'bold', color: '#2e7d32' }}>{(receiptDataForPrint.paid_amount || receiptDataForPrint.cash_amount || 0).toFixed(2)}€</span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold' }}>
                            <span style={{ color: '#c62828' }}>MBETUR:</span>
                            <span style={{ fontSize: '11px', color: '#c62828' }}>{(receiptDataForPrint.remaining_debt || 0).toFixed(2)}€</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Receipt End Mark */}
                <div style={{ 
                  textAlign: 'center', 
                  margin: '8px 0',
                  fontSize: '8px',
                  letterSpacing: '2px'
                }}>
                  ================================
                </div>
              </div>
            )}
          </div>
          
          {/* Print Options */}
          <div className="bg-gray-50 rounded-lg p-3 border">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="directPrint"
                    checked={directPrintEnabled}
                    onChange={(e) => toggleDirectPrint(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-green-600 focus:ring-green-500"
                  />
                  <label htmlFor="directPrint" className="text-sm font-medium text-gray-700">
                    🖨️ Printim direkt (pa dialog)
                  </label>
                </div>
              </div>
              <span className="text-xs text-gray-500">
                {directPrintEnabled ? '✓ Aktiv' : 'Çaktivizuar'}
              </span>
            </div>
            {directPrintEnabled && (
              <p className="text-xs text-green-600 mt-2">
                Kur klikoni &quot;Printo Direkt&quot;, kuponi dërgohet automatikisht në printer pa hapur dialogun.
              </p>
            )}
          </div>
          
          {/* Bottom actions */}
          <div className="flex gap-2 pt-2 border-t">
            <Button variant="outline" className="flex-1" onClick={() => setShowReceiptPreview(false)}>
              Mbyll
            </Button>
            {directPrintEnabled && (
              <Button 
                className="flex-1 bg-green-600 hover:bg-green-700" 
                onClick={executeDirectPrint}
              >
                <Printer className="h-4 w-4 mr-2" />
                Printo Direkt
              </Button>
            )}
            <Button 
              className="flex-1 bg-[#00a79d] hover:bg-[#008f86]" 
              onClick={() => executeThermalPrint(true)}
            >
              <Printer className="h-4 w-4 mr-2" />
              {directPrintEnabled ? 'Zgjidh Printer' : 'Printo Kuponin'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Invoice A4 Dialog */}
      <Dialog open={showInvoiceA4} onOpenChange={setShowInvoiceA4}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span>Fatura A4 - {currentSaleForPrint?.receipt_number || 'Preview'}</span>
              <Button
                onClick={executePrint}
                className="bg-[#00a79d] hover:bg-[#008f86]"
              >
                <Printer className="h-4 w-4 mr-2" />
                Printo
              </Button>
            </DialogTitle>
          </DialogHeader>
          {/* Printer selection info for A4 */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 -mt-2 mb-2">
            <p className="text-sm text-blue-700">
              <span className="font-medium">💡 Udhëzim:</span> Kur klikoni &quot;Printo&quot;, do të hapet dialogu ku mund të zgjidhni printerin dhe madhësinë e letrës (A4).
            </p>
          </div>
          <div className="border rounded-lg overflow-hidden">
            <InvoiceA4 ref={invoiceRef} sale={currentSaleForPrint} companyInfo={companySettings} />
          </div>
        </DialogContent>
      </Dialog>

      {/* Buyer Info Form Dialog */}
      <Dialog open={showBuyerForm} onOpenChange={setShowBuyerForm}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Të Dhënat e Blerësit</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Emri i Blerësit / Kompanisë</Label>
              <Input
                value={buyerInfo.name}
                onChange={(e) => setBuyerInfo({ ...buyerInfo, name: e.target.value })}
                placeholder="Emri i plotë ose emri i kompanisë"
              />
            </div>
            <div className="space-y-2">
              <Label>Adresa</Label>
              <Input
                value={buyerInfo.address}
                onChange={(e) => setBuyerInfo({ ...buyerInfo, address: e.target.value })}
                placeholder="Adresa e blerësit"
              />
            </div>
            <div className="space-y-2">
              <Label>Telefoni</Label>
              <Input
                value={buyerInfo.phone}
                onChange={(e) => setBuyerInfo({ ...buyerInfo, phone: e.target.value })}
                placeholder="+383 XX XXX XXX"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>NUI</Label>
                <Input
                  value={buyerInfo.nui}
                  onChange={(e) => setBuyerInfo({ ...buyerInfo, nui: e.target.value })}
                  placeholder="Numri Unik"
                />
              </div>
              <div className="space-y-2">
                <Label>NF</Label>
                <Input
                  value={buyerInfo.nf}
                  onChange={(e) => setBuyerInfo({ ...buyerInfo, nf: e.target.value })}
                  placeholder="Numri Fiskal"
                />
              </div>
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowBuyerForm(false)}>
              Anulo
            </Button>
            <Button 
              onClick={proceedToPrintA4}
              className="bg-[#00a79d] hover:bg-[#008f86]"
            >
              <FileDown className="h-4 w-4 mr-2" />
              Vazhdo me Faturën
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Warranty (Garancioni) Dialog - Professional A4 Design */}
      <Dialog open={showWarranty} onOpenChange={setShowWarranty}>
        <DialogContent className="sm:max-w-6xl max-h-[95vh] overflow-hidden flex flex-col">
          <DialogHeader className="pb-2 border-b">
            <DialogTitle className="flex items-center gap-2 text-emerald-700">
              <Shield className="h-5 w-5" />
              Dokument Garancioni - Format A4
            </DialogTitle>
          </DialogHeader>
          
          <div className="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-4 py-4">
            {/* Left Side - Compact Form */}
            <div className="space-y-3 overflow-y-auto pr-2">
              {/* Customer Section */}
              <div className="bg-slate-50 rounded-lg p-3 space-y-2">
                <h3 className="font-medium text-sm text-slate-700 flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Klienti
                </h3>
                <Input
                  value={warrantyData.customerName}
                  onChange={(e) => setWarrantyData({...warrantyData, customerName: e.target.value})}
                  placeholder="Emri dhe Mbiemri"
                  className="h-8 text-sm"
                />
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    value={warrantyData.customerPhone}
                    onChange={(e) => setWarrantyData({...warrantyData, customerPhone: e.target.value})}
                    placeholder="Telefoni"
                    className="h-8 text-sm"
                  />
                  <Input
                    value={warrantyData.customerAddress}
                    onChange={(e) => setWarrantyData({...warrantyData, customerAddress: e.target.value})}
                    placeholder="Adresa/Qyteti"
                    className="h-8 text-sm"
                  />
                </div>
              </div>

              {/* Product Section */}
              <div className="bg-slate-50 rounded-lg p-3 space-y-2">
                <h3 className="font-medium text-sm text-slate-700 flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  Produkti
                </h3>
                <Input
                  value={warrantyData.productName}
                  onChange={(e) => setWarrantyData({...warrantyData, productName: e.target.value})}
                  placeholder="Emri i Produktit"
                  className="h-8 text-sm"
                />
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    value={warrantyData.productBrand}
                    onChange={(e) => setWarrantyData({...warrantyData, productBrand: e.target.value})}
                    placeholder="Marka"
                    className="h-8 text-sm"
                  />
                  <Input
                    value={warrantyData.productModel}
                    onChange={(e) => setWarrantyData({...warrantyData, productModel: e.target.value})}
                    placeholder="Modeli"
                    className="h-8 text-sm"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    value={warrantyData.serialNumber}
                    onChange={(e) => setWarrantyData({...warrantyData, serialNumber: e.target.value})}
                    placeholder="Nr. Serik (S/N)"
                    className="h-8 text-sm"
                  />
                  <Input
                    value={warrantyData.imei}
                    onChange={(e) => setWarrantyData({...warrantyData, imei: e.target.value})}
                    placeholder="IMEI"
                    className="h-8 text-sm"
                  />
                </div>
                <select
                  value={warrantyData.productCondition}
                  onChange={(e) => setWarrantyData({...warrantyData, productCondition: e.target.value})}
                  className="w-full h-8 px-3 border border-gray-200 rounded-md text-sm bg-white"
                >
                  <option value="I ri">I ri (New)</option>
                  <option value="I përdorur">I përdorur (Used)</option>
                  <option value="I rinovuar">I rinovuar (Refurbished)</option>
                </select>
              </div>

              {/* Warranty Details Section */}
              <div className="bg-emerald-50 rounded-lg p-3 space-y-2 border border-emerald-200">
                <h3 className="font-medium text-sm text-emerald-700 flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Garancia
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="date"
                    value={warrantyData.purchaseDate}
                    onChange={(e) => setWarrantyData({...warrantyData, purchaseDate: e.target.value})}
                    className="h-8 text-sm"
                  />
                  <select
                    value={warrantyData.warrantyPeriod}
                    onChange={(e) => setWarrantyData({...warrantyData, warrantyPeriod: e.target.value})}
                    className="w-full h-8 px-2 border border-gray-200 rounded-md text-sm bg-white"
                  >
                    <option value="1">1 muaj</option>
                    <option value="3">3 muaj</option>
                    <option value="6">6 muaj</option>
                    <option value="12">12 muaj</option>
                    <option value="24">24 muaj</option>
                    <option value="36">36 muaj</option>
                  </select>
                </div>
              </div>

              {/* Extras */}
              <div className="bg-slate-50 rounded-lg p-3 space-y-2">
                <Input
                  value={warrantyData.accessories}
                  onChange={(e) => setWarrantyData({...warrantyData, accessories: e.target.value})}
                  placeholder="Aksesorët (Karikues, Kufje...)"
                  className="h-8 text-sm"
                />
                <Textarea
                  value={warrantyData.notes}
                  onChange={(e) => setWarrantyData({...warrantyData, notes: e.target.value})}
                  placeholder="Shënime shtesë..."
                  className="h-14 text-sm resize-none"
                />
              </div>
            </div>

            {/* Right Side - A4 Preview */}
            <div className="border rounded-lg bg-gray-100 overflow-auto flex justify-center py-3">
              <div 
                ref={warrantyRef}
                className="bg-white shadow-2xl"
                style={{ 
                  width: '210mm', 
                  minHeight: '297mm',
                  padding: '15mm',
                  fontSize: '11pt',
                  fontFamily: "'Segoe UI', Arial, sans-serif",
                  transform: 'scale(0.52)',
                  transformOrigin: 'top center',
                  marginBottom: '-400px'
                }}
              >
                {/* Professional A4 Warranty Document */}
                <div style={{ height: '100%', display: 'flex', flexDirection: 'column', color: '#1f2937' }}>
                  <div style={ { height: '6px', background: '#00a79d', borderRadius: '4px', marginBottom: '16px' } }></div>
                  
                  {/* Header with Logo Area */}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'flex-start',
                    borderBottom: '3px solid #00a79d',
                    paddingBottom: '15px',
                    marginBottom: '20px'
                  }}>
                    <div>
                      {companySettings?.logo_url ? (
                        <img 
                          src={companySettings.logo_url} 
                          alt="Logo" 
                          style={{ height: '50px', marginBottom: '8px' }}
                          onError={(e) => e.target.style.display = 'none'}
                        />
                      ) : (
                        <div style={{ 
                          width: '50px', 
                          height: '50px', 
                          background: '#00a79d',
                          borderRadius: '8px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontWeight: 'bold',
                          fontSize: '20px',
                          marginBottom: '8px'
                        }}>
                          {(companySettings?.company_name || 'D')[0]}
                        </div>
                      )}
                      <div style={{ fontSize: '18px', fontWeight: '700', color: '#1f2937' }}>
                        {companySettings?.company_name || 'Emri i Kompanisë'}
                      </div>
                      <div style={{ fontSize: '10px', color: '#6b7280', marginTop: '2px' }}>
                        {companySettings?.address || 'Adresa e Biznesit'}
                        {companySettings?.city && `, ${companySettings.city}`}
                      </div>
                      <div style={{ fontSize: '10px', color: '#6b7280' }}>
                        Tel: {companySettings?.phone || '+383 XX XXX XXX'}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ 
                        fontSize: '28px', 
                        fontWeight: '800', 
                        color: '#00a79d',
                        letterSpacing: '1px'
                      }}>
                        GARANCIONI
                      </div>
                      <div style={{ fontSize: '10px', color: '#9ca3af', marginTop: '2px' }}>
                        WARRANTY CERTIFICATE
                      </div>
                      <div style={{ 
                        fontSize: '10px', 
                        color: '#6b7280', 
                        marginTop: '10px',
                        padding: '4px 10px',
                        background: '#f3f4f6',
                        borderRadius: '4px'
                      }}>
                        NUI: {companySettings?.nui || '________'} | NF: {companySettings?.nf || '________'}
                      </div>
                    </div>
                  </div>

                  {/* Main Content Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
                    
                    {/* Customer Info Box */}
                    <div style={{ 
                      border: '1px solid #e5e7eb', 
                      borderRadius: '8px', 
                      padding: '15px',
                      background: '#fafafa'
                    }}>
                      <div style={{ 
                        fontSize: '11px', 
                        fontWeight: '600', 
                        color: '#00a79d',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                        marginBottom: '12px',
                        paddingBottom: '8px',
                        borderBottom: '2px solid #00a79d'
                      }}>
                        Të Dhënat e Klientit
                      </div>
                      <table style={{ width: '100%', fontSize: '10px' }}>
                        <tbody>
                          <tr>
                            <td style={{ color: '#6b7280', padding: '4px 0', width: '70px' }}>Emri:</td>
                            <td style={{ fontWeight: '600', padding: '4px 0' }}>{warrantyData.customerName || '________________________________'}</td>
                          </tr>
                          <tr>
                            <td style={{ color: '#6b7280', padding: '4px 0' }}>Telefoni:</td>
                            <td style={{ padding: '4px 0' }}>{warrantyData.customerPhone || '________________________________'}</td>
                          </tr>
                          <tr>
                            <td style={{ color: '#6b7280', padding: '4px 0' }}>Adresa:</td>
                            <td style={{ padding: '4px 0' }}>{warrantyData.customerAddress || '________________________________'}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    {/* Warranty Period Box */}
                    <div style={{ 
                      border: '2px solid #00a79d', 
                      borderRadius: '8px', 
                      padding: '15px',
                      background: '#eaf7f5'
                    }}>
                      <div style={{ 
                        fontSize: '11px', 
                        fontWeight: '600', 
                        color: '#00a79d',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                        marginBottom: '12px',
                        paddingBottom: '8px',
                        borderBottom: '2px solid #00a79d'
                      }}>
                        Periudha e Garancisë
                      </div>
                      <div style={{ textAlign: 'center', marginBottom: '10px' }}>
                        <div style={{ 
                          fontSize: '32px', 
                          fontWeight: '800', 
                          color: '#00a79d'
                        }}>
                          {warrantyData.warrantyPeriod} MUAJ
                        </div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                        <div>
                          <div style={{ color: '#6b7280' }}>Data e Blerjes:</div>
                          <div style={{ fontWeight: '600' }}>
                            {warrantyData.purchaseDate ? new Date(warrantyData.purchaseDate).toLocaleDateString('sq-AL') : '__.____.____'}
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ color: '#6b7280' }}>Skadon më:</div>
                          <div style={{ fontWeight: '600', color: '#dc2626' }}>
                            {warrantyData.purchaseDate ? 
                              new Date(new Date(warrantyData.purchaseDate).setMonth(
                                new Date(warrantyData.purchaseDate).getMonth() + parseInt(warrantyData.warrantyPeriod)
                              )).toLocaleDateString('sq-AL') : '__.____.____'
                            }
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Product Info - Full Width */}
                  <div style={{ 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '8px', 
                    padding: '15px',
                    marginBottom: '20px',
                    background: '#fafafa'
                  }}>
                    <div style={{ 
                      fontSize: '11px', 
                      fontWeight: '600', 
                      color: '#00a79d',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                      marginBottom: '12px',
                      paddingBottom: '8px',
                      borderBottom: '2px solid #00a79d'
                    }}>
                      Të Dhënat e Produktit
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '15px', fontSize: '10px' }}>
                      <div>
                        <div style={{ color: '#6b7280', marginBottom: '2px' }}>Produkti:</div>
                        <div style={{ fontWeight: '700', fontSize: '12px' }}>{warrantyData.productName || '________________________'}</div>
                      </div>
                      <div>
                        <div style={{ color: '#6b7280', marginBottom: '2px' }}>Marka:</div>
                        <div style={{ fontWeight: '600' }}>{warrantyData.productBrand || '________________'}</div>
                      </div>
                      <div>
                        <div style={{ color: '#6b7280', marginBottom: '2px' }}>Modeli:</div>
                        <div style={{ fontWeight: '600' }}>{warrantyData.productModel || '________________'}</div>
                      </div>
                      <div>
                        <div style={{ color: '#6b7280', marginBottom: '2px' }}>Numri Serik (S/N):</div>
                        <div style={{ fontWeight: '600', fontFamily: 'monospace' }}>{warrantyData.serialNumber || '________________________'}</div>
                      </div>
                      <div>
                        <div style={{ color: '#6b7280', marginBottom: '2px' }}>IMEI:</div>
                        <div style={{ fontWeight: '600', fontFamily: 'monospace' }}>{warrantyData.imei || '________________________'}</div>
                      </div>
                      <div>
                        <div style={{ color: '#6b7280', marginBottom: '2px' }}>Gjendja:</div>
                        <div style={{ fontWeight: '600' }}>{warrantyData.productCondition}</div>
                      </div>
                    </div>
                    {warrantyData.accessories && (
                      <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px dashed #d1d5db', fontSize: '10px' }}>
                        <span style={{ color: '#6b7280' }}>Aksesorët e përfshirë: </span>
                        <span style={{ fontWeight: '500' }}>{warrantyData.accessories}</span>
                      </div>
                    )}
                  </div>

                  {/* Terms & Conditions */}
                  <div style={{ 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '8px', 
                    padding: '15px',
                    marginBottom: '20px',
                    background: '#fff'
                  }}>
                    <div style={{ 
                      fontSize: '11px', 
                      fontWeight: '600', 
                      color: '#374151',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                      marginBottom: '10px'
                    }}>
                      Kushtet e Garancisë
                    </div>
                    <div style={{ fontSize: '9px', color: '#4b5563', lineHeight: '1.6' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                        <div>
                          <p style={{ marginBottom: '5px' }}>✓ Garancia mbulon defektet e prodhimit dhe pjesët elektronike.</p>
                          <p style={{ marginBottom: '5px' }}>✓ Afati maksimal për riparim është 30 ditë pune.</p>
                          <p style={{ marginBottom: '5px' }}>✓ Produkti duhet të kthehet me dokumentet origjinale.</p>
                        </div>
                        <div>
                          <p style={{ marginBottom: '5px', color: '#dc2626' }}>✗ Garancia NUK mbulon dëmtimet fizike ose ujin.</p>
                          <p style={{ marginBottom: '5px', color: '#dc2626' }}>✗ Garancia NUK mbulon përdorimin e gabuar.</p>
                          <p style={{ marginBottom: '5px', color: '#dc2626' }}>✗ Garancia humbet nëse produkti hapet nga të tretët.</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Notes Section - Only if has notes */}
                  {warrantyData.notes && (
                    <div style={{ 
                      border: '1px solid #fbbf24', 
                      borderRadius: '8px', 
                      padding: '12px',
                      marginBottom: '20px',
                      background: '#fffbeb',
                      fontSize: '10px'
                    }}>
                      <span style={{ fontWeight: '600', color: '#92400e' }}>Shënime: </span>
                      <span style={{ color: '#78350f' }}>{warrantyData.notes}</span>
                    </div>
                  )}

                  {/* Spacer to push signatures to bottom */}
                  <div style={{ flex: 1, minHeight: '20px' }}></div>

                  {/* Signatures Section */}
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: '1fr 1fr', 
                    gap: '60px',
                    paddingTop: '20px',
                    borderTop: '2px solid #e5e7eb',
                    marginTop: 'auto'
                  }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ 
                        height: '60px', 
                        borderBottom: '2px solid #374151',
                        marginBottom: '8px',
                        display: 'flex',
                        alignItems: 'flex-end',
                        justifyContent: 'center',
                        paddingBottom: '5px',
                        color: '#9ca3af',
                        fontSize: '9px'
                      }}>
                        (Vula dhe Nënshkrimi)
                      </div>
                      <div style={{ fontSize: '10px', fontWeight: '600', color: '#374151' }}>SHITËSI</div>
                      <div style={{ fontSize: '9px', color: '#6b7280' }}>{companySettings?.company_name || 'Emri i Kompanisë'}</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ 
                        height: '60px', 
                        borderBottom: '2px solid #374151',
                        marginBottom: '8px',
                        display: 'flex',
                        alignItems: 'flex-end',
                        justifyContent: 'center',
                        paddingBottom: '5px',
                        color: '#9ca3af',
                        fontSize: '9px'
                      }}>
                        (Nënshkrimi i Klientit)
                      </div>
                      <div style={{ fontSize: '10px', fontWeight: '600', color: '#374151' }}>BLERËSI</div>
                      <div style={{ fontSize: '9px', color: '#6b7280' }}>{warrantyData.customerName || 'Emri i Klientit'}</div>
                    </div>
                  </div>

                  {/* Legal Footer */}
                  <div style={{ 
                    marginTop: '20px',
                    paddingTop: '15px',
                    borderTop: '1px solid #e5e7eb',
                    fontSize: '8px',
                    color: '#9ca3af',
                    textAlign: 'center',
                    lineHeight: '1.5'
                  }}>
                    <p style={{ marginBottom: '5px' }}>
                      <strong>NJOFTIM LIGJOR:</strong> Ky dokument garancioni respekton Ligjin Nr. 06/L-034 për Mbrojtjen e Konsumatorit të Republikës së Kosovës.
                    </p>
                    <p style={{ marginBottom: '5px' }}>
                      Të drejtat ligjore të konsumatorit për produkte jo-konforme nuk preken nga kushtet e këtij garancioni.
                    </p>
                    <p style={{ color: '#d1d5db', marginTop: '10px' }}>
                      Dokumenti u gjenerua më {new Date().toLocaleDateString('sq-AL')} në {new Date().toLocaleTimeString('sq-AL', {hour: '2-digit', minute: '2-digit'})}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter className="gap-2 pt-3 border-t flex-wrap">
            <Button variant="outline" onClick={() => setShowWarranty(false)}>
              Mbyll
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                setWarrantyData({
                  customerName: '',
                  customerPhone: '',
                  customerAddress: '',
                  productName: '',
                  productBrand: '',
                  productModel: '',
                  serialNumber: '',
                  imei: '',
                  purchaseDate: new Date().toISOString().split('T')[0],
                  warrantyPeriod: '12',
                  productCondition: 'I ri',
                  notes: '',
                  accessories: ''
                });
              }}
            >
              Pastro Formën
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                const saved = await saveWarranty();
                if (saved) {
                  // Clear form after save
                  setWarrantyData({
                    customerName: '',
                    customerPhone: '',
                    customerAddress: '',
                    productName: '',
                    productBrand: '',
                    productModel: '',
                    serialNumber: '',
                    imei: '',
                    purchaseDate: new Date().toISOString().split('T')[0],
                    warrantyPeriod: '12',
                    productCondition: 'I ri',
                    notes: '',
                    accessories: ''
                  });
                }
              }}
              className="border-emerald-300 text-emerald-700 hover:bg-emerald-50"
            >
              <Save className="h-4 w-4 mr-2" />
              Ruaj
            </Button>
            <Button 
              onClick={async () => {
                // Save first, then print
                const saved = await saveWarranty();
                if (saved) {
                  // Print warranty document - A4 format
                  const printContent = warrantyRef.current;
                  if (printContent) {
                    const printWindow = window.open('', '_blank');
                    printWindow.document.write(`
                      <!DOCTYPE html>
                      <html>
                      <head>
                        <title>Garancioni - ${saved.warranty_number}${warrantyData.customerName ? ' - ' + warrantyData.customerName : ''}</title>
                        <style>
                          @page { 
                            size: A4 portrait; 
                            margin: 0; 
                          }
                          * { 
                            box-sizing: border-box; 
                            margin: 0;
                            padding: 0;
                          }
                          html, body { 
                            width: 210mm;
                            min-height: 297mm;
                            font-family: 'Segoe UI', Arial, sans-serif;
                            -webkit-print-color-adjust: exact !important;
                            print-color-adjust: exact !important;
                          }
                          body > div {
                            width: 210mm !important;
                            min-height: 297mm !important;
                            padding: 15mm !important;
                            transform: none !important;
                            margin: 0 !important;
                          }
                        </style>
                      </head>
                      <body>
                        ${printContent.outerHTML.replace(/transform:[^;]+;/g, 'transform: none;').replace(/margin-bottom:[^;]+;/g, 'margin-bottom: 0;')}
                      </body>
                      </html>
                    `);
                    printWindow.document.close();
                    printWindow.focus();
                    setTimeout(() => {
                      printWindow.print();
                    }, 500);
                  }
                }
              }}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-6"
            >
              <Printer className="h-4 w-4 mr-2" />
              Ruaj & Printo (A4)
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Warranty List Dialog */}
      <Dialog open={showWarrantyList} onOpenChange={setShowWarrantyList}>
        <DialogContent className="sm:max-w-3xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader className="pb-3 border-b">
            <DialogTitle className="flex items-center gap-2 text-emerald-700">
              <Shield className="h-5 w-5" />
              Garancione të Ruajtura
            </DialogTitle>
          </DialogHeader>
          
          {/* Search */}
          <div className="py-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Kërko sipas emrit, produktit, IMEI, S/N..."
                className="pl-10"
                value={warrantySearch}
                onChange={(e) => {
                  setWarrantySearch(e.target.value);
                  loadWarranties(e.target.value);
                }}
              />
            </div>
          </div>

          {/* List */}
          <ScrollArea className="flex-1 pr-2">
            {loadingWarranties ? (
              <div className="flex items-center justify-center py-8">
                <div className="spinner" />
              </div>
            ) : savedWarranties.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Shield className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                <p>Nuk ka garancione të ruajtura</p>
                <p className="text-sm">Krijoni një garancioni të ri dhe ruajeni</p>
              </div>
            ) : (
              <div className="space-y-2">
                {savedWarranties.map((warranty) => (
                  <div 
                    key={warranty.id}
                    className="p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex justify-between items-start gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">
                            {warranty.warranty_number}
                          </span>
                          <span className="text-xs text-gray-400">
                            {new Date(warranty.created_at).toLocaleDateString('sq-AL')}
                          </span>
                        </div>
                        <p className="font-medium text-gray-900 truncate">
                          {warranty.product_name || 'Pa emër produkti'}
                          {warranty.product_brand && ` - ${warranty.product_brand}`}
                        </p>
                        <p className="text-sm text-gray-600 truncate">
                          {warranty.customer_name || 'Pa emër klienti'}
                          {warranty.customer_phone && ` • ${warranty.customer_phone}`}
                        </p>
                        <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                          {warranty.serial_number && (
                            <span>S/N: {warranty.serial_number}</span>
                          )}
                          {warranty.imei && (
                            <span>IMEI: {warranty.imei}</span>
                          )}
                          <span className={`font-medium ${
                            warranty.expiry_date && new Date(warranty.expiry_date) < new Date() 
                              ? 'text-red-600' 
                              : 'text-emerald-600'
                          }`}>
                            {warranty.warranty_period} muaj garanci
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => loadWarrantyToForm(warranty)}
                          className="h-8 px-2 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                          title="Hap & Printo"
                        >
                          <Printer className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteWarranty(warranty.id)}
                          className="h-8 px-2 text-red-500 hover:text-red-600 hover:bg-red-50"
                          title="Fshij"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>

          <DialogFooter className="pt-3 border-t">
            <Button variant="outline" onClick={() => setShowWarrantyList(false)}>
              Mbyll
            </Button>
            <Button 
              onClick={() => {
                setShowWarrantyList(false);
                setShowWarranty(true);
              }}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              <Plus className="h-4 w-4 mr-2" />
              Garancioni i Ri
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );

  // If cashier - show fullscreen POS with header
  if (isCashierFullscreen) {
    return (
      <div className="min-h-screen bg-[#F8FAFC]">
        {/* Cashier Header */}
        <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Company Logo */}
            {companySettings?.logo_url ? (
              <img 
                src={companySettings.logo_url} 
                alt="Logo" 
                className="h-8 w-auto object-contain"
                onError={(e) => e.target.style.display = 'none'}
              />
            ) : (
              <div className="bg-[#00a79d] p-1.5 rounded-lg">
                <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
                  <line x1="12" y1="18" x2="12" y2="18"/>
                </svg>
              </div>
            )}
            {/* Company Name */}
            <span className="text-xl font-bold text-[#00a79d]">
              {companySettings?.company_name || 'DataPOS'}
            </span>
            <span className="text-gray-400 mx-2">|</span>
            <span className="text-gray-600">Arka</span>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
              <p className="text-xs text-gray-500">Arkëtar</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="gap-2 text-red-600 border-red-200 hover:bg-red-50"
              data-testid="logout-btn"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Çkyçu</span>
            </Button>
          </div>
        </header>
        
        {/* POS Content */}
        <main className="p-4">
          {posContent}
        </main>
      </div>
    );
  }

  // For admin/manager - return normal content (will be inside MainLayout)
  return posContent;
};

export default POS;
