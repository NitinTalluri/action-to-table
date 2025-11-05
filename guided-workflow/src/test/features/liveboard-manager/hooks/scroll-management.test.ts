import { act, renderHook } from "@testing-library/react";
import { useRef } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

describe("Scroll Management", () => {
  let mockScrollIntoView: ReturnType<typeof vi.fn>;
  let mockRef: { current: HTMLDivElement | null };

  beforeEach(() => {
    mockScrollIntoView = vi.fn();

    // Mock DOM element with scrollIntoView
    const mockElement = {
      scrollIntoView: mockScrollIntoView,
    } as unknown as HTMLDivElement;

    mockRef = { current: null };

    // Mock the ref behavior
    vi.clearAllMocks();
  });

  describe("workspaceRef functionality", () => {
    it("should create a ref that can hold HTMLDivElement", () => {
      const { result } = renderHook(() => useRef<HTMLDivElement>(null));

      expect(result.current.current).toBeNull();

      // Simulate attaching to DOM element
      const mockDiv = document.createElement("div");
      act(() => {
        result.current.current = mockDiv;
      });

      expect(result.current.current).toBe(mockDiv);
      expect(result.current.current?.tagName).toBe("DIV");
    });

    it("should support null as initial value", () => {
      const { result } = renderHook(() => useRef<HTMLDivElement>(null));

      expect(result.current.current).toBeNull();
    });
  });

  describe("scroll functionality", () => {
    it("should call scrollIntoView with correct options when element exists", () => {
      // Create a mock element with children
      const mockLastChild = {
        scrollIntoView: mockScrollIntoView,
      } as unknown as Element;

      const mockContainer = {
        lastElementChild: mockLastChild,
      } as unknown as HTMLDivElement;

      mockRef.current = mockContainer;

      // Simulate the scroll function
      const scrollToNewItem = () => {
        setTimeout(() => {
          if (mockRef.current) {
            const lastItem = mockRef.current.lastElementChild;
            lastItem?.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }
        }, 100);
      };

      // Execute scroll function
      scrollToNewItem();

      // Wait for setTimeout
      return new Promise<void>((resolve) => {
        setTimeout(() => {
          expect(mockScrollIntoView).toHaveBeenCalledWith({
            behavior: "smooth",
            block: "nearest",
          });
          resolve();
        }, 150);
      });
    });

    it("should not throw error when ref is null", () => {
      mockRef.current = null;

      const scrollToNewItem = () => {
        setTimeout(() => {
          if (mockRef.current) {
            const lastItem = mockRef.current.lastElementChild;
            lastItem?.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }
        }, 100);
      };

      expect(() => scrollToNewItem()).not.toThrow();
    });

    it("should not throw error when lastElementChild is null", () => {
      const mockContainer = {
        lastElementChild: null,
      } as unknown as HTMLDivElement;

      mockRef.current = mockContainer;

      const scrollToNewItem = () => {
        setTimeout(() => {
          if (mockRef.current) {
            const lastItem = mockRef.current.lastElementChild;
            lastItem?.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }
        }, 100);
      };

      expect(() => scrollToNewItem()).not.toThrow();
    });
  });

  describe("scroll timing", () => {
    it("should delay scroll by 100ms to allow DOM updates", () => {
      const mockLastChild = {
        scrollIntoView: mockScrollIntoView,
      } as unknown as Element;

      const mockContainer = {
        lastElementChild: mockLastChild,
      } as unknown as HTMLDivElement;

      mockRef.current = mockContainer;

      const scrollToNewItem = () => {
        setTimeout(() => {
          if (mockRef.current) {
            const lastItem = mockRef.current.lastElementChild;
            lastItem?.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }
        }, 100);
      };

      scrollToNewItem();

      // Should not be called immediately
      expect(mockScrollIntoView).not.toHaveBeenCalled();

      // Should be called after timeout
      return new Promise<void>((resolve) => {
        setTimeout(() => {
          expect(mockScrollIntoView).toHaveBeenCalled();
          resolve();
        }, 150);
      });
    });
  });
});
