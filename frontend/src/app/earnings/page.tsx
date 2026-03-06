'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { EarningsRecord, EarningsFilterParams, EarningsPaginatedResponse } from '@/types/earnings';
import { getEarnings } from '@/lib/api/earnings';
import { EarningsFilters } from '@/components/earnings';
import { EarningsTable } from '@/components/earnings';
import { EarningsDetail } from '@/components/earnings';

export default function EarningsPage() {
  const [earnings, setEarnings] = useState<EarningsRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalRecords, setTotalRecords] = useState(0);
  const [selectedEarning, setSelectedEarning] = useState<EarningsRecord | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [filters, setFilters] = useState<EarningsFilterParams>({
    limit: 25,
    offset: 0,
  });

  const fetchEarnings = useCallback(async (params: EarningsFilterParams) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getEarnings(params);
      setEarnings(response.data);
      setTotalRecords(response.meta.total);
      setCurrentPage(params.offset || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch earnings');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEarnings(filters);
  }, [filters, fetchEarnings]);

  const handleFiltersChange = useCallback((newParams: EarningsFilterParams) => {
    setFilters({
      ...newParams,
      offset: 0, // Reset to first page on filter change
    });
  }, []);

  const handlePreviousPage = useCallback(() => {
    if (currentPage >= 25) {
      setFilters((prev) => ({
        ...prev,
        offset: Math.max(0, (prev.offset || 0) - (prev.limit || 25)),
      }));
    }
  }, [currentPage]);

  const handleNextPage = useCallback(() => {
    if (currentPage + (filters.limit || 25) < totalRecords) {
      setFilters((prev) => ({
        ...prev,
        offset: (prev.offset || 0) + (prev.limit || 25),
      }));
    }
  }, [currentPage, totalRecords, filters.limit]);

  const handleEarningClick = (earning: EarningsRecord) => {
    setSelectedEarning(earning);
    setIsDetailOpen(true);
  };

  const hasNextPage = currentPage + (filters.limit || 25) < totalRecords;
  const hasPreviousPage = currentPage > 0;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Earnings Calendar</h1>
          <p className="text-gray-600 mt-2">
            Track upcoming and past earnings announcements with estimates and actual results
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {error}
          </div>
        )}

        {/* Filters */}
        <EarningsFilters
          onFiltersChange={handleFiltersChange}
          isLoading={isLoading}
        />

        {/* Earnings Table */}
        <EarningsTable
          earnings={earnings}
          isLoading={isLoading}
          onEarningClick={handleEarningClick}
        />

        {/* Pagination */}
        {totalRecords > 0 && (
          <div className="mt-6 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing {currentPage + 1}-{Math.min(currentPage + (filters.limit || 25), totalRecords)} of{' '}
              {totalRecords} earnings
            </div>
            <div className="flex gap-2">
              <button
                onClick={handlePreviousPage}
                disabled={!hasPreviousPage || isLoading}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md text-sm font-medium hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400"
              >
                Previous
              </button>
              <button
                onClick={handleNextPage}
                disabled={!hasNextPage || isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:bg-gray-400"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Detail Modal */}
        <EarningsDetail
          earning={selectedEarning}
          isOpen={isDetailOpen}
          onClose={() => setIsDetailOpen(false)}
        />
      </div>
    </div>
  );
}