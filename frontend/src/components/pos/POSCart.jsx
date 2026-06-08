import React from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Table, TableBody, TableCell, TableRow } from '../ui/table';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '../ui/select';
import { Minus, Plus, Trash2, Package } from 'lucide-react';

export const POSCart = ({
  cart,
  products,
  selectedItemIndex,
  setSelectedItemIndex,
  user,
  applyNoVat,
  // Functions
  calculateItemTotal,
  updateQuantity,
  updateDiscount,
  removeFromCart,
  setCart
}) => {
  const canEdit = user?.role === 'admin' || user?.role === 'manager';

  return (
    <Card className="flex-1 border-0 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-[#00a79d]/10 px-4 py-2 border-b border-[#00a79d]/20">
        <div className="grid grid-cols-12 gap-2 text-xs font-semibold text-gray-600">
          <div className="col-span-1">Nr</div>
          <div className="col-span-3">Emërtimi</div>
          <div className="col-span-1 text-center">Sasia</div>
          <div className="col-span-2 text-right">Çmimi</div>
          <div className="col-span-1 text-center">Zbritja %</div>
          <div className="col-span-1 text-center">Tvsh %</div>
          <div className="col-span-2 text-right">Çmimi me tvsh</div>
          <div className="col-span-1 text-right">Total</div>
        </div>
      </div>
      
      {/* Cart Items */}
      <div className="overflow-auto flex-1" style={{ maxHeight: 'calc(100vh - 24rem)' }}>
        <Table>
          <TableBody>
            {cart.length === 0 ? (
              <TableRow>
                <TableCell colSpan={12} className="text-center py-12 text-gray-400">
                  <Package className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  Shtoni produkte në shportë
                </TableCell>
              </TableRow>
            ) : (
              cart.map((item, index) => {
                const { subtotal, total } = calculateItemTotal(item);
                return (
                  <TableRow 
                    key={item.product_id} 
                    className={`table-row-hover cursor-pointer ${selectedItemIndex === index ? 'bg-[#00a79d]/10' : ''}`}
                    onClick={() => setSelectedItemIndex(index)}
                  >
                    {/* Nr */}
                    <TableCell className="w-12">{index + 1}</TableCell>
                    
                    {/* Product Name */}
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
                                  max_stock: product.current_stock
                                } : it
                              ));
                            }
                          }}
                        >
                          <SelectTrigger className="border-[#00a79d]">
                            <SelectValue>{item.product_name || 'Zgjidh'}</SelectValue>
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
                        <span className="font-medium">{item.product_name || 'Produkt'}</span>
                      )}
                    </TableCell>
                    
                    {/* Quantity */}
                    <TableCell>
                      <div className="flex items-center justify-center gap-1">
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-6 w-6 border-gray-300"
                          onClick={(e) => { e.stopPropagation(); updateQuantity(item.product_id, -1); }}
                        >
                          <Minus className="h-3 w-3" />
                        </Button>
                        <span className="w-8 text-center font-semibold">{item.quantity}</span>
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-6 w-6 border-gray-300"
                          onClick={(e) => { e.stopPropagation(); updateQuantity(item.product_id, 1); }}
                        >
                          <Plus className="h-3 w-3" />
                        </Button>
                      </div>
                    </TableCell>
                    
                    {/* Price */}
                    <TableCell className="text-right">
                      {canEdit ? (
                        <Input
                          type="number"
                          value={item.unit_price}
                          onChange={(e) => {
                            const newPrice = parseFloat(e.target.value) || 0;
                            setCart(prev => prev.map((it, i) => 
                              i === index ? { ...it, unit_price: newPrice } : it
                            ));
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="w-20 h-7 text-right text-sm border-[#00a79d]"
                          min="0"
                          step="0.01"
                        />
                      ) : (
                        <span>€{item.unit_price.toFixed(2)}</span>
                      )}
                    </TableCell>
                    
                    {/* Discount */}
                    <TableCell className="text-center">
                      {canEdit ? (
                        <Input
                          type="number"
                          value={item.discount_percent || 0}
                          onChange={(e) => updateDiscount(item.product_id, parseFloat(e.target.value) || 0)}
                          onClick={(e) => e.stopPropagation()}
                          className="w-16 h-7 text-center text-sm border-[#00a79d]"
                          min="0"
                          max="100"
                        />
                      ) : (
                        <span>{item.discount_percent || 0}%</span>
                      )}
                    </TableCell>
                    
                    {/* VAT */}
                    <TableCell className="text-center text-gray-500">
                      {item.vat_percent || 0}%
                    </TableCell>
                    
                    {/* Price with VAT */}
                    <TableCell className="text-right">
                      €{(item.unit_price * (1 + (item.vat_percent || 0) / 100)).toFixed(2)}
                    </TableCell>
                    
                    {/* Total */}
                    <TableCell className="text-right font-bold text-[#00a79d]">
                      €{total.toFixed(2)}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 ml-2 text-red-500 hover:text-red-600"
                        onClick={(e) => { e.stopPropagation(); removeFromCart(item.product_id); }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
};

export default POSCart;
