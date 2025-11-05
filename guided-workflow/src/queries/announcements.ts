import { getAnnouncement, getAnnouncements } from "~/api/announcements";
import { announcementsQueryKeys } from "~/utils/queryKeys";

export const getAnnouncementsQuery = (dashboardView: boolean) => ({
  queryKey: announcementsQueryKeys.list(dashboardView),
  queryFn: () => getAnnouncements(dashboardView),
});

export const getAnnouncementQuery = (id: number) => ({
  queryKey: announcementsQueryKeys.detail(id),
  queryFn: () => getAnnouncement(id),
});
