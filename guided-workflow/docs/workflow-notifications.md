# Workflow Notifications

The workflow feature currently fetches an array of notifications. Each notification has an assigned `engagement_id`, `dc_user_id`, and `tree_id` so ensure the correct user sees the correct notification in the correct place within the workflow UI.

Example Noticiation:

```ts
{
  tree_id: 601,
  notification_category: "error",
  subject: "SNIF Report",
  // the data key is unique and will be expanded upon below
  data: { ... },
  dc_user_id: 866,
  dc_engagement_id: 20251,
  notification_id: 3501,
  create_dtm: "2024-03-25T20:45:31.724394",
  update_dtm: null,
  created_by: "jeffryth@cisco.com",
}
```

Beyond the various IDs, each notification is assigned a `notification_category` to determine the treatment it receives within the UI.

The options for `notification_category` are `result`, `error`, or `task`. The category is used within the UI for filtering down notifications.

The notification's `data` key is unique in that it can be an object or array which will directly effect the way its data's is presented within the UI.

## Object Data

If the data is returned as an object, the object is parsed via a Zod schema based on the `eventUiEnum` (serial-tagging, customer-upload, etc) which is determined by the URL.

```ts
{
  previously_resolved: 0,
  multi_resolved: 34,
  multi_with_same_parent_id_resolved: 7,
  single_resolved: 11,
  not_tagged: 90,
}
```

After a successful parsing, the data is mapped to the screen via the object's entries.

If parsing fails, the notification's detail secion will remain blank.

## Array Data

Data returned as an array will be mapped over based on its `type`.

```ts
[
  {
    type: "message",
    data: "This is a message from the 'message' type.",
  },
  {
    type: "action",
    data: {
      label: "Check out this stuff (comes from the 'action' type with a link)",
      type: "link",
      url: "https://google.com",
    },
  },
  {
    type: "table",
    data: {
      "Label 1": "This table of values comes from the 'list' type.",
      "Label 2": "Value 2",
    },
  },
  {
    type: "action",
    data: {
      label: "Download the file (comes from the 'action' type)",
      type: "download",
      url: "https://example.com",
    },
  },
];
```

The data's `type` can currently by one of three enums: `message`, `action`, or `table`. The order of the array determines the order the information will be mapped to the screen. Given this, the backend can create "custom" UIs, albiet not increadibly complex ones.

### Message

```ts
{
  type: "message",
  data: "This is message data.",
}
```

Messages are objects with the `type` of `message` and a simple string as `data`. This message will be rendered to the string in a `p` tag.

### Action

```ts
{
  type: "action",
  data: {
    label: "Button label",
    type: "link", // type here can be either link or download
    url: "https://google.com",
  }
}
```

The Action data type renders a `Button` within the UI. This button will either act to trigger a download _or_ link the user to a new URL. This is determined by the data's type (`link` or `download`).

### List

```ts
{
  type: "list",
  data: {
    number_of_bananas: 47,
    monkey_name: "Harambe",
    description: "A very hungry animal."
  }
}
```

The List data type renders a two column `table` within the UI. The first column are the keys of the object and the second column are the related values. If the keys are written in `snake_case`, they will be parsed to replace all underscores with whitespace so as to be more human readable.

### Table

```ts
{
  type: "table",
  data: [
    {
      bananas: 47,
      name: 'Harambe',
    },
    {
      bananas: 12,
      name: 'Joe',
    },
  ]
}
```

The Table data type renders a `table` with the keys as the column headers. If the keys are written in `snake_case`, they will be parsed to replace all underscores with whitespace so as to be more human readable. Each object in the array must be identical in structure. Values are not formatted by the frontend, so anything returned will be displayed as is.
