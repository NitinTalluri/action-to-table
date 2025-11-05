# Workflow Tree Proposal

## API Endpoints

### GET Nav tree shape (left side bar)

`/api/v2/workflows/actions`

This endpoint fetches the shape of the nav tree to be displayed.

```ts
type WorkflowTree = Array<{
  tree_id: number;
  action_label: string; // to be displayed in the UI
  ui_enum:
    | "log-signoff"
    | "instance-tagging"
    | "serial-tagging"
    | "generate-docusign-scope"
    | "customer-upload"
    | "snif-report"
    | null; // an optional key used to determine which, if any, UI route should be displayed
  child_ids: Array<number>; // used by the UI to determine parent-child relationships to properly nest elements
}>;
```

### GET Notifications

`/api/v2/workflows/notifications`

This endpoint fetches any notifications used to "decorate" the workflow tree.

```ts
type Notifications = Array<{
  notification_id: number;
  tree_id: number; // corresponds with the tree id to pair notification within the UI
  notification_category: "result" | "error" | "task";
  message: string;
  created_dtm: string;
  update_dtm: string | null;
}>;
```

## UI Elements

Within the UI, we will create a number of routes and components. Each route will correspond with a `ui_enum`.

```tsx
<>
  <Route path="/workflows/:engagementId" element={<WorkflowScreen />}>
    <Route path="log-signoff" element={<LogSignOffRoute />} />
    {/* etc etc... */}
  </Route>
</>
```
