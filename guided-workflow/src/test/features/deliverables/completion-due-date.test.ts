import { describe, it, expect } from "vitest";
import {
  UpdateTaskStatusSchema,
  UpdateTaskStatusResponseSchema,
} from "~/domain/Deliverables";

describe("Completion Due Date Integration", () => {
  it("should validate UpdateTaskStatusSchema with due_date", () => {
    const validPayload = {
      sub_task_id: 61,
      booking_contract: 123456,
      cycle_iterator: 1,
      completion_type_id: 1,
      dc_engagement_id: 727,
      due_date: "2024-01-15",
      is_completed: true,
    };

    const result = UpdateTaskStatusSchema.safeParse(validPayload);
    expect(result.success).toBe(true);

    if (result.success) {
      expect(result.data.due_date).toBe("2024-01-15");
    }
  });

  it("should fail validation when due_date is missing", () => {
    const invalidPayload = {
      sub_task_id: 61,
      booking_contract: 123456,
      cycle_iterator: 1,
      completion_type_id: 1,
      dc_engagement_id: 727,
      // missing due_date
      is_completed: true,
    };

    const result = UpdateTaskStatusSchema.safeParse(invalidPayload);
    expect(result.success).toBe(false);
  });

  it("should validate UpdateTaskStatusResponseSchema with due_date", () => {
    const validResponse = {
      sub_task_id: 61,
      booking_contract: 123456,
      dc_user_id: 4,
      cycle_iterator: 1,
      completion_type_id: 1,
      dc_engagement_id: 727,
      due_date: "2024-01-15",
      created_by: "test@cisco.com",
      create_dtm: "2024-01-01T00:00:00",
      updated_by: null,
      update_dtm: null,
      is_completed: true,
    };

    const result = UpdateTaskStatusResponseSchema.safeParse(validResponse);
    expect(result.success).toBe(true);

    if (result.success) {
      expect(result.data.due_date).toBe("2024-01-15");
    }
  });

  it("should handle CXEA Scale collision scenario", () => {
    // Two completion requests with same logical key except due_date
    const completion1 = {
      sub_task_id: 100,
      booking_contract: 123456,
      cycle_iterator: 1, // Same cycle_iterator
      completion_type_id: 1,
      dc_engagement_id: 727,
      due_date: "2024-01-15", // Different due_date
      is_completed: true,
    };

    const completion2 = {
      sub_task_id: 100,
      booking_contract: 123456,
      cycle_iterator: 1, // Same cycle_iterator
      completion_type_id: 1,
      dc_engagement_id: 727,
      due_date: "2024-02-15", // Different due_date
      is_completed: true,
    };

    const result1 = UpdateTaskStatusSchema.safeParse(completion1);
    const result2 = UpdateTaskStatusSchema.safeParse(completion2);

    expect(result1.success).toBe(true);
    expect(result2.success).toBe(true);

    // They should have different due_dates making them unique
    if (result1.success && result2.success) {
      expect(result1.data.due_date).not.toBe(result2.data.due_date);
      expect(result1.data.due_date).toBe("2024-01-15");
      expect(result2.data.due_date).toBe("2024-02-15");
    }
  });
});