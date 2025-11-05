import { z } from "zod";

export const AnnouncementCategoryEnums = z.enum([
  "Bugs",
  "Campaigns",
  "Training Requirements",
  "Releases",
  "General",
  "Alerts",
  "Process / SDP Changes",
]);

export const AnnouncementSchema = z.object({
  id: z.number(),
  title: z.string(),
  subtitle: z.string(),
  body: z.string(),
  priority: z.number(),
  category: AnnouncementCategoryEnums,
  push_date: z.string(),
  expiration_date: z.string(),
  is_dismissed_by_user: z.boolean(),
  audience: z.array(z.string()),
  links: z.array(
    z.object({
      id: z.number().nullish(),
      name: z.string(),
      href: z.string(),
    }),
  ),
});

export type TAnnouncement = z.infer<typeof AnnouncementSchema>;

export const AnnouncementRequestSchema = z.object({
  title: z.string(),
  subtitle: z.string(),
  body: z.string(),
  priority: z.number(),
  category: z.string(),
  push_date: z.string(),
  audience: z.array(z.string()),
  expiration_date: z.string(),
  links: z.array(
    z.object({
      id: z.number().nullish(),
      name: z.string(),
      href: z.string(),
    }),
  ),
});

export type TAnnouncementRequest = z.infer<typeof AnnouncementRequestSchema>;
