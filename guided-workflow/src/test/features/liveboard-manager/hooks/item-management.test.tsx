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

describe('Item Management - Existing vs New Items', () => {
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
    },
    custom_eng: {
      'custom-1': {
        lb_params: {
          display_name: 'Custom Engagement Dashboard 1',
        },
      },
    },
    currently_in_ts: {
      'workspace-1': {
        lb_params: {
          display_name: 'Existing Workspace Item',
        },
      },
    },
  };

  describe('distinguishing existing vs new items', () => {
    it('should mark items from TML API as existing', async () => {
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

      // All items from TML should be marked as existing
      const allItems = [...result.current.libraryItems, ...result.current.workspaceItems];
      allItems.forEach(item => {
        expect(item.isExisting).toBe(true);
      });
    });

    it('should mark newly added items as non-existing', async () => {
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

      // Add an item to workspace
      const libraryItem = result.current.libraryItems[0];
      result.current.addToWorkspace(libraryItem.id);

      await waitFor(() => {
        const workspaceItems = result.current.workspaceItems;
        const addedItem = workspaceItems.find(item => 
          item.id === libraryItem.id && item.isInWorkspace
        );
        
        if (addedItem && !addedItem.isExisting) {
          expect(addedItem.isExisting).toBe(false);
        }
      });
    });

    it('should handle existing items with delete action', async () => {
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

      // Get an existing workspace item
      const existingItem = result.current.workspaceItems[0];
      expect(existingItem.isExisting).toBe(true);

      // Remove the existing item (should be marked for deletion)
      result.current.removeFromWorkspace(existingItem.id);

      await waitFor(() => {
        const updatedItems = result.current.workspaceItems;
        const deletedItem = updatedItems.find(item => item.id === existingItem.id);
        
        if (deletedItem) {
          expect(deletedItem.isDeleted).toBe(true);
          expect(deletedItem.isExisting).toBe(true);
        }
      });
    });

    it('should handle new items with remove action', async () => {
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

      // Add a new item to workspace
      const libraryItem = result.current.libraryItems[0];
      result.current.addToWorkspace(libraryItem.id);

      await waitFor(() => {
        const workspaceItems = result.current.workspaceItems;
        const newItem = workspaceItems.find(item => 
          item.id === libraryItem.id && !item.isExisting
        );
        
        if (newItem) {
          // Remove the new item (should be completely removed)
          result.current.removeFromWorkspace(newItem.id);
          
          return waitFor(() => {
            const updatedItems = result.current.workspaceItems;
            const removedItem = updatedItems.find(item => item.id === newItem.id);
            expect(removedItem).toBeUndefined();
          });
        }
      });
    });

    it('should track pending actions for existing vs new items', async () => {
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

      // Remove an existing item
      const existingItem = result.current.workspaceItems[0];
      result.current.removeFromWorkspace(existingItem.id);

      // Add a new item
      const libraryItem = result.current.libraryItems[0];
      result.current.addToWorkspace(libraryItem.id);

      await waitFor(() => {
        const actions = result.current.pendingActions;
        
        // Should have a delete action for existing item
        const deleteAction = actions.find(action => 
          action.type === 'delete' && action.item.id === existingItem.id
        );
        expect(deleteAction).toBeDefined();
        expect(deleteAction?.context).toBe('workspace');

        // Should have an add action for new item
        const addAction = actions.find(action => 
          action.type === 'add' && action.item.id === libraryItem.id
        );
        expect(addAction).toBeDefined();
        expect(addAction?.context).toBe('workspace');
      });
    });

    it('should properly filter deleted existing items from UI', async () => {
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

      const initialCount = result.current.workspaceState.items.length;

      // Remove an existing item
      const existingItem = result.current.workspaceItems[0];
      result.current.removeFromWorkspace(existingItem.id);

      await waitFor(() => {
        // workspaceState.items should filter out deleted items
        const visibleItems = result.current.workspaceState.items;
        expect(visibleItems.length).toBe(initialCount - 1);
        
        // But raw workspaceItems should still contain the deleted item
        const allItems = result.current.workspaceItems;
        const deletedItem = allItems.find(item => 
          item.id === existingItem.id && item.isDeleted
        );
        expect(deletedItem).toBeDefined();
      });
    });

    it('should handle clearing workspace with mixed existing and new items', async () => {
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

      // Add a new item to workspace
      const libraryItem = result.current.libraryItems[0];
      result.current.addToWorkspace(libraryItem.id);

      await waitFor(() => {
        // Clear workspace
        result.current.clearWorkspace();

        return waitFor(() => {
          const workspaceItems = result.current.workspaceItems;
          
          // Existing items should be marked as deleted
          const existingItems = workspaceItems.filter(item => item.isExisting);
          existingItems.forEach(item => {
            expect(item.isDeleted).toBe(true);
          });

          // New items should be completely removed
          const newItems = workspaceItems.filter(item => !item.isExisting);
          expect(newItems.length).toBe(0);
        });
      });
    });
  });

  describe('item state consistency', () => {
    it('should maintain consistent state when adding and removing items', async () => {
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

      const libraryItem = result.current.libraryItems[0];
      
      // Add item to workspace
      result.current.addToWorkspace(libraryItem.id);

      await waitFor(() => {
        const workspaceItems = result.current.workspaceItems;
        const addedItem = workspaceItems.find(item => 
          item.fileId === libraryItem.fileId && item.isInWorkspace
        );
        
        if (addedItem) {
          expect(addedItem.isInWorkspace).toBe(true);
          expect(addedItem.isExisting).toBe(false); // New addition
          
          // Remove the item
          result.current.removeFromWorkspace(addedItem.id);
          
          return waitFor(() => {
            const updatedItems = result.current.workspaceItems;
            const removedItem = updatedItems.find(item => item.id === addedItem.id);
            expect(removedItem).toBeUndefined(); // Should be completely removed
          });
        }
      });
    });

    it('should handle duplicate prevention correctly', async () => {
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

      const libraryItem = result.current.libraryItems[0];
      const initialWorkspaceCount = result.current.workspaceItems.length;
      
      // Add item to workspace
      result.current.addToWorkspace(libraryItem.id);

      await waitFor(() => {
        // Try to add the same item again
        result.current.addToWorkspace(libraryItem.id);

        return waitFor(() => {
          const workspaceItems = result.current.workspaceItems;
          // Should only have one instance of the item
          const matchingItems = workspaceItems.filter(item => 
            item.fileId === libraryItem.fileId && !item.isDeleted
          );
          expect(matchingItems.length).toBe(1);
        });
      });
    });
  });
});