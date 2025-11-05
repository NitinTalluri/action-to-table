# CAM Guided workflow

## TODOs

Verified bookings directory should be deleted once the claimed bookings feature is complete

## Description

App consists of two main views, One to manage tasks and one to manage templates. The task are going to be pulled from a
queue based on the value_points field. Tasks view consist of two main components, the reference header and a table.

Header component takes reference data from the task data, and has two grids, the template reference data grid, which
grabs its data and configuration from the template and the reference grid which, while it takes its box sizes from the
template, it grabs the data from the instace data.

Template view lets the user view, add and edit the templates stored in the dynamoDB table.

## Deployment

### Environment

A quick note about environment variables and how they are used in javascript. As javascript is a client side language,
environment variables are not available to the client. A common pattern is to use environment variables to configure
your application at build time. For us, this happens during the CodeBuild stage of the pipeline.

With `vite`, anytime we would like to add an environment variable, we must prefix it with `VITE_`.
To reference the environment variable in our code, we would use `import.meta.env.VITE_MY_ENV_VAR`. This should not
include any sensitive information as it will be available to the client.

Any change to the environment variables will require a rebuild of the application.

This project is configured to use three different environments:

- Local Development
  - Uses localhost:3000 and proxies to localhost:8080 for API calls
  - Uses Dev AWS Amplify
  - Configure using a .env.local file
- Development
  - Uses Dev AWS Amplify
  - CodeBuild [datacanvas-frontend](https://us-east-1.console.aws.amazon.com/codesuite/codebuild/837578041534/projects/datacanvas-frontend/) will reference **buildspec.dev.yml**
  - The Dev Env Variables are currently coded in the buildspec.dev.yml file
- Production
  - Uses Prod AWS Amplify
  - CodeBuild [datacanvas-frontend-prod](https://us-east-1.console.aws.amazon.com/codesuite/codebuild/837578041534/projects/datacanvas-frontend-prod) will reference **buildspec.yml**
  - The Prod Env Variables are currently coded in the buildspec.yml file

### Pipeline

1. Production builds will listen to the master branch and will be deployed to the production environment.
2. Development builds will listen to the develop branch and will be deployed to the development environment.

Feature branches should be merged into the develop branch. The develop branch should be merged into the master branch
when ready for production.

After building, the Kubernetes cluster (dev or prod) will require a manual deployment to update the application. To do this,
delete the existing pod, and kube will create a new one with the latest image.

There may be a time delay between the 'latest' image being available and which image is being used by the pod. Keep this
in mind when deploying.

## Task and Templates

Templates tell guided workflow how to display task data and what you can do with it. Let's go over our example
at/src/templates/template.json.

```json
  "id": "4646",
"data_color_scheme": "default",
"top_actions": ["helloWorld"],
"bottom_actions": ["fooBar"],
```

## Available Scripts

In the project directory, you can run:

### `npm install`

### `npm run dev`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### Running with Docker

Run the app in Docker by running the following commands.

Ensure you have run `docker login` to access the private docker registry.

```sh
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 837578041534.dkr.ecr.us-east-1.amazonaws.com
```

```sh
docker build . -t guided-workflow

docker run -p 3000:80 -d guided-workflow
```

Now open the app at `http://localhost:3000` and you will be good to go.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more
information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**
