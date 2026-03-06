'use client';

import { useState, useEffect } from 'react';
import { X, Plus, Trash2, Edit2 } from 'lucide-react';
import {
  getWatchlistGroups,
  createWatchlistGroup,
  updateWatchlistGroup,
  deleteWatchlistGroup,
} from '@/lib/api';
import type { WatchlistGroup } from '@/lib/types';

interface WatchlistGroupsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGroupsChange: () => void;
}

const COLORS = [
  '#6366f1', // indigo
  '#3b82f6', // blue
  '#0ea5e9', // cyan
  '#06b6d4', // sky
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ef4444', // red
  '#ec4899', // pink
  '#8b5cf6', // purple
  '#6b21a8', // violet-900
];

export default function WatchlistGroupsModal({
  isOpen,
  onClose,
  onGroupsChange,
}: WatchlistGroupsModalProps) {
  const [groups, setGroups] = useState<WatchlistGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDescription, setNewGroupDescription] = useState('');
  const [selectedColor, setSelectedColor] = useState('#6366f1');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [editColor, setEditColor] = useState('#6366f1');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadGroups();
    }
  }, [isOpen]);

  const loadGroups = async () => {
    setLoading(true);
    try {
      const data = await getWatchlistGroups();
      setGroups(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load groups');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGroupName.trim()) {
      setError('Group name is required');
      return;
    }

    setLoading(true);
    try {
      await createWatchlistGroup(newGroupName, selectedColor, newGroupDescription);
      setNewGroupName('');
      setNewGroupDescription('');
      setSelectedColor('#6366f1');
      await loadGroups();
      onGroupsChange();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create group');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateGroup = async (groupId: number) => {
    if (!editName.trim()) {
      setError('Group name is required');
      return;
    }

    setLoading(true);
    try {
      await updateWatchlistGroup(groupId, { name: editName, color: editColor });
      setEditingId(null);
      setEditName('');
      setEditColor('#6366f1');
      await loadGroups();
      onGroupsChange();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update group');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteGroup = async (groupId: number) => {
    if (!confirm('Delete this group? Stocks will be moved to "All".')) return;

    setLoading(true);
    try {
      await deleteWatchlistGroup(groupId);
      await loadGroups();
      onGroupsChange();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete group');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border border-slate-700 bg-slate-900 p-6 shadow-xl">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Watchlist Groups</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-300 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Create Group Form */}
        <form onSubmit={handleCreateGroup} className="mb-6 space-y-3">
          <input
            type="text"
            value={newGroupName}
            onChange={(e) => setNewGroupName(e.target.value)}
            placeholder="New group name..."
            className="w-full rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-sm text-white placeholder-slate-500 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50"
          />

          <input
            type="text"
            value={newGroupDescription}
            onChange={(e) => setNewGroupDescription(e.target.value)}
            placeholder="Description (optional)..."
            className="w-full rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-sm text-white placeholder-slate-500 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50"
          />

          {/* Color Picker */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Color:</span>
            <div className="flex flex-wrap gap-2">
              {COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setSelectedColor(color)}
                  className={`h-6 w-6 rounded-full border-2 transition-all ${
                    selectedColor === color
                      ? 'border-white shadow-lg'
                      : 'border-slate-600 hover:border-slate-400'
                  }`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <Plus className="inline h-4 w-4 mr-1" />
            Create Group
          </button>
        </form>

        {/* Groups List */}
        <div className="max-h-96 space-y-2 overflow-y-auto">
          {loading && !groups.length ? (
            <p className="text-center text-sm text-slate-400">Loading...</p>
          ) : groups.length === 0 ? (
            <p className="text-center text-sm text-slate-400">No groups yet</p>
          ) : (
            groups.map((group) => (
              <div
                key={group.id}
                className="flex items-center justify-between rounded-lg border border-slate-700/50 bg-slate-800/30 p-3"
              >
                {editingId === group.id ? (
                  <div className="flex-1 space-y-2">
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="w-full rounded-lg border border-slate-700 bg-slate-800/50 px-2 py-1 text-sm text-white outline-none focus:border-blue-500"
                    />
                    <div className="flex gap-1">
                      {COLORS.map((color) => (
                        <button
                          key={color}
                          onClick={() => setEditColor(color)}
                          className={`h-5 w-5 rounded-full border ${
                            editColor === color
                              ? 'border-white'
                              : 'border-slate-600'
                          }`}
                          style={{ backgroundColor: color }}
                        />
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleUpdateGroup(group.id)}
                        className="flex-1 rounded-lg bg-green-600 px-2 py-1 text-xs text-white hover:bg-green-700"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="flex-1 rounded-lg bg-slate-700 px-2 py-1 text-xs text-white hover:bg-slate-600"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-3">
                      <div
                        className="h-4 w-4 rounded-full"
                        style={{ backgroundColor: group.color }}
                      />
                      <div>
                        <p className="text-sm font-medium text-white">{group.name}</p>
                        <p className="text-xs text-slate-400">
                          {group.stock_count} stock{group.stock_count !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          setEditingId(group.id);
                          setEditName(group.name);
                          setEditColor(group.color);
                        }}
                        className="text-slate-400 hover:text-slate-300 transition-colors"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteGroup(group.id)}
                        className="text-slate-400 hover:text-red-400 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}