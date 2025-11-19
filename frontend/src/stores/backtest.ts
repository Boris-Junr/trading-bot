import { defineStore } from 'pinia';
import { ref, computed, onUnmounted } from 'vue';
import type { BacktestResult, BacktestScenario } from '../types';
import type { RealtimeChannel } from '@supabase/supabase-js';
import api from '../services/api';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/composables/useAuth';

export const useBacktestStore = defineStore('backtest', () => {
  // State
  const backtests = ref<BacktestResult[]>([]);
  const currentBacktest = ref<BacktestResult | null>(null);
  const scenarios = ref<BacktestScenario[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Real-time subscription
  let realtimeChannel: RealtimeChannel | null = null;

  // Get authenticated user
  const { user } = useAuth();

  // Getters
  const sortedBacktests = computed(() => {
    return [...backtests.value].sort((a, b) => {
      // Sort by creation date (when the backtest was run), most recent first
      let dateA: number;
      let dateB: number;

      // Try to get created_at, otherwise parse from ID, otherwise fall back to end_date
      if (a.created_at) {
        dateA = new Date(a.created_at).getTime();
      } else if (a.id) {
        // Parse timestamp from ID format: Strategy_Symbol_YYYYMMDD_HHMMSS
        const match = a.id.match(/_(\d{8})_(\d{6})$/);
        if (match && match[1] && match[2]) {
          const dateStr = match[1];
          const timeStr = match[2];
          const year = dateStr.substring(0, 4);
          const month = dateStr.substring(4, 6);
          const day = dateStr.substring(6, 8);
          const hour = timeStr.substring(0, 2);
          const minute = timeStr.substring(2, 4);
          const second = timeStr.substring(4, 6);
          dateA = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`).getTime();
        } else {
          dateA = new Date(a.end_date).getTime();
        }
      } else {
        dateA = new Date(a.end_date).getTime();
      }

      if (b.created_at) {
        dateB = new Date(b.created_at).getTime();
      } else if (b.id) {
        const match = b.id.match(/_(\d{8})_(\d{6})$/);
        if (match && match[1] && match[2]) {
          const dateStr = match[1];
          const timeStr = match[2];
          const year = dateStr.substring(0, 4);
          const month = dateStr.substring(4, 6);
          const day = dateStr.substring(6, 8);
          const hour = timeStr.substring(0, 2);
          const minute = timeStr.substring(2, 4);
          const second = timeStr.substring(4, 6);
          dateB = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`).getTime();
        } else {
          dateB = new Date(b.end_date).getTime();
        }
      } else {
        dateB = new Date(b.end_date).getTime();
      }

      return dateB - dateA; // Larger (more recent) timestamp comes first
    });
  });

  const bestBacktest = computed(() => {
    // Filter out failed backtests before finding the best one
    const successfulBacktests = backtests.value.filter(bt => bt.status !== 'failed' && bt.performance);
    if (successfulBacktests.length === 0) return null;
    return [...successfulBacktests].sort((a, b) =>
      b.performance!.total_return - a.performance!.total_return
    )[0];
  });

  // Actions
  async function fetchBacktests() {
    loading.value = true;
    error.value = null;
    try {
      if (!user.value) {
        console.log('No authenticated user, skipping backtest fetch');
        backtests.value = [];
        return;
      }

      // Fetch from Supabase
      const { data, error: fetchError } = await supabase
        .from('backtests')
        .select('*')
        .eq('user_id', user.value.id)
        .order('created_at', { ascending: false });

      if (fetchError) throw fetchError;

      backtests.value = (data || []).map((bt: any) => ({
        id: bt.id,
        strategy: bt.strategy,
        symbol: bt.symbol,
        start_date: bt.start_date,
        end_date: bt.end_date,
        created_at: bt.created_at,
        status: bt.status || 'completed',
        performance: bt.performance || {},
        trading: bt.trading || {},
        error: bt.error
      }));

      // Set up real-time subscription if not already set up
      if (!realtimeChannel) {
        setupRealtimeSubscription();
      }
    } catch (e: any) {
      console.error('Error fetching backtests:', e);
      error.value = e.message || 'Failed to fetch backtests';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function fetchBacktest(id: string) {
    loading.value = true;
    error.value = null;
    try {
      // Fetch from Supabase
      const { data, error: fetchError } = await supabase
        .from('backtests')
        .select('*')
        .eq('id', id)
        .single();

      if (fetchError) throw fetchError;

      currentBacktest.value = {
        id: data.id,
        strategy: data.strategy,
        symbol: data.symbol,
        start_date: data.start_date,
        end_date: data.end_date,
        created_at: data.created_at,
        status: data.status || 'completed',
        performance: data.performance || {},
        trading: data.trading || {},
        error: data.error
      } as BacktestResult;

      return currentBacktest.value;
    } catch (e: any) {
      console.error('Error fetching backtest:', e);
      error.value = e.message || 'Failed to fetch backtest';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function runBacktest(scenario: BacktestScenario) {
    loading.value = true;
    error.value = null;
    try {
      const result = await api.runBacktest(scenario);
      backtests.value.push(result);
      currentBacktest.value = result;
      return result;
    } catch (e: any) {
      error.value = e.message || 'Failed to run backtest';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function fetchScenarios() {
    loading.value = true;
    error.value = null;
    try {
      scenarios.value = await api.getBacktestScenarios();
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch scenarios';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  function setCurrentBacktest(backtest: BacktestResult) {
    currentBacktest.value = backtest;
  }

  function clearError() {
    error.value = null;
  }

  function setupRealtimeSubscription() {
    if (!user.value) return;

    console.log('Setting up real-time subscription for backtests');

    realtimeChannel = supabase
      .channel('backtests_changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'backtests',
          filter: `user_id=eq.${user.value.id}`
        },
        (payload: any) => {
          console.log('Backtest change detected:', payload);

          if (payload.eventType === 'INSERT') {
            // New backtest added
            const newBacktest = {
              id: payload.new.id,
              strategy: payload.new.strategy,
              symbol: payload.new.symbol,
              start_date: payload.new.start_date,
              end_date: payload.new.end_date,
              created_at: payload.new.created_at,
              status: payload.new.status || 'completed',
              performance: payload.new.performance || {},
              trading: payload.new.trading || {},
              error: payload.new.error
            };
            backtests.value.unshift(newBacktest);
          } else if (payload.eventType === 'UPDATE') {
            // Backtest updated (e.g., status changed from running to completed)
            const index = backtests.value.findIndex(bt => bt.id === payload.new.id);
            if (index !== -1) {
              const currentBacktest = backtests.value[index];
              if (currentBacktest) {
                backtests.value[index] = {
                  ...currentBacktest,
                  status: payload.new.status || currentBacktest.status,
                  performance: payload.new.performance || currentBacktest.performance,
                  trading: payload.new.trading || currentBacktest.trading,
                  error: payload.new.error
                } as BacktestResult;
              }
            }
          } else if (payload.eventType === 'DELETE') {
            // Backtest deleted
            backtests.value = backtests.value.filter(bt => bt.id !== payload.old.id);
          }
        }
      )
      .subscribe();
  }

  function unsubscribeRealtime() {
    if (realtimeChannel) {
      console.log('Unsubscribing from real-time backtest updates');
      supabase.removeChannel(realtimeChannel);
      realtimeChannel = null;
    }
  }

  // Cleanup on store disposal
  onUnmounted(() => {
    unsubscribeRealtime();
  });

  return {
    // State
    backtests,
    currentBacktest,
    scenarios,
    loading,
    error,
    // Getters
    sortedBacktests,
    bestBacktest,
    // Actions
    fetchBacktests,
    fetchBacktest,
    runBacktest,
    fetchScenarios,
    setCurrentBacktest,
    clearError,
    setupRealtimeSubscription,
    unsubscribeRealtime,
  };
});
