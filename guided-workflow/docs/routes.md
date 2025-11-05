# Routes

This is a basic overview of our routing structure and methodology. For in-depth information on our chosen routing library visit [React Router's documentation](https://reactrouter.com/home).

**Note: We are using React Router v7 as a _library_ and not as a _framework_. However, we are otherwise primed to switch to using their framework if we found it advantagous.**

## File Structure

Our main `App` component contains a `RouterProvider` from react router. This renders all the app's routes and UI's via the `router` prop. We are providing a `Router` object with react router's `createBrowserRouter` util which takes in an array of routes.

All routes within the app are defined within the `/src/router` directory and are split into separate files by feature. Each of these "feature-based" route files are then added to the `base-routes`'s routes array.

## Loaders and Actions

React router allows for the use of route based data fetching and mutations called `loaders` and `actions`. These run outside of react's lifecycle and can be very useful in the right situations. We have chosen to use `Tanstack Query` to handle our data fetching and mutations.

We are, however, using `loaders` for redirects in specific cases. We use them for redirecting to "valid" paths and to redirect for permission based reasons.

EX:

```jsx
// the root route's first  child is the base "/" route.
{
  path: "/",
  // we should redirect to the "engagements" route since it is acting as our "landing" page
  // and we are not providing a UI element for this route
  loader: () => redirect("engagements"),
},
```

Permission based EX:

```jsx
// in this loader, we check if the user is an admin
{
  path: "some-admin-path",
  element: <SomeAdminRoute />,
  loader: () => {
    // if not, we redirect home
    if (!user?.isAdmin) {
      return redirect("/");
    }
    // if they are, we return nothing
    // loaders cannot return undefined - so we return null
    return null;
  },
  // if the user is not admin, any child routes will also be unreachable
  children: [...]
},
```

Because `loaders` are run outside of the react life-cycle, the user experience can differ from what is expected. In the above cases, the redirects are instantaneous because there are no async actions to resolve. So the user is immediately redirected without the need for a loading indicator.

**If** we add a loader with some async functions, the loader will resolve _before_ the user is routed. So some loading indication will likely need to be added globally or on the route we routing from as opposed to the route we are routing to.

## Route definitions

When setting up a new feature with new routes it may be beneficial to create a new route file.

This file should export either a single `RouteObject` or an array of `RouteObject`s depending on what makes the most sense for the feature and should be added to the base-route file as a child of the `RootRoute`.

If your route(s) need the user object to check permissions, you can create a function that takes in the `IAmplifyUser` as an arg and returns either a `RouteObject` or array of `RouteObject`s. There are several examples of this throughout the route files.

See the react router docs for more info but routes could contain any of the below items:

- **path**: the path of the route
- **index**: a boolean that, if true, lets the router know it is a `/` (base) route
- **element**: the React component to be loaded when the user visits the route.
- **loader**: useful in our app for redirects if needed
- **children**: an array of child routes
