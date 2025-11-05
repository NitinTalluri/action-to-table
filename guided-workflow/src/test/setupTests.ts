import "@testing-library/jest-dom";

import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll } from "vitest";

// Import MSW handlers from the mocks directory
import { handlers } from "../../mocks/handlers";

// This configures a request mocking server with the given request handlers.
const server = setupServer(...handlers);

// Establish API mocking before all tests.
beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));

// Reset any request handlers that are declared as a part of our tests
// (i.e. for testing one-off error scenarios or multiple successful responses).
afterEach(() => server.resetHandlers());

// Clean up after the tests are finished.
afterAll(() => server.close());
