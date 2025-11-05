# Queries and Mutations

This is meant to be an outline for our method of organizing code related to queries and mutations when interfacing with an API. There will be many exceptions to these rules as the app continues to grow, but this article should at least be considered as a reference when organizing new code.

This document is a review of our patterns and not a how-to for react-query. For more examples and documentation of `useQuery`, `useMutation`, and `useQueryClient` visit [Tanstack Query](https://tanstack.com/query/latest).

---

### Table of contents

- [Pre-reqs](#pre-reqs)
- [Queries](#queries-get)
- [Mutations](#mutations-post-patch-delete-etc)
- [Mocking](#mocking)

## Pre-reqs

1. Decide on a data schema with the backend or whoever feels they can confidently dictate what your data should look like.
2. Create a `zod` schema and `type` from the previously agreed upon data shape.
   1. Zod schema should live in the `domain/` folder. If no corresponding file is available within the `domain` folder, created your own.
   2. The `type` can be created with `zod`'s `infer` method. Our convention is to add a `T` at the start of types and an `I` at the start of interfaces.
   3. An example of this can be seen at `/domain/file-management`

```ts
// example file: domain/person.ts
import { z } from "zod";

export const PersonSchema = z.object({
  id: z.number(),
  name: z.string(),
  age: z.number(),
});

// Note the naming convention of type "T" Person from the "Person" Schema
export type TPerson = z.infer<typeof PersonSchema>;
```

3. Create api function
   1. Go to the correct api file found in `src/api/`. If no corresponding api file is available, create your own.
   2. Create any GET, POST, PATCH, etc requests here. The return of these functions should be validated with your previously made zod schemas. Doing so will type the function’s return so no custom types will be needed.
   - NOTE: Any response body that does not pass your zod schema's validation will throw an error. To combate this, consider adding catches to your schema.
   3. An example of this can be seen at `/src/api/file-management`

```ts
// example file: src/api/person.ts

import client, { V2_URL } from "~/app/api";
import { z } from "zod";
import { PersonSchema, type TPerson } from "~/domain/person";

// GET and POST functions can be created with the same syntax
export const getPerson = async (id: number) => {
  const response = await client.get(`${V2_URL}/person/${id}`);
  return PersonSchema.parse(response.data);
};

export const getPeople = async () => {
  const response = await client.get(`${V2_URL}/people`);
  return z.array(PersonSchema).parse(response.data);
};

export const createPerson = async (person: Omit<TPerson, "id">) => {
  const reponse = await client.post(`${V2_URL}/person/create`);
  return PersonSchema.parse(response.data);
};
```

## Queries (GET)

1. You will need to create query keys. You can do this within `src/utils/queryKeys.ts`
   1. Add a unique key to the `rootQueryKey` object.
   2. Then create and export a set of keys by creating a new variable and using the `createQueryKeys` function along with the new `rootQueryKey` you just added.

```ts
// within queryKeys.ts
export const rootQueryKey = {
  ...
  // add new key
  person: "PERSON",
};

// export new keys created with createQueryKeys function
export const personQueryKeys = createQueryKeys(rootQueryKey.person);
```

2. Create a query object to be used within the `useQuery` hook.
   1. Open the corresponding `src/queries/` file. If no file is available related to your GET request, create a new one.
   2. Create a query object that has the newly created `queryKey` and `queryFn`. If necessary, this query may need to be a function that returns an object if params like IDs are needed within your query function.
   3. An example of this can be seen at `src/queries/file-management.ts`

```ts
// example file: src/queries/person.ts

export const personQuery = (personId: number) => ({
  queryKey: personQueryKeys.detail(personId),
  queryFn: () => getPerson(personId),
});
```

3. Use this query object/function within the necessary component.
   1. Where data is needed, wrap this object/function in useQuery. Because your function was parsed with a zod schema, this query will be type safe, no additional typing is needed.
   2. An example of this can be seen at `/src/features/tml/archived-liveboards/ArchivedLiveBoards.tsx`
      1. NOTE: this example features the `select` option, this is not often needed, but shows how the query functions can be augmented if needed.

```tsx
import { useQuery } from "@tanstack/react-query";

// this hook's return object has many keys, use whatever is appropriate for your situation
const { data: person, isLoading, isFetching } = useQuery(personQuery(personId));
```

## Mutations (POST, PATCH, DELETE, ETC)

1. Mutations should be used within the `useMutation` hook.
   1. Within this hook, pass your api mutation to the `mutationFn` key.
   2. It is often desirable to invalidate a corresponding `GET` request. For example, you have a todo list, you mark an item as done, once that mutation is successful, we want to `GET` the latest todos.
      1. This can be handled with the `queryClient` provided by `useQueryClient` by using the following within the `onSettled` key: `queryClient.invalidateQueries({queryKey: <<your query key here>>})`
      2. We use onSettled as opposed to onSuccess to ensure the query is invalidated regardless of a success or error.
   3. If possible, we try to provide some optimistic UI via the `onMutate` callback.
      1. With the `queryClient`, `setQueryData` of your relevant GET request to add/remove/edit an entry.
2. This hook returns an object with a number of keys, we primarily use `mutateAsync` to call the mutation with some sort of `onSubmit` function.
3. The `mutateAsync` function should almost always be wrapped in our `toast` to properly notify the user that we have registered their request.
   1. We typically use `toast.promise()` which takes two arguments, the `mutateAsync` function and an object of loading, success, and error messages.
4. An example of this can be seen at `src/features/contract/tabs/bookings/useBookingContracts.ts`

```tsx
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createPerson } from "~/api/person";
import { personQueryKeys } from "~/utils/queryKeys";

// bring in query client for invalidation and optimistic updates
const queryClient = useQueryClient();
// set up mutation
const { mutateAsync } = useMutation({
  mutationFn: createPerson,
  onMutate: () => {
    // perform any wanted optimistic updates here
    queryClient.setQueryData(
      personQueryKeys.list(),
      (prevPersons?: TPerson[]) => {
        // ...some update
      },
    );
  },
  onSettled: () => {
    // invalidate list call after creation call ends to refetch any lists
    queryClient.invalidateQueries({ queryKey: personQueryKeys.list() });
  },
});

const onSubmit = (person: TPerson) => {
  // toast.promise will allow the toast to automatically update between loading and success/error states
  toast.promise(mutateAsync(person), {
    loading: "Creating person...",
    success: (person) => `${person.name} created!`,
    error: "Could not create person",
  });
};
```

## Mocking

We use a package called MSW to mock network requests. Their [docs are available here](https://mswjs.io).

This package is useful when the backend endpoint is not yet available, but you want to develop an end-to-end experience locally. It is also useful to test against specific response bodies.

See our `mocking.md` file for further information on how to set this up locally within the frontend
