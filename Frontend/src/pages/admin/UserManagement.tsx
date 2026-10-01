import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { PageHeading } from '../../components/pilot/PageHeading';
import {
  ShieldCheckIcon, ShieldAlertIcon, Edit2Icon, KeyIcon, XIcon,
  CheckIcon, SearchIcon, AlertTriangleIcon, UserIcon, EyeIcon, EyeOffIcon
} from 'lucide-react';

interface UserRecord {
  id: number;
  username: string;
  name: string;
  email: string;
  role: string;
  organisation: string;
  station: string;
  is_active: boolean;
}

/* ── Confirmation Dialog ──────────────────────────────────────────── */
function ConfirmDialog({ open, title, message, onConfirm, onCancel, variant = 'danger' }: {
  open: boolean; title: string; message: string; onConfirm: () => void; onCancel: () => void; variant?: 'danger' | 'info';
}) {
  if (!open) return null;
  const isDanger = variant === 'danger';
  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/80 px-4 backdrop-blur-sm">
      <div className={`w-full max-w-sm rounded-2xl border ${isDanger ? 'border-rose-900/60' : 'border-sky-900/60'} bg-panel p-6 shadow-2xl`}>
        <div className="flex items-center gap-3 mb-4">
          <div className={`flex h-10 w-10 items-center justify-center rounded-full ${isDanger ? 'bg-rose-900/30' : 'bg-sky-900/30'}`}>
            <AlertTriangleIcon className={`h-5 w-5 ${isDanger ? 'text-rose-400' : 'text-sky-400'}`} />
          </div>
          <h3 className="text-lg font-bold text-white">{title}</h3>
        </div>
        <p className="text-sm text-slate-300 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button onClick={onCancel} className="rounded-lg px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors">Cancel</button>
          <button onClick={onConfirm} className={`rounded-lg px-5 py-2 text-sm font-semibold text-white transition-colors ${isDanger ? 'bg-rose-600 hover:bg-rose-500' : 'bg-sky-600 hover:bg-sky-500'}`}>Confirm</button>
        </div>
      </div>
    </div>
  );
}

export function UserManagement() {
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Edit modal state
  const [editUser, setEditUser] = useState<UserRecord | null>(null);
  const [editForm, setEditForm] = useState({ name: '', email: '', role: '', organisation: '', station: '' });

  // Password modal state
  const [pwUser, setPwUser] = useState<UserRecord | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [showPw, setShowPw] = useState(false);

  // Confirm dialog state
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<(() => void) | null>(null);
  const [confirmTitle, setConfirmTitle] = useState('');
  const [confirmMsg, setConfirmMsg] = useState('');
  const [confirmVariant, setConfirmVariant] = useState<'danger' | 'info'>('danger');

  const showConfirm = (title: string, msg: string, action: () => void, variant: 'danger' | 'info' = 'danger') => {
    setConfirmTitle(title);
    setConfirmMsg(msg);
    setConfirmAction(() => action);
    setConfirmVariant(variant);
    setConfirmOpen(true);
  };

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await axios.get('http://localhost:8000/admin/users');
      setUsers(res.data);
    } catch (err) {
      console.error("Failed to fetch users", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  /* ── Search filter ────────────────────────────────────────────── */
  const filtered = useMemo(() => {
    if (!search.trim()) return users;
    const q = search.toLowerCase();
    return users.filter(u =>
      u.username.toLowerCase().includes(q) ||
      u.name.toLowerCase().includes(q) ||
      u.role.toLowerCase().includes(q) ||
      (u.organisation && u.organisation.toLowerCase().includes(q))
    );
  }, [users, search]);

  /* ── Status toggle ────────────────────────────────────────────── */
  const toggleUserStatus = (user: UserRecord) => {
    const action = user.is_active ? 'deactivate' : 'activate';
    showConfirm(
      `${user.is_active ? 'Deactivate' : 'Activate'} User`,
      `Are you sure you want to ${action} "${user.name}" (${user.username})? ${user.is_active ? 'They will no longer be able to log in.' : 'They will regain access to the system.'}`,
      async () => {
        try {
          await axios.put(`http://localhost:8000/admin/users/${user.id}/status`, { is_active: !user.is_active });
          fetchUsers();
        } catch (err: any) {
          alert(err.response?.data?.detail || "Failed to update user status");
        }
      },
      user.is_active ? 'danger' : 'info'
    );
  };

  /* ── Open edit modal ──────────────────────────────────────────── */
  const openEdit = (user: UserRecord) => {
    setEditUser(user);
    setEditForm({
      name: user.name || '',
      email: user.email || '',
      role: user.role || '',
      organisation: user.organisation || '',
      station: user.station || '',
    });
  };

  const handleEditSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editUser) return;
    try {
      await axios.put(`http://localhost:8000/admin/users/${editUser.id}`, editForm);
      setEditUser(null);
      fetchUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to update user.");
    }
  };

  /* ── Password reset ───────────────────────────────────────────── */
  const openPasswordReset = (user: UserRecord) => {
    setPwUser(user);
    setNewPassword('');
    setShowPw(false);
  };

  const handlePasswordReset = () => {
    if (!pwUser) return;
    if (newPassword.length < 6) {
      alert("Password must be at least 6 characters.");
      return;
    }
    showConfirm(
      'Reset Password',
      `Are you sure you want to reset the password for "${pwUser.name}" (${pwUser.username})? This action cannot be undone.`,
      async () => {
        try {
          await axios.put(`http://localhost:8000/admin/users/${pwUser.id}/password`, { new_password: newPassword });
          alert(`Password for ${pwUser.username} has been reset successfully.`);
          setPwUser(null);
          setNewPassword('');
        } catch (err: any) {
          alert(err.response?.data?.detail || "Failed to reset password.");
        }
      },
      'danger'
    );
  };

  return (
    <div className="w-full space-y-6">
      <PageHeading
        eyebrow="Admin Portal"
        title="User Management"
        description="View, edit, activate/deactivate users and reset passwords."
      />

      {/* Search bar */}
      <div className="relative w-full sm:w-80">
        <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
        <input
          type="text"
          placeholder="Search users by name, ID, role..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-line bg-ink pl-10 pr-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent placeholder:text-slate-500"
        />
      </div>

      <p className="text-xs text-slate-500">Showing {filtered.length} of {users.length} users</p>

      <section className="rounded-xl border border-line bg-panel p-5">
        {loading ? (
          <p className="py-10 text-center text-sm text-slate-400">Loading users...</p>
        ) : filtered.length === 0 ? (
          <p className="py-10 text-center text-sm text-slate-400">
            {users.length === 0 ? 'No users found in the system.' : 'No users match your search.'}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="border-b border-line text-xs uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-4 py-3 font-semibold">Username / ID</th>
                  <th className="px-4 py-3 font-semibold">Name</th>
                  <th className="px-4 py-3 font-semibold">Role</th>
                  <th className="px-4 py-3 font-semibold">Organisation</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/60">
                {filtered.map((user) => (
                  <tr key={user.id} className="transition-colors hover:bg-slate-800/30 cursor-pointer" onClick={() => openEdit(user)}>
                    <td className="whitespace-nowrap px-4 py-3.5 font-mono text-sky-bright font-bold">
                      {user.username}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5 font-medium text-slate-200">
                      {user.name}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5 capitalize">
                      <span className={`rounded px-2 py-0.5 text-xs font-semibold badge-${user.role}`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5 text-slate-300">
                      {user.organisation || '-'}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5">
                      <span className={`flex items-center gap-1.5 text-xs font-semibold ${user.is_active ? 'status-active' : 'status-inactive'}`}>
                        {user.is_active ? <ShieldCheckIcon className="h-3.5 w-3.5" /> : <ShieldAlertIcon className="h-3.5 w-3.5" />}
                        {user.is_active ? 'Active' : 'Deactivated'}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5 text-right space-x-2" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => openEdit(user)}
                        className="rounded p-1.5 text-slate-400 hover:bg-slate-800 hover:text-sky-400 transition-colors"
                        title="Edit User Details"
                      >
                        <Edit2Icon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => openPasswordReset(user)}
                        className="rounded p-1.5 text-slate-400 hover:bg-amber-900/50 hover:text-amber-400 transition-colors"
                        title="Reset Password"
                      >
                        <KeyIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => toggleUserStatus(user)}
                        className={`rounded px-3 py-1 text-xs font-semibold transition-colors ${user.is_active ? 'btn-deactivate' : 'btn-activate'}`}
                      >
                        {user.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ── Edit User Modal ───────────────────────────────────────── */}
      {editUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-line bg-panel p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-sky-900/30">
                  <UserIcon className="h-5 w-5 text-sky-400" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Edit User</h3>
                  <p className="text-xs text-slate-400 font-mono">{editUser.username}</p>
                </div>
              </div>
              <button onClick={() => setEditUser(null)} className="text-slate-400 hover:text-white transition-colors">
                <XIcon className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleEditSave} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Full Name</label>
                  <input type="text" value={editForm.name}
                    onChange={(e) => setEditForm({...editForm, name: e.target.value})}
                    className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Email</label>
                  <input type="email" value={editForm.email}
                    onChange={(e) => setEditForm({...editForm, email: e.target.value})}
                    className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Role</label>
                  <select value={editForm.role}
                    onChange={(e) => setEditForm({...editForm, role: e.target.value})}
                    className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent">
                    <option value="forecaster">Forecaster</option>
                    <option value="pilot">Pilot</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Organisation</label>
                  <input type="text" value={editForm.organisation}
                    onChange={(e) => setEditForm({...editForm, organisation: e.target.value})}
                    className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Station</label>
                  <input type="text" value={editForm.station}
                    onChange={(e) => setEditForm({...editForm, station: e.target.value})}
                    className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent" />
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-line pt-4 mt-6">
                <button type="button" onClick={() => { setEditUser(null); openPasswordReset(editUser); }}
                  className="flex items-center gap-2 rounded-lg border border-amber-900/50 px-4 py-2 text-sm font-semibold text-amber-400 hover:bg-amber-900/20 transition-colors">
                  <KeyIcon className="h-4 w-4" /> Reset Password
                </button>
                <div className="flex gap-3">
                  <button type="button" onClick={() => setEditUser(null)}
                    className="rounded-lg px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors">Cancel</button>
                  <button type="submit"
                    className="flex items-center gap-2 rounded-lg bg-accent px-5 py-2 text-sm font-semibold text-white hover:bg-sky-500 transition-colors">
                    <CheckIcon className="h-4 w-4" /> Save Changes
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Password Reset Modal ──────────────────────────────────── */}
      {pwUser && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/80 px-4 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl border border-amber-900/60 bg-panel p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-900/30">
                  <KeyIcon className="h-5 w-5 text-amber-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Reset Password</h3>
                  <p className="text-xs text-slate-400 font-mono">{pwUser.username} — {pwUser.name}</p>
                </div>
              </div>
              <button onClick={() => setPwUser(null)} className="text-slate-400 hover:text-white transition-colors">
                <XIcon className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">New Password (min 6 chars)</label>
                <div className="relative">
                  <input
                    type={showPw ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password..."
                    className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 pr-10 text-sm text-slate-200 outline-none transition-colors focus:border-amber-500 placeholder:text-slate-500"
                  />
                  <button type="button" onClick={() => setShowPw(!showPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                    {showPw ? <EyeOffIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div className="flex justify-end gap-3 border-t border-line pt-4">
                <button onClick={() => setPwUser(null)}
                  className="rounded-lg px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors">Cancel</button>
                <button onClick={handlePasswordReset}
                  className="flex items-center gap-2 rounded-lg bg-amber-600 px-5 py-2 text-sm font-semibold text-white hover:bg-amber-500 transition-colors">
                  <KeyIcon className="h-4 w-4" /> Reset Password
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Dialog */}
      <ConfirmDialog
        open={confirmOpen}
        title={confirmTitle}
        message={confirmMsg}
        variant={confirmVariant}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={() => { confirmAction?.(); setConfirmOpen(false); }}
      />
    </div>
  );
}
