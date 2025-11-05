import { IBookingsContract, IResponsibleUser } from "~/domain/Contracts";

export const useBookingWarnings = (bookings: IBookingsContract[]) => {
  const relaventBookings =
    bookings?.reduce((acc: IBookingsContract[], curr) => {
      const hasBlockOwner = curr.responsible_users.some(
        (user: IResponsibleUser) => user.is_block_owner === "T",
      );
      const endDate = curr.effective_end_date
        ? new Date(curr.effective_end_date).getTime()
        : Infinity;
      const now = new Date().getTime();
      const isExpired = now > endDate;
      if (hasBlockOwner && !isExpired) {
        acc.push(curr);
      }
      return acc;
    }, []) || [];

  const allExpired = bookings.every((booking) => {
    const now = new Date().getTime();
    const endDate = booking.effective_end_date
      ? new Date(booking.effective_end_date).getTime()
      : Infinity;
    return now > endDate;
  });
  const notBlockOwner = bookings.every((booking) =>
    booking.responsible_users.every((user) => user.is_block_owner !== "T"),
  );

  return {
    bookings: relaventBookings,
    warnings: { notBlockOwner, allExpired },
  };
};
