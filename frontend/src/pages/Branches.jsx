import React, { useState, useEffect } from 'react';
import { api } from '../App';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import {
  Plus,
  Edit2,
  Trash2,
  Building2,
  MapPin,
  Phone
} from 'lucide-react';

const Branches = () => {
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingBranch, setEditingBranch] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    phone: '',
    is_active: true
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/branches');
      setBranches(response.data);
    } catch (error) {
      console.error('Error loading branches:', error);
      toast.error('Gabim gjatë ngarkimit');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingBranch) {
        await api.put(`/branches/${editingBranch.id}`, formData);
        toast.success('Dega u përditësua');
      } else {
        await api.post('/branches', formData);
        toast.success('Dega u krijua');
      }

      setShowDialog(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë ruajtjes');
    }
  };

  const handleEdit = (branch) => {
    setEditingBranch(branch);
    setFormData({
      name: branch.name,
      address: branch.address || '',
      phone: branch.phone || '',
      is_active: branch.is_active
    });
    setShowDialog(true);
  };

  const handleDelete = async (branch) => {
    if (!window.confirm(`Jeni të sigurt që doni të fshini degën "${branch.name}"?`)) return;

    try {
      await api.delete(`/branches/${branch.id}`);
      toast.success('Dega u fshi');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë fshirjes');
    }
  };

  const resetForm = () => {
    setEditingBranch(null);
    setFormData({
      name: '',
      address: '',
      phone: '',
      is_active: true
    });
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="branches-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Degët</h1>
          <p className="text-gray-500">Menaxho filialet e biznesit</p>
        </div>
        <Button
          className="bg-[#00a79d] hover:bg-[#008f86] gap-2 rounded-xl shadow-md shadow-[#00a79d]/20"
          onClick={() => {
            resetForm();
            setShowDialog(true);
          }}
          data-testid="add-branch-btn"
        >
          <Plus className="h-4 w-4" />
          Shto Degë
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Degë</p>
                <p className="text-3xl font-bold mt-1">{branches.length}</p>
              </div>
              <Building2 className="h-8 w-8 text-gray-300" />
            </div>
          </CardContent>
        </Card>
        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Degë Aktive</p>
                <p className="text-3xl font-bold mt-1 text-green-600">
                  {branches.filter(b => b.is_active).length}
                </p>
              </div>
              <Building2 className="h-8 w-8 text-green-300" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Branches Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full flex items-center justify-center py-12">
            <div className="spinner" />
          </div>
        ) : branches.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <Building2 className="h-12 w-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">Nuk ka degë të regjistruara</p>
          </div>
        ) : (
          branches.map((branch) => (
            <Card key={branch.id} className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md hover-lift">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-[#00a79d]/15 to-[#00a79d]/5 flex items-center justify-center">
                      <Building2 className="h-5 w-5 text-[#00a79d]" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{branch.name}</CardTitle>
                      <Badge className={branch.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}>
                        {branch.is_active ? 'Aktive' : 'Joaktive'}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleEdit(branch)}
                      data-testid={`edit-branch-${branch.id}`}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-red-500 hover:text-red-700"
                      onClick={() => handleDelete(branch)}
                      data-testid={`delete-branch-${branch.id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  {branch.address && (
                    <div className="flex items-center gap-2 text-gray-500">
                      <MapPin className="h-4 w-4" />
                      <span>{branch.address}</span>
                    </div>
                  )}
                  {branch.phone && (
                    <div className="flex items-center gap-2 text-gray-500">
                      <Phone className="h-4 w-4" />
                      <span>{branch.phone}</span>
                    </div>
                  )}
                  <p className="text-xs text-gray-400 pt-2">
                    Krijuar: {new Date(branch.created_at).toLocaleDateString('sq-AL')}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Add/Edit Branch Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingBranch ? 'Modifiko Degën' : 'Shto Degë të Re'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Emri i Degës</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="p.sh. Dega Qendrore"
                  required
                  data-testid="branch-name-input"
                />
              </div>

              <div className="space-y-2">
                <Label>Adresa</Label>
                <Input
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="p.sh. Rruga Skënderbej, Nr. 10"
                  data-testid="branch-address-input"
                />
              </div>

              <div className="space-y-2">
                <Label>Telefoni</Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="p.sh. +383 44 123 456"
                  data-testid="branch-phone-input"
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>
                Anulo
              </Button>
              <Button type="submit" className="bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20" data-testid="save-branch-btn">
                {editingBranch ? 'Ruaj Ndryshimet' : 'Krijo Degën'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Branches;
