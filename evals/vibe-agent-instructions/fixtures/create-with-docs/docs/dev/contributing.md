# Contributing

Developer documentation for the widget service lives in this folder.

## Local setup

Install dependencies with `npm ci`, then run `npm run lint` and
`npm run test:unit` before opening a pull request.

## Release procedure

1. Update the `version` field in `package.json`.
2. Run `npm run build` and confirm `dist/widget.js` is produced.
3. Run `npm run lint` and `npm run test:unit`.
4. Tag the release as `v<version>` and push the tag.
