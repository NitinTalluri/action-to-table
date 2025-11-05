import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as tmlApi from '~/api/tml';
import type { ITmlResponse } from '~/domain/Tml';
import { useLiveboardManager } from '~/features/liveboard-manager/hooks/useLiveboardManager';

// Mock the TML API
vi.mock('~/api/tml');
const mockGetTml = vi.mocked(tmlApi.getTml);

// Mock toast notifications
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

describe('useLiveboardManager - Library and Workspace Separation', () => {
  let queryClient: QueryClient;
  let wrapper: React.FC<{ children: React.ReactNode }>;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    wrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    vi.clearAllMocks();
  });

  const mockTmlResponse: ITmlResponse = {
    common: {
      'standard-1': {
        lb_params: {
          display_name: 'Standard Dashboard 1',
        },
      },
      'standard-2': {
        lb_params: {
          display_name: 'Standard Dashboard 2',
        },
      },
    },
    custom_eng: {
      'custom-1': {
        lb_params: {
          display_name: 'Custom Engagement Dashboard 1',
        },
      },
      'custom-2': {
        lb_params: {
          display_name: 'Custom Engagement Dashboard 2',
        },
      },
    },
    currently_in_ts: {
      'workspace-1': {
        lb_params: {
          display_name: 'Active Workspace Item 1',
        },
      },
      'workspace-2': {
        lb_params: {
          display_name: 'Active Workspace Item 2',
        },
      },
    },
    delete: {
      'deleted-1': {
        lb_params: {
          display_name: 'Deleted Dashboard 1',
        },
      },
    },
  };

  it('should properly separate library items from TML response', async () => {
    mockGetTml.mockResolvedValue(mockTmlResponse);

    const { result } = renderHook(
      () =>
        useLiveboardManager({
          engagementId: 1,
          canvasId: 1,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.libraryState.isLoading).toBe(false);
    });

    const libraryItems = result.current.libraryState.items;

    // Should have 4 library items (2 common + 2 custom_eng) + 1 deleted item
    expect(libraryItems).toHaveLength(5);

    // Check common (standard) items
    const standardItems = libraryItems.filter(item => item.category === 'standard');
    expect(standardItems).toHaveLength(2);
    expect(standardItems[0]).toMatchObject({
      bucketId: 'common',
      category: 'standard',
      isInWorkspace: false,
      isExisting: true,
      isDeleted: false,
    });
    expect(standardItems[1]).toMatchObject({
      bucketId: 'common',
      category: 'standard',
      isInWorkspace: false,
      isExisting: true,
      isDeleted: false,
    });

    // Check custom_eng (engagement) items
    const engagementItems = libraryItems.filter(
      item => item.category === 'engagement' && !item.isDeleted
    );
    expect(engagementItems).toHaveLength(2);
    expect(engagementItems[0]).toMatchObject({
      bucketId: 'custom_eng',
      category: 'engagement',
      isInWorkspace: false,
      isExisting: true,
      isDeleted: false,
    });
    expect(engagementItems[1]).toMatchObject({
      bucketId: 'custom_eng',
      category: 'engagement',
      isInWorkspace: false,
      isExisting: true,
      isDeleted: false,
    });

    // Check deleted items (should be in library but marked as deleted)
    const deletedItems = libraryItems.filter(item => item.isDeleted);
    expect(deletedItems).toHaveLength(1);
    expect(deletedItems[0]).toMatchObject({
      bucketId: 'delete',
      category: 'engagement',
      isInWorkspace: false,
      isExisting: true,
      isDeleted: true,
    });
  });

  it('should properly separate workspace items from TML response', async () => {
    mockGetTml.mockResolvedValue(mockTmlResponse);

    const { result } = renderHook(
      () =>
        useLiveboardManager({
          engagementId: 1,
          canvasId: 1,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.workspaceState.isLoading).toBe(false);
    });

    const workspaceItems = result.current.workspaceState.items;

    // Should have 2 workspace items (currently_in_ts bucket)
    expect(workspaceItems).toHaveLength(2);

    workspaceItems.forEach(item => {
      expect(item).toMatchObject({
        bucketId: 'currently_in_ts',
        category: 'engagement',
        isInWorkspace: true,
        isExisting: true,
        isDeleted: false,
      });
    });

    // Verify specific items
    expect(workspaceItems[0].display_name).toBe('Active Workspace Item 1');
    expect(workspaceItems[1].display_name).toBe('Active Workspace Item 2');
  });

  it('should exclude deleted items from workspace', async () => {
    const responseWithDeletedWorkspaceItem: ITmlResponse = {
      ...mockTmlResponse,
      delete: {
        'deleted-workspace-item': {
          lb_params: {
            display_name: 'Deleted Workspace Item',
          },
        },
      },
    };

    mockGetTml.mockResolvedValue(responseWithDeletedWorkspaceItem);

    const { result } = renderHook(
      () =>
        useLiveboardManager({
          engagementId: 1,
          canvasId: 1,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.workspaceState.isLoading).toBe(false);
    });

    const workspaceItems = result.current.workspaceState.items;

    // Workspace should still only have 2 items (deleted items are excluded)
    expect(workspaceItems).toHaveLength(2);
    expect(workspaceItems.every(item => !item.isDeleted)).toBe(true);
    expect(workspaceItems.every(item => item.bucketId === 'currently_in_ts')).toBe(true);
  });

  it('should filter out deleted items from library state items', async () => {
    mockGetTml.mockResolvedValue(mockTmlResponse);

    const { result } = renderHook(
      () =>
        useLiveboardManager({
          engagementId: 1,
          canvasId: 1,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.libraryState.isLoading).toBe(false);
    });

    // The libraryState.items should filter out deleted items for UI display
    const visibleLibraryItems = result.current.libraryState.items;
    
    // Should only show non-deleted items (4 total: 2 common + 2 custom_eng)
    expect(visibleLibraryItems).toHaveLength(4);
    expect(visibleLibraryItems.every(item => !item.isDeleted)).toBe(true);
  });

  it('should handle empty buckets gracefully', async () => {
    const emptyResponse: ITmlResponse = {
      common: {},
      custom_eng: {},
      currently_in_ts: {},
      delete: {},
    };

    mockGetTml.mockResolvedValue(emptyResponse);

    const { result } = renderHook(
      () =>
        useLiveboardManager({
          engagementId: 1,
          canvasId: 1,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.libraryState.isLoading).toBe(false);
    });

    expect(result.current.libraryState.items).toHaveLength(0);
    expect(result.current.workspaceState.items).toHaveLength(0);
  });

  it('should handle missing buckets gracefully', async () => {
    const partialResponse: ITmlResponse = {
      common: {
        'only-item': {
          lb_params: {
            display_name: 'Only Common Item',
          },
        },
      },
    };

    mockGetTml.mockResolvedValue(partialResponse);

    const { result } = renderHook(
      () =>
        useLiveboardManager({
          engagementId: 1,
          canvasId: 1,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.libraryState.isLoading).toBe(false);
    });

    expect(result.current.libraryState.items).toHaveLength(1);
    expect(result.current.workspaceState.items).toHaveLength(0);
    expect(result.current.libraryState.items[0]).toMatchObject({
      bucketId: 'common',
      category: 'standard',
      isInWorkspace: false,
      isExisting: true,
      isDeleted: false,
    });
  });

  it('should maintain proper item properties during separation', async () => {
    mockGetTml.mockResolvedValue(mockTmlResponse);

    const { result } = renderHook(
      () =>
        useLiveboardManager({
          engagementId: 1,
          canvasId: 1,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.libraryState.isLoading).toBe(false);
    });

    const allLibraryItems = result.current.libraryItems; // Direct access to include deleted
    const allWorkspaceItems = result.current.workspaceItems;

    // Verify all library items have correct properties
    allLibraryItems.forEach(item => {
      expect(item).toHaveProperty('fileId');
      expect(item).toHaveProperty('display_name');
      expect(item).toHaveProperty('bucketId');
      expect(item).toHaveProperty('id');
      expect(item).toHaveProperty('category');
      expect(item).toHaveProperty('isInWorkspace');
      expect(item).toHaveProperty('isExisting');
      expect(item).toHaveProperty('isDeleted');
      
      // Library items should not be in workspace
      if (!item.isDeleted) {
        expect(item.isInWorkspace).toBe(false);
      }
      expect(item.isExisting).toBe(true);
    });

    // Verify all workspace items have correct properties
    allWorkspaceItems.forEach(item => {
      expect(item).toHaveProperty('fileId');
      expect(item).toHaveProperty('display_name');
      expect(item).toHaveProperty('bucketId');
      expect(item).toHaveProperty('id');
      expect(item).toHaveProperty('category');
      expect(item).toHaveProperty('isInWorkspace');
      expect(item).toHaveProperty('isExisting');
      expect(item).toHaveProperty('isDeleted');
      
      // Workspace items should be in workspace and not deleted
      expect(item.isInWorkspace).toBe(true);
      expect(item.isExisting).toBe(true);
      expect(item.isDeleted).toBe(false);
    });
  });

  it('should generate unique IDs for items across buckets', async () => {
    const responseWithDuplicateFileIds: ITmlResponse = {
      common: {
        'duplicate-id': {
          lb_params: {
            display_name: 'Common Item',
          },
        },
      },
      custom_eng: {
        'duplicate-id': {
          lb_params: {
            display_name: 'Custom Item',
          },
        },
      },
      currently_in_ts: {
        'duplicate-id': {
          lb_params: {
            display_name: 'Workspace Item',
          },
        },
      },
    };

    mockGetTml.mockResolvedValue(responseWithDuplicateFileIds);

    const { result } = renderHook(
      () =>
        useLiveboardManager({
          engagementId: 1,
          canvasId: 1,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.libraryState.isLoading).toBe(false);
    });

    const allItems = [...result.current.libraryItems, ...result.current.workspaceItems];
    const ids = allItems.map(item => item.id);
    const uniqueIds = [...new Set(ids)];

    // All IDs should be unique
    expect(uniqueIds).toHaveLength(ids.length);
    
    // Verify the ID format includes bucket prefix
    expect(ids).toContain('common-duplicate-id');
    expect(ids).toContain('custom_eng-duplicate-id');
    expect(ids).toContain('currently_in_ts-duplicate-id');
  });
});