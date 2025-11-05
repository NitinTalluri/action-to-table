import {
  getActiveDeliverables,
  getClosedDeliverables,
  getDeliverables,
  getScheduledDeliverables,
} from "~/api/deliverables";
import {
  activeDeliverablesQueryKeys,
  closedDeliverablesQueryKeys,
  deliverablesQueryKeys,
  scheduledDeliverablesQueryKeys,
} from "~/utils/queryKeys";

type TSortableDeliverable = {
  task_desc: string;
  due_date: string;
};

type TSortableTasks = {
  sort_date: string | null;
  sub_task_id: number;
};

const compareDates = (a: Date, b: Date) => {
  const aDetail = {
    year: a.getUTCFullYear(),
    month: a.getUTCMonth(),
    day: a.getUTCDay(),
  };

  const bDetail = {
    year: b.getUTCFullYear(),
    month: b.getUTCMonth(),
    day: b.getUTCDay(),
  };

  if (
    aDetail.day === bDetail.day &&
    aDetail.month === bDetail.month &&
    aDetail.year === bDetail.year
  ) {
    return 0;
  }

  return a.getTime() < b.getTime() ? -1 : 1;
};

const selectSortedDeliverables = <T extends TSortableDeliverable>(
  data: T[],
) => {
  return data.sort((a, b) => {
    const dueDateA = a.due_date ? new Date(a.due_date) : new Date();
    const dueDateB = b.due_date ? new Date(b.due_date) : new Date();

    const comparison = compareDates(dueDateA, dueDateB);

    if (comparison === 0) {
      return a.task_desc < b.task_desc ? -1 : 1;
    }

    return comparison;
  });
};

const selectSortedTasks = <T extends TSortableTasks>(data: T[]) => {
  return data.sort((a, b) => {
    const sortDateA = a.sort_date ? new Date(a.sort_date) : new Date();
    const sortDateB = b.sort_date ? new Date(b.sort_date) : new Date();

    const comparison = compareDates(sortDateA, sortDateB);

    if (comparison === 0) {
      return a.sub_task_id < b.sub_task_id ? -1 : 1;
    }

    return comparison;
  });
};

export const deliverablesQuery = (engagementID: number) => ({
  queryKey: deliverablesQueryKeys.list(engagementID),
  queryFn: () => getDeliverables(engagementID),
});

export const scheduledDeliverablesQuery = (engagementID: number) => ({
  queryKey: scheduledDeliverablesQueryKeys.list(engagementID),
  queryFn: () => getScheduledDeliverables(engagementID),
  select: (data: Awaited<ReturnType<typeof getScheduledDeliverables>>) => {
    const sortedData = selectSortedDeliverables(data);
    const sortedTasks = sortedData.map((d) => {
      d.tasks = selectSortedTasks(d.tasks);
      return d;
    });

    return sortedTasks;
  },
});

export const activeDeliverablesQuery = (engagementID: number) => ({
  queryKey: activeDeliverablesQueryKeys.list(engagementID),
  queryFn: () => getActiveDeliverables(engagementID),
  select: (data: Awaited<ReturnType<typeof getActiveDeliverables>>) => {
    const sortedData = selectSortedDeliverables(data);
    const sortedTasks = sortedData.map((d) => {
      d.tasks = selectSortedTasks(d.tasks);
      return d;
    });

    return sortedTasks;
  },
});

export const closedDeliverablesQuery = (engagementID: number) => ({
  queryKey: closedDeliverablesQueryKeys.list(engagementID),
  queryFn: () => getClosedDeliverables(engagementID),
  select: (data: Awaited<ReturnType<typeof getClosedDeliverables>>) => {
    const sortedData = selectSortedDeliverables(data);
    const sortedTasks = sortedData.map((d) => {
      d.tasks = selectSortedTasks(d.tasks);
      return d;
    });

    return sortedTasks;
  },
});
