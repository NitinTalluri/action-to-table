# Mocking

Mocking data can be a very useful step in our development process. Especially if the backend is unable to immediately supply an endpoint with data. To prevent slowdown, we can instead write a contract with the backend and then mock the data locally so that the frontend may continue its progress.

**NOTE: This document will have some overlap with the "Queries and Mutation" document as data fetching and mocking are heavily entwined. For further information on our fetching and mutation strategy, it is highly advised to read that document after this one.**

## Developing a Contract

The first step is to develop a contract with the backend so that you both can work towards the same data structure. Ideally, business requirements have been fully fleshed out by this point. If not, time should be taken to fully explore those. Sometimes writing the contract in tandem has the added benfit of exposing weaknesses in the understanding of the request from business or business not fully understanding all the steps required to acheive a given feature request.

The result of writing the contract should leave frontend, backend, and the business side with a clear understanding of exactly what data is needed to achieve the feature requested.

**Note: Subtle contract changed should be expected along the way, but repeated major updates to a contract is a good sign that business logic is not fully fleshed out or there has been a fundamental misunderstanding amungst devs or between devs and business.**

## Writing the Contract

The contract should be written in a format that both the frontend and backend can understand. Within our project, we are all familar with TypeScript so it has historically been the go to language. Specifially, we often write our contracts with a `Zod` schema as it helps specify additional business rules that TypeScript along cannot, such as a minimum or maximum value on a field for example.

EX:

```ts
// The Zod schema can later be used to validate incoming data from the API
const MyExampleSchema = z.object({
  title: z.string(),
  id: z.number(),
  last_updated: z.string().nullish(),
  type: z.union([z.literal("new"), z.literal("updated")]),
});

// Zod has a helper to infer types of schemas
type TMyExample = z.infer<typeof MyExampleSchema>;
```

## Mocking the Data with MSW

We use the `msw` (Mock Service Worker) package to handle mocking API calls. This allows for the frontend to write code as if we had a real endpoint in place so very little revision is needed when the real endpoint becomes available.

Within the root directory of the application create a `mocks` folder with a `worker.ts` file within. This `worker` file will be used to serve your mock API requests.

Then, run `npm run init-msw` to initialize the package locally.

**NOTE: For full docs and examples of the msw package, [visit their documentation here](https://mswjs.io).**

### Worker file

The `worker` file should export a `worker` which is created with `msw`'s `setWorker` util.

EXAMPLE of an exported worker:

```ts
import { http, passthrough } from "msw";
import { setupWorker } from "msw/browser";

// handlers are an array of mocked http requests/API endpoints
const handlers = [
  // we return a passthrough for all so that we can still hit real API endpoints as expected
  http.all("/*", () => {
    return passthrough();
  }),
];

export const worker = setupWorker(...handlers);
```

### Handlers

The msw package can fully mock an api request as if we were building a Node API within the frontend.

EXAMPLE:

```ts
import { http, HttpResponse, passthrough } from "msw";
import { setupWorker } from "msw/browser";
import { V2_URL } from "~/app/api";

// A handy util to create the appearance of loading/fetching within the UI
const sleep = (ms?: number) =>
  new Promise((resolve) => setTimeout(resolve, ms || 300));

const handlers = [
  // The /my-endpoint/:myParam function can easily be abstracted into its own function for a cleaner look
  http.get(`${V2_URL}/my-endpoint/:myParam`, ({cookies, params, request, requestId}) => {
    // params can be used to taylor an individual response, if needed
    const { myParam } = params

    // without this sleep util, the request will resolve immediatly and unrealistically.
    // this func is useful to ensure your UI correctly handles loading states
    sleep(500)

    // if the request body needs to be parsed, it is available to do so
    // cookies and the requestId are also available

    // We can type our data to make sure the UI will receive exactly what is expected
    const data: TMyExample[] = [
      {
        title: "example",
        id: 1,
        last_updated: null,
        type: "new",
      },
      {
        title: "another example",
        id: 2,
        last_updated: "11-02-2024",
        type: "updated",
      },
    ]

    return HttpResponse.json(data)
  })
  // ... other handlers
  http.all("/*", () => {
    return passthrough();
  }),
]
```

The `http` object from `msw` has an HTTP request handler for each type (GET, POST, PUT, etc). [See their docs for more examples](https://mswjs.io).

## Conclusion

With endpoints fully mocked, the frontend can then worry about the UI and UX of a given feature. When the real endpoint becomes available, all we have to do to use it is remove our mocked endpoint from our `worker`. If the contracts have been upheld it should be a painless transition from mocked to real data.

If contracts have shifted during development, it will likely be immediately obvious due to typescript and runtime errors and necessitate changes on either the frontend, backend, or both. If this happens, usually the fix is as simple as renaming a key on a response object, but if there is a major difference between the frontend's mock and the backend's response it likely means that the initial contract was not fully talked through and assumptions were made in isolation on one side or another.
