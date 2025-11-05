import {
  getUnverifiedBookings,
  getVerifiedBookings,
} from "~/api/financial-admin";
import { IVerifiedBookingResponse } from "~/domain/admin/bookings/verifiedBooking";
import {
  unverifiedBookingsQueryKeys,
  verifiedBookingsQueryKeys,
} from "~/utils/queryKeys";

export const unverifiedBookingsQuery = {
  queryKey: unverifiedBookingsQueryKeys.lists(),
  queryFn: getUnverifiedBookings,
};

export const verifiedBookingsQuery = {
  queryKey: verifiedBookingsQueryKeys.lists(),
  queryFn: getVerifiedBookings,
};

export const selectBookingsByIssue = (data: IVerifiedBookingResponse[]) => {
  // Flag data with issues and include the issue
  // Does it have 0 assignments?

  const hasNoAssignments = (booking: IVerifiedBookingResponse) => {
    if (booking.assignments.length === 0) {
      return 1;
    }
    return 0;
  };

  // Does it have sub-allocations that do not add up to 1
  const hasSubAllocations = (booking: IVerifiedBookingResponse) => {
    const { assignments } = booking;
    if (assignments.length === 0) return 0;
    let issues = 0;
    const totalSwSubAllocations = assignments.reduce(
      (acc, curr) => acc + curr.sub_allocation_sw,
      0,
    );
    if (totalSwSubAllocations !== 1) {
      issues += 1;
    }
    const totalHwSubAllocations = assignments.reduce(
      (acc, curr) => acc + curr.sub_allocation_hw,
      0,
    );
    if (totalHwSubAllocations !== 1) {
      issues += 1;
    }
    return issues;
  };

  // Hold array of objects with position and sort value
  const mappedData = data.map((booking, index) => {
    let issues = 0;
    if (!booking.is_current_and_unassigned) {
      return {
        index,
        issues: 0,
      };
    }
    issues += hasNoAssignments(booking);
    issues += hasSubAllocations(booking);
    return {
      index,
      issues,
    };
  });

  mappedData.sort((a, b) => b.issues - a.issues);
  return mappedData.map((booking) => data[booking.index]);
};

export const getVerifiedBookingIssues = (
  data: IVerifiedBookingResponse,
): string[] | null => {
  const hasNoAssignments = (booking: IVerifiedBookingResponse) => {
    if (booking.assignments.length === 0) {
      return "Booking Has 0 Assignments";
    }
    return false;
  };

  const hasSwSubAllocations = (booking: IVerifiedBookingResponse) => {
    const { assignments } = booking;
    if (assignments.length === 0) return false;
    const totalSwSubAllocations = assignments.reduce(
      (acc, curr) => acc + curr.sub_allocation_sw,
      0,
    );
    if (totalSwSubAllocations !== 1) {
      return "SW Sub-Allocation Total != 100%";
    }
    return false;
  };

  const hasHwSubAllocations = (booking: IVerifiedBookingResponse) => {
    const { assignments } = booking;
    if (assignments.length === 0) return false;
    const totalSwSubAllocations = assignments.reduce(
      (acc, curr) => acc + curr.sub_allocation_hw,
      0,
    );
    if (totalSwSubAllocations !== 1) {
      return "HW Sub-Allocation Total != 100%";
    }
    return false;
  };

  if (data.is_current_and_unassigned === false) {
    // If the booking is not current and unassigned, it is not an issue
    return null;
  }

  const issues = [];
  issues.push(hasNoAssignments(data));
  issues.push(hasSwSubAllocations(data));
  issues.push(hasHwSubAllocations(data));
  const filteredIssues = issues.filter((issue) => issue !== false);

  if (filteredIssues.length === 0) {
    return null;
  }
  return filteredIssues as string[];
};
