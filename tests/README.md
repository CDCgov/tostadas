# Running nf-tests Locally

This repository uses [nf-test](https://code.askimed.com/nf-test/) to test our
Nextflow pipeline. These tests are automatically run in our
[GitHub Actions](https://docs.github.com/en/actions) CI workflow
on every push and pull request.

If CI tests are failing, it's usually because snapshots are out of date
or the pipeline output has changed. This guide shows how to run them locally
and update snapshots if needed.

---

## 📦 1. Install nf-test

Install nf-test globally (only needed once):

```bash
curl -fsSL https://code.askimed.com/install/nf-test | bash
```

Make sure it's available in your PATH:

`nf-test version`

🧪 2. Run the tests

Run all tests in the tests/ folder:

`nf-test test`

Run a specific test file:

`nf-test test tests/<name_of_test>.nf.test`


📝 3. Updating snapshots

If the test output has intentionally changed, you'll need to update the saved
snapshots so the tests will pass again:

`nf-test test --update-snapshots`

Commit and push the updated .snap files.

⚙️ 4. Matching the CI environment

Our CI workflow pins the Nextflow version it uses.
To match it locally, set the same version before running tests:

`export NXF_VER=<version_used_in_CI>`


You can find this version in .github/workflows/CIi.yml (look for NXF_VER=).